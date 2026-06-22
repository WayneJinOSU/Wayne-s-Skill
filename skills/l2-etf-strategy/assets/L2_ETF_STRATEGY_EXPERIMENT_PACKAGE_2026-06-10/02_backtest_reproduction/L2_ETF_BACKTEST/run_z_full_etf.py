#!/usr/bin/env python3
"""Z — E12.7.2 ADAPTIVE on FULL ETF universe (623 ETFs).

Pool selection AT EACH REBAL POINT t (NO LOOK-AHEAD):
  - Listed at least 130 days before t (so 120d momentum is valid)
  - Trailing 60-day avg daily AMOUNT >= ADV_MIN at t (liquidity filter, pure backward-looking)

Strategy = E12.7.2 ADAPTIVE:
  - HS300 regime (close vs MA60 + slope)
  - TREND -> pick Top-K by 120d momentum
  - REVERSAL -> pick Bottom-K by 120d momentum
  - Equal-weight quarterly rebalance

Also runs TRD_only and REV_only baselines for comparison.
"""
import json, csv
from pathlib import Path
import pandas as pd
import numpy as np
from collections import defaultdict

Y = Path("/home/mira/files/experiments_archive/Y_l2_etf_mapping_20260529")
CACHE = Y / "kline_cache_all"
OUT = Y / "baselines_full"; OUT.mkdir(exist_ok=True)
HS300 = "/home/mira/files/e12_narrative/data/hs300_daily.csv"

START = "2024-01-31"
END   = "2026-05-26"
INIT_CASH = 200_000.0
FEE = 0.001
ADV_MIN_LIST = [5e6, 20e6, 50e6]   # 5M / 20M / 50M yuan
TOPK_LIST = [10, 20, 30]
REBAL = ["2024-01-31","2024-04-30","2024-07-31","2024-10-31",
         "2025-01-31","2025-04-30","2025-07-31","2025-10-31","2026-01-31"]

# Load pool
with (Y/"all_etf_pool.csv").open() as f:
    pool = [(r['code'], r['name']) for r in csv.DictReader(f)]
codes = [c for c,_ in pool]
name_map = dict(pool)

# Load each ETF
print(f'Loading {len(codes)} ETFs...')
code_data = {}
for c in codes:
    p = CACHE / f"{c}.json"
    if not p.exists(): continue
    d = json.loads(p.read_text())
    if not d: continue
    df = pd.DataFrame(d)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    code_data[c] = df
print(f'  Loaded {len(code_data)} ETFs')

# Load HS300
hs = pd.read_csv(HS300)
hs['date'] = pd.to_datetime(hs['date'])
hs = hs.sort_values('date').reset_index(drop=True)
hs['ma60'] = hs['close'].rolling(60).mean()
hs['ma60_slope'] = (hs['ma60']/hs['ma60'].shift(60) - 1) * 100

def regime_at(d):
    s = hs[hs['date'] <= pd.Timestamp(d)]
    if s.empty: return "REVERSAL"
    last = s.iloc[-1]
    if pd.isna(last['ma60']) or pd.isna(last['ma60_slope']): return "REVERSAL"
    return "TREND" if (last['close']>last['ma60'] and last['ma60_slope']>0) else "REVERSAL"

def pool_at(cutoff_str, adv_min):
    """Pool eligible at cutoff: listed >=130d AND trailing 60d avg AMOUNT (vol*close) >= adv_min."""
    cutoff = pd.Timestamp(cutoff_str)
    eligible = []
    for c, df in code_data.items():
        snap = df[df['date'] <= cutoff]
        if len(snap) < 130: continue  # need 120d momentum
        tail = snap.tail(60)
        adv = (tail['volume'] * tail['close'] * 100).mean()  # vol(手) * 100 * price = yuan amount
        if adv < adv_min: continue
        eligible.append((c, adv))
    return eligible

def signal_topk(cutoff_str, mode, k, adv_min):
    cutoff = pd.Timestamp(cutoff_str)
    pool_e = pool_at(cutoff_str, adv_min)
    if not pool_e: return []
    rows = []
    for c, _ in pool_e:
        snap = code_data[c][code_data[c]['date'] <= cutoff]
        if len(snap) < 121: continue
        ret = snap.iloc[-1]['close'] / snap.iloc[-120]['close'] - 1
        rows.append((c, ret))
    df = pd.DataFrame(rows, columns=['code','ret'])
    if mode == "REVERSAL":
        return df.nsmallest(k, 'ret')['code'].tolist()
    else:
        return df.nlargest(k, 'ret')['code'].tolist()

def market_all(cutoff_str, k, adv_min):
    """Buy ALL ETFs passing pool_at filter at cutoff, equal weight."""
    return [c for c,_ in pool_at(cutoff_str, adv_min)]

# Align rebal to first trading day >= target
def first_td_geq(t_str):
    t = pd.Timestamp(t_str)
    cal = next(iter(code_data.values()))
    cands = cal[cal['date'] >= t]
    return cands.iloc[0]['date'].strftime('%Y-%m-%d') if len(cands) else None

real_rebal = [first_td_geq(d) for d in REBAL]
print('Rebal dates (aligned):', real_rebal)
print('Regime sequence:')
for r in real_rebal:
    print(f"  {r}  {regime_at(r):<9s}")

# Daily price matrix (close only, indexed by date_str)
print('Building price matrix...')
price_at = defaultdict(dict)
for c, df in code_data.items():
    for _, r in df.iterrows():
        if pd.Timestamp(START) <= r['date'] <= pd.Timestamp(END):
            price_at[r['date'].strftime('%Y-%m-%d')][c] = float(r['close'])

# === Trading simulator ===
def rebalance(cash, holdings, dp, targets, equity):
    fee = 0.0
    tset = set(targets)
    # sell non-targets
    for c in list(holdings.keys()):
        if c not in tset and c in dp:
            q = holdings[c]; px = dp[c]
            proc = q * px
            cash += proc * (1-FEE); fee += proc * FEE
            del holdings[c]
    n = sum(1 for c in targets if c in dp)
    if n == 0: return cash, holdings, fee
    w = 1.0 / n
    tqty = {}
    for c in targets:
        if c not in dp: continue
        budget = equity * w
        lot = dp[c] * 100
        q = int(budget / lot) * 100
        tqty[c] = q
    # sell excess
    for c in list(holdings.keys()):
        if c in tqty and holdings[c] > tqty[c]:
            d = holdings[c]-tqty[c]; px = dp[c]
            proc = d*px
            cash += proc*(1-FEE); fee += proc*FEE
            holdings[c] = tqty[c]
            if holdings[c]==0: del holdings[c]
    # buy short
    for c, tq in tqty.items():
        cur = holdings.get(c, 0)
        if tq > cur:
            d = tq - cur; px = dp[c]; cost = d*px; tot = cost*(1+FEE)
            if cash >= tot:
                cash -= tot; fee += cost*FEE; holdings[c] = cur + d
            else:
                aff = int(cash / (px*100*(1+FEE)))
                if aff > 0:
                    q = aff*100; cost = q*px
                    cash -= cost*(1+FEE); fee += cost*FEE
                    holdings[c] = cur + q
    return cash, holdings, fee

def equity_total(cash, holdings, dp):
    e = cash
    for c, q in holdings.items():
        if c in dp: e += q * dp[c]
    return e

def run(name, picker, k, adv_min):
    cash = INIT_CASH; holdings = {}; curve = []; total_fee = 0; rlog = []
    idx = 0
    days = sorted(price_at.keys())
    for day in days:
        dp = price_at[day]
        if idx < len(real_rebal) and day >= real_rebal[idx]:
            cutoff = real_rebal[idx]
            picks = picker(cutoff, k, adv_min)
            eq = equity_total(cash, holdings, dp)
            cash, holdings, fee = rebalance(cash, holdings, dp, picks, eq)
            total_fee += fee
            rlog.append({"date":day,"cutoff":cutoff,"regime":regime_at(cutoff),
                         "n_picks":len(picks),"picks":",".join(picks[:30])})
            idx += 1
        curve.append({"date":day,"equity":equity_total(cash, holdings, dp),
                      "cash":cash, "n_pos":len(holdings)})
    pd.DataFrame(curve).to_csv(OUT/f"equity_{name}.csv", index=False)
    pd.DataFrame(rlog).to_csv(OUT/f"rebal_{name}.csv", index=False)
    return curve, rlog, total_fee

def summarize(name, curve, fee):
    init = INIT_CASH
    final = curve[-1]["equity"]
    peak = max(p["equity"] for p in curve)
    pkd = [p["date"] for p in curve if p["equity"]==peak][0]
    rmax=0; mdd=0
    for p in curve:
        e = p["equity"]
        if e>rmax: rmax = e
        if rmax>0:
            dd = (e-rmax)/rmax
            if dd<mdd: mdd = dd
    tot = (final/init-1)*100
    days = len(curve)
    years = days/252.0
    cagr = ((final/init)**(1/years)-1)*100
    cal = -tot/(mdd*100) if mdd<0 else float('inf')
    print(f"  {name:36s} Fin:{final:>10,.0f} Ret:{tot:+7.2f}% MDD:{mdd*100:+7.2f}% CAGR:{cagr:+6.2f}% Cal:{cal:5.2f} Fee:{fee:,.0f}")
    return {"name":name,"final":final,"tot_ret":tot,"mdd":mdd*100,"cagr":cagr,"calmar":cal,"fee":fee}

# === Run ===
print(f'\n{"="*130}\nZ — Full ETF universe ({len(code_data)} candidates) | ADV filter sweep\n{"="*130}\n')
results = []
for adv in ADV_MIN_LIST:
    adv_tag = f"ADV{int(adv/1e6)}M"
    # Print pool size at each rebal for this ADV
    print(f"\n--- {adv_tag} ---")
    for r in real_rebal:
        pe = pool_at(r, adv)
        print(f"  {r} regime={regime_at(r):<9s} eligible={len(pe)}")
    for k in TOPK_LIST:
        sims = {
            f"MARKET_{adv_tag}":       (lambda d,k_,a_=adv: market_all(d,k_,a_), None),
            f"TRD_K{k}_{adv_tag}":     (lambda d,k_,a_=adv: signal_topk(d,"TREND",k_,a_), k),
            f"REV_K{k}_{adv_tag}":     (lambda d,k_,a_=adv: signal_topk(d,"REVERSAL",k_,a_), k),
            f"ADAPT_K{k}_{adv_tag}":   (lambda d,k_,a_=adv: signal_topk(d, regime_at(d), k_, a_), k),
        }
        for nm, (fn, kk) in sims.items():
            if nm.startswith("MARKET") and any(r['name']==nm for r in results): continue  # dedupe
            curve, rlog, fee = run(nm, fn, k, adv)
            results.append(summarize(nm, curve, fee))
        print()

with (OUT/"z_summary.csv").open('w',newline='') as f:
    w = csv.DictWriter(f, fieldnames=["name","final","tot_ret","mdd","cagr","calmar","fee"])
    w.writeheader()
    for r in results: w.writerow(r)
print(f'\nSaved {len(results)} results to baselines_full/z_summary.csv')

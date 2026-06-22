#!/usr/bin/env python3
"""Z-50K — Same matrix as Z but with INIT_CASH = 50,000 (vs 200,000 baseline).
Goal: measure capital scale effect — does small capital + 100-share lot cause
allocation drag (high-priced ETF gets 0 shares, low-priced ETF eats >1/K weight)?

Also adds:
 - forward-fill LAST_PX (matches Z2/Z3 fix; Z original lacked this)
 - per-rebal diagnostics: n_picks_in_dp, n_actually_held, leftover_cash_pct, min/max weight
"""
import json, csv
from pathlib import Path
import pandas as pd
import numpy as np
from collections import defaultdict

Y = Path("/home/mira/files/experiments_archive/Y_l2_etf_mapping_20260529")
CACHE = Y / "kline_cache_all"
OUT = Y / "baselines_50k"; OUT.mkdir(exist_ok=True)
HS300 = "/home/mira/files/e12_narrative/data/hs300_daily.csv"

START = "2024-01-31"
END   = "2026-05-26"
INIT_CASH = 50_000.0          # ★ 5万 vs 原 20万
FEE = 0.001
ADV_MIN_LIST = [5e6, 20e6, 50e6]
TOPK_LIST = [10, 20, 30]
REBAL = ["2024-01-31","2024-04-30","2024-07-31","2024-10-31",
         "2025-01-31","2025-04-30","2025-07-31","2025-10-31","2026-01-31"]

with (Y/"all_etf_pool.csv").open() as f:
    pool = [(r['code'], r['name']) for r in csv.DictReader(f)]
codes = [c for c,_ in pool]
name_map = dict(pool)

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
    cutoff = pd.Timestamp(cutoff_str)
    eligible = []
    for c, df in code_data.items():
        snap = df[df['date'] <= cutoff]
        if len(snap) < 130: continue
        tail = snap.tail(60)
        adv = (tail['volume'] * tail['close'] * 100).mean()
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
    return [c for c,_ in pool_at(cutoff_str, adv_min)]

def first_td_geq(t_str):
    t = pd.Timestamp(t_str)
    cands = hs[hs['date'] >= t]
    return cands.iloc[0]['date'].strftime('%Y-%m-%d') if len(cands) else None

real_rebal = [first_td_geq(d) for d in REBAL]

print('Building price matrix...')
price_at = defaultdict(dict)
for c, df in code_data.items():
    for _, r in df.iterrows():
        if pd.Timestamp(START) <= r['date'] <= pd.Timestamp(END):
            price_at[r['date'].strftime('%Y-%m-%d')][c] = float(r['close'])

LAST_PX = {}

def rebalance(cash, holdings, dp, targets, equity):
    fee = 0.0
    tset = set(targets)
    for c in list(holdings.keys()):
        if c not in tset and c in dp:
            q = holdings[c]; px = dp[c]
            proc = q * px
            cash += proc * (1-FEE); fee += proc * FEE
            del holdings[c]
    n = sum(1 for c in targets if c in dp)
    if n == 0: return cash, holdings, fee, {"n_target":0}
    w = 1.0 / n
    tqty = {}
    zero_alloc = []  # codes whose budget can't afford 1 lot
    for c in targets:
        if c not in dp: continue
        budget = equity * w
        lot = dp[c] * 100
        q = int(budget / lot) * 100
        tqty[c] = q
        if q == 0:
            zero_alloc.append((c, dp[c]))
    for c in list(holdings.keys()):
        if c in tqty and holdings[c] > tqty[c]:
            d = holdings[c]-tqty[c]; px = dp[c]; proc = d*px
            cash += proc*(1-FEE); fee += proc*FEE
            holdings[c] = tqty[c]
            if holdings[c]==0: del holdings[c]
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
    diag = {
        "n_target": n,
        "n_held": len(holdings),
        "n_zero_alloc": len(zero_alloc),
        "cash_pct": cash / equity * 100 if equity > 0 else 0,
    }
    return cash, holdings, fee, diag

def equity_total(cash, holdings, dp):
    e = cash
    for c, q in holdings.items():
        if c in dp:
            LAST_PX[c] = dp[c]
            e += q * dp[c]
        elif c in LAST_PX:
            e += q * LAST_PX[c]
    return e

def run(name, picker, k, adv_min):
    global LAST_PX
    LAST_PX = {}
    cash = INIT_CASH; holdings = {}; curve = []; total_fee = 0; rlog = []
    idx = 0
    days = sorted(price_at.keys())
    for day in days:
        dp = price_at[day]
        for c, px in dp.items():
            LAST_PX[c] = px
        if idx < len(real_rebal) and day >= real_rebal[idx]:
            cutoff = real_rebal[idx]
            picks = picker(cutoff, k, adv_min)
            eq = equity_total(cash, holdings, dp)
            cash, holdings, fee, diag = rebalance(cash, holdings, dp, picks, eq)
            total_fee += fee
            rlog.append({"date":day,"cutoff":cutoff,"regime":regime_at(cutoff),
                         "n_picks":len(picks), "n_held":diag.get("n_held",0),
                         "n_zero_alloc":diag.get("n_zero_alloc",0),
                         "cash_pct":round(diag.get("cash_pct",0),2),
                         "equity":round(eq,0)})
            idx += 1
        curve.append({"date":day,"equity":equity_total(cash, holdings, dp),
                      "cash":cash, "n_pos":len(holdings)})
    pd.DataFrame(curve).to_csv(OUT/f"equity_{name}.csv", index=False)
    pd.DataFrame(rlog).to_csv(OUT/f"rebal_{name}.csv", index=False)
    return curve, rlog, total_fee

def summarize(name, curve, fee, rlog):
    init = INIT_CASH
    final = curve[-1]["equity"]
    rmax=0; mdd=0
    for p in curve:
        e = p["equity"]
        if e>rmax: rmax = e
        if rmax>0:
            dd = (e-rmax)/rmax
            if dd<mdd: mdd = dd
    tot = (final/init-1)*100
    years = len(curve)/252.0
    cagr = ((final/init)**(1/years)-1)*100 if final>0 else -100
    cal = -tot/(mdd*100) if mdd<0 else float('inf')
    avg_cash_pct = np.mean([r.get("cash_pct",0) for r in rlog]) if rlog else 0
    avg_zero = np.mean([r.get("n_zero_alloc",0) for r in rlog]) if rlog else 0
    print(f"  {name:30s} Fin:{final:>9,.0f} Ret:{tot:+7.2f}% MDD:{mdd*100:+6.2f}% Cal:{cal:5.2f} "
          f"AvgCash:{avg_cash_pct:5.2f}% AvgZeroAlloc:{avg_zero:4.1f}")
    return {"name":name,"final":final,"tot_ret":tot,"mdd":mdd*100,"cagr":cagr,
            "calmar":cal,"fee":fee,"avg_cash_pct":avg_cash_pct,"avg_zero_alloc":avg_zero}

print(f'\n{"="*135}\nZ-50K — Capital sweep (INIT={INIT_CASH:,.0f})  '
      f'window 2024-01 → 2026-05  full {len(code_data)} ETF universe\n{"="*135}')
results = []
for adv in ADV_MIN_LIST:
    tag = f"ADV{int(adv/1e6)}M"
    print(f"\n--- {tag} ---")
    for k in TOPK_LIST:
        sims = {
            f"MARKET_{tag}":      (lambda d,k_,a_=adv: market_all(d,k_,a_), None),
            f"TRD_K{k}_{tag}":    (lambda d,k_,a_=adv: signal_topk(d,"TREND",k_,a_), k),
            f"REV_K{k}_{tag}":    (lambda d,k_,a_=adv: signal_topk(d,"REVERSAL",k_,a_), k),
            f"ADAPT_K{k}_{tag}":  (lambda d,k_,a_=adv: signal_topk(d, regime_at(d), k_, a_), k),
        }
        for nm, (fn, kk) in sims.items():
            if nm.startswith("MARKET") and any(r['name']==nm for r in results): continue
            curve, rlog, fee = run(nm, fn, k, adv)
            results.append(summarize(nm, curve, fee, rlog))
        print()

with (OUT/"z_50k_summary.csv").open('w',newline='') as f:
    w = csv.DictWriter(f, fieldnames=["name","final","tot_ret","mdd","cagr","calmar","fee",
                                       "avg_cash_pct","avg_zero_alloc"])
    w.writeheader()
    for r in results: w.writerow(r)
print(f'\nSaved to baselines_50k/z_50k_summary.csv')

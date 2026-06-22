#!/usr/bin/env python3
"""Z3 — Same ADAPTIVE/TRD/REV sweep on 2023-01-31 → 2023-12-29 only (4 quarters).
2023: HS300 -11.7%, MDD -21.5%, 4/4 REVERSAL regime, pool 已成熟 (140-160 @ ADV5M).
Clean bear year test, much less data-coverage issue than Z2.
"""
import json, csv
from pathlib import Path
import pandas as pd
import numpy as np
from collections import defaultdict

Y = Path("/home/mira/files/experiments_archive/Y_l2_etf_mapping_20260529")
CACHE = Y / "kline_cache_all"
OUT = Y / "baselines_z3"; OUT.mkdir(exist_ok=True)
HS300 = "/home/mira/files/e12_narrative/data/hs300_daily.csv"

START = "2023-01-31"
END   = "2023-12-29"
INIT_CASH = 200_000.0
FEE = 0.001
ADV_MIN_LIST = [5e6, 20e6, 50e6]
TOPK_LIST = [10, 20, 30]
REBAL = ["2023-01-31","2023-04-28","2023-07-31","2023-10-31"]

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

def regime_info(d):
    s = hs[hs['date'] <= pd.Timestamp(d)]
    if s.empty: return ""
    last = s.iloc[-1]
    return f"close={last['close']:.0f}, ma60={last['ma60']:.0f}, slope={last['ma60_slope']:+.1f}%"

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
print('\nRebal calendar:')
for r0, r1 in zip(REBAL, real_rebal):
    print(f'  intended {r0} -> actual {r1}  regime={regime_at(r1)}  {regime_info(r1)}')

print('\nBuilding price matrix...')
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
    if n == 0: return cash, holdings, fee
    w = 1.0 / n
    tqty = {}
    for c in targets:
        if c not in dp: continue
        budget = equity * w
        lot = dp[c] * 100
        q = int(budget / lot) * 100
        tqty[c] = q
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
    return cash, holdings, fee

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
    print(f"  {name:36s} Fin:{final:>10,.0f} Ret:{tot:+7.2f}% MDD:{mdd*100:+7.2f}% CAGR:{cagr:+6.2f}% Cal:{cal:5.2f} Fee:{fee:,.0f}")
    return {"name":name,"final":final,"tot_ret":tot,"mdd":mdd*100,"cagr":cagr,"calmar":cal,"fee":fee}

print(f'\n{"="*130}\nZ3 — Full ETF universe 2023-01 → 2023-12 (PURE BEAR YEAR, 4 REVERSAL quarters)\n{"="*130}\n')
results = []
for adv in ADV_MIN_LIST:
    tag = f"ADV{int(adv/1e6)}M"
    print(f"\n--- {tag} ---")
    for r in real_rebal:
        pe = pool_at(r, adv)
        print(f"  {r} regime={regime_at(r):<9s} eligible={len(pe)}")
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
            results.append(summarize(nm, curve, fee))
        print()

with (OUT/"z3_summary.csv").open('w',newline='') as f:
    w = csv.DictWriter(f, fieldnames=["name","final","tot_ret","mdd","cagr","calmar","fee"])
    w.writeheader()
    for r in results: w.writerow(r)
print(f'\nSaved to baselines_z3/z3_summary.csv')

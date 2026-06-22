#!/usr/bin/env python3
"""Capital scaling sweep: 1w / 2w / 3w / 5w / 10w / 20w
Focus: TRD/REV/ADAPT × K10/K20/K30 × ADV5M/20M/50M
Output: capital_curve.csv — per-strategy NAV/Calmar/cash_drag at each cap level
"""
import json, csv, argparse, sys
from pathlib import Path
import pandas as pd
import numpy as np
from collections import defaultdict

# ----- Path resolution (relative-first, with back-compat fallback) -----
SCRIPT_DIR = Path(__file__).resolve().parent

def _resolve_paths():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data-dir', type=Path, default=SCRIPT_DIR / 'data',
                    help='Directory containing all_etf_pool.csv + kline_cache_all/ '
                         '(default: ./data/ next to this script)')
    ap.add_argument('--hs300', type=Path, default=SCRIPT_DIR / 'hs300_daily.csv',
                    help='HS300 daily csv (default: ./hs300_daily.csv next to this script)')
    ap.add_argument('--out-dir', type=Path, default=SCRIPT_DIR / 'baselines_capsweep',
                    help='Output directory (default: ./baselines_capsweep/)')
    args, _ = ap.parse_known_args()
    data_dir = args.data_dir
    pool_csv = data_dir / 'all_etf_pool.csv'
    cache    = data_dir / 'kline_cache_all'
    hs300    = args.hs300
    if not (pool_csv.exists() and cache.exists()):
        fb = Path('/home/mira/files/experiments_archive/Y_l2_etf_mapping_20260529')
        if (fb / 'all_etf_pool.csv').exists() and (fb / 'kline_cache_all').exists():
            print(f'[info] data fallback: {fb}', file=sys.stderr)
            data_dir = fb; pool_csv = fb / 'all_etf_pool.csv'; cache = fb / 'kline_cache_all'
    if not hs300.exists():
        fb_hs = Path('/home/mira/files/e12_narrative/data/hs300_daily.csv')
        if fb_hs.exists():
            print(f'[info] hs300 fallback: {fb_hs}', file=sys.stderr); hs300 = fb_hs
    for p, label in [(pool_csv, 'all_etf_pool.csv'), (cache, 'kline_cache_all/'), (hs300, 'hs300_daily.csv')]:
        if not p.exists():
            raise SystemExit(f'FATAL: missing {label} (looked at {p}). '
                             f'Pass --data-dir / --hs300, or unzip L2_ETF_DATA_*.zip into ./data/.')
    out = args.out_dir; out.mkdir(parents=True, exist_ok=True)
    return data_dir, pool_csv, cache, hs300, out

DATA_DIR, POOL_CSV, CACHE, HS300, OUT = _resolve_paths()
Y = DATA_DIR  # back-compat alias

START = "2024-01-31"
END   = "2026-05-26"
FEE = 0.001
CAP_LIST = [10_000, 20_000, 30_000, 50_000, 100_000, 200_000]
ADV_MIN_LIST = [5e6, 20e6, 50e6]
TOPK_LIST = [10, 20, 30]
REBAL = ["2024-01-31","2024-04-30","2024-07-31","2024-10-31",
         "2025-01-31","2025-04-30","2025-07-31","2025-10-31","2026-01-31"]

with POOL_CSV.open() as f:
    pool = [(r['code'], r['name']) for r in csv.DictReader(f)]
codes = [c for c,_ in pool]

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

# Pre-cache pool & signals (independent of capital → reuse across cap levels)
print('Pre-caching pools/signals/markets...')
POOL_CACHE = {}     # (cutoff, adv_min) -> [code list]
SIGNAL_CACHE = {}   # (cutoff, mode, k, adv_min) -> picks

def first_td_geq(t_str):
    t = pd.Timestamp(t_str)
    cands = hs[hs['date'] >= t]
    return cands.iloc[0]['date'].strftime('%Y-%m-%d') if len(cands) else None
real_rebal = [first_td_geq(d) for d in REBAL]

def pool_at(cutoff_str, adv_min):
    key = (cutoff_str, adv_min)
    if key in POOL_CACHE: return POOL_CACHE[key]
    cutoff = pd.Timestamp(cutoff_str)
    eligible = []
    for c, df in code_data.items():
        snap = df[df['date'] <= cutoff]
        if len(snap) < 130: continue
        tail = snap.tail(60)
        adv = (tail['volume'] * tail['close'] * 100).mean()
        if adv < adv_min: continue
        eligible.append((c, adv))
    POOL_CACHE[key] = eligible
    return eligible

def signal_topk(cutoff_str, mode, k, adv_min):
    key = (cutoff_str, mode, k, adv_min)
    if key in SIGNAL_CACHE: return SIGNAL_CACHE[key]
    pool_e = pool_at(cutoff_str, adv_min)
    rows = []
    for c, _ in pool_e:
        snap = code_data[c][code_data[c]['date'] <= pd.Timestamp(cutoff_str)]
        if len(snap) < 121: continue
        ret = snap.iloc[-1]['close'] / snap.iloc[-120]['close'] - 1
        rows.append((c, ret))
    df = pd.DataFrame(rows, columns=['code','ret'])
    if mode == "REVERSAL":
        res = df.nsmallest(k, 'ret')['code'].tolist()
    else:
        res = df.nlargest(k, 'ret')['code'].tolist()
    SIGNAL_CACHE[key] = res
    return res

def market_all(cutoff_str, k, adv_min):
    return [c for c,_ in pool_at(cutoff_str, adv_min)]

print('Building price matrix...')
price_at = defaultdict(dict)
for c, df in code_data.items():
    for _, r in df.iterrows():
        if pd.Timestamp(START) <= r['date'] <= pd.Timestamp(END):
            price_at[r['date'].strftime('%Y-%m-%d')][c] = float(r['close'])

LAST_PX = {}

def rebalance(cash, holdings, dp, targets, equity):
    fee = 0.0; tset = set(targets)
    for c in list(holdings.keys()):
        if c not in tset and c in dp:
            q = holdings[c]; px = dp[c]
            proc = q * px
            cash += proc * (1-FEE); fee += proc * FEE
            del holdings[c]
    n = sum(1 for c in targets if c in dp)
    if n == 0: return cash, holdings, fee, {"n_target":0,"n_held":len(holdings),"n_zero_alloc":0,"cash_pct":100.0}
    w = 1.0 / n
    tqty = {}; zero = 0
    for c in targets:
        if c not in dp: continue
        budget = equity * w; lot = dp[c] * 100
        q = int(budget / lot) * 100
        tqty[c] = q
        if q == 0: zero += 1
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
    diag = {"n_target":n,"n_held":len(holdings),"n_zero_alloc":zero,
            "cash_pct": cash/equity*100 if equity>0 else 0}
    return cash, holdings, fee, diag

def equity_total(cash, holdings, dp):
    e = cash
    for c, q in holdings.items():
        if c in dp:
            LAST_PX[c] = dp[c]; e += q * dp[c]
        elif c in LAST_PX: e += q * LAST_PX[c]
    return e

def run(init_cash, picker, k, adv_min):
    global LAST_PX; LAST_PX = {}
    cash = float(init_cash); holdings = {}; curve = []; fee_tot = 0; rlog = []
    idx = 0; days = sorted(price_at.keys())
    for day in days:
        dp = price_at[day]
        for c, px in dp.items(): LAST_PX[c] = px
        if idx < len(real_rebal) and day >= real_rebal[idx]:
            cutoff = real_rebal[idx]
            picks = picker(cutoff, k, adv_min)
            eq = equity_total(cash, holdings, dp)
            cash, holdings, fee, diag = rebalance(cash, holdings, dp, picks, eq)
            fee_tot += fee
            rlog.append(diag)
            idx += 1
        curve.append(equity_total(cash, holdings, dp))
    return curve, rlog, fee_tot

def stats(init, curve, rlog, fee):
    final = curve[-1]
    rmax=0; mdd=0
    for e in curve:
        if e>rmax: rmax = e
        if rmax>0:
            dd = (e-rmax)/rmax
            if dd<mdd: mdd = dd
    tot = (final/init-1)*100
    cal = -tot/(mdd*100) if mdd<0 else float('inf')
    avg_cash = np.mean([r["cash_pct"] for r in rlog]) if rlog else 0
    avg_zero = np.mean([r["n_zero_alloc"] for r in rlog]) if rlog else 0
    avg_held = np.mean([r["n_held"] for r in rlog]) if rlog else 0
    return {"final":final,"tot_ret":tot,"mdd":mdd*100,"calmar":cal,
            "avg_cash_pct":avg_cash,"avg_zero_alloc":avg_zero,"avg_held":avg_held,"fee":fee}

# Run sweep
print(f'\n{"="*150}')
print(f'Capital scaling sweep | window 2024-01 → 2026-05')
print(f'{"="*150}')

# Strategies: MARKET + TRD_K10/20/30 × ADV5M/20M/50M (×6 cap levels = 60 sims × 6 = 360 runs)
strategies = []
for adv in ADV_MIN_LIST:
    tag = f"ADV{int(adv/1e6)}M"
    strategies.append((f"MARKET_{tag}", lambda d,k_,a_=adv: market_all(d,k_,a_), None, adv))
    for k in TOPK_LIST:
        strategies.append((f"TRD_K{k}_{tag}",   lambda d,k_,a_=adv: signal_topk(d,"TREND",k_,a_), k, adv))
        strategies.append((f"ADAPT_K{k}_{tag}", lambda d,k_,a_=adv: signal_topk(d, regime_at(d), k_, a_), k, adv))

rows = []
for name, fn, k, adv in strategies:
    for cap in CAP_LIST:
        curve, rlog, fee = run(cap, fn, k if k else 0, adv)
        s = stats(cap, curve, rlog, fee)
        row = {"strategy":name, "capital":cap, **s}
        rows.append(row)
    # Compact row print (one line per strategy, capital across cols)
    rets = {r["capital"]: r["tot_ret"] for r in rows if r["strategy"]==name}
    cashes = {r["capital"]: r["avg_cash_pct"] for r in rows if r["strategy"]==name}
    print(f"{name:24s}  ret: " + "  ".join(f"{cap//10000}w:{rets[cap]:+6.1f}%" for cap in CAP_LIST)
          + "  | cash% " + " ".join(f"{cashes[cap]:4.1f}" for cap in CAP_LIST))

out_csv = OUT/"capsweep_summary.csv"
pd.DataFrame(rows).to_csv(out_csv, index=False)
print(f'\nSaved {len(rows)} rows → {out_csv}')

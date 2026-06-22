#!/usr/bin/env python3
"""L2 ETF Live - Quarterly rebalance picker.

Strategy: TRD_K20_ADV50M_NoKCB (locked, see README.md §1)
Usage:
    python3 quarterly_picks.py                  # auto cutoff = last trading day
    python3 quarterly_picks.py --cutoff 2026-07-30
    python3 quarterly_picks.py --capital 50000  # default 50000
    python3 quarterly_picks.py --refresh-data   # re-fetch latest kline (skip if you trust cache)

Outputs (written to this directory):
    picks_<cutoff>.csv      target holdings
    trades_<cutoff>.csv     diff vs current_holdings.json (SELL + BUY)
    current_holdings.json   updated after you confirm fills (manual or --commit)
"""
import argparse, json, csv, os, sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

HOME = Path(os.environ.get("L2_ETF_LIVE_HOME", Path(__file__).resolve().parent))
DATA_ROOT = Path(os.environ.get(
    "L2_ETF_DATA_ROOT",
    "/home/mira/files/experiments_archive/Y_l2_etf_mapping_20260529",
))
CACHE = DATA_ROOT / "kline_cache_all"
POOL_CSV = DATA_ROOT / "all_etf_pool.csv"

# ========= STRATEGY CONSTANTS (LOCKED) =========
K = 20
ADV_MIN_YUAN = 50e6
MOMENTUM_WINDOW = 120
LOOKBACK_MIN_DAYS = 130
ADV_LOOKBACK = 60
EXCLUDE_PREFIXES = ('588', '589')   # 科创板,无权限
LOT_SIZE = 100
DEFAULT_CAPITAL = 50_000.0
DEFAULT_FEE = 0.001
# ===============================================


def log(msg):
    print(msg, file=sys.stderr)


def load_pool():
    if not POOL_CSV.exists():
        raise SystemExit(f"FATAL: pool file missing: {POOL_CSV}")
    with POOL_CSV.open() as f:
        return [(r['code'], r['name']) for r in csv.DictReader(f)]


def load_kline(code):
    """Returns sorted list of dicts {date, close, volume} or None."""
    p = CACHE / f"{code}.json"
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text())
    except Exception:
        return None
    if not d:
        return None
    rows = []
    for r in d:
        try:
            rows.append({
                'date': r['date'],
                'close': float(r['close']),
                'volume': float(r['volume']),
            })
        except (KeyError, ValueError, TypeError):
            continue
    rows.sort(key=lambda x: x['date'])
    return rows if rows else None


def filter_by_cutoff(rows, cutoff_str):
    return [r for r in rows if r['date'] <= cutoff_str]


def compute_adv(rows_tail):
    # adv (yuan) = mean(volume * close * 100)
    if not rows_tail:
        return 0.0
    return sum(r['volume'] * r['close'] * 100 for r in rows_tail) / len(rows_tail)


def compute_momentum(rows, window):
    if len(rows) < window + 1:
        return None
    return rows[-1]['close'] / rows[-window]['close'] - 1


def latest_data_date_in_cache():
    """Return the common latest date in the ETF cache, deterministically."""
    pool = load_pool()
    latest_dates = []
    n_with_data = 0
    for c, _ in pool:
        rows = load_kline(c)
        if rows:
            n_with_data += 1
            latest_dates.append(rows[-1]['date'])
    log(f"  cache latest date scan: {n_with_data}/{len(pool)} ETFs have kline data")
    if not latest_dates:
        return ""
    counts = Counter(latest_dates)
    cutoff, n_cutoff = sorted(counts.items(), key=lambda x: (-x[1], x[0]))[0]
    max_date = max(latest_dates)
    if cutoff != max_date:
        log(f"  WARN: newest cache date is {max_date}, but common cutoff is {cutoff} ({n_cutoff} ETFs)")
    return cutoff


def pick_top_k(cutoff_str, capital, fee=DEFAULT_FEE):
    pool = load_pool()
    name_map = {c: n for c, n in pool}
    eligible = []
    for c, _ in pool:
        if c.startswith(EXCLUDE_PREFIXES):
            continue
        rows = load_kline(c)
        if not rows:
            continue
        snap = filter_by_cutoff(rows, cutoff_str)
        if len(snap) < LOOKBACK_MIN_DAYS:
            continue
        adv = compute_adv(snap[-ADV_LOOKBACK:])
        if adv < ADV_MIN_YUAN:
            continue
        mom = compute_momentum(snap, MOMENTUM_WINDOW)
        if mom is None:
            continue
        eligible.append({
            'code': c,
            'name': name_map.get(c, ''),
            'last_px': snap[-1]['close'],
            'last_date': snap[-1]['date'],
            'adv_M': adv / 1e6,
            'mom_120d': mom * 100,
        })

    if not eligible:
        raise SystemExit(f"FATAL: 0 eligible ETFs at cutoff {cutoff_str}. Check cache freshness.")

    eligible.sort(key=lambda x: -x['mom_120d'])
    top = eligible[:K]

    # lot sizing
    budget_each = capital / K
    total_cost = 0
    for r in top:
        lot_cost = r['last_px'] * LOT_SIZE
        shares = int(budget_each / (lot_cost * (1 + fee))) * LOT_SIZE
        cost = shares * r['last_px']
        r['shares'] = shares
        r['cost'] = cost
        r['market'] = market_of(r['code'])
        r['tag'] = '创' if (r['code'].startswith('159') and len(r['code']) >= 4 and r['code'][3] in '23') else ''
        total_cost += cost

    return top, eligible, total_cost


def latest_price_map(cutoff_str):
    """Latest close at or before cutoff for every ETF in the pool."""
    out = {}
    for code, _ in load_pool():
        rows = load_kline(code)
        if not rows:
            continue
        snap = filter_by_cutoff(rows, cutoff_str)
        if snap:
            out[code] = snap[-1]['close']
    return out


def market_of(code):
    if code.startswith(('51', '58', '56')):
        return '沪'
    if code.startswith(('15', '16')):
        return '深'
    return '?'


def load_holdings():
    p = HOME / "current_holdings.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}


def save_holdings(holdings, cutoff_str):
    p = HOME / "current_holdings.json"
    p.write_text(json.dumps({"as_of": cutoff_str, "holdings": holdings}, indent=2, ensure_ascii=False))
    log(f"  → current_holdings.json updated (as_of={cutoff_str})")


def normalize_holdings(data):
    current = data.get('holdings', {}) if isinstance(data, dict) and 'holdings' in data else data
    if not isinstance(current, dict):
        return {}
    out = {}
    for code, qty in current.items():
        try:
            qty_i = int(qty)
        except (TypeError, ValueError):
            continue
        if qty_i > 0:
            out[str(code)] = qty_i
    return out


def compute_trades(target, current, pool_name_map=None, price_map=None):
    """target = list of dicts with code/shares; current = dict {code: shares}.
    Returns sorted trades [{side, code, shares}, ...]
    """
    pool_name_map = pool_name_map or {}
    price_map = price_map or {}
    tgt = {r['code']: r['shares'] for r in target}
    name_map = {**pool_name_map, **{r['code']: r['name'] for r in target}}
    px_map = {**price_map, **{r['code']: r['last_px'] for r in target}}
    trades = []
    # SELL first (release cash)
    for code, qty in current.items():
        tq = tgt.get(code, 0)
        if qty > tq:
            trades.append({
                'side': 'SELL', 'code': code, 'name': name_map.get(code, '?'),
                'shares': qty - tq, 'ref_px': px_map.get(code, ''),
            })
    # BUY second
    for code, tq in tgt.items():
        cq = current.get(code, 0)
        if tq > cq:
            trades.append({
                'side': 'BUY', 'code': code, 'name': name_map.get(code, '?'),
                'shares': tq - cq, 'ref_px': px_map.get(code, ''),
            })
    return trades


def write_picks_csv(top, cutoff_str, capital, total_cost):
    out = HOME / f"picks_{cutoff_str}.csv"
    with out.open('wb') as f:
        f.write(b'\xef\xbb\xbf')  # BOM for Excel
        f.write('序号,代码,名称,市场,标签,最新价,日均额(M),120日动量(%),目标股数,预估金额\n'.encode('utf-8'))
        for i, r in enumerate(top, 1):
            line = (f"{i},{r['code']},{r['name']},{r['market']},{r['tag']},"
                    f"{r['last_px']:.3f},{r['adv_M']:.1f},{r['mom_120d']:.1f},"
                    f"{r['shares']},{r['cost']:.0f}\n")
            f.write(line.encode('utf-8'))
        f.write(f"\n合计实买,{total_cost:.0f},余,{capital - total_cost:.0f},利用率,{total_cost/capital*100:.1f}%\n".encode('utf-8'))
    return out


def write_trades_csv(trades, cutoff_str):
    out = HOME / f"trades_{cutoff_str}.csv"
    with out.open('wb') as f:
        f.write(b'\xef\xbb\xbf')
        f.write('方向,代码,名称,股数,参考价,预估金额\n'.encode('utf-8'))
        for t in trades:
            ref = t['ref_px']
            ref_s = f"{ref:.3f}" if isinstance(ref, (int, float)) else ''
            est = (t['shares'] * ref) if isinstance(ref, (int, float)) else 0
            line = f"{t['side']},{t['code']},{t['name']},{t['shares']},{ref_s},{est:.0f}\n"
            f.write(line.encode('utf-8'))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cutoff', help='YYYY-MM-DD; default = latest data date in cache')
    ap.add_argument('--capital', type=float, default=DEFAULT_CAPITAL)
    ap.add_argument('--commit', action='store_true', help='Write current_holdings.json from picks (assumes fully filled)')
    ap.add_argument('--show-pool-size', action='store_true')
    ap.add_argument('--refresh-data', action='store_true',
                    help='Reserved flag. This package does not include a data fetcher; refresh cache before running.')
    args = ap.parse_args()

    if args.refresh_data:
        raise SystemExit(
            "FATAL: --refresh-data was documented but no data refresh implementation is bundled. "
            "Refresh kline_cache_all externally, then rerun quarterly_picks.py."
        )

    cutoff = args.cutoff or latest_data_date_in_cache()
    if not cutoff:
        raise SystemExit("FATAL: cannot determine cutoff date from cache.")
    log(f"[1/4] cutoff = {cutoff}  capital = {args.capital:,.0f}")

    log(f"[2/4] running TRD_K20_ADV50M_NoKCB picker...")
    top, eligible, total_cost = pick_top_k(cutoff, args.capital)
    log(f"  eligible pool = {len(eligible)}  selected = {len(top)}  total_cost = {total_cost:,.0f}  "
        f"cash_left = {args.capital - total_cost:,.0f}  util = {total_cost/args.capital*100:.1f}%")

    if args.show_pool_size:
        print(f"eligible_pool={len(eligible)} selected={len(top)} cutoff={cutoff}")
        return

    log(f"[3/4] writing picks_{cutoff}.csv ...")
    picks_path = write_picks_csv(top, cutoff, args.capital, total_cost)

    log(f"[4/4] diff vs current_holdings.json ...")
    current = normalize_holdings(load_holdings())
    pool_name_map = dict(load_pool())
    price_map = latest_price_map(cutoff)
    trades = compute_trades(top, current, pool_name_map=pool_name_map, price_map=price_map)
    trades_path = write_trades_csv(trades, cutoff)

    print(f"\n=== Picks (cutoff={cutoff}) ===")
    print(f"{'#':>3} {'code':<7} {'name':<25} {'mkt':<3} {'tag':<3} {'px':>7} {'adv_M':>7} {'mom%':>7} {'shares':>7} {'cost':>7}")
    for i, r in enumerate(top, 1):
        print(f"{i:>3} {r['code']:<7} {r['name']:<25} {r['market']:<3} {r['tag']:<3} "
              f"{r['last_px']:>7.3f} {r['adv_M']:>7.1f} {r['mom_120d']:>+6.1f}% {r['shares']:>7} {r['cost']:>7.0f}")
    print(f"\nTotal: 实买 {total_cost:,.0f} / 余 {args.capital - total_cost:,.0f} / 利用率 {total_cost/args.capital*100:.1f}%")

    print(f"\n=== Trades (vs current_holdings) ===")
    if not current:
        print("(no current_holdings.json — treat all picks as initial BUY)")
    if not trades:
        print("(no trades needed)")
    else:
        n_sell = sum(1 for t in trades if t['side'] == 'SELL')
        n_buy = sum(1 for t in trades if t['side'] == 'BUY')
        print(f"SELL: {n_sell}  BUY: {n_buy}")
        for t in trades:
            ref = t['ref_px']
            ref_s = f"@{ref:.3f}" if isinstance(ref, (int, float)) else ''
            print(f"  {t['side']:<5} {t['code']} {t['name']:<25} x{t['shares']:>6} {ref_s}")

    print(f"\nFiles: {picks_path.name} | {trades_path.name}")

    if args.commit:
        new_holdings = {r['code']: r['shares'] for r in top if r['shares'] > 0}
        save_holdings(new_holdings, cutoff)
    else:
        print("\n[hint] After actual fills, run with --commit to update current_holdings.json")


if __name__ == '__main__':
    main()

from __future__ import annotations

from math import comb, log

import numpy as np


def union_log_coverage(levels, tolerance: float, lower: float, upper: float) -> float:
    """Union coverage of symmetric percentage bands on a log-price axis."""
    if lower <= 0 or upper <= lower:
        raise ValueError("invalid positive price range")
    lo_domain, hi_domain = log(lower), log(upper)
    intervals = []
    for level in levels:
        level = float(level)
        if level <= 0:
            continue
        lo = max(lo_domain, log(level * (1.0 - tolerance)))
        hi = min(hi_domain, log(level * (1.0 + tolerance)))
        if lo <= hi:
            intervals.append((lo, hi))
    if not intervals:
        return 0.0
    intervals.sort()
    covered = 0.0
    current_lo, current_hi = intervals[0]
    for lo, hi in intervals[1:]:
        if lo <= current_hi:
            current_hi = max(current_hi, hi)
        else:
            covered += current_hi - current_lo
            current_lo, current_hi = lo, hi
    covered += current_hi - current_lo
    return min(1.0, covered / (hi_domain - lo_domain))


def binomial_upper_p_value(successes: int, trials: int, null_probability: float) -> float:
    if trials <= 0:
        return float("nan")
    p = min(max(float(null_probability), 0.0), 1.0)
    if p == 0:
        return 0.0 if successes > 0 else 1.0
    if p == 1:
        return 1.0
    return float(sum(comb(trials, k) * p**k * (1.0 - p) ** (trials - k) for k in range(successes, trials + 1)))


def random_log_price_hit_mean(
    daily_level_sets: list[list[float]],
    tolerance: float,
    lower: float,
    upper: float,
    simulations: int = 1000,
    seed: int = 20260816,
) -> float:
    """Monte Carlo cross-check for the analytical log-axis coverage baseline."""
    if not daily_level_sets:
        return float("nan")
    rng = np.random.default_rng(seed)
    log_lower, log_upper = np.log(lower), np.log(upper)
    rates = []
    for _ in range(simulations):
        hits = 0
        for values in daily_level_sets:
            pseudo_price = float(np.exp(rng.uniform(log_lower, log_upper)))
            if any(abs(pseudo_price / level - 1.0) <= tolerance for level in values if level > 0):
                hits += 1
        rates.append(hits / len(daily_level_sets))
    return float(np.mean(rates))

# pywencai Notes

## Preconditions

- Install runtime dependencies before live queries:
  - `pip install pywencai pandas`
- Use a fresh browser cookie from `https://www.iwencai.com/`.
- Some `pywencai` versions rely on Node.js being available. If requests fail unexpectedly after installation, verify a recent Node.js runtime is on `PATH`.

## Good Query Patterns

Prefer one concrete Chinese sentence. Good examples:

- `近20个交易日涨停次数大于等于2次，按成交额从高到低排序`
- `今天首板，非ST，最新价小于30元`
- `PE-TTM小于20，ROE大于15%，总市值从小到大排序`
- `近5日主力资金净流入为正，所属概念包含机器人`

## Output Strategy

- Use markdown preview for fast inspection in the terminal.
- Use `--out result.json` for full-fidelity export.
- Use `--find 股票简称 --find 最新价` to keep only a few columns.

## Common Failure Modes

- Cookie expired: refresh login and copy a new cookie.
- No rows returned: simplify the sentence and remove extra ranking clauses.
- Package import error: install `pywencai` and `pandas` into the Python environment used by Codex.
- Schema drift: Wencai column names can change over time; inspect the returned column list before doing strict downstream parsing.

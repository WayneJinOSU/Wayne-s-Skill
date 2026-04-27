---
name: wencai-query
description: Query Tonghuashun Wencai with the `pywencai` Python package for Chinese-market screening, ranking, and tabular result retrieval. Use when Codex needs to execute or explain a natural-language Wencai request such as A-share stock screening, concept or industry ranking, valuation or financial-factor filtering, limit-up or turnover queries, export Wencai results, or summarize the returned table. Trigger when the user mentions "问财", "同花顺问财", or `pywencai`, or asks to turn a Chinese stock screener prompt into executable code or structured output.
---

# Wencai Query

Use this skill to turn a Chinese natural-language stock screener prompt into a reproducible Wencai query, run it with `pywencai`, and summarize the returned table.

## Quick Start

1. Ensure the runtime has `pywencai` installed.
2. Run anonymously first for lightweight queries. If anonymous access fails or returns incomplete data, export a valid cookie before retrying.
3. Run the bundled script for deterministic execution.

```bash
python3 /Users/a/.codex/skills/wencai-query/scripts/query_wencai.py "近20日涨停次数大于等于2次，按成交额从高到低排序"
```

If the user asks for code only, prefer the same `pywencai.get(...)` parameters that the script uses.

## Workflow

1. Rewrite the user intent as one Wencai query sentence in Chinese.
2. Keep the query concrete. Include sort direction, date window, market, and threshold conditions in the sentence when possible.
3. Choose `query_type` only when the market is clear. Default to `stock` for A-share screening.
4. Run `scripts/query_wencai.py` for a live query or provide equivalent Python code.
5. Summarize the result table with the exact query sentence, row count, key columns, and the top observations.

## Parameter Choices

Use these defaults unless the task requires something else:

- `query_type=stock`: Default for A-share, ETF, and most stock-screening prompts.
- `perpage=100`: Good default. Raise only when the user explicitly wants more rows.
- `sort_key`: Set only when the user explicitly requests a ranking field.
- `sort_order=desc`: Default for ranking prompts like "从高到低".
- `loop=False`: Use a single request unless the user needs a larger result set and the query is stable.
- `find`: Use only when the user wants a small subset of columns.

Common `query_type` values:

- `stock`: A-share and most equity screening tasks.
- `fund`: Fund-related questions.
- `index`: Index ranking or constituent queries.
- `hkstock`: Hong Kong stock queries.
- `usstock`: US-listed stock queries.
- `future`: Futures queries.
- `bond`: Bond or convertible-bond style queries when supported by the current Wencai endpoint.

## Result Handling

When results come back:

- Preserve the exact query text in the response.
- Call out whether the script returned a table, a list of records, or an empty result.
- Mention truncated previews explicitly if only the first few rows are shown.
- If the user wants export files, pass `--out <path>` and choose `.json`, `.csv`, or `.tsv`.

## Failure Handling

If the query fails:

- Check `WENCAI_COOKIE` first. Expired cookies are the most common failure mode.
- If `pywencai` is missing, tell the user to install it before retrying.
- If the endpoint rejects the request, simplify the sentence and remove optional sort fields before retrying.
- Avoid aggressive retry loops. Wencai pages and cookies can rate-limit or invalidate quickly.

## Cookie Guidance

Cookie is optional. The script omits the cookie parameter when neither `--cookie` nor `WENCAI_COOKIE` is provided, allowing `pywencai` to try anonymous access. This often works for lightweight single-stock and small screening queries, but may fail, rate-limit, or return less complete data.

Use either `--cookie` or the `WENCAI_COOKIE` environment variable when:

- anonymous access fails
- the endpoint rate-limits
- the result is incomplete
- the query needs login-only fields or larger pagination

To refresh the cookie:

1. Log in at `https://www.iwencai.com/` in a browser.
2. Open DevTools and inspect a successful request to the site.
3. Copy the full `Cookie` request header.
4. Export it into `WENCAI_COOKIE` before running the script.

## Resources

- Script: `scripts/query_wencai.py`
- Reference: `references/pywencai-notes.md`

# A 股一致预期硬性预检

当 A 股 PEG-ready 包缺一致预期、接口报错、或准备进入 `no_consensus_mode` 时读取本文件。目标是在降级前穷尽轻量、结构化、可复现的数据入口，避免把“入口选错”误判成“市场无一致预期”。

## 降级前必须完成

除非用户明确禁止联网或接口包不可用，进入 `no_consensus_mode` 前至少完成以下四步，并记录每步结果：

1. AkShare-同花顺盈利预测：主口径。
2. AkShare-东方财富盈利预测：交叉验证，注意全量过滤绕路。
3. Wencai/pywencai：分年查询，不用宽泛长句作为唯一判断。
4. 腾讯财经：只校验行情/市值边界；不要把腾讯行情失败或预测接口失败当成一致预期不可得。

只要任一来源取得“预测年份 + 机构数 + 净利润或 EPS 均值”，即先标记为 `consensus_available` 或 `partial_consensus_available`，再做口径校验；不要直接写 `data_gap`。

## AkShare-同花顺主口径

优先调用：

```python
import akshare as ak

code = "600522"
np_df = ak.stock_profit_forecast_ths(symbol=code, indicator="预测年报净利润")
eps_df = ak.stock_profit_forecast_ths(symbol=code, indicator="预测年报每股收益")
inst_df = ak.stock_profit_forecast_ths(symbol=code, indicator="业绩预测详表-机构")
detail_df = ak.stock_profit_forecast_ths(symbol=code, indicator="业绩预测详表-详细指标预测")
```

最低抽取字段：

| 字段 | 要求 |
| --- | --- |
| 预测年份 | 至少未来两年，能取则三年 |
| 预测机构数 | 必须保留 |
| 净利润均值 | 优先使用，单位统一为亿元 |
| EPS均值 | 与净利润交叉校验 |
| 最小值/最大值 | 用于判断分歧度 |
| 机构明细 | 能取则保留机构、分析师、报告日期、逐年 EPS/净利润 |

同花顺口径能同时取得净利润、EPS、机构数时，默认可作为 A 股 PEG 一致预期主源。

## AkShare-东方财富绕路

`stock_profit_forecast_em(symbol="<股票代码>")` 直接传股票代码可能失败，因为该函数的 `symbol` 常用于行业板块或空值全量。不要因直接代码调用失败就判定东方财富不可用。

优先尝试：

```python
import akshare as ak

em_df = ak.stock_profit_forecast_em()
row = em_df[
    em_df.astype(str).apply(lambda s: s.str.contains("600522|中天科技", regex=True)).any(axis=1)
]
```

可用字段通常包括研报数、未来年度 EPS、近六月买入/增持/中性/减持/卖出数量。若只有 EPS 没有净利润，可作为同花顺/Wencai 的交叉验证；若需从 EPS 推净利润，必须用同一日期股本并标注为“推算值”。

## Wencai/pywencai 分年查询

宽泛句子容易误路由或只返回单年。优先按年份拆分：

```bash
python3 /Users/a/.codex/skills/wencai-query/scripts/query_wencai.py \
  '600522 中天科技 2026年 预测年报净利润 预测每股收益 预测机构数' \
  --out /tmp/wencai_600522_predict_2026.json
```

```bash
python3 /Users/a/.codex/skills/wencai-query/scripts/query_wencai.py \
  '600522 中天科技 2027年 预测年报净利润 预测每股收益 预测机构数' \
  --out /tmp/wencai_600522_predict_2027.json
```

```bash
python3 /Users/a/.codex/skills/wencai-query/scripts/query_wencai.py \
  '600522 中天科技 2028年 预测年报净利润 预测每股收益 预测机构数' \
  --out /tmp/wencai_600522_predict_2028.json
```

解析时重点找 `tableV1` 或同义字段：

| Wencai 字段 | 统一字段 |
| --- | --- |
| `时间区间` | 预测年份 |
| `预测净利润平均值` | consensus_profit |
| `预测每股收益平均值` | consensus_EPS |
| `预测家数` | 预测机构数 |
| `预测市盈率(pe,最新预测)` | 预测 PE |
| `预测peg值` | 预测 PEG |

若宽泛问法失败但分年查询成功，输出要写“Wencai 可用，但必须分年查询”。若匿名查询字段不完整，再提示需要 `WENCAI_COOKIE`；不要把匿名宽泛查询失败直接记为 `data_gap`。

## 腾讯财经边界

腾讯行情接口可用于校验股价、市值、PE/PB：

```text
https://qt.gtimg.cn/q=sh600522
```

腾讯页面可能有“价格预测/机构评级”展示，但公开接口不稳定。常见预测接口返回控制器错误时，只能记录为“腾讯一致预期暂不可用”；不要继续消耗大量时间反编译页面，除非用户明确要求。

## 口径校验

取得数据后至少做以下检查：

- 年份：字段必须对应 2026E/2027E/2028E，不要把报告日期当预测年份。
- 机构数：`预测机构数 > 1` 才能称为一致预期；单家预测写 `single_or_unverified_forecast`。
- EPS 与净利润：`EPS × 总股本` 应与净利润大体匹配；差异较大时检查单位、股本日期、是否扣非或归母口径。
- 数值单位：Wencai 常返回元，AkShare 表可能已经是亿元；统一为亿元后再入估值。
- 缺失值：若某年净利润为 NaN 但 EPS 和机构数存在，不要直接丢弃；先看其他来源或机构明细。
- 分歧度：最大值/最小值跨度很大时，在估值报告中提示一致预期离散度。

## 输出要求

把预检结果写入 PEG-ready 包的 `source_notes`，或新增 `<标的>_consensus_source_check.md`。最少包含：

```text
检查日期：
主源：
交叉验证源：
成功接口：
失败接口及失败原因：
2026E/2027E/2028E 净利润、EPS、机构数：
是否可进入 consensus_mode：
```

只有完成上述预检仍无法取得“年份 + 机构数 + 净利润/EPS”时，才能标记 `data_gap` 并进入 `no_consensus_mode`。

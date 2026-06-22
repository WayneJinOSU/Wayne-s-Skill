# Data Source Fallbacks

用于行情、市值、一致预期、公告或窄字段财务数据缺失时。普通 PEG 估值若 PEG-ready 已完整，不要读取本文件。

## Source Ladder

| 数据需求 | 主接口 | 第一备用 | 第二备用 | 纪律 |
| --- | --- | --- | --- | --- |
| 股价、市值、股本、PE/PB | PEG-ready 包内市场字段 | `$akshare` A 股行情/历史行情 | `$tushare` `daily_basic`/行情 | 同一张表只保留一套主口径；换源需说明原因 |
| 一致预期 | `$akshare` `stock_profit_forecast_ths` | `$akshare` `stock_profit_forecast_em` 全量过滤 | `$wencai-query` 分年查询 | 单家预测不得冒充一致预期；保留机构数和接口日期 |
| 财务窄字段 | facts_core / PEG-ready | `$tushare` `income`/`balancesheet`/`cashflow`/`fina_indicator` | `$akshare` 财务报表 | 不得用净利润替代 EBIT；字段需口径校验 |
| 公告、权益分派、异常波动 | facts_core / evidence_index | `$akshare` 公告接口 | `$wencai-query` 公告查询 | 记录公告标题、日期和来源 |
| 预测线索交叉检查 | `$akshare` 预测明细 | `$wencai-query` 分年查询 | 无 | 失败即记录 `data_gap` |

## A-Share Consensus Preflight

A 股一致预期缺失或接口异常时，先读取 `references/a-share-consensus-preflight.md`。不得因单一接口失败直接进入 `no_consensus_mode`。

## Wencai Fallback

使用 `$wencai-query` 时：

- 把缺口改写成具体查询句，例如：`002463 沪电股份 2026年 2027年 2028年 机构一致预期净利润 EPS 预测机构数`。
- 默认 `query_type=stock`。
- 宽泛问法失败时按年份拆分查询。
- 输出必须保留查询句、抓取日期、返回行数、关键列和接口状态。
- 问财只做补线索、筛表和交叉检查，不替代公告事实或定期报告事实。

## Data Integrity

- 不使用非接口网页、公开搜索或手工摘研报替代接口数据，除非用户明确要求人工补证，且必须标注为非主口径。
- 若多源数值冲突，优先选择字段更完整、日期更近、口径更清楚的接口，并记录弃用原因。
- 一致预期必须至少覆盖未来两年；能取得时覆盖第三年。

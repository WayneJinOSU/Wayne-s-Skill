# Wayne's Skill

Personal Codex skills maintained as versioned assets.

## Skills

- `akshare`: Chinese financial data access using AkShare library. Fetch real-time and historical data for A-shares, Hong Kong stocks, US stocks, futures, funds, and macroeconomic indicators. Use when user requests Chinese market data, stock prices, market analysis, or financial information from Chinese exchanges. Supports stock quotes, historical data, futures market data, fund information, macroeconomic indicators, and real-time market updates.
- `chassis-growth-agentic-research`: 用多角色研究、中间产物、反方审查和投资人写作重构底盘型成长股研究；保留旧业务底盘、第二曲线、平台复用、承接动作、利润桥和远期估值框架。
- `chassis-growth-research`: 研究A股制造业底盘型成长股，识别旧业务托底、新周期第二成长曲线、平台复用、承接动作、利润桥与远期估值；可调度 `$tushare` skill、`$wencai-query` skill 和公告 PDF 形成证据链。
- `doc`: Professional document creation, editing, and analysis for Office formats (docx, pdf, pptx, xlsx). Use when working with Word documents, PDFs, PowerPoint presentations, or Excel spreadsheets.
- `finance-research-xhs`: 将金融研报、股票研究、行业分析、财报解读、投资复盘和估值框架改写成小红书长文本笔记。适用于非种草、非带货、非标题党风格，强调信息密度、证据链、事实/推断/假设分层、风险和证伪点保留。Use when the user asks for 金融研报小红书、投研小红书长文、股票分析笔记、行业研究改写、财报解读小红书、非种草风格XHS长文本。
- `find-skills`: Helps users discover and install agent skills when they ask questions like "how do I do X", "find a skill for X", "is there a skill that can...", or express interest in extending capabilities. This skill should be used when the user is looking for functionality that might exist as an installable skill.
- `frontend-design`: Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when the user asks to build web components, pages, artifacts, posters, or applications (examples include websites, landing pages, dashboards, React components, HTML/CSS layouts, or when styling/beautifying any web UI). Generates creative, polished code and UI design that avoids generic AI aesthetics.
- `growth-base-business`: 分析底盘型成长股的旧业务底盘，包括收入利润、现金流、客户基础、行业地位、财务质量和下限支撑。
- `growth-execution-signals`: 分析底盘型成长股的新业务承接动作，包括扩产、融资、设备、客户验证、订单、量产、海外基地和研发投入。
- `growth-forward-valuation`: 分析底盘型成长股远期估值、当前市值反推PE、估值透支与关键证伪点。
- `growth-platform-reuse`: 分析底盘型成长股的平台复用能力，包括技术、客户、工艺、产能、供应链、认证体系和跨界可信度。
- `growth-profit-bridge`: 为底盘型成长股建立利润桥，拆分存量利润、新业务利润、扩张成本，并做保守中性乐观情景。
- `growth-second-curve`: 分析底盘型成长股的第二成长曲线，包括新赛道空间、增速、产业链位置、价值量提升和天花板重估。
- `industry-chain-agentic-research`: 用多角色研究、中间产物、产业链利润池、需求供给价格、竞争格局、财务映射、反方审查和投资人写作，完成行业产业链研究报告。适用于 A 股/港股/美股行业研究、产业链研究、赛道研究、行业对公司财务影响研究，以及用户要求 subagent/agentic/多角色行业研究时。
- `local-bank-research`: 研究城商行、农商行等地方商业银行股的利润桥、资产质量、区域beta、债券投资、分红与预期差。
- `pipecat-deploy`: Deploy an agent to Pipecat Cloud
- `pipecat-init`: Scaffold a new Pipecat project with guided setup
- `pipecat-talk`: Start a voice conversation using the Pipecat MCP server
- `skill-github-sync`: Sync local Codex skills from ~/.codex/skills into a GitHub skills repository, update README, commit, and optionally push.
- `supply-chain-agentic-research`: 独立主控供应链平台型成长股正式研究；用多角色/subagent、中间产物、反方审查和投资人写作，完整覆盖产业周期、供应链地位、订单出货、承接动作、利润桥和远期估值。Use when 用户需要深度分析 AI算力、数据中心、新能源、机器人、先进封装、半导体设备/材料等供应链公司，判断身份切换、订单放量、利润中枢上移和估值透支，并优先调度对应子 skill。
- `supply-chain-cycle-capex`: 分析供应链平台型成长股所处的产业周期、客户资本开支、下游需求持续性、产品平台迭代和周期见顶风险。Use when researching AI 算力、云厂商 capex、AI服务器、高速PCB、液冷、电源、连接器、光模块、先进封装设备/材料等供应链公司，判断下游周期是否足以支撑订单和利润中枢上移。
- `supply-chain-orders-shipments`: 分析供应链平台型成长股的订单、排产、出货、海关数据、库存、应收、合同负债、收入确认、利润释放和经营现金流质量。Use when researching AI服务器、高速PCB、液冷、电源、连接器、光模块、先进封装设备/材料等公司，判断订单出货是否领先财报、是否能支撑利润中枢上移。
- `supply-chain-position-moat`: 分析供应链平台型成长股在产业链中的位置、客户认证、规模交付、复杂产品量产、全球产能、供应链组织、可替代性和议价权。Use when researching 工业富联、AI服务器制造、高速PCB、液冷、电源、连接器、光模块、先进封装材料/设备等公司是否具备关键供应链平台地位，而不是普通代工或可替代供应商。
- `tushare`: 面向中文自然语言的 Tushare 数据研究技能。用于把“看看这只股票最近怎么样”“帮我查财报趋势”“最近哪个板块最强”“北向资金在买什么”“给我导出一份行情数据”这类请求，转成可执行的数据获取、清洗、对比、筛选、导出与简要分析流程。适用于 A 股、指数、ETF/基金、财务、估值、资金流、公告新闻、板块概念与宏观数据等研究场景。
- `wencai-query`: Query Tonghuashun Wencai with the `pywencai` Python package for Chinese-market screening, ranking, and tabular result retrieval. Use when Codex needs to execute or explain a natural-language Wencai request such as A-share stock screening, concept or industry ranking, valuation or financial-factor filtering, limit-up or turnover queries, export Wencai results, or summarize the returned table. Trigger when the user mentions "问财", "同花顺问财", or `pywencai`, or asks to turn a Chinese stock screener prompt into executable code or structured output.

## Local install

Install or update all skills from this repo into Codex:

```bash
mkdir -p ~/.codex/skills
cp -R skills/* ~/.codex/skills/
```

Restart Codex after installing or updating skills.

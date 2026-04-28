---
name: finance-research-xhs
description: 将金融研报、股票研究、行业分析、财报解读、投资复盘和估值框架改写成小红书长文本笔记。适用于非种草、非带货、非标题党风格，强调信息密度、证据链、事实/推断/假设分层、风险和证伪点保留。Use when the user asks for 金融研报小红书、投研小红书长文、股票分析笔记、行业研究改写、财报解读小红书、非种草风格XHS长文本。
---

# Finance Research XHS

## Core Goal

Turn financial research into a readable Xiaohongshu longform note without flattening the investment logic.

Default posture:

- Preserve the core judgment, evidence, reasoning, valuation logic, and risks.
- Write like a clear research note for intelligent public readers, not like a product seeding post.
- If a single post would lose important content, propose a series instead of over-compressing.
- Do not publish or automate Xiaohongshu posting unless the user separately asks and a posting tool is available.

## When To Use

Use this skill for:

- A-share, HK, US stock research rewritten for Xiaohongshu.
- Industry research, company analysis, financial statement notes, earnings call summaries.
- Investment review, portfolio review, trading review, valuation framework posts.
- Converting long research answers into XHS long text while keeping important details.
- Drafting non-promotional financial content for public platforms.

Do not use it for:

- Product seeding, lifestyle marketing, brand ads, paid promotion copy.
- Cute influencer tone, short video scripts, or viral emotional hooks.
- Direct buy/sell recommendations.

## Voice

Default voice:

- Calm, specific, evidence-based, lightly conversational.
- Has a point of view, but marks uncertainty clearly.
- Uses plain Chinese; avoids broker-report stiffness unless the user asks for it.
- Keeps important numbers, dates, and assumptions visible.

Avoid:

- "姐妹们", "闭眼入", "狠狠拿捏", "普通人一定要看".
- Exaggerated certainty: "必涨", "稳了", "确定性拉满".
- Clickbait fear or greed framing.
- Turning uncertainty into a conclusion.

## Workflow

### 1. Classify The Source

Identify the input type:

- Company research
- Industry research
- Earnings or announcement interpretation
- Investment review
- Valuation or profit bridge
- Screening or watchlist note

Then infer the audience:

- General finance readers
- Serious retail investors
- Professional-ish investors
- Existing followers who know the context

### 2. Extract The Research Skeleton

Before writing, extract:

- Main conclusion
- What the market is pricing
- 3 to 5 core arguments
- Evidence behind each argument
- Key numbers and date/source口径
- Valuation or profit bridge, if present
- Risks, counterarguments, and证伪点
- What to track next

For investment content, always separate:

- 已披露事实
- 合理推断
- 情景假设
- 个人判断

### 3. Decide Single Post Or Series

Do not force all research into one post.

Use a single post when:

- The argument can be preserved under roughly 1200-1800 Chinese characters.
- There are no more than 3 core arguments.
- Valuation and risks can be stated without losing nuance.

Suggest a series when:

- There are multiple businesses, industries, or scenarios.
- The source includes a profit bridge, valuation table, and risk framework.
- Removing details would make the conclusion feel unsupported.

Common series plan:

- Post 1: 主结论 + 最大分歧
- Post 2: 业务/行业拆解
- Post 3: 利润桥/估值
- Post 4: 证伪点/跟踪清单

### 4. Build The XHS Structure

Default longform structure:

```text
标题：
开头判断：
一、市场现在在交易什么
二、我认为真正的核心矛盾
三、支持这个判断的证据
四、利润/估值怎么消化
五、反证、风险和证伪点
六、后面跟踪什么
标签：
```

Adjust headings to the source. Keep headings concrete; do not use vague motivational labels.

### 5. Compression Rules

Delete in this order:

1. Repeated wording
2. Generic industry background
3. Decorative rhetoric
4. Secondary examples
5. Less important historical detail

Do not delete:

- Core financial numbers
- Time and source口径
- The evidence needed for the conclusion
- Valuation assumptions
- Counterarguments and risks
- Tracking indicators

### 6. Financial Safety Rules

For stocks, funds, sectors, and financial products:

- Do not write direct buy/sell instructions.
- Use "我会关注", "核心变量是", "风险在于", "更像是".
- Mention that the note is research/observation, not investment advice, when the content could be interpreted as a recommendation.
- Keep uncertainty visible.
- Avoid price targets unless the source already has a scenario table and the user wants it retained.

### 7. Output Format

Unless the user asks for "直接成稿", output strategy first:

```text
改写策略：
- 内容类型：
- 建议形式：单篇 / 系列
- 保留重点：
- 压缩重点：
- 风格：

标题：
正文：
标签：

可拆系列标题：
后续跟踪指标：
```

For a direct draft, still include:

- Title
- Body
- Tags
- Tracking indicators or证伪点

## Quality Checklist

Before finalizing, check:

- Does the title avoid clickbait while still naming the conflict?
- Can a reader understand the main conclusion in the first 3 paragraphs?
- Are facts, assumptions, and personal judgment distinguishable?
- Are risks and counterarguments present?
- Did important details survive compression?
- Is the tone non-promotional and non-seeding?


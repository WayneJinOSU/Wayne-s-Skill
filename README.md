# Wayne's Skill

Personal Codex skills maintained as versioned assets.

## Skills

- `chassis-growth-research`: 研究A股制造业底盘型成长股，识别旧业务托底、新周期第二成长曲线、平台复用、承接动作、利润桥与远期估值。
- `doc`: Professional document creation, editing, and analysis for Office formats (docx, pdf, pptx, xlsx). Use when working with Word documents, PDFs, PowerPoint presentations, or Excel spreadsheets.
- `find-skills`: Helps users discover and install agent skills when they ask questions like "how do I do X", "find a skill for X", "is there a skill that can...", or express interest in extending capabilities. This skill should be used when the user is looking for functionality that might exist as an installable skill.
- `frontend-design`: Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when the user asks to build web components, pages, artifacts, posters, or applications (examples include websites, landing pages, dashboards, React components, HTML/CSS layouts, or when styling/beautifying any web UI). Generates creative, polished code and UI design that avoids generic AI aesthetics.
- `growth-base-business`: 分析底盘型成长股的旧业务底盘，包括收入利润、现金流、客户基础、行业地位、财务质量和下限支撑。
- `growth-execution-signals`: 分析底盘型成长股的新业务承接动作，包括扩产、融资、设备、客户验证、订单、量产、海外基地和研发投入。
- `growth-forward-valuation`: 分析底盘型成长股远期估值、当前市值反推PE、估值透支与关键证伪点。
- `growth-platform-reuse`: 分析底盘型成长股的平台复用能力，包括技术、客户、工艺、产能、供应链、认证体系和跨界可信度。
- `growth-profit-bridge`: 为底盘型成长股建立利润桥，拆分存量利润、新业务利润、扩张成本，并做保守中性乐观情景。
- `growth-second-curve`: 分析底盘型成长股的第二成长曲线，包括新赛道空间、增速、产业链位置、价值量提升和天花板重估。
- `local-bank-research`: 研究城商行、农商行等地方商业银行股的利润桥、资产质量、区域beta、债券投资、分红与预期差。
- `pipecat-deploy`: Deploy an agent to Pipecat Cloud
- `pipecat-init`: Scaffold a new Pipecat project with guided setup
- `pipecat-talk`: Start a voice conversation using the Pipecat MCP server
- `skill-github-sync`: Sync local Codex skills from ~/.codex/skills into a GitHub skills repository, update README, commit, and optionally push.
- `wencai-query`: Query Tonghuashun Wencai with the `pywencai` Python package for Chinese-market screening, ranking, and tabular result retrieval. Use when Codex needs to execute or explain a natural-language Wencai request such as A-share stock screening, concept or industry ranking, valuation or financial-factor filtering, limit-up or turnover queries, export Wencai results, or summarize the returned table. Trigger when the user mentions "问财", "同花顺问财", or `pywencai`, or asks to turn a Chinese stock screener prompt into executable code or structured output.

## Local install

Install or update all skills from this repo into Codex:

```bash
mkdir -p ~/.codex/skills
cp -R skills/* ~/.codex/skills/
```

Restart Codex after installing or updating skills.

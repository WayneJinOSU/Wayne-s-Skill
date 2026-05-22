---
name: markdown-report-pdf
description: Convert one or more Markdown reports into a polished HTML/CSS research-report PDF. Use when the user asks for Markdown -> HTML/CSS -> PDF, md to pdf, markdown report PDF, 投研报告 PDF, 研报排版导出, or wants a reusable report export workflow with Chinese typography, tables, print CSS, and PDF verification.
---

# Markdown Report PDF

Use this skill to turn Markdown reports into a styled HTML file and a PDF through the fixed path:

```text
Markdown -> HTML/CSS -> headless Chrome PDF -> pdfinfo/pdftotext verification
```

## Workflow

1. Identify source Markdown files and output directory. If multiple files belong together, preserve their logical order and combine them into one PDF.
2. Run the bundled script:

```bash
node ~/.codex/skills/markdown-report-pdf/scripts/render_markdown_report_pdf.mjs \
  --title "报告标题" \
  --subtitle "一句话结论或报告副标题" \
  --date "YYYY-MM-DD" \
  --out-dir "/absolute/output/dir" \
  --basename "output_basename" \
  "/absolute/source1.md" "/absolute/source2.md"
```

3. Verify the PDF:

```bash
pdfinfo "/absolute/output/dir/output_basename.pdf"
pdftotext "/absolute/output/dir/output_basename.pdf" - | sed -n '1,80p'
```

4. Report the HTML and PDF absolute paths to the user.

## Defaults

- Use A4 print CSS.
- Use a restrained professional research-report style suitable for Chinese financial reports.
- Keep source Markdown untouched.
- Generate both `.html` and `.pdf`.
- Add a cover page when `--title` is provided.
- Include all Markdown files as separate sections; files after the first start on a new page.

## Tool Notes

- The script uses `/Applications/Google Chrome.app` on macOS when available.
- If Chrome is missing, install a stable renderer such as Chrome, Playwright, Pandoc + wkhtmltopdf, or WeasyPrint, then rerun.
- Prefer the bundled script over ad hoc conversion commands so report typography, tables, print margins, and validation stay consistent.


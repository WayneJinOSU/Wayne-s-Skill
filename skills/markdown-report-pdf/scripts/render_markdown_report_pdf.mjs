#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
import { basename, dirname, extname, resolve } from "node:path";
import { tmpdir } from "node:os";
import { pathToFileURL } from "node:url";

function parseArgs(argv) {
  const options = {
    title: "",
    subtitle: "",
    date: new Date().toISOString().slice(0, 10),
    outDir: "",
    basename: "",
    chromePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    noCover: false,
    sources: [],
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--title") options.title = argv[++i] ?? "";
    else if (arg === "--subtitle") options.subtitle = argv[++i] ?? "";
    else if (arg === "--date") options.date = argv[++i] ?? "";
    else if (arg === "--out-dir") options.outDir = argv[++i] ?? "";
    else if (arg === "--basename") options.basename = argv[++i] ?? "";
    else if (arg === "--chrome") options.chromePath = argv[++i] ?? "";
    else if (arg === "--no-cover") options.noCover = true;
    else if (arg === "--help" || arg === "-h") {
      printHelp();
      process.exit(0);
    } else if (arg.startsWith("--")) {
      throw new Error(`Unknown option: ${arg}`);
    } else {
      options.sources.push(resolve(arg));
    }
  }

  if (options.sources.length === 0) throw new Error("At least one Markdown source is required.");
  options.sources.forEach((source) => {
    if (!existsSync(source)) throw new Error(`Source not found: ${source}`);
  });

  if (!options.outDir) options.outDir = dirname(options.sources[0]);
  options.outDir = resolve(options.outDir);
  if (!options.basename) {
    const first = basename(options.sources[0], extname(options.sources[0]));
    options.basename = options.sources.length === 1 ? `${first}_report` : "markdown_report";
  }

  return options;
}

function printHelp() {
  console.log(`Usage:
node render_markdown_report_pdf.mjs [options] source1.md [source2.md ...]

Options:
  --title      Cover/report title
  --subtitle   Cover subtitle
  --date       Report date, default today
  --out-dir    Output directory, default first source directory
  --basename   Output basename without extension
  --chrome     Chrome executable path
  --no-cover   Omit cover page
`);
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function addSlashBreakHints(html) {
  return html
    .split(/(<[^>]+>)/g)
    .map((part) => {
      if (part.startsWith("<")) return part;
      return part.replace(
        /\b[A-Za-z0-9][A-Za-z0-9+._-]*(?:\/[A-Za-z0-9][A-Za-z0-9+._-]*)+\b/g,
        (token) => token.replaceAll("/", "/<wbr>"),
      );
    })
    .join("");
}

function renderInline(raw) {
  const codeSpans = [];
  let text = escapeHtml(raw).replace(/`([^`]+)`/g, (_, code) => {
    const token = `@@CODE_${codeSpans.length}@@`;
    codeSpans.push(`<code>${code}</code>`);
    return token;
  });

  text = text
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');

  codeSpans.forEach((code, index) => {
    text = text.replace(`@@CODE_${index}@@`, code);
  });

  return addSlashBreakHints(text);
}

function isTableDivider(line) {
  return /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(line);
}

function parseTable(lines, startIndex) {
  const tableLines = [];
  let index = startIndex;
  while (index < lines.length && lines[index].trim().startsWith("|")) {
    tableLines.push(lines[index].trim());
    index += 1;
  }

  if (tableLines.length < 2 || !isTableDivider(tableLines[1])) return null;

  const splitRow = (line) =>
    line
      .replace(/^\|/, "")
      .replace(/\|$/, "")
      .split("|")
      .map((cell) => cell.trim());

  const headers = splitRow(tableLines[0]);
  const aligns = splitRow(tableLines[1]).map((cell) => {
    if (cell.startsWith(":") && cell.endsWith(":")) return "center";
    if (cell.endsWith(":")) return "right";
    return "left";
  });
  const rows = tableLines.slice(2).map(splitRow);
  const cellClass = (align, cell) => {
    const plain = cell.replace(/[`*_~]/g, "").trim();
    const cjkLength = Array.from(plain).filter((char) => /[\u3400-\u9fff]/.test(char)).length;
    const isShortCjk = cjkLength > 0 && Array.from(plain).length <= 6;
    return `${align || "left"}${isShortCjk ? " nowrap-cell" : ""}`;
  };

  const thead = `<thead><tr>${headers
    .map((cell, i) => `<th class="${cellClass(aligns[i], cell)}">${renderInline(cell)}</th>`)
    .join("")}</tr></thead>`;
  const tbody = `<tbody>${rows
    .map(
      (row) =>
        `<tr>${headers
          .map((_, i) => `<td class="${cellClass(aligns[i], row[i] ?? "")}">${renderInline(row[i] ?? "")}</td>`)
          .join("")}</tr>`,
    )
    .join("")}</tbody>`;

  return {
    html: `<div class="table-wrap"><table>${thead}${tbody}</table></div>`,
    nextIndex: index,
  };
}

function parseMarkdown(markdown) {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  const html = [];
  let index = 0;

  while (index < lines.length) {
    const trimmed = lines[index].trim();

    if (!trimmed) {
      index += 1;
      continue;
    }

    if (trimmed.startsWith("```")) {
      const code = [];
      index += 1;
      while (index < lines.length && !lines[index].trim().startsWith("```")) {
        code.push(lines[index]);
        index += 1;
      }
      index += 1;
      html.push(`<pre><code>${escapeHtml(code.join("\n"))}</code></pre>`);
      continue;
    }

    const heading = /^(#{1,6})\s+(.+)$/.exec(trimmed);
    if (heading) {
      const level = heading[1].length;
      html.push(`<h${level}>${renderInline(heading[2])}</h${level}>`);
      index += 1;
      continue;
    }

    const table = parseTable(lines, index);
    if (table) {
      html.push(table.html);
      index = table.nextIndex;
      continue;
    }

    if (/^[-*]\s+/.test(trimmed)) {
      const items = [];
      while (index < lines.length && /^[-*]\s+/.test(lines[index].trim())) {
        items.push(lines[index].trim().replace(/^[-*]\s+/, ""));
        index += 1;
      }
      html.push(`<ul>${items.map((item) => `<li>${renderInline(item)}</li>`).join("")}</ul>`);
      continue;
    }

    if (/^\d+\.\s+/.test(trimmed)) {
      const items = [];
      while (index < lines.length && /^\d+\.\s+/.test(lines[index].trim())) {
        items.push(lines[index].trim().replace(/^\d+\.\s+/, ""));
        index += 1;
      }
      html.push(`<ol>${items.map((item) => `<li>${renderInline(item)}</li>`).join("")}</ol>`);
      continue;
    }

    const paragraph = [];
    while (
      index < lines.length &&
      lines[index].trim() &&
      !/^(#{1,6})\s+/.test(lines[index].trim()) &&
      !lines[index].trim().startsWith("```") &&
      !lines[index].trim().startsWith("|") &&
      !/^[-*]\s+/.test(lines[index].trim()) &&
      !/^\d+\.\s+/.test(lines[index].trim())
    ) {
      paragraph.push(lines[index].trim());
      index += 1;
    }
    html.push(`<p>${renderInline(paragraph.join(" ").replace(/\s{2,}/g, " "))}</p>`);
  }

  return html.join("\n");
}

function buildHtml(options) {
  const sections = options.sources.map((source, index) => {
    const markdown = readFileSync(source, "utf8");
    const label = basename(source);
    return `<section class="report-section${index > 0 ? " page-break" : ""}" aria-label="${escapeHtml(label)}">
${parseMarkdown(markdown)}
</section>`;
  });

  const title = options.title || "Markdown Report";
  const subtitle = options.subtitle || "Generated from Markdown with HTML/CSS print styling.";
  const cover = options.noCover
    ? ""
    : `<section class="cover">
  <div class="cover-top">
    <div class="kicker">研究报告 / ${escapeHtml(options.date)}</div>
    <h1>${renderInline(title)}</h1>
    <p class="subtitle">${renderInline(subtitle)}</p>
  </div>
</section>`;

  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${escapeHtml(title)}</title>
  <style>
    :root {
      --ink: #1d232b;
      --muted: #667085;
      --line: #d9dee7;
      --line-strong: #aeb8c8;
      --wash: #f5f7fa;
      --blue: #184e77;
      --teal: #0f766e;
      --gold: #b7791f;
    }
    * { box-sizing: border-box; }
    html, body {
      margin: 0;
      padding: 0;
      background: #fff;
      color: var(--ink);
      font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
      font-size: 13px;
      line-height: 1.72;
      letter-spacing: 0;
      word-break: normal;
      overflow-wrap: normal;
      hyphens: none;
    }
    @page { size: A4; margin: 14mm 13mm 15mm; }
    a { color: var(--blue); text-decoration: none; overflow-wrap: break-word; }
    .cover {
      min-height: 257mm;
      display: grid;
      align-content: space-between;
      page-break-after: always;
    }
    .cover-top {
      border-top: 6px solid var(--blue);
      padding-top: 18mm;
    }
    .kicker {
      color: var(--teal);
      font-size: 12px;
      font-weight: 700;
      margin-bottom: 10mm;
    }
    .cover h1 {
      margin: 0;
      max-width: 160mm;
      font-size: 32px;
      line-height: 1.18;
      font-weight: 850;
      color: #111827;
    }
    .subtitle {
      margin: 8mm 0 0;
      max-width: 155mm;
      color: #374151;
      font-size: 16px;
      line-height: 1.7;
      font-weight: 520;
    }
    .cover-bottom {
      border-left: 3px solid var(--gold);
      padding: 8px 0 8px 13px;
      color: #334155;
      font-size: 12px;
    }
    .report-section {
      max-width: 181mm;
      margin: 0 auto;
    }
    .page-break { page-break-before: always; }
    h1, h2, h3, h4 {
      color: #111827;
      line-height: 1.32;
      page-break-after: avoid;
      break-after: avoid;
    }
    h1 {
      margin: 0 0 12px;
      padding-bottom: 10px;
      border-bottom: 2px solid var(--blue);
      font-size: 24px;
      font-weight: 850;
    }
    h2 {
      margin: 22px 0 9px;
      padding-top: 8px;
      border-top: 1px solid var(--line-strong);
      font-size: 18px;
      font-weight: 800;
    }
    h3 {
      margin: 16px 0 7px;
      font-size: 14.5px;
      font-weight: 800;
      color: var(--blue);
    }
    p { margin: 6px 0 8px; }
    strong { font-weight: 800; color: #101828; }
    code {
      padding: 1px 4px;
      border-radius: 4px;
      background: #eef2f7;
      color: #263241;
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
      font-size: 0.92em;
    }
    pre {
      margin: 10px 0 12px;
      padding: 10px 12px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #f8fafc;
      white-space: pre-wrap;
      page-break-inside: avoid;
    }
    pre code { padding: 0; background: transparent; color: #334155; font-size: 11.5px; line-height: 1.55; }
    ul, ol { margin: 6px 0 10px 19px; padding: 0; }
    li { margin: 3px 0; padding-left: 2px; }
    .table-wrap {
      margin: 9px 0 13px;
      page-break-inside: avoid;
      break-inside: avoid;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      border: 1px solid var(--line-strong);
      font-size: 10.6px;
      line-height: 1.45;
      table-layout: auto;
    }
    th, td {
      border: 1px solid var(--line);
      padding: 6px 7px;
      vertical-align: top;
      word-break: normal;
      overflow-wrap: normal;
      hyphens: none;
      line-break: strict;
    }
    th {
      background: #eaf1f7;
      color: #172033;
      font-weight: 800;
    }
    tbody tr:nth-child(even) td { background: #fafbfc; }
    .nowrap-cell {
      white-space: nowrap;
      word-break: keep-all;
    }
    td.right, th.right { text-align: right; white-space: nowrap; }
    td.center, th.center { text-align: center; }
    @media print {
      body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
      .table-wrap { overflow: visible; }
    }
  </style>
</head>
<body>
  <main>
    ${cover}
    ${sections.join("\n")}
  </main>
</body>
</html>`;
}

function printPdf(htmlPath, pdfPath, options) {
  if (!existsSync(options.chromePath)) {
    throw new Error(`Chrome not found: ${options.chromePath}`);
  }

  const userDataDir = mkdtempSync(resolve(tmpdir(), "markdown-report-pdf-chrome-"));
  const args = [
    "--headless",
    "--disable-gpu",
    "--disable-background-networking",
    "--disable-component-update",
    "--disable-default-apps",
    "--disable-extensions",
    "--disable-sync",
    "--metrics-recording-only",
    "--no-first-run",
    "--no-default-browser-check",
    `--user-data-dir=${userDataDir}`,
    "--no-pdf-header-footer",
    `--print-to-pdf=${pdfPath}`,
    pathToFileURL(htmlPath).href,
  ];

  try {
    const result = spawnSync(options.chromePath, args, {
      encoding: "utf8",
      killSignal: "SIGTERM",
      stdio: ["ignore", "pipe", "pipe"],
      timeout: 15000,
    });

    const pdfReady = (() => {
      try {
        return statSync(pdfPath).size > 10000;
      } catch {
        return false;
      }
    })();

    if (result.error && !(result.error.code === "ETIMEDOUT" && pdfReady)) throw result.error;
    if (result.status !== 0 && !pdfReady) {
      throw new Error(result.stderr || `Chrome exited with status ${result.status}`);
    }
  } finally {
    rmSync(userDataDir, { recursive: true, force: true });
  }
}

function main() {
  const options = parseArgs(process.argv.slice(2));
  const htmlPath = resolve(options.outDir, `${options.basename}.html`);
  const pdfPath = resolve(options.outDir, `${options.basename}.pdf`);

  writeFileSync(htmlPath, buildHtml(options), "utf8");
  printPdf(htmlPath, pdfPath, options);

  console.log(`HTML: ${htmlPath}`);
  console.log(`PDF: ${pdfPath}`);
}

main();

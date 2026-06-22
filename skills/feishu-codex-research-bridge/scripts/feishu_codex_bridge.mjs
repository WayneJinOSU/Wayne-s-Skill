#!/usr/bin/env node
import { spawn } from "node:child_process";
import { createInterface } from "node:readline";
import { randomUUID } from "node:crypto";
import { mkdir, readFile, readdir, rename, unlink, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { tmpdir } from "node:os";

const env = process.env;
const bridgeCwd = env.LARK_BRIDGE_CWD || process.cwd();
const gitCeilingDirectories = env.GIT_CEILING_DIRECTORIES || join(bridgeCwd, "..");
process.env.GIT_CEILING_DIRECTORIES = gitCeilingDirectories;

const CONFIG = {
  trigger: env.LARK_BRIDGE_TRIGGER || "/codex",
  researchTrigger: env.LARK_RESEARCH_TRIGGER || "/投研",
  defaultResearchNotifyChatId: env.LARK_RESEARCH_NOTIFY_CHAT_ID || "oc_817c284fb7fc2140b5817cdb0e0bb6a2",
  cwd: bridgeCwd,
  stateDir: env.LARK_BRIDGE_STATE_DIR || join(bridgeCwd, ".codex_research", "feishu_bridge"),
  replyAs: env.LARK_BRIDGE_REPLY_AS || "bot",
  consumeAs: env.LARK_BRIDGE_CONSUME_AS || "bot",
  maxReplyChars: Number(env.LARK_BRIDGE_MAX_REPLY_CHARS || 3500),
  maxPromptChars: Number(env.LARK_BRIDGE_MAX_PROMPT_CHARS || 12000),
  maxProcessedMessages: Number(env.LARK_BRIDGE_MAX_PROCESSED_MESSAGES || 2000),
  gitCeilingDirectories,
};

const dryRun = process.argv.includes("--dry-run");
const ignoreEventsBeforeMs = Date.now() - Number(env.LARK_BRIDGE_STARTUP_GRACE_MS || 30_000);
const chatQueues = new Map();
let sessionStoreCache = null;

function log(...args) {
  console.error("[bridge]", ...args);
}

function truncate(text, max) {
  if (!text || text.length <= max) return text || "";
  return `${text.slice(0, max)}\n\n[已截断，原始长度 ${text.length} 字符]`;
}

function cleanPrompt(event) {
  const raw = (event.content || "").trim();
  if (!raw) return "";

  if (event.chat_type === "p2p") {
    return raw.startsWith(CONFIG.trigger) ? raw.slice(CONFIG.trigger.length).trim() : raw;
  }

  if (raw.startsWith(CONFIG.trigger)) {
    return raw.slice(CONFIG.trigger.length).trim();
  }

  return "";
}

function researchCommandText(event) {
  const raw = (event.content || "").trim();
  if (!raw) return null;

  const triggers = Array.from(new Set([
    CONFIG.researchTrigger,
    CONFIG.researchTrigger.replace(/^\//, ""),
  ]));

  for (const trigger of triggers) {
    if (raw === trigger) return "";
    if (raw.startsWith(`${trigger} `)) return raw.slice(trigger.length).trim();
  }

  return null;
}

function codexSessionKey(event) {
  const chatId = event.chat_id || event.sender_id || "unknown";
  return `${event.chat_type || "chat"}:${chatId}`;
}

function sessionStorePath() {
  return join(CONFIG.stateDir, "codex_sessions.json");
}

async function loadSessionStore() {
  if (sessionStoreCache) return sessionStoreCache;
  try {
    sessionStoreCache = JSON.parse(await readFile(sessionStorePath(), "utf8"));
  } catch {
    sessionStoreCache = { version: 1, sessions: {}, processedMessages: {} };
  }
  if (!sessionStoreCache.sessions) sessionStoreCache.sessions = {};
  if (!sessionStoreCache.processedMessages) sessionStoreCache.processedMessages = {};
  return sessionStoreCache;
}

async function saveSessionStore(store) {
  await mkdir(CONFIG.stateDir, { recursive: true });
  const file = sessionStorePath();
  const tmp = `${file}.${process.pid}.${Date.now()}.tmp`;
  await writeFile(tmp, `${JSON.stringify(store, null, 2)}\n`, "utf8");
  await rename(tmp, file);
}

async function clearCodexSession(event) {
  const store = await loadSessionStore();
  const key = codexSessionKey(event);
  const old = store.sessions[key]?.threadId;
  delete store.sessions[key];
  await saveSessionStore(store);
  return old ? `已断开当前飞书会话绑定的 Codex session：${old}` : "当前飞书会话还没有绑定 Codex session。";
}

function eventTimeMs(event) {
  const raw = event.create_time || event.timestamp || "";
  const value = Number(raw);
  return Number.isFinite(value) ? value : 0;
}

function isStaleStartupEvent(event) {
  const ts = eventTimeMs(event);
  return ts > 0 && ts < ignoreEventsBeforeMs;
}

function processedMessageKey(event, messageId) {
  return event.event_id || messageId;
}

function pruneProcessedMessages(store) {
  const entries = Object.entries(store.processedMessages || {});
  if (entries.length <= CONFIG.maxProcessedMessages) return;
  entries.sort((a, b) => String(a[1].receivedAt || "").localeCompare(String(b[1].receivedAt || "")));
  store.processedMessages = Object.fromEntries(entries.slice(-CONFIG.maxProcessedMessages));
}

async function markMessageForProcessing(event, messageId) {
  const store = await loadSessionStore();
  const key = processedMessageKey(event, messageId);
  if (store.processedMessages[key]) return false;

  store.processedMessages[key] = {
    messageId,
    eventId: event.event_id || "",
    chatId: event.chat_id || "",
    chatType: event.chat_type || "",
    createTime: event.create_time || "",
    receivedAt: new Date().toISOString(),
  };
  pruneProcessedMessages(store);
  await saveSessionStore(store);
  return true;
}

function shouldIgnore(event) {
  if (!event || event.type !== "im.message.receive_v1") return true;
  if (event.message_type && !["text", "post"].includes(event.message_type)) return true;
  if (researchCommandText(event) !== null) return false;
  const prompt = cleanPrompt(event);
  return prompt.length === 0;
}

function runCommand(cmd, args, options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(cmd, args, {
      cwd: options.cwd || CONFIG.cwd,
      env: { ...process.env, ...(options.env || {}) },
      stdio: ["pipe", "pipe", "pipe"],
    });

    let stdout = "";
    let stderr = "";
    const timeoutMs = options.timeoutMs || 10 * 60 * 1000;
    const timer = setTimeout(() => {
      child.kill("SIGTERM");
      reject(new Error(`command timed out: ${cmd} ${args.join(" ")}`));
    }, timeoutMs);

    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", (chunk) => { stdout += chunk; });
    child.stderr.on("data", (chunk) => { stderr += chunk; });
    child.on("error", (err) => {
      clearTimeout(timer);
      reject(err);
    });
    child.on("close", (code) => {
      clearTimeout(timer);
      if (code === 0) resolve({ stdout, stderr });
      else reject(new Error(`command failed (${code}): ${cmd} ${args.join(" ")}\n${stderr || stdout}`));
    });

    child.stdin.end();
  });
}

function parseCodexJson(stdout) {
  let threadId = "";
  let agentText = "";
  for (const line of stdout.split(/\r?\n/)) {
    if (!line.trim()) continue;
    let item;
    try {
      item = JSON.parse(line);
    } catch {
      continue;
    }
    if (item.thread_id) threadId = item.thread_id;
    if (item.type === "item.completed" && item.item?.type === "agent_message" && item.item.text) {
      agentText = item.item.text;
    }
  }
  return { threadId, agentText };
}

async function readOutputFile(file) {
  try {
    return (await readFile(file, "utf8")).trim();
  } catch {
    return "";
  }
}

async function runCodex(args, positionals = []) {
  const outputFile = join(tmpdir(), `feishu-codex-${randomUUID()}.txt`);
  const fullArgs = [...args, "--output-last-message", outputFile, ...positionals];

  try {
    const { stdout, stderr } = await runCommand("codex", fullArgs, {
      cwd: CONFIG.cwd,
      timeoutMs: Number(env.LARK_BRIDGE_CODEX_TIMEOUT_MS || 20 * 60 * 1000),
    });

    const parsed = parseCodexJson(stdout);
    const outputText = await readOutputFile(outputFile);
    const text = outputText || parsed.agentText.trim() || stdout.trim() || stderr.trim();
    return {
      threadId: parsed.threadId,
      text: text || "Codex 没有返回可展示内容。",
    };
  } finally {
    await unlink(outputFile).catch(() => {});
  }
}

async function startCodexSession(prompt) {
  const args = [
    "exec",
    "--json",
    "--cd", CONFIG.cwd,
    "--sandbox", "workspace-write",
  ];

  const result = await runCodex(args, [prompt]);
  if (!result.threadId) throw new Error("Codex did not report a thread_id for the new session");
  return result;
}

async function resumeCodexSession(threadId, prompt) {
  const args = [
    "exec",
    "resume",
    "--json",
  ];
  const result = await runCodex(args, [threadId, prompt]);
  return { ...result, threadId: result.threadId || threadId };
}

async function callCodex(prompt, event) {
  const store = await loadSessionStore();
  const key = codexSessionKey(event);
  const existingThreadId = store.sessions[key]?.threadId;

  if (existingThreadId) {
    try {
      const resumed = await resumeCodexSession(existingThreadId, prompt);
      store.sessions[key] = {
        ...store.sessions[key],
        threadId: resumed.threadId,
        chatId: event.chat_id || "",
        chatType: event.chat_type || "",
        updatedAt: new Date().toISOString(),
      };
      await saveSessionStore(store);
      return resumed.text;
    } catch (err) {
      log("codex resume failed; starting a new session", { key, existingThreadId, error: err.message });
    }
  }

  const started = await startCodexSession(prompt);
  store.sessions[key] = {
    threadId: started.threadId,
    chatId: event.chat_id || "",
    chatType: event.chat_type || "",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
  await saveSessionStore(store);
  return started.text;
}

async function replyToMessage(messageId, text) {
  const reply = truncate(text, CONFIG.maxReplyChars);

  await runCommand("lark-cli", [
    "im", "+messages-reply",
    "--message-id", messageId,
    "--text", reply,
    "--as", CONFIG.replyAs,
    "--idempotency-key", randomUUID(),
  ], { cwd: CONFIG.cwd, timeoutMs: 60 * 1000 });
}

function localDateString(date = new Date()) {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(date);
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${values.year}-${values.month}-${values.day}`;
}

function safeTaskName(name) {
  return name
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "_")
    .replace(/[/:]+/g, "_")
    .replace(/[^\p{L}\p{N}_.-]+/gu, "_")
    .replace(/_+/g, "_")
    .replace(/^_+|_+$/g, "") || "research_task";
}

function normalizeSkill(raw = "auto") {
  const value = raw.toLowerCase().replace(/[` \t]/g, "");
  if (!value || value === "auto") return "auto";
  if (["supply", "supply-chain", "supply-chain-agentic", "supply-chain-agentic-research", "供应链", "供应链平台"].includes(value)) return "supply-chain-agentic-research";
  if (["chassis", "chassis-growth", "chassis-growth-agentic", "chassis-growth-agentic-research", "成长股", "底盘", "底盘成长"].includes(value)) return "chassis-growth-agentic-research";
  if (["catalyst", "tracker", "equity-catalyst", "equity-catalyst-tracker", "爆点", "跟踪", "催化"].includes(value)) return "equity-catalyst-tracker";
  if (["valuation", "growth-stock-valuation", "估值", "peg"].includes(value)) return "growth-stock-valuation";
  if (["xhs", "redbook", "xiaohongshu", "finance-research-xhs", "小红书", "小红书写作", "投研小红书", "笔记", "长文笔记"].includes(value)) return "finance-research-xhs";
  if (["industry", "industry-chain", "industry-chain-agentic", "industry-chain-agentic-research", "行业", "产业链"].includes(value)) return "industry-chain-agentic-research";
  return value;
}

function isKnownSkill(raw = "") {
  return [
    "auto",
    "supply-chain-agentic-research",
    "chassis-growth-agentic-research",
    "equity-catalyst-tracker",
    "growth-stock-valuation",
    "finance-research-xhs",
    "industry-chain-agentic-research",
  ].includes(normalizeSkill(raw));
}

function naturalTaskName(text) {
  const snippet = text
    .replace(/\s+/g, "")
    .replace(/[^\p{L}\p{N}_.-]+/gu, "")
    .slice(0, 64);
  return snippet ? `自然语言_${snippet}` : "自然语言投研任务";
}

function naturalTaskDescription(text) {
  return [
    "用户原始指令：",
    text,
    "",
    "执行要求：",
    "- 不要依赖 bridge 脚本做公司名、行业或 skill 判断。",
    "- 请 Codex 根据用户原始指令自行理解任务，选择合适的投研 skill，并按该 skill 的正式流程执行。",
    "- 是否启动 subagent 以用户原始指令为准；若用户明确说不启动 subagent，则不得启动真实 subagent。",
    "- 输出正式投研产物，并保留中间研究文件、证据边界、反方审查和跟踪/估值接力所需材料。",
  ].join("\n");
}

function renderBrief(template, { name, description, skill }) {
  const lines = template.split(/\r?\n/);
  const out = [];
  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i];
    if (line === "# 任务名称") {
      out.push(`# ${name}`);
      continue;
    }
    if (line === "- 公司/行业：") {
      out.push(`- 公司/行业：${name}`);
      continue;
    }
    if (/^- 推荐 skill：/.test(line)) {
      out.push(`- 推荐 skill：${skill}`);
      continue;
    }
    out.push(line);
    if (line === "## 核心问题" && description) {
      out.push("");
      out.push(description);
    }
  }
  return `${out.join("\n").replace(/\n+$/g, "")}\n`;
}

async function uniqueTaskDir(taskName) {
  const tasksDir = join(CONFIG.cwd, "tasks");
  const base = `${localDateString()}_${safeTaskName(taskName)}`;
  let candidate = join(tasksDir, base);
  for (let idx = 2; ; idx += 1) {
    try {
      await readFile(join(candidate, "status"), "utf8");
      candidate = join(tasksDir, `${base}_${idx}`);
    } catch {
      return candidate;
    }
  }
}

function taskNotifyChatId(event) {
  if (event.chat_type === "group" && event.chat_id) return event.chat_id;
  return CONFIG.defaultResearchNotifyChatId;
}

async function createResearchTask({ name, skill, description, event }) {
  const taskDir = await uniqueTaskDir(name);
  const template = await readFile(join(CONFIG.cwd, "tasks", "_template", "brief.md"), "utf8");
  const normalizedSkill = normalizeSkill(skill || "auto");
  const now = new Date().toISOString();

  await mkdir(join(taskDir, "sources"), { recursive: true });
  await writeFile(join(taskDir, "brief.md"), renderBrief(template, {
    name,
    skill: normalizedSkill,
    description,
  }), "utf8");
  await writeFile(join(taskDir, "status"), "queued\n", "utf8");
  await writeFile(join(taskDir, "skill"), `${normalizedSkill}\n`, "utf8");
  await writeFile(join(taskDir, "created_at"), `${now}\n`, "utf8");
  await writeFile(join(taskDir, "notify.json"), `${JSON.stringify({
    source: "feishu",
    source_chat_id: event.chat_id || "",
    source_chat_type: event.chat_type || "",
    sender_id: event.sender_id || "",
    source_message_id: event.message_id || event.id || "",
    notify_chat_id: taskNotifyChatId(event),
    notify_as: CONFIG.replyAs,
    created_at: now,
  }, null, 2)}\n`, "utf8");
  await writeFile(join(taskDir, "source_message.json"), `${JSON.stringify({
    event_id: event.event_id || "",
    message_id: event.message_id || event.id || "",
    chat_id: event.chat_id || "",
    chat_type: event.chat_type || "",
    sender_id: event.sender_id || "",
    content: event.content || "",
    create_time: event.create_time || "",
  }, null, 2)}\n`, "utf8");

  return {
    taskDir,
    skill: normalizedSkill,
    notifyChatId: taskNotifyChatId(event),
  };
}

async function kickResearchQueue() {
  try {
    const { stdout, stderr } = await runCommand(join(CONFIG.cwd, "scripts", "kick_research_queue.sh"), [], {
      cwd: CONFIG.cwd,
      timeoutMs: 15 * 1000,
    });
    return {
      ok: true,
      message: (stdout || stderr).trim() || "research queue kicked",
    };
  } catch (err) {
    return {
      ok: false,
      message: err.message,
    };
  }
}

async function readTaskSummaries() {
  const tasksDir = join(CONFIG.cwd, "tasks");
  const entries = await readdir(tasksDir, { withFileTypes: true });
  const summaries = [];
  for (const entry of entries) {
    if (!entry.isDirectory() || entry.name === "_template") continue;
    const taskDir = join(tasksDir, entry.name);
    const readFirst = async (file, fallback = "") => {
      try {
        return (await readFile(join(taskDir, file), "utf8")).trim();
      } catch {
        return fallback;
      }
    };
    const brief = await readFirst("brief.md");
    const title = brief.split(/\r?\n/).find((line) => line.startsWith("# "))?.slice(2).trim() || entry.name;
    summaries.push({
      id: entry.name,
      title,
      status: await readFirst("status", "unknown"),
      skill: await readFirst("selected_skill", await readFirst("skill", "auto")),
      createdAt: await readFirst("created_at", ""),
      finishedAt: await readFirst("finished_at", ""),
    });
  }
  summaries.sort((a, b) => a.id.localeCompare(b.id));
  return summaries;
}

function formatTaskSummary(task) {
  const time = task.finishedAt || task.createdAt || "";
  return `- ${task.id} | ${task.status} | ${task.skill}${time ? ` | ${time}` : ""}`;
}

async function handleResearchCommand(commandText, event) {
  const tokens = commandText.trim().split(/\s+/).filter(Boolean);
  const command = tokens.shift() || "help";

  if (["help", "帮助"].includes(command)) {
    return [
      "投研命令：",
      "/投研 <自然语言任务>",
      "/投研 new <任务名> [skill] <任务描述>",
      "/投研 list",
      "/投研 status [关键词]",
    ].join("\n");
  }

  if (!commandText.trim()) {
    return "请在 /投研 后面写自然语言任务，或使用 /投研 help 查看用法。";
  }

  if (["new", "create", "创建", "新增"].includes(command)) {
    const name = tokens.shift();
    if (!name) return "缺少任务名。用法：/投研 new <任务名> [skill] <任务描述>";

    let skill = "auto";
    if (tokens[0] && isKnownSkill(tokens[0])) {
      skill = normalizeSkill(tokens.shift());
    }
    const description = tokens.join(" ").trim();
    const task = await createResearchTask({ name, skill, description, event });
    const kick = await kickResearchQueue();
    return [
      "已创建投研任务：",
      `任务：${name}`,
      `Skill：${task.skill}`,
      "状态：queued",
      `目录：${task.taskDir}`,
      `完成后发送到：${task.notifyChatId}`,
      `队列触发：${kick.ok ? kick.message : `失败：${kick.message}`}`,
    ].join("\n");
  }

  if (["list", "列表"].includes(command)) {
    const tasks = await readTaskSummaries();
    if (tasks.length === 0) return "当前没有投研任务。";
    return `最近投研任务：\n${tasks.slice(-10).map(formatTaskSummary).join("\n")}`;
  }

  if (["status", "状态"].includes(command)) {
    const keyword = tokens.join(" ").trim();
    let tasks = await readTaskSummaries();
    if (keyword) tasks = tasks.filter((task) => task.id.includes(keyword) || task.title.includes(keyword));
    if (tasks.length === 0) return keyword ? `没有找到匹配任务：${keyword}` : "当前没有投研任务。";
    return `投研任务状态：\n${tasks.slice(-10).map(formatTaskSummary).join("\n")}`;
  }

  const naturalText = commandText.trim();
  const task = await createResearchTask({
    name: naturalTaskName(naturalText),
    skill: "auto",
    description: naturalTaskDescription(naturalText),
    event,
  });
  const kick = await kickResearchQueue();
  return [
    "已创建投研任务：",
    "来源：自然语言透传",
    `任务：${naturalTaskName(naturalText)}`,
    `Skill：${task.skill}`,
    "状态：queued",
    `目录：${task.taskDir}`,
    `完成后发送到：${task.notifyChatId}`,
    `队列触发：${kick.ok ? kick.message : `失败：${kick.message}`}`,
  ].join("\n");
}

async function handleEvent(event) {
  if (shouldIgnore(event)) return;

  const researchText = researchCommandText(event);
  const prompt = researchText === null ? cleanPrompt(event) : `${CONFIG.researchTrigger} ${researchText}`.trim();
  const messageId = event.message_id || event.id;
  if (!messageId) return;

  if (isStaleStartupEvent(event)) {
    log("ignored stale startup event", {
      message_id: messageId,
      create_time: event.create_time || "",
      prompt: truncate(prompt, 120),
    });
    return;
  }

  if (!(await markMessageForProcessing(event, messageId))) {
    log("ignored duplicate event", {
      message_id: messageId,
      event_id: event.event_id || "",
      prompt: truncate(prompt, 120),
    });
    return;
  }

  log("received", {
    chat_type: event.chat_type,
    message_type: event.message_type,
    message_id: messageId,
    prompt: truncate(prompt, 120),
  });

  if (dryRun) return;

  try {
    if (researchText !== null) {
      await replyToMessage(messageId, await handleResearchCommand(researchText, event));
      return;
    }

    if (/^\/?(reset|new|new-session)$/i.test(prompt.trim())) {
      await replyToMessage(messageId, await clearCodexSession(event));
      return;
    }

    const answer = await callCodex(truncate(prompt, CONFIG.maxPromptChars), event);
    await replyToMessage(messageId, answer);
  } catch (err) {
    log("handler failed", err.message);
    await replyToMessage(messageId, `处理失败：${err.message}`);
  }
}

function enqueueEvent(event) {
  const key = codexSessionKey(event);
  const previous = chatQueues.get(key) || Promise.resolve();
  const next = previous.catch(() => {}).then(() => handleEvent(event));
  const tracked = next.finally(() => {
    if (chatQueues.get(key) === tracked) chatQueues.delete(key);
  });
  chatQueues.set(key, tracked);
}

function startConsumer() {
  const eventKey = "im.message.receive_v1";
  const args = ["event", "consume", eventKey, "--as", CONFIG.consumeAs];

  log("starting", {
    eventKey,
    trigger: CONFIG.trigger,
    cwd: CONFIG.cwd,
    gitCeilingDirectories: CONFIG.gitCeilingDirectories,
  });

  const child = spawn("lark-cli", args, {
    cwd: CONFIG.cwd,
    env: process.env,
    stdio: ["pipe", "pipe", "pipe"],
  });

  child.stdin.write("\n");

  child.stderr.setEncoding("utf8");
  child.stderr.on("data", (chunk) => {
    for (const line of chunk.split(/\r?\n/)) {
      if (line.trim()) log("event stderr:", line);
    }
  });

  const rl = createInterface({ input: child.stdout });
  rl.on("line", async (line) => {
    if (!line.trim()) return;
    try {
      const event = JSON.parse(line);
      enqueueEvent(event);
    } catch (err) {
      log("bad event line", err.message, line.slice(0, 300));
    }
  });

  child.on("exit", (code, signal) => {
    log("event consumer exited", { code, signal });
    process.exit(code ?? 0);
  });

  process.on("SIGINT", () => {
    log("stopping");
    child.kill("SIGTERM");
  });
  process.on("SIGTERM", () => {
    log("stopping");
    child.kill("SIGTERM");
  });
}

startConsumer();

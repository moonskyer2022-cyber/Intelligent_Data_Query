const API_BASE = window.location.origin;
const SESSION_KEY = "aiquery_session_id";

const state = {
  loading: false,
};

const chat = document.getElementById("chat");
const welcome = document.getElementById("welcome");
const composer = document.getElementById("composer");
const questionInput = document.getElementById("questionInput");
const sendBtn = document.getElementById("sendBtn");
const clearChatBtn = document.getElementById("clearChatBtn");
const examplesEl = document.getElementById("examples");
const tableGridEl = document.getElementById("tableGrid");
const runBadge = document.getElementById("runBadge");
const statusDot = document.getElementById("statusDot");
const servicePill = document.getElementById("servicePill");
const databasePill = document.getElementById("databasePill");
const llmPill = document.getElementById("llmPill");
const serviceDetail = document.getElementById("serviceDetail");
const databaseDetail = document.getElementById("databaseDetail");
const llmDetail = document.getElementById("llmDetail");
const viewButtons = document.querySelectorAll(".view-switch button");
const visualPanels = document.querySelectorAll(".visual-panel");

const businessNames = {
  product: "商品信息",
  category: "商品分类",
  user: "用户信息",
  orders: "订单记录",
  order_item: "订单明细",
  purchase_record: "采购记录",
  chat_record: "对话记录",
  query_example: "示例问题",
};

const businessMeta = {
  product: { icon: "商", desc: "商品名称、价格、库存等基础信息" },
  category: { icon: "类", desc: "商品分类、类目层级和归属关系" },
  user: { icon: "客", desc: "用户基础资料和增长情况" },
  orders: { icon: "单", desc: "订单金额、时间、地区和状态" },
  order_item: { icon: "明", desc: "订单中的商品明细和数量" },
  purchase_record: { icon: "采", desc: "采购金额、供应和入库记录" },
  chat_record: { icon: "问", desc: "历史问数记录和上下文" },
  query_example: { icon: "例", desc: "常用业务问题模板" },
};

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function getSessionId() {
  let id = localStorage.getItem(SESSION_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(SESSION_KEY, id);
  }
  return id;
}

function setLoading(value) {
  state.loading = value;
  questionInput.disabled = value;
  sendBtn.disabled = value;
  sendBtn.innerHTML = value ? "<span>分析中</span><b>…</b>" : "<span>开始分析</span><b>↗</b>";
  runBadge.textContent = value ? "正在分析" : "等待提问";
}

function scrollToBottom() {
  chat.scrollTop = chat.scrollHeight;
}

function setPill(element, text, type) {
  element.textContent = text;
  element.className = `pill ${type}`;
}

function getStatusLabel(payload) {
  if (!payload) return "未知";
  if (payload.status === "ok") return "正常";
  if (payload.status === "warning") return "需检查";
  return "异常";
}

function simplifyBackendMessage(message, fallback) {
  if (!message) return fallback;
  if (message.includes("API") || message.includes("FastAPI")) return "服务已可用";
  if (message.includes("LLM") || message.includes("API Key")) return "智能分析已就绪";
  if (message.includes("数据库") || message.includes("表")) return "数据连接正常";
  return fallback;
}

function renderExamples(examples) {
  const fallback = [
    "各省份订单金额排名，并生成图表",
    "本月订单 GMV 是多少？",
    "各类目商品销量对比",
    "新增用户趋势如何？",
  ];
  const list = examples.length ? examples : fallback;

  examplesEl.innerHTML = `
    <div class="prompt-title">推荐问题</div>
    <div class="prompt-list">
      ${list.slice(0, 6).map((item) => `
        <button type="button" title="${escapeHtml(item)}">
          <span>${escapeHtml(item)}</span>
          <b>运行</b>
        </button>
      `).join("")}
    </div>
  `;

  examplesEl.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      questionInput.value = button.textContent;
      questionInput.focus();
    });
  });
}

function renderTables(tables) {
  if (!tables.length) {
    tableGridEl.innerHTML = '<p class="empty-note">暂时没有加载到可分析数据。</p>';
    return;
  }

  tableGridEl.innerHTML = tables.map(({ label, name }, index) => {
    const displayName = businessNames[name] || label;
    const meta = businessMeta[name] || { icon: "▦", desc: "可用于业务分析" };
    return `
      <article class="scope-card">
        <span class="scope-icon">${meta.icon}</span>
        <div>
          <strong>${escapeHtml(displayName)}</strong>
          <small>${escapeHtml(meta.desc)}</small>
        </div>
      </article>
    `;
  }).join("");
}

function appendMessage(role, content, options = {}) {
  welcome.hidden = true;
  document.querySelector(".visual-tabs")?.setAttribute("hidden", "");
  const article = document.createElement("article");
  article.className = `message ${role}`;
  const title = role === "user" ? "业务问题" : "分析结果";
  const chart = options.chartUrl
    ? `<figure class="chart-frame"><img src="${options.chartUrl.startsWith("http") ? options.chartUrl : `${API_BASE}${options.chartUrl}`}" alt="分析结果图表" /></figure>`
    : "";
  const details = options.detailsHtml || "";

  article.innerHTML = `
    <header>
      <strong>${title}</strong>
      <span>${escapeHtml(options.meta || "")}</span>
    </header>
    <div class="message-body">${escapeHtml(content)}</div>
    ${details}
    ${chart}
  `;
  chat.appendChild(article);
  scrollToBottom();
  return article;
}

function renderResultDetails(data) {
  const rows = Array.isArray(data.rows) ? data.rows.slice(0, 8) : [];
  const plan = data.query_plan ? escapeHtml(JSON.stringify(data.query_plan, null, 2)) : "暂无结构化查询计划";
  const rowsHtml = rows.length
    ? `<div class="result-rows">${rows.map((row) => {
        const fields = row.fields || row;
        return `<div class="result-row">${Object.entries(fields).map(([key, value]) => `<span><b>${escapeHtml(key)}</b>${escapeHtml(value)}</span>`).join("")}</div>`;
      }).join("")}</div>`
    : "<p class=\"result-empty\">暂无结果明细</p>";
  const elapsed = Number.isFinite(data.execution_ms) ? ` · ${data.execution_ms} ms` : "";
  return `<details class="result-details"><summary>查看查询过程与结果${elapsed}</summary><div class="result-details-body"><strong>结构化查询计划</strong><pre>${plan}</pre><strong>结果明细（最多展示 8 条）</strong>${rowsHtml}</div></details>`;
}

function appendProgress() {
  welcome.hidden = true;
  const article = document.createElement("article");
  article.className = "message assistant progress";
  article.innerHTML = `
    <header><strong>处理进度</strong><span>实时</span></header>
    <div class="progress-track">
      <span>理解问题</span>
      <span>匹配数据</span>
      <span>计算结果</span>
      <span>生成结论</span>
    </div>
  `;
  chat.appendChild(article);
  scrollToBottom();
  return article;
}

function setOffline() {
  statusDot.className = "status-dot danger";
  setPill(servicePill, "问数服务离线", "danger");
  setPill(databasePill, "数据连接未知", "muted");
  setPill(llmPill, "智能分析未知", "muted");
  serviceDetail.textContent = "问数服务未响应";
  databaseDetail.textContent = "暂时无法确认数据连接";
  llmDetail.textContent = "暂时无法确认智能分析能力";
}

function updateHealth(payload) {
  const serviceOk = payload.service?.status === "ok";
  const databaseOk = payload.database?.status === "ok";
  const llmOk = payload.llm?.status === "ok";
  const allOk = serviceOk && databaseOk && llmOk;

  statusDot.className = `status-dot ${allOk ? "ok" : "warning"}`;
  setPill(servicePill, serviceOk ? "问数服务正常" : "问数服务异常", serviceOk ? "ok" : "danger");
  setPill(databasePill, `数据连接${getStatusLabel(payload.database)}`, databaseOk ? "ok" : "warning");
  setPill(llmPill, `智能分析${getStatusLabel(payload.llm)}`, llmOk ? "ok" : "warning");

  serviceDetail.textContent = serviceOk ? "服务已可用" : "服务状态异常";
  databaseDetail.textContent = simplifyBackendMessage(payload.database?.message, databaseOk ? "数据连接正常" : "数据连接需检查");
  llmDetail.textContent = simplifyBackendMessage(payload.llm?.message, llmOk ? "智能分析已就绪" : "智能分析需检查");
}

async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE}/health`);
    if (!response.ok) throw new Error("health failed");
    updateHealth(await response.json());
  } catch {
    setOffline();
  }
}

async function loadMeta() {
  try {
    const [examplesResponse, tablesResponse] = await Promise.all([
      fetch(`${API_BASE}/examples`),
      fetch(`${API_BASE}/tables`),
    ]);
    const examples = examplesResponse.ok ? (await examplesResponse.json()).examples || [] : [];
    const tables = tablesResponse.ok ? (await tablesResponse.json()).tables || [] : [];
    renderExamples(examples);
    renderTables(tables);
  } catch {
    renderExamples([]);
    renderTables([]);
  }
}

async function submitQuestion() {
  const question = questionInput.value.trim();
  if (!question || state.loading) return;

  appendMessage("user", question, { meta: "已提交" });
  questionInput.value = "";
  setLoading(true);
  const progress = appendProgress();

  try {
    const response = await fetch(`${API_BASE}/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_question: question,
        session_id: getSessionId(),
      }),
    });

    progress.remove();
    if (!response.ok) {
      const errorPayload = await response.json().catch(() => ({}));
      const detail = errorPayload.detail || {};
      const message = typeof detail === "string" ? detail : detail.message;
      appendMessage("assistant", message || "本次分析没有成功，请稍后重试或换一个更明确的问题。", { meta: detail.code || "分析失败" }).classList.add("error");
      runBadge.textContent = "分析失败";
      return;
    }

    const data = await response.json();
    appendMessage("assistant", data.final_answer || "暂未得到有效结论。", {
      chartUrl: data.chart_url,
      detailsHtml: renderResultDetails(data),
      meta: data.chart_url ? "已生成图表" : "已生成结论",
    });
    runBadge.textContent = data.chart_url ? "已生成图表" : "已生成结论";
  } catch {
    progress.remove();
    appendMessage("assistant", "当前无法完成分析，请确认本地服务正在运行。", { meta: "连接失败" }).classList.add("error");
    runBadge.textContent = "连接失败";
  } finally {
    setLoading(false);
    questionInput.focus();
  }
}

function clearConversation() {
  chat.innerHTML = "";
  welcome.hidden = false;
  document.querySelector(".visual-tabs")?.removeAttribute("hidden");
  runBadge.textContent = "等待提问";
  localStorage.removeItem(SESSION_KEY);
  questionInput.focus();
}

function bindSpotlightCards() {
  document.querySelectorAll(".surface-card").forEach((card) => {
    card.addEventListener("pointermove", (event) => {
      const rect = card.getBoundingClientRect();
      card.style.setProperty("--mx", `${event.clientX - rect.left}px`);
      card.style.setProperty("--my", `${event.clientY - rect.top}px`);
    });
  });
}

function bindViewSwitch() {
  viewButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const view = button.dataset.view;
      viewButtons.forEach((item) => item.classList.toggle("active", item === button));
      visualPanels.forEach((panel) => panel.classList.toggle("active", panel.dataset.panel === view));
    });
  });
}

composer.addEventListener("submit", (event) => {
  event.preventDefault();
  submitQuestion();
});

questionInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    submitQuestion();
  }
});

clearChatBtn.addEventListener("click", clearConversation);

bindSpotlightCards();
bindViewSwitch();
loadMeta();
checkHealth();
setInterval(checkHealth, 30000);

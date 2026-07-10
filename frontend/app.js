const API_BASE = window.location.origin;
const SESSION_KEY = "aiquery_session_id";

const appState = {
  loading: false,
  health: null,
};

const chat = document.getElementById("chat");
const welcome = document.getElementById("welcome");
const composer = document.getElementById("composer");
const questionInput = document.getElementById("questionInput");
const sendBtn = document.getElementById("sendBtn");
const clearChatBtn = document.getElementById("clearChatBtn");
const statusDot = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");
const serviceDetail = document.getElementById("serviceDetail");
const databaseDetail = document.getElementById("databaseDetail");
const llmDetail = document.getElementById("llmDetail");
const heroServiceState = document.getElementById("heroServiceState");
const heroDataState = document.getElementById("heroDataState");
const heroHealthSummary = document.getElementById("heroHealthSummary");
const healthStatusBadge = document.getElementById("healthStatusBadge");
const examplesEl = document.getElementById("examples");
const tableGridEl = document.getElementById("tableGrid");

function getSessionId() {
  let id = localStorage.getItem(SESSION_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(SESSION_KEY, id);
  }
  return id;
}

function resetSession() {
  localStorage.removeItem(SESSION_KEY);
}

function setLoading(value) {
  appState.loading = value;
  sendBtn.disabled = value;
  questionInput.disabled = value;
}

function hideWelcome() {
  if (welcome) {
    welcome.style.display = "none";
  }
}

function showWelcome() {
  if (welcome) {
    welcome.style.display = "";
  }
}

function scrollToBottom() {
  chat.scrollTop = chat.scrollHeight;
}

function formatRelativeStatus(data) {
  if (!data) {
    return "等待状态";
  }
  if (data.status === "ok") {
    return "已就绪";
  }
  if (data.status === "warning") {
    return "需检查";
  }
  return "不可用";
}

function setHealthPill(el, label, type) {
  el.textContent = label;
  el.classList.remove("muted", "is-warning", "is-danger");
  if (type === "warning") {
    el.classList.add("is-warning");
  } else if (type === "danger") {
    el.classList.add("is-danger");
  } else if (type === "muted") {
    el.classList.add("muted");
  }
}

function renderExamples(examples) {
  examplesEl.innerHTML = "";

  if (!examples.length) {
    const empty = document.createElement("div");
    empty.className = "empty-grid-note";
    empty.textContent = "暂时没有示例问题，启动后端并检查 query_example 表即可加载。";
    examplesEl.appendChild(empty);
    return;
  }

  examples.forEach((text, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "example-card";
    button.innerHTML = `
      <div>
        <div class="table-meta">Demo Prompt ${String(index + 1).padStart(2, "0")}</div>
        <h3>${text}</h3>
      </div>
      <div class="example-card-footer">
        <span>直接运行</span>
        <span aria-hidden="true">→</span>
      </div>
    `;
    button.addEventListener("click", () => {
      questionInput.value = text;
      questionInput.focus();
      submitQuestion();
    });
    examplesEl.appendChild(button);
  });
}

function renderTables(tables) {
  tableGridEl.innerHTML = "";

  if (!tables.length) {
    const empty = document.createElement("div");
    empty.className = "empty-grid-note";
    empty.textContent = "未能加载数据表信息，请检查 /tables 接口和数据库连接。";
    tableGridEl.appendChild(empty);
    return;
  }

  tables.forEach(({ label, name }) => {
    const card = document.createElement("article");
    card.className = "table-card";
    card.innerHTML = `
      <div class="table-card-header">
        <div>
          <div class="table-meta">Logical Table</div>
          <strong>${label}</strong>
        </div>
        <span class="table-token">${name}</span>
      </div>
    `;
    tableGridEl.appendChild(card);
  });
}

function createMessage(role, content, chartUrl, metaText = "") {
  hideWelcome();

  const message = document.createElement("article");
  message.className = `message ${role}`;

  const roleLabel = role === "user" ? "你" : "AI";
  const chartMarkup = chartUrl
    ? `
      <div class="message-chart">
        <img src="${chartUrl.startsWith("http") ? chartUrl : `${API_BASE}${chartUrl}`}" alt="查询结果图表" loading="lazy" />
      </div>
    `
    : "";

  const metaMarkup = metaText ? `<div class="message-meta">${metaText}</div>` : "";

  message.innerHTML = `
    <div class="message-head">
      <span class="message-role">${roleLabel}</span>
      ${metaMarkup}
    </div>
    <div class="message-body">${content}</div>
    ${chartMarkup}
  `;

  chat.appendChild(message);
  scrollToBottom();
}

function createLoadingMessage() {
  hideWelcome();

  const loading = document.createElement("article");
  loading.className = "loading-message";
  loading.id = "loadingMsg";
  loading.innerHTML = `
    <div class="message-head">
      <span class="message-role">AI</span>
      <div class="message-meta">正在执行查询链路</div>
    </div>
    <div class="message-body">
      正在解析问题、规划查询并组织结果
      <span class="loading-dots" aria-hidden="true"><span></span><span></span><span></span></span>
    </div>
  `;
  chat.appendChild(loading);
  scrollToBottom();
  return loading;
}

function setStatusOffline(message = "服务不可用") {
  statusDot.className = "status-dot offline";
  statusText.textContent = message;
  serviceDetail.textContent = "后端未响应";
  databaseDetail.textContent = "无法获取数据库状态";
  llmDetail.textContent = "无法获取模型状态";
  setHealthPill(heroServiceState, "服务离线", "danger");
  setHealthPill(heroDataState, "状态未知", "danger");
  heroHealthSummary.textContent = "后端未连接";
  healthStatusBadge.textContent = "离线";
}

function updateHealthUI(payload) {
  appState.health = payload;
  const status = payload.status || "warning";

  if (status === "ok") {
    statusDot.className = "status-dot online";
    statusText.textContent = "服务与依赖已就绪";
  } else {
    statusDot.className = "status-dot";
    statusText.textContent = "服务在线，部分依赖待检查";
  }

  serviceDetail.textContent = payload.service?.status === "ok" ? "API 服务可访问" : "服务状态异常";
  databaseDetail.textContent = payload.database?.message || "数据库状态未知";
  llmDetail.textContent = payload.llm?.message || "LLM 状态未知";

  setHealthPill(
    heroServiceState,
    payload.service?.status === "ok" ? "服务在线" : "服务异常",
    payload.service?.status === "ok" ? "ok" : "danger"
  );
  setHealthPill(heroDataState, `数据库 ${formatRelativeStatus(payload.database)}`, payload.database?.status || "warning");

  heroHealthSummary.textContent =
    status === "ok" ? "服务、数据库、LLM 已全部就绪" : "服务可用，但仍有配置项需要关注";
  healthStatusBadge.textContent = status === "ok" ? "全部通过" : "存在告警";
}

async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) {
      throw new Error("health-check-failed");
    }
    const payload = await res.json();
    updateHealthUI(payload);
  } catch {
    setStatusOffline("无法连接后端服务");
  }
}

async function loadMeta() {
  try {
    const [exampleRes, tableRes] = await Promise.all([
      fetch(`${API_BASE}/examples`),
      fetch(`${API_BASE}/tables`),
    ]);

    if (exampleRes.ok) {
      const data = await exampleRes.json();
      renderExamples(data.examples || []);
    } else {
      renderExamples([]);
    }

    if (tableRes.ok) {
      const data = await tableRes.json();
      renderTables(data.tables || []);
    } else {
      renderTables([]);
    }
  } catch {
    renderExamples([
      "本月订单 GMV 是多少？",
      "各省份订单金额排名",
      "查询所有商品名称和价格",
      "各类目销量对比图",
    ]);
    renderTables([]);
  }
}

async function submitQuestion() {
  const question = questionInput.value.trim();
  if (!question || appState.loading) {
    return;
  }

  createMessage("user", question, null, "已发送到 AIQuery");
  questionInput.value = "";
  questionInput.style.height = "auto";
  setLoading(true);

  const loadingMessage = createLoadingMessage();

  try {
    const response = await fetch(`${API_BASE}/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_question: question,
        session_id: getSessionId(),
      }),
    });

    loadingMessage.remove();

    if (!response.ok) {
      const errorPayload = await response.json().catch(() => ({}));
      const detail = errorPayload.detail || `请求失败（${response.status}）`;
      createMessage("assistant", typeof detail === "string" ? detail : JSON.stringify(detail), null, "返回错误");
      chat.lastElementChild?.classList.add("error");
      return;
    }

    const data = await response.json();
    const meta = data.chart_url ? "已返回文本结果与图表" : "已返回文本结果";
    createMessage("assistant", data.final_answer || "没有拿到有效回答。", data.chart_url, meta);
  } catch {
    loadingMessage.remove();
    createMessage(
      "assistant",
      "无法连接后端服务，请确认已经运行 `python run.py --server`，并检查健康检查接口是否可访问。",
      null,
      "连接失败"
    );
    chat.lastElementChild?.classList.add("error");
  } finally {
    setLoading(false);
    questionInput.focus();
  }
}

function clearConversation() {
  chat.querySelectorAll(".message, .loading-message").forEach((node) => node.remove());
  resetSession();
  showWelcome();
  questionInput.focus();
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

questionInput.addEventListener("input", () => {
  questionInput.style.height = "auto";
  questionInput.style.height = `${Math.min(questionInput.scrollHeight, 180)}px`;
});

clearChatBtn.addEventListener("click", clearConversation);

loadMeta();
checkHealth();
setInterval(checkHealth, 30000);

const API_BASE = window.location.origin;
const SESSION_KEY = "aiquery_session_id";

const chat = document.getElementById("chat");
const welcome = document.getElementById("welcome");
const composer = document.getElementById("composer");
const questionInput = document.getElementById("questionInput");
const sendBtn = document.getElementById("sendBtn");
const statusDot = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");
const examplesEl = document.getElementById("examples");
const tableListEl = document.getElementById("tableList");

let loading = false;

function getSessionId() {
  let id = localStorage.getItem(SESSION_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(SESSION_KEY, id);
  }
  return id;
}

function initExamples(examples) {
  examplesEl.innerHTML = "";
  examples.forEach((text) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "example-btn";
    btn.textContent = text;
    btn.addEventListener("click", () => {
      questionInput.value = text;
      questionInput.focus();
      submitQuestion();
    });
    examplesEl.appendChild(btn);
  });
}

function initTables(tables) {
  tableListEl.innerHTML = "";
  tables.forEach(({ label, name }) => {
    const li = document.createElement("li");
    li.innerHTML = `<strong>${label}</strong><span>${name}</span>`;
    tableListEl.appendChild(li);
  });
}

async function loadMeta() {
  try {
    const [exampleRes, tableRes] = await Promise.all([
      fetch(`${API_BASE}/examples`),
      fetch(`${API_BASE}/tables`),
    ]);
    if (exampleRes.ok) {
      const data = await exampleRes.json();
      initExamples(data.examples || []);
    }
    if (tableRes.ok) {
      const data = await tableRes.json();
      initTables(data.tables || []);
    }
  } catch {
    initExamples([
      "本月订单GMV是多少？",
      "各省份订单金额排名",
      "查询所有商品名称和价格",
    ]);
  }
}

async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error("offline");
    statusDot.className = "status-dot online";
    statusText.textContent = "服务在线";
  } catch {
    statusDot.className = "status-dot offline";
    statusText.textContent = "服务离线";
  }
}

function hideWelcome() {
  if (welcome) welcome.style.display = "none";
}

function scrollToBottom() {
  chat.scrollTop = chat.scrollHeight;
}

function createMessage(role, content, chartUrl) {
  hideWelcome();

  const msg = document.createElement("div");
  msg.className = `message ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.textContent = role === "user" ? "我" : "AI";

  const body = document.createElement("div");
  body.className = "message-body";
  body.textContent = content;

  if (chartUrl) {
    const chartWrap = document.createElement("div");
    chartWrap.className = "message-chart";
    const img = document.createElement("img");
    img.src = chartUrl.startsWith("http") ? chartUrl : `${API_BASE}${chartUrl}`;
    img.alt = "数据图表";
    img.loading = "lazy";
    chartWrap.appendChild(img);
    body.appendChild(chartWrap);
  }

  msg.appendChild(avatar);
  msg.appendChild(body);
  chat.appendChild(msg);
  scrollToBottom();
}

function createLoadingMessage() {
  hideWelcome();
  const msg = document.createElement("div");
  msg.className = "message assistant loading";
  msg.id = "loadingMsg";

  msg.innerHTML = `
    <div class="message-avatar">AI</div>
    <div class="message-body">
      正在分析并查询数据
      <span class="dots"><span>.</span><span>.</span><span>.</span></span>
    </div>
  `;
  chat.appendChild(msg);
  scrollToBottom();
  return msg;
}

function setLoading(value) {
  loading = value;
  sendBtn.disabled = value;
  questionInput.disabled = value;
}

async function submitQuestion() {
  const question = questionInput.value.trim();
  if (!question || loading) return;

  createMessage("user", question);
  questionInput.value = "";
  questionInput.style.height = "auto";

  setLoading(true);
  const loadingMsg = createLoadingMessage();

  try {
    const res = await fetch(`${API_BASE}/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_question: question, session_id: getSessionId() }),
    });

    loadingMsg.remove();

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const detail = err.detail || `请求失败 (${res.status})`;
      createMessage("assistant", typeof detail === "string" ? detail : JSON.stringify(detail));
      chat.lastElementChild?.classList.add("error");
      return;
    }

    const data = await res.json();
    createMessage("assistant", data.final_answer || "（无回答）", data.chart_url);
  } catch {
    loadingMsg.remove();
    const errMsg = document.createElement("div");
    errMsg.className = "message assistant error";
    errMsg.innerHTML = `
      <div class="message-avatar">AI</div>
      <div class="message-body">无法连接后端服务，请确认已运行：python run.py --server</div>
    `;
    chat.appendChild(errMsg);
    scrollToBottom();
  } finally {
    setLoading(false);
    questionInput.focus();
  }
}

composer.addEventListener("submit", (e) => {
  e.preventDefault();
  submitQuestion();
});

questionInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    submitQuestion();
  }
});

questionInput.addEventListener("input", () => {
  questionInput.style.height = "auto";
  questionInput.style.height = `${Math.min(questionInput.scrollHeight, 160)}px`;
});

loadMeta();
checkHealth();
setInterval(checkHealth, 30000);

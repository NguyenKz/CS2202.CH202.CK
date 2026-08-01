const $ = (id) => document.getElementById(id);

const sentenceEl = $("sentence");
const statusEl = $("status");
const resultEl = $("result");
const resultSummaryEl = $("result-summary");
const resultListEl = $("result-list");
const scoreBtn = $("score-btn");
const clearBtn = $("clear-btn");
const allExamplesBtn = $("all-examples-btn");
const examplesEl = $("examples");
const modelNameEl = $("model-name");
const thinkingToggle = $("thinking-toggle");

let cachedExamples = [];

function setStatus(text, isError = false) {
  statusEl.textContent = text || "";
  statusEl.classList.toggle("error", Boolean(isError));
}

function parseLines(text) {
  const seen = new Set();
  const lines = [];
  for (const raw of String(text || "").split(/\r?\n/)) {
    const line = raw.trim().replace(/\s+/g, " ");
    if (!line || seen.has(line)) continue;
    seen.add(line);
    lines.push(line);
  }
  return lines;
}

function hideResult() {
  resultEl.classList.remove("visible");
  resultSummaryEl.textContent = "";
  resultListEl.innerHTML = "";
}

function showResults(payload) {
  const results = payload.results || [];
  resultEl.classList.add("visible");
  resultListEl.innerHTML = "";

  const ok = results.filter((r) => r.score != null);
  const fail = results.length - ok.length;
  const mean =
    ok.length > 0
      ? (ok.reduce((s, r) => s + r.score, 0) / ok.length).toFixed(2)
      : "—";
  const withThink = results.filter((r) => r.thinking).length;

  resultSummaryEl.innerHTML = [
    `Model: <strong>${payload.model}</strong>`,
    `MODE: <strong>${payload.mode || (payload.thinking ? "T" : "ORIG")}</strong>`,
    `${results.length} câu`,
    ok.length ? `mean <strong>${mean}</strong>` : null,
    withThink ? `thinking ×${withThink}` : null,
    fail ? `<span class="fail-count">${fail} lỗi</span>` : null,
  ]
    .filter(Boolean)
    .join(" · ");

  for (const row of results) {
    const card = document.createElement("article");
    card.className = "result-card" + (row.error ? " has-error" : "");

    const top = document.createElement("div");
    top.className = "result-card-top";

    const score = document.createElement("div");
    score.className = "score-value";
    score.textContent = row.score != null ? String(row.score) : "—";

    const body = document.createElement("div");
    body.className = "result-card-body";

    const sent = document.createElement("p");
    sent.className = "result-sentence";
    sent.textContent = row.sentence;

    const meta = document.createElement("p");
    meta.className = "meta";
    const bits = [];
    if (row.score != null) bits.push("/ 7");
    if (row.human_mean != null) bits.push(`human ${row.human_mean}`);
    if (row.sample_id) bits.push(row.sample_id);
    if (row.latency_ms) bits.push(`${row.latency_ms} ms`);
    if (row.error) bits.push(row.error);
    meta.textContent = bits.join(" · ");

    const expl = document.createElement("p");
    expl.className = "explanation";
    expl.textContent = row.explanation || "";

    const bar = document.createElement("div");
    bar.className = "bar";
    const fill = document.createElement("span");
    fill.style.width =
      row.score != null ? `${(row.score / 7) * 100}%` : "0%";
    bar.appendChild(fill);

    body.appendChild(sent);
    body.appendChild(meta);
    if (row.explanation) body.appendChild(expl);

    if (row.thinking) {
      const details = document.createElement("details");
      details.className = "thinking-box";
      details.open = true;
      const summary = document.createElement("summary");
      summary.textContent = "Thinking";
      const pre = document.createElement("pre");
      pre.textContent = row.thinking;
      details.appendChild(summary);
      details.appendChild(pre);
      body.appendChild(details);
    } else if (payload.thinking) {
      const note = document.createElement("p");
      note.className = "thinking-empty";
      note.textContent = "Thinking: (model không trả reasoning text)";
      body.appendChild(note);
    }

    body.appendChild(bar);

    top.appendChild(score);
    top.appendChild(body);
    card.appendChild(top);
    resultListEl.appendChild(card);
  }
}

async function loadHealth() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    if (data.model) modelNameEl.textContent = data.model;
    if (!data.token_set) {
      setStatus("Chưa có API key — kiểm tra OPENAI_API_KEY trong doan/.env", true);
    }
  } catch {
    setStatus("Không kết nối được server.", true);
  }
}

function runAllExamples() {
  if (!cachedExamples.length) {
    setStatus("Chưa có câu mẫu.", true);
    return;
  }
  sentenceEl.value = cachedExamples.map((ex) => ex.sentence).join("\n");
  scoreSentences();
}

async function loadExamples() {
  try {
    const res = await fetch("/api/examples");
    const data = await res.json();
    cachedExamples = data.examples || [];
    examplesEl.innerHTML = "";
    for (const ex of cachedExamples) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "chip";
      const human =
        ex.human_mean != null ? ` (human ${ex.human_mean})` : "";
      btn.textContent = `${ex.sentence}${human}`;
      btn.title = ex.sentence;
      btn.addEventListener("click", () => {
        sentenceEl.value = ex.sentence;
        scoreSentences();
      });
      examplesEl.appendChild(btn);
    }

    if (cachedExamples.length > 1) {
      const multi = document.createElement("button");
      multi.type = "button";
      multi.className = "chip chip-multi";
      multi.textContent = `Nhiều câu (${cachedExamples.length} dòng) — chạy hết`;
      multi.title = cachedExamples.map((ex) => ex.sentence).join("\n");
      multi.addEventListener("click", runAllExamples);
      examplesEl.appendChild(multi);
    }
  } catch {
    // examples are optional
  }
}

function setBusy(busy) {
  scoreBtn.disabled = busy;
  clearBtn.disabled = busy;
  allExamplesBtn.disabled = busy;
  thinkingToggle.disabled = busy;
  for (const btn of examplesEl.querySelectorAll("button")) {
    btn.disabled = busy;
  }
}

async function scoreSentences() {
  const lines = parseLines(sentenceEl.value);
  if (!lines.length) {
    setStatus("Nhập ít nhất một câu (mỗi câu một dòng).", true);
    return;
  }

  const thinking = Boolean(thinkingToggle.checked);
  sentenceEl.value = lines.join("\n");
  setBusy(true);
  setStatus(
    lines.length === 1
      ? `Đang gọi gpt-5.6-luna (${thinking ? "T" : "ORIG"})…`
      : `Đang chấm ${lines.length} câu (${thinking ? "T" : "ORIG"})…`
  );
  hideResult();

  try {
    const res = await fetch("/api/score", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: lines.join("\n"),
        thinking,
      }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail =
        typeof data.detail === "string"
          ? data.detail
          : data.detail
            ? JSON.stringify(data.detail)
            : `HTTP ${res.status}`;
      throw new Error(detail);
    }
    showResults(data);
    const fail = (data.results || []).filter((r) => r.error).length;
    setStatus(
      fail
        ? `Xong — ${data.results.length - fail}/${data.results.length} câu OK (${data.mode}).`
        : `Xong — ${data.results.length} câu (${data.mode}).`
    );
  } catch (err) {
    setStatus(err.message || String(err), true);
  } finally {
    setBusy(false);
  }
}

scoreBtn.addEventListener("click", scoreSentences);
clearBtn.addEventListener("click", () => {
  sentenceEl.value = "";
  setStatus("");
  hideResult();
  sentenceEl.focus();
});
allExamplesBtn.addEventListener("click", runAllExamples);

sentenceEl.addEventListener("keydown", (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
    e.preventDefault();
    scoreSentences();
  }
});

loadHealth();
loadExamples();

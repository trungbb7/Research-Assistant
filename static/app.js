// State variables
let currentReportContent = "";
let isRunning = false;

// Initialize icons and state on load
document.addEventListener("DOMContentLoaded", () => {
  lucide.createIcons();
});

// Switch between tabs
function switchTab(event, tabId) {
  // Remove active class from all buttons
  const tabButtons = document.querySelectorAll(".tab-btn");
  tabButtons.forEach((btn) => btn.classList.remove("active"));

  // Add active class to clicked button
  if (event) {
    event.currentTarget.classList.add("active");
  } else {
    // Fallback for programmatically switching
    const targetBtn = Array.from(tabButtons).find((btn) =>
      btn.getAttribute("onclick").includes(tabId),
    );
    if (targetBtn) targetBtn.classList.add("active");
  }

  // Hide all tab contents
  const tabContents = document.querySelectorAll(".tab-content");
  tabContents.forEach((content) => content.classList.remove("active"));

  // Show selected tab content
  const targetContent = document.getElementById(tabId);
  if (targetContent) {
    targetContent.classList.add("active");
  }
}

// Suggestion tags helper
function useSuggestion(element) {
  const text = element.innerText;
  document.getElementById("query-input").value = text;
}

// Clear Terminal logs
function clearLogs() {
  const consoleLogs = document.getElementById("terminal-logs");
  consoleLogs.innerHTML = `<div class="log-line system-line">[SYSTEM] Logs cleared.</div>`;
}

// Append log helper
function appendLog(type, content) {
  const consoleLogs = document.getElementById("terminal-logs");
  const logLine = document.createElement("div");

  // Choose CSS class based on log type
  let logClass = "text-line";
  if (type === "system") logClass = "system-line";
  else if (type === "node") logClass = "node-line";
  else if (type === "tool") logClass = "tool-line";
  else if (type === "error") logClass = "error-line";
  else if (type === "complete") logClass = "complete-line";

  logLine.className = `log-line ${logClass}`;

  const timeStr = new Date().toLocaleTimeString();
  logLine.innerText = `[${timeStr}] ${content}`;

  consoleLogs.appendChild(logLine);
  consoleLogs.scrollTop = consoleLogs.scrollHeight;
}

// Reset Pipeline UI state
function resetPipelineUI() {
  const nodes = document.querySelectorAll(".pipeline-node");
  nodes.forEach((n) => {
    n.classList.remove("active", "completed");
  });

  const lines = document.querySelectorAll(".pipeline-line");
  lines.forEach((l) => {
    l.classList.remove("active", "completed");
  });
}

// Update Pipeline Active Node
function updatePipelineNode(activeNodeId) {
  const nodesOrder = [
    "node-start",
    "node-search",
    "node-ingest",
    "node-select",
    "node-analyze",
    "node-report",
    "node-finish",
  ];
  const targetIdx = nodesOrder.indexOf(activeNodeId);

  if (targetIdx === -1) return;

  nodesOrder.forEach((nodeId, idx) => {
    const nodeEl = document.getElementById(nodeId);
    if (!nodeEl) return;

    // Setup line connecting to the next node
    const lineEl =
      nodeEl.nextElementSibling &&
      nodeEl.nextElementSibling.classList.contains("pipeline-line")
        ? nodeEl.nextElementSibling
        : null;

    if (idx < targetIdx) {
      nodeEl.classList.remove("active");
      nodeEl.classList.add("completed");
      if (lineEl) {
        lineEl.classList.remove("active");
        lineEl.classList.add("completed");
      }
    } else if (idx === targetIdx) {
      nodeEl.classList.remove("completed");
      nodeEl.classList.add("active");
      if (lineEl) {
        lineEl.classList.remove("completed");
        lineEl.classList.add("active");
      }
    } else {
      nodeEl.classList.remove("active", "completed");
      if (lineEl) {
        lineEl.classList.remove("active", "completed");
      }
    }
  });
}

// Copy Markdown Report to Clipboard
function copyReport() {
  if (!currentReportContent) {
    alert("Chưa có nội dung báo cáo để copy!");
    return;
  }

  navigator.clipboard
    .writeText(currentReportContent)
    .then(() => alert("Đã sao chép báo cáo Markdown vào bộ nhớ tạm!"))
    .catch((err) => console.error("Lỗi khi copy: ", err));
}

// Download Report as .md file
function downloadReport() {
  if (!currentReportContent) {
    alert("Chưa có nội dung báo cáo để tải xuống!");
    return;
  }

  const blob = new Blob([currentReportContent], {
    type: "text/markdown;charset=utf-8;",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute(
    "download",
    `research_report_${new Date().toISOString().slice(0, 10)}.md`,
  );
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// Main function to trigger the agent research via SSE POST stream
async function startResearch() {
  if (isRunning) return;

  const queryInput = document.getElementById("query-input");
  const runBtn = document.getElementById("run-btn");
  const btnText = document.getElementById("btn-text");
  const statusIndicator = document.querySelector(".status-indicator");
  const statusText = document.querySelector(".system-status span");
  const query = queryInput.value.trim();

  if (!query) {
    alert("Vui lòng nhập chủ đề nghiên cứu!");
    return;
  }

  // UI state updates
  isRunning = true;
  queryInput.disabled = true;
  runBtn.disabled = true;
  btnText.innerText = "Đang chạy nghiên cứu...";
  statusIndicator.className = "status-indicator running";
  statusText.innerText = "Hệ thống: Đang thực thi";

  // Clear old data
  currentReportContent = "";
  document.getElementById("report-view").innerHTML = `
        <div class="empty-state">
            <i data-lucide="loader-2" class="large-empty-icon animate-spin"></i>
            <h3>Đang thu thập và biên soạn tài liệu...</h3>
            <p>Vui lòng theo dõi quá trình chạy trực quan trong cột Pipeline hoặc xem Terminal Logs.</p>
        </div>
    `;
  lucide.createIcons();

  // Clear tabs details
  document.getElementById("state-plan-content").innerText =
    "Chờ kế hoạch nghiên cứu...";
  document.getElementById("state-findings-content").innerText =
    "Chờ kết quả phân tích...";
  document.getElementById("state-comparison-content").innerText =
    "Chờ bảng so sánh...";
  document.getElementById("state-trends-content").innerText =
    "Chờ phân tích xu hướng...";
  document.getElementById("papers-list").innerHTML = `
        <div class="empty-state">
            <i data-lucide="files" class="large-empty-icon"></i>
            <h3>Chưa chọn tài liệu</h3>
            <p>Các tài liệu liên quan sẽ hiện ở đây sau khi kết thúc tìm kiếm.</p>
        </div>
    `;

  clearLogs();
  resetPipelineUI();
  appendLog("system", `Gửi yêu cầu nghiên cứu: "${query}"`);

  // Auto-switch to Logs tab to show logs immediately
  switchTab(null, "tab-logs");

  try {
    const response = await fetch("/api/research", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: query }),
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(
        errData.error || `HTTP error! Status: ${response.status}`,
      );
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");

      // Keep the last partial line in the buffer
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.trim()) continue;

        // Parse EventSource-style format
        const eventMatch = line.match(/^event:\s*(.+)$/m);
        const dataMatch = line.match(/^data:\s*(.+)$/m);

        if (eventMatch && dataMatch) {
          const event = eventMatch[1].trim();
          const data = JSON.parse(dataMatch[1].trim());
          handleSSEEvent(event, data);
        }
      }
    }
  } catch (err) {
    console.error("Lỗi thực thi nghiên cứu:", err);
    appendLog("error", `Lỗi: ${err.message}`);
    document.getElementById("report-view").innerHTML = `
            <div class="empty-state text-red">
                <i data-lucide="alert-triangle" class="large-empty-icon"></i>
                <h3>Đã xảy ra lỗi thực thi</h3>
                <p>${err.message}</p>
            </div>
        `;
    statusIndicator.className = "status-indicator";
    statusText.innerText = "Hệ thống: Bị lỗi";
    lucide.createIcons();
  } finally {
    isRunning = false;
    queryInput.disabled = false;
    runBtn.disabled = false;
    btnText.innerText = "Bắt đầu nghiên cứu";
    if (statusIndicator.className === "status-indicator running") {
      statusIndicator.className = "status-indicator online";
      statusText.innerText = "Hệ thống: Sẵn sàng";
    }
  }
}

// Process single SSE event
function handleSSEEvent(event, data) {
  switch (event) {
    case "start":
      appendLog("system", `Bắt đầu phân tích cho query: ${data.query}`);
      updatePipelineNode("node-start");
      break;

    case "node_start":
      appendLog("node", `---> Bắt đầu Node: ${data.node}`);
      // Map node to visual pipeline Node
      mapNodeToPipeline(data.node);
      break;

    case "node_end":
      appendLog("system", `<--- Kết thúc Node: ${data.node}`);
      break;

    case "tool_call":
      appendLog(
        "tool",
        `Chạy tool [${data.tool}] với tham số: ${JSON.stringify(data.arguments)}`,
      );
      // Dynamic check for tool category to light up pipeline
      mapToolToPipeline(data.tool);
      break;

    case "log":
      appendLog("text", data.content);
      break;

    case "state_update":
      handleStateUpdate(data.key, data.value, data.node);
      break;

    case "complete":
      appendLog(
        "complete",
        "Quá trình nghiên cứu hoàn tất! Báo cáo đã sẵn sàng.",
      );
      updatePipelineNode("node-finish");
      // Auto switch to Report Tab
      switchTab(null, "tab-report");
      break;

    case "error":
      appendLog(
        "error",
        `LỖI TẠI NODE [${data.node || "Hệ thống"}]: ${data.message}`,
      );
      if (data.traceback) {
        console.error(data.traceback);
      }
      break;

    default:
      console.log("Sự kiện chưa xử lý:", event, data);
  }
}

// Maps LangGraph Node to HTML Pipeline Indicator
function mapNodeToPipeline(node) {
  const nodeMapping = {
    llm: "node-start",
    retrieve_chunks: "node-analyze",
    extract_findings: "node-analyze",
    compare_papers: "node-analyze",
    trends_analysis: "node-analyze",
    generate_report: "node-report",
    write_final_report: "node-report",
    finalize: "node-finish",
  };

  if (nodeMapping[node]) {
    updatePipelineNode(nodeMapping[node]);
  }
}

// Maps Called Tools to HTML Pipeline Indicator for precision
function mapToolToPipeline(toolName) {
  const toolSearch = [
    "search_website_url",
    "fetch_web_content",
    "arxiv_search",
  ];
  const toolIngest = ["download_pdf", "add_documents"];
  const toolSelect = ["select_papers", "retrieve_paper_summaries"];

  if (toolSearch.includes(toolName)) {
    updatePipelineNode("node-search");
  } else if (toolIngest.includes(toolName)) {
    updatePipelineNode("node-ingest");
  } else if (toolSelect.includes(toolName)) {
    updatePipelineNode("node-select");
  }
}

// Handles intermediate agent state data and renders it in tabs
function handleStateUpdate(key, value, node) {
  if (!value) return;

  if (key === "plan") {
    let planHtml = `<h4>Chủ đề: ${value.topic || ""}</h4><ul>`;
    if (value.tasks && Array.isArray(value.tasks)) {
      value.tasks.forEach((t) => {
        planHtml += `<li><i data-lucide="check" class="list-bullet"></i> ${t}</li>`;
      });
    }
    planHtml += `</ul>`;
    document.getElementById("state-plan-content").innerHTML = planHtml;
    lucide.createIcons();
  } else if (key === "findings") {
    let findingsHtml = "";
    if (Array.isArray(value)) {
      value.forEach((f, i) => {
        findingsHtml += `
                    <div class="finding-item">
                        <h5>Tài liệu #${i + 1} (${f.paper_id || "Chưa rõ ID"})</h5>
                        <p><b>Phương pháp:</b> ${Array.isArray(f.method) ? f.method.join(", ") : f.method}</p>
                        <p><b>Dữ liệu đánh giá:</b> ${Array.isArray(f.datasets) ? f.datasets.join(", ") : f.datasets}</p>
                        <p><b>Kết quả:</b> ${Array.isArray(f.results) ? f.results.join(", ") : f.results}</p>
                        <p><b>Ưu điểm:</b> ${Array.isArray(f.strengths) ? f.strengths.join(", ") : f.strengths}</p>
                        <p><b>Hạn chế:</b> ${Array.isArray(f.limitations) ? f.limitations.join(", ") : f.limitations}</p>
                    </div>
                `;
      });
    }
    document.getElementById("state-findings-content").innerHTML =
      findingsHtml || "Chưa có findings trích xuất.";
  } else if (key === "comparison") {
    let compHtml = `
            <p><b>Điểm chung:</b> ${Array.isArray(value.similarities) ? value.similarities.join("; ") : value.similarities}</p>
            <p><b>Điểm khác biệt:</b> ${Array.isArray(value.differences) ? value.differences.join("; ") : value.differences}</p>
            <p><b>Phương pháp tối ưu nhất:</b> ${Array.isArray(value.best_methods) ? value.best_methods.join("; ") : value.best_methods}</p>
            <p><b>Đánh đổi (Trade-offs):</b> ${Array.isArray(value.tradeoffs) ? value.tradeoffs.join("; ") : value.tradeoffs}</p>
        `;
    document.getElementById("state-comparison-content").innerHTML = compHtml;
  } else if (key === "trends") {
    let trendsHtml = `
            <p><b>Xu hướng chính:</b> ${Array.isArray(value.major_trend) ? value.major_trend.join("; ") : value.major_trend}</p>
            <p><b>Hướng phát triển mới nổi:</b> ${Array.isArray(value.emerging_directions) ? value.emerging_directions.join("; ") : value.emerging_directions}</p>
            <p><b>Hạn chế phổ biến:</b> ${Array.isArray(value.common_limitations) ? value.common_limitations.join("; ") : value.common_limitations}</p>
            <p><b>Hướng nghiên cứu tương lai:</b> ${Array.isArray(value.feature_researchs) ? value.feature_researchs.join("; ") : value.feature_researchs}</p>
        `;
    document.getElementById("state-trends-content").innerHTML = trendsHtml;
  } else if (key === "selected_paper_ids") {
    let papersHtml = "";
    if (Array.isArray(value)) {
      value.forEach((paperId) => {
        papersHtml += `
                    <div class="paper-card">
                        <i data-lucide="file-text" class="text-teal"></i>
                        <h4>ID: ${paperId}</h4>
                        <div class="paper-badges">
                            <span class="badge category">Academic Paper</span>
                            <span class="badge">Analyzed</span>
                        </div>
                    </div>
                `;
      });
    }
    if (papersHtml) {
      document.getElementById("papers-list").innerHTML = papersHtml;
      lucide.createIcons();
    }
  } else if (key === "report" || key === "final_report") {
    currentReportContent = value;
    // Parse markdown and render
    document.getElementById("report-view").innerHTML = marked.parse(value);
  }
}

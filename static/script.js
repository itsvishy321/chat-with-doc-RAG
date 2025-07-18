let currentSessionId = null;

// DOM elements
const urlInput = document.getElementById("urlInput");
const processBtn = document.getElementById("processBtn");
const questionInput = document.getElementById("questionInput");
const askBtn = document.getElementById("askBtn");
const chatSection = document.getElementById("chatSection");
const chatHistory = document.getElementById("chatHistory");
const status = document.getElementById("status");
const loading = document.getElementById("loading");
const documentUrl = document.getElementById("documentUrl");

// Event listeners
processBtn.addEventListener("click", processDocument);
askBtn.addEventListener("click", askQuestion);
questionInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") {
    askQuestion();
  }
});

urlInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") {
    processDocument();
  }
});

document
  .getElementById("loadSessionsBtn")
  .addEventListener("click", loadSessions);

// Load sessions when page loads
document.addEventListener("DOMContentLoaded", () => {
  loadSessions();
});

async function processDocument() {
  const url = urlInput.value.trim();

  if (!url) {
    showStatus("Please enter a URL", "error");
    return;
  }

  if (!isValidUrl(url)) {
    showStatus("Please enter a valid URL", "error");
    return;
  }

  setLoading(true);
  processBtn.disabled = true;

  try {
    const response = await fetch("/api/process_url", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ url: url }),
    });

    const data = await response.json();

    if (response.ok) {
      currentSessionId = data.session_id;
      documentUrl.textContent = url;
      chatSection.style.display = "block";
      chatHistory.innerHTML = "";
      showStatus(
        `Document processed successfully! Found ${data.chunks_count} content chunks.`,
        "success"
      );
    } else {
      showStatus(`Error: ${data.error}`, "error");
    }
  } catch (error) {
    showStatus(`Error: ${error.message}`, "error");
  } finally {
    setLoading(false);
    processBtn.disabled = false;
  }
}

async function askQuestion() {
  const question = questionInput.value.trim();

  if (!question) {
    showStatus("Please enter a question", "error");
    return;
  }

  if (!currentSessionId) {
    showStatus("Please process a document first", "error");
    return;
  }

  setLoading(true);
  askBtn.disabled = true;

  // Add question to chat history immediately
  addMessageToHistory(question, "question");
  questionInput.value = "";

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        session_id: currentSessionId,
        question: question,
      }),
    });

    const data = await response.json();

    if (response.ok) {
      addMessageToHistory(data.answer, "answer");
      showStatus(
        `Found answer using ${data.relevant_chunks_count} relevant content chunks`,
        "success"
      );
    } else {
      addMessageToHistory(`Error: ${data.error}`, "answer");
      showStatus(`Error: ${data.error}`, "error");
    }
  } catch (error) {
    addMessageToHistory(`Error: ${error.message}`, "answer");
    showStatus(`Error: ${error.message}`, "error");
  } finally {
    setLoading(false);
    askBtn.disabled = false;
    questionInput.focus();
  }
}

function addMessageToHistory(message, type) {
  const messageDiv = document.createElement("div");
  messageDiv.className = `message ${type}`;

  const labelDiv = document.createElement("div");
  labelDiv.className = "message-label";
  labelDiv.textContent = type === "question" ? "Question" : "Answer";

  const contentDiv = document.createElement("div");
  contentDiv.textContent = message;

  messageDiv.appendChild(labelDiv);
  messageDiv.appendChild(contentDiv);
  chatHistory.appendChild(messageDiv);

  // Scroll to bottom
  chatHistory.scrollTop = chatHistory.scrollHeight;
}

function showStatus(message, type) {
  status.textContent = message;
  status.className = `status ${type}`;
  status.style.display = "block";

  // Auto-hide after 5 seconds
  setTimeout(() => {
    status.style.display = "none";
  }, 5000);
}

function setLoading(isLoading) {
  loading.style.display = isLoading ? "flex" : "none";
}

function isValidUrl(string) {
  try {
    new URL(string);
    return true;
  } catch (_) {
    return false;
  }
}

// Load and display sessions
async function loadSessions() {
  try {
    const response = await fetch("/api/sessions");
    const data = await response.json();

    if (response.ok) {
      allSessions = data.sessions;
      displaySessions(allSessions);
    } else {
      console.error("Failed to load sessions:", data.error);
    }
  } catch (error) {
    console.error("Error loading sessions:", error);
  }
}

// Restore a session
async function restoreSession(sessionId) {
  try {
    setLoading(true);

    const response = await fetch(`/api/sessions/${sessionId}/restore`, {
      method: "POST",
    });

    const data = await response.json();

    if (response.ok) {
      currentSessionId = sessionId;
      const sessionInfo = data.session_info;
      const chatHistoryData = data.chat_history;

      console.log("Restored session:", sessionInfo, chatHistoryData);

      // Update UI
      urlInput.value = sessionInfo.document_url;
      documentUrl.textContent = sessionInfo.document_url;
      chatSection.style.display = "block";

      // Restore chat history
      chatHistory.innerHTML = "";
      chatHistoryData.forEach((msg) => {
        addMessageToHistory(msg.question, "question");
        addMessageToHistory(msg.answer, "answer");
      });

      // Update sessions display
      displaySessions(allSessions);

      showStatus("Session restored successfully!", "success");
    } else {
      showStatus(`Error: ${data.error}`, "error");
    }
  } catch (error) {
    showStatus(`Error: ${error.message}`, "error");
  } finally {
    setLoading(false);
  }
}

// Display sessions in the UI
function displaySessions(sessions) {
  const sessionsList = document.getElementById("sessionsList");

  if (sessions.length === 0) {
    sessionsList.innerHTML =
      '<p style="text-align: center; color: #666; padding: 20px;">No previous sessions found</p>';
    return;
  }

  sessionsList.innerHTML = sessions
    .map(
      (session) => `
        <div class="session-item ${
          session.session_id === currentSessionId ? "active" : ""
        }" data-session-id="${session.session_id}">
            <div class="session-url">${session.document_url}</div>
            <div class="session-meta">
                <span>${session.chunks_count} chunks • ${formatDate(
        session.updated_at
      )}</span>
                <div class="session-actions">
                    <button class="restore-btn" onclick="restoreSession('${
                      session.session_id
                    }')">View</button>
                </div>
            </div>
        </div>
    `
    )
    .join("");
}

// Format date for display
function formatDate(dateString) {
  const date = new Date(dateString);
  return (
    date.toLocaleDateString() +
    " " +
    date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
  );
}

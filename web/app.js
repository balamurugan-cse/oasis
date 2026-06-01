const chatLog = document.getElementById("chatLog");
const statusLabel = document.getElementById("status");
const onlineCount = document.getElementById("onlineCount");
const composer = document.getElementById("composer");
const nameInput = document.getElementById("nameInput");
const messageInput = document.getElementById("messageInput");

const storedName = localStorage.getItem("oasis-chat-name");
if (storedName) {
  nameInput.value = storedName;
}

let lastMessageId = 0;
let visibleMessages = 0;

function formatTime(iso) {
  const value = new Date(iso);
  return value.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function renderMessage(message) {
  if (message.system) {
    const item = document.createElement("div");
    item.className = "message system";
    item.textContent = message.text;
    chatLog.appendChild(item);
    return;
  }

  const item = document.createElement("article");
  item.className = "message";
  item.innerHTML = `
    <div class="meta">
      <span class="name">${escapeHtml(message.name)}</span>
      <span>${formatTime(message.timestamp)}</span>
    </div>
    <div class="body">${escapeHtml(message.text)}</div>
  `;
  chatLog.appendChild(item);
}

function updateCounter() {
  onlineCount.textContent = `${visibleMessages} message${visibleMessages === 1 ? "" : "s"}`;
}

function scrollToBottom() {
  chatLog.scrollTop = chatLog.scrollHeight;
}

async function fetchMessages() {
  try {
    const response = await fetch(`/api/messages?after=${lastMessageId}&wait=25`, {
      headers: { Accept: "application/json" },
    });

    if (!response.ok) {
      throw new Error("Failed to fetch messages");
    }

    const payload = await response.json();
    if (payload.messages.length > 0) {
      for (const message of payload.messages) {
        renderMessage(message);
        lastMessageId = message.id;
        visibleMessages += 1;
      }
      updateCounter();
      scrollToBottom();
      statusLabel.textContent = "Connected and listening for new messages.";
    }
  } catch (error) {
    statusLabel.textContent = "Connection paused. Reconnecting...";
  } finally {
    setTimeout(fetchMessages, 250);
  }
}

composer.addEventListener("submit", async (event) => {
  event.preventDefault();

  const name = (nameInput.value || "Anonymous").trim().slice(0, 32);
  const text = messageInput.value.trim();
  if (!text) {
    return;
  }

  localStorage.setItem("oasis-chat-name", name);
  messageInput.value = "";
  messageInput.focus();

  const response = await fetch("/api/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, text }),
  });

  if (!response.ok) {
    statusLabel.textContent = "Message could not be sent.";
  }
});

nameInput.addEventListener("change", () => {
  localStorage.setItem("oasis-chat-name", nameInput.value.trim().slice(0, 32));
});

statusLabel.textContent = "Connected and listening for new messages.";
fetchMessages();
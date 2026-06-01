from __future__ import annotations

import argparse
import json
import mimetypes
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"


@dataclass(frozen=True)
class Message:
    id: int
    name: str
    text: str
    timestamp: str


class ChatState:
    def __init__(self) -> None:
        self._messages: list[Message] = []
        self._next_id = 1
        self._condition = threading.Condition()

    def add_message(self, name: str, text: str) -> Message:
        with self._condition:
            message = Message(
                id=self._next_id,
                name=name,
                text=text,
                timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            )
            self._next_id += 1
            self._messages.append(message)
            self._condition.notify_all()
            return message

    def messages_after(self, after_id: int) -> list[Message]:
        with self._condition:
            return [message for message in self._messages if message.id > after_id]

    def wait_for_messages(self, after_id: int, timeout: float) -> list[Message]:
        with self._condition:
            if not any(message.id > after_id for message in self._messages):
                self._condition.wait(timeout=timeout)
            return [message for message in self._messages if message.id > after_id]


STATE = ChatState()


def load_text(path: Path, fallback: str) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else fallback


INDEX_HTML = load_text(
    WEB_DIR / "index.html",
    """<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Oasis Chat</title>
    <link rel=\"stylesheet\" href=\"/styles.css\" />
  </head>
  <body>
    <main class=\"shell\">
      <section class=\"hero\">
        <p class=\"eyebrow\">Realtime conversation space</p>
        <h1>Oasis Chat</h1>
        <p class=\"lede\">A clean browser-based chat room powered by Python. Open it in multiple tabs or share the link with teammates.</p>
      </section>

      <section class=\"panel\">
        <header class=\"panel-header\">
          <div>
            <h2>Live Room</h2>
            <p id=\"status\">Connecting to the room...</p>
          </div>
          <div class=\"badge\" id=\"onlineCount\">0 online</div>
        </header>

        <div class=\"chat-log\" id=\"chatLog\" aria-live=\"polite\"></div>

        <form class=\"composer\" id=\"composer\">
          <input id=\"nameInput\" name=\"name\" type=\"text\" maxlength=\"32\" placeholder=\"Your name\" />
          <input id=\"messageInput\" name=\"message\" type=\"text\" maxlength=\"500\" placeholder=\"Type a message\" autocomplete=\"off\" />
          <button type=\"submit\">Send</button>
        </form>
      </section>
    </main>

    <script src=\"/app.js\"></script>
  </body>
</html>
""",
)

STYLES_CSS = load_text(
    WEB_DIR / "styles.css",
    """* {
  box-sizing: border-box;
}

:root {
  color-scheme: dark;
  --bg: #07111f;
  --bg-accent: #11243f;
  --panel: rgba(10, 18, 32, 0.82);
  --panel-border: rgba(159, 209, 255, 0.18);
  --text: #ecf4ff;
  --muted: #96adc6;
  --accent: #6dd3ff;
  --accent-strong: #9ef2ff;
  --bubble: rgba(125, 189, 255, 0.12);
  --bubble-border: rgba(125, 189, 255, 0.18);
  --shadow: 0 30px 80px rgba(0, 0, 0, 0.35);
}

html, body {
  margin: 0;
  min-height: 100%;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background:
    radial-gradient(circle at top left, rgba(109, 211, 255, 0.25), transparent 35%),
    radial-gradient(circle at bottom right, rgba(57, 107, 168, 0.28), transparent 32%),
    linear-gradient(145deg, var(--bg), var(--bg-accent));
  color: var(--text);
}

body {
  padding: 32px;
}

.shell {
  width: min(1120px, 100%);
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1.05fr 1.2fr;
  gap: 28px;
  align-items: stretch;
}

.hero, .panel {
  border: 1px solid var(--panel-border);
  border-radius: 28px;
  background: var(--panel);
  backdrop-filter: blur(18px);
  box-shadow: var(--shadow);
}

.hero {
  padding: 40px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 620px;
}

.eyebrow {
  margin: 0 0 16px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--accent);
  font-size: 0.78rem;
}

h1 {
  margin: 0;
  font-size: clamp(3rem, 7vw, 5.8rem);
  line-height: 0.95;
  letter-spacing: -0.05em;
}

.lede {
  max-width: 34rem;
  margin: 18px 0 0;
  font-size: 1.07rem;
  line-height: 1.75;
  color: var(--muted);
}

.hero::after {
  content: "";
  display: block;
  height: 200px;
  margin-top: 32px;
  border-radius: 24px;
  background:
    radial-gradient(circle at 20% 20%, rgba(158, 242, 255, 0.3), transparent 28%),
    radial-gradient(circle at 80% 30%, rgba(109, 211, 255, 0.22), transparent 26%),
    linear-gradient(135deg, rgba(16, 30, 54, 0.9), rgba(10, 18, 32, 0.7));
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.panel {
  padding: 24px;
  display: grid;
  grid-template-rows: auto 1fr auto;
  gap: 18px;
  min-height: 620px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: 16px;
}

.panel-header h2 {
  margin: 0;
  font-size: 1.5rem;
}

.panel-header p {
  margin: 6px 0 0;
  color: var(--muted);
}

.badge {
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(109, 211, 255, 0.14);
  color: var(--accent-strong);
  border: 1px solid rgba(109, 211, 255, 0.18);
  font-size: 0.9rem;
  white-space: nowrap;
}

.chat-log {
  overflow: auto;
  padding: 6px;
  display: grid;
  gap: 12px;
}

.message {
  border: 1px solid var(--bubble-border);
  background: var(--bubble);
  border-radius: 18px;
  padding: 14px 16px;
}

.message .meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
  color: var(--muted);
  font-size: 0.86rem;
}

.message .name {
  color: var(--accent-strong);
  font-weight: 700;
}

.message.system {
  text-align: center;
  color: var(--muted);
  font-style: italic;
}

.composer {
  display: grid;
  grid-template-columns: 160px 1fr auto;
  gap: 12px;
}

.composer input, .composer button {
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 16px;
  font: inherit;
}

.composer input {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text);
  padding: 14px 16px;
}

.composer input::placeholder {
  color: rgba(236, 244, 255, 0.45);
}

.composer button {
  padding: 14px 20px;
  background: linear-gradient(135deg, var(--accent), var(--accent-strong));
  color: #03263a;
  font-weight: 800;
  cursor: pointer;
  transition: transform 160ms ease, box-shadow 160ms ease;
}

.composer button:hover {
  transform: translateY(-1px);
  box-shadow: 0 12px 28px rgba(109, 211, 255, 0.22);
}

.composer button:active {
  transform: translateY(0);
}

@media (max-width: 900px) {
  body {
    padding: 18px;
  }

  .shell {
    grid-template-columns: 1fr;
  }

  .hero, .panel {
    min-height: auto;
  }

  .composer {
    grid-template-columns: 1fr;
  }
}
""",
)

APP_JS = load_text(
    WEB_DIR / "app.js",
    """const chatLog = document.getElementById("chatLog");
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
""",
)


class ChatHandler(BaseHTTPRequestHandler):
    server_version = "OasisChat/1.0"

    def _send_json(self, status: HTTPStatus, payload: dict) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _send_text(self, status: HTTPStatus, content: str, content_type: str) -> None:
        data = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/index.html"}:
            self._send_text(HTTPStatus.OK, INDEX_HTML, "text/html")
            return

        if parsed.path == "/styles.css":
            self._send_text(HTTPStatus.OK, STYLES_CSS, "text/css")
            return

        if parsed.path == "/app.js":
            self._send_text(HTTPStatus.OK, APP_JS, "application/javascript")
            return

        if parsed.path == "/api/messages":
            self._handle_messages(parsed.query)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/messages":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)

        try:
            body = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid JSON body."})
            return

        name = str(body.get("name", "Anonymous")).strip()[:32] or "Anonymous"
        text = str(body.get("text", "")).strip()[:500]
        if not text:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Message text is required."})
            return

        message = STATE.add_message(name, text)
        self._send_json(HTTPStatus.CREATED, {"message": asdict(message)})

    def _handle_messages(self, query: str) -> None:
        params = parse_qs(query)
        after = int(params.get("after", ["0"])[0] or 0)
        wait = float(params.get("wait", ["0"])[0] or 0)

        if wait > 0:
            messages = STATE.wait_for_messages(after, min(wait, 30.0))
        else:
            messages = STATE.messages_after(after)

        self._send_json(
            HTTPStatus.OK,
            {"messages": [asdict(message) for message in messages]},
        )

    def log_message(self, format: str, *args: object) -> None:
        return


def seed_welcome_message() -> None:
    if not STATE.messages_after(0):
        STATE.add_message("Oasis", "Welcome to the room. Start a conversation.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Oasis Chat website.")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    args = parser.parse_args()

    mimetypes.add_type("text/css", ".css")
    mimetypes.add_type("application/javascript", ".js")
    seed_welcome_message()

    server = ThreadingHTTPServer((args.host, args.port), ChatHandler)
    print(f"Oasis Chat running at http://{args.host}:{args.port}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down website...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
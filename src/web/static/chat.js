(function () {
  const form = document.getElementById("chat-form");
  const input = document.getElementById("question-input");
  const messageList = document.getElementById("message-list");
  const loadingIndicator = document.getElementById("loading-indicator");
  const errorEl = document.getElementById("chat-error");
  if (!form) return;

  function renderMessage(message) {
    const div = document.createElement("div");
    div.className = `message message-${message.role}`;
    const contentDiv = document.createElement("div");
    contentDiv.className = "message-content";
    contentDiv.textContent = message.content;
    div.appendChild(contentDiv);

    if (message.sources && message.sources.length > 0) {
      const ul = document.createElement("ul");
      ul.className = "sources";
      message.sources.forEach((s) => {
        const li = document.createElement("li");
        // Quellenangabe bleibt lesbar, auch wenn document_id auf ein
        // inzwischen entferntes Dokument zeigt (data-model.md: filename
        // ist redundant in `sources` gespeichert).
        const pageText = s.page_number ? `, Seite ${s.page_number}` : "";
        li.textContent = `${s.filename}${pageText}`;
        ul.appendChild(li);
      });
      div.appendChild(ul);
    }
    return div;
  }

  const ERROR_MESSAGES = {
    no_documents: "Diesem Projekt sind noch keine (verarbeiteten) Dokumente zugeordnet. Bitte zuerst ein PDF hochladen.",
    content_required: "Bitte eine Frage eingeben.",
    ai_unavailable: "Die Anthropic API ist gerade nicht erreichbar oder der API-Key ist ungültig/ausgeschöpft.",
    context_too_large: "Die Dokumente dieses Projekts sind aktuell zu umfangreich für eine Anfrage. Bitte nicht benötigte Dokumente entfernen.",
  };

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const question = input.value.trim();
    if (!question) return;

    errorEl.hidden = true;
    messageList.appendChild(renderMessage({ role: "user", content: question, sources: [] }));
    input.value = "";
    loadingIndicator.hidden = false;

    try {
      const response = await fetch(`/api/projects/${window.PROJECT_ID}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: question }),
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        errorEl.textContent = ERROR_MESSAGES[body.error] || body.detail || "Unbekannter Fehler.";
        errorEl.hidden = false;
        return;
      }
      messageList.appendChild(renderMessage(body));
      messageList.scrollTop = messageList.scrollHeight;
    } catch (err) {
      errorEl.textContent = "Netzwerkfehler – bitte erneut versuchen.";
      errorEl.hidden = false;
    } finally {
      loadingIndicator.hidden = true;
    }
  });
})();

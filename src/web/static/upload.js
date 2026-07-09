(function () {
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");
  const documentList = document.getElementById("document-list");
  if (!dropzone) return;

  function renderDocument(doc) {
    const li = document.createElement("li");
    li.dataset.documentId = doc.id;
    let statusHtml = `<span class="doc-status status-${doc.status}">${doc.status}</span>`;
    if (doc.status === "failed" && doc.error_message) {
      statusHtml += `<span class="error-banner">${doc.error_message}</span>`;
    }
    li.innerHTML = `
      <span class="doc-filename">${doc.filename}</span>
      ${statusHtml}
      <button class="remove-doc" data-document-id="${doc.id}">Entfernen</button>
    `;
    return li;
  }

  async function uploadFile(file) {
    const noDocsHint = document.getElementById("no-documents-hint");
    if (noDocsHint) noDocsHint.remove();

    const formData = new FormData();
    formData.append("file", file);
    const response = await fetch(`/api/projects/${window.PROJECT_ID}/documents`, {
      method: "POST",
      body: formData,
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      alert(body.detail || "Datei konnte nicht hochgeladen werden.");
      return;
    }
    documentList.appendChild(renderDocument(body));
  }

  dropzone.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", () => {
    Array.from(fileInput.files).forEach(uploadFile);
    fileInput.value = "";
  });

  ["dragenter", "dragover"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (event) => {
      event.preventDefault();
      dropzone.classList.add("dragover");
    });
  });
  ["dragleave", "drop"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (event) => {
      event.preventDefault();
      dropzone.classList.remove("dragover");
    });
  });
  dropzone.addEventListener("drop", (event) => {
    const files = Array.from(event.dataTransfer.files).filter((f) => f.type === "application/pdf");
    files.forEach(uploadFile);
  });

  documentList.addEventListener("click", async (event) => {
    const button = event.target.closest(".remove-doc");
    if (!button) return;
    const documentId = button.dataset.documentId;
    const response = await fetch(`/api/projects/${window.PROJECT_ID}/documents/${documentId}`, {
      method: "DELETE",
    });
    if (response.ok || response.status === 204) {
      button.closest("li").remove();
    }
  });
})();

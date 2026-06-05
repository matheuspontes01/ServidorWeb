const form = document.querySelector("#request-form");
const submitButton = document.querySelector("#submit");
const statusBox = document.querySelector("#status-box");
const statusText = document.querySelector("#status");
const contentTypeText = document.querySelector("#content-type");
const contentLengthText = document.querySelector("#content-length");
const bodyText = document.querySelector("#body");
const emptyPreview = document.querySelector("#empty-preview");
const htmlPreview = document.querySelector("#html-preview");

function setMetricState(state) {
  statusBox.classList.remove("ok", "error");
  if (state) {
    statusBox.classList.add(state);
  }
}

function setPreview(html) {
  if (html === null) {
    htmlPreview.hidden = true;
    htmlPreview.removeAttribute("srcdoc");
    emptyPreview.hidden = false;
    return;
  }

  emptyPreview.hidden = true;
  htmlPreview.hidden = false;
  htmlPreview.srcdoc = html;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  submitButton.disabled = true;
  statusText.textContent = "Buscando...";
  contentTypeText.textContent = "-";
  contentLengthText.textContent = "-";
  bodyText.textContent = "";
  setPreview(null);
  setMetricState("");

  const params = new URLSearchParams(new FormData(form));

  try {
    const response = await fetch(`/api/request?${params}`);
    const data = await response.json();

    if (!response.ok || !data.ok) {
      throw new Error(data.error || "Falha ao buscar recurso");
    }

    statusText.textContent = data.status;
    contentTypeText.textContent = data.content_type;
    contentLengthText.textContent = `${data.content_length} bytes`;
    bodyText.textContent = data.body_text;
    setMetricState(data.status.startsWith("200 ") ? "ok" : "error");

    if (data.is_html) {
      setPreview(data.body_text);
    }
  } catch (error) {
    statusText.textContent = "Erro";
    contentTypeText.textContent = "-";
    contentLengthText.textContent = "-";
    bodyText.textContent = error.message;
    setMetricState("error");
  } finally {
    submitButton.disabled = false;
  }
});

const selectTab = (tabId) => {
  document.querySelectorAll(".tab").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === tabId);
  });
  document.querySelectorAll(".tab-panel").forEach((panel) => {
    panel.classList.toggle("active", panel.id === `tab-${tabId}`);
  });
};

document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => selectTab(btn.dataset.tab));
});

const postForm = async (form, url, options = {}) => {
  const formData = new FormData(form);
  const isJson = options.json === true;
  const payload = isJson ? JSON.stringify(Object.fromEntries(formData.entries())) : formData;

  const res = await fetch(url, {
    method: "POST",
    headers: isJson ? { "Content-Type": "application/json" } : undefined,
    body: payload,
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.message || "Erreur serveur");
  }
  return res.json();
};

const bindForm = (id, url, options) => {
  const form = document.getElementById(id);
  if (!form) return;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await postForm(form, url, options);
      window.location.reload();
    } catch (err) {
      alert(err.message);
    }
  });
};

bindForm("profileForm", "/api/profile", { json: true });
bindForm("eventForm", "/api/events", { json: true });
bindForm("performanceForm", "/api/performances", { json: true });
bindForm("chatForm", "/api/messages", { json: true });

const mediaUploadForm = document.getElementById("mediaUploadForm");
if (mediaUploadForm) {
  mediaUploadForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await postForm(mediaUploadForm, "/api/media/upload");
      window.location.reload();
    } catch (err) {
      alert(err.message);
    }
  });
}

bindForm("mediaUrlForm", "/api/media/url", { json: true });

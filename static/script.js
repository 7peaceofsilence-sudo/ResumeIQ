(() => {
  const input = document.getElementById("resumes");
  const dropzone = document.getElementById("dropzone");
  const fileList = document.getElementById("file-list");
  const form = document.getElementById("analyze-form");
  const textarea = document.getElementById("job_description");
  const charCount = document.getElementById("char-count");
  const overlay = document.getElementById("loading-overlay");
  const button = document.getElementById("submit-button");
  if (!input || !dropzone || !fileList || !form) return;

  const maxFiles = 10;
  const maxTotalBytes = 10 * 1024 * 1024;
  const allowed = [".pdf", ".docx"];
  let chosenFiles = [];

  const prettySize = bytes => bytes < 1024 * 1024
    ? `${Math.max(1, Math.round(bytes / 1024))} KB`
    : `${(bytes / (1024 * 1024)).toFixed(1)} MB`;

  function renderFiles() {
    fileList.replaceChildren();
    if (!chosenFiles.length) {
      const empty = document.createElement("span");
      empty.className = "empty-files";
      empty.textContent = "No files selected yet";
      fileList.appendChild(empty);
      return;
    }
    chosenFiles.forEach(file => {
      const row = document.createElement("div");
      row.className = "file-item";
      const badge = document.createElement("span");
      badge.className = "file-badge";
      badge.textContent = file.name.toLowerCase().endsWith(".pdf") ? "PDF" : "DOCX";
      const name = document.createElement("span");
      name.className = "file-name";
      name.textContent = file.name;
      const size = document.createElement("span");
      size.className = "file-size";
      size.textContent = prettySize(file.size);
      row.append(badge, name, size);
      fileList.appendChild(row);
    });
  }

  function setFiles(files) {
    const incoming = Array.from(files);
    const valid = incoming.filter(file => allowed.some(ext => file.name.toLowerCase().endsWith(ext)));
    const combined = [...chosenFiles, ...valid];
    const unique = [];
    const seen = new Set();
    for (const file of combined) {
      const key = `${file.name}:${file.size}:${file.lastModified}`;
      if (!seen.has(key)) { seen.add(key); unique.push(file); }
    }
    if (incoming.some(file => !allowed.some(ext => file.name.toLowerCase().endsWith(ext)))) {
      alert("Only PDF and DOCX files are supported.");
    }
    if (unique.length > maxFiles) {
      alert(`Please choose no more than ${maxFiles} files.`);
      return;
    }
    if (unique.reduce((sum, file) => sum + file.size, 0) > maxTotalBytes) {
      alert("Total upload size must be under 10 MB.");
      return;
    }
    chosenFiles = unique;
    const transfer = new DataTransfer();
    chosenFiles.forEach(file => transfer.items.add(file));
    input.files = transfer.files;
    renderFiles();
  }

  input.addEventListener("change", () => {
    const selected = Array.from(input.files);
    chosenFiles = [];
    setFiles(selected);
  });
  ["dragenter", "dragover"].forEach(type => dropzone.addEventListener(type, event => {
    event.preventDefault();
    dropzone.classList.add("dragover");
  }));
  ["dragleave", "drop"].forEach(type => dropzone.addEventListener(type, event => {
    event.preventDefault();
    dropzone.classList.remove("dragover");
  }));
  dropzone.addEventListener("drop", event => setFiles(event.dataTransfer.files));

  function updateCount() {
    if (textarea && charCount) charCount.textContent = `${textarea.value.length.toLocaleString()} characters`;
  }
  textarea?.addEventListener("input", updateCount);
  updateCount();

  form.addEventListener("submit", event => {
    if (!chosenFiles.length && !input.files.length) {
      event.preventDefault();
      alert("Please upload at least one PDF or DOCX resume.");
      return;
    }
    if (!textarea.value.trim()) {
      event.preventDefault();
      textarea.focus();
      alert("Please paste the job description.");
      return;
    }
    if (overlay) {
      overlay.classList.add("visible");
      overlay.setAttribute("aria-hidden", "false");
    }
    if (button) {
      button.disabled = true;
      button.querySelector(".button-label").textContent = "Analyzing resumes…";
    }
  });

  if (window.location.hash === "#results") {
    document.getElementById("results")?.scrollIntoView({ behavior: "smooth" });
  }
})();

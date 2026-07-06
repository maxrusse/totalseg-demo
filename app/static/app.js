const state = {
  currentPath: "",
  selectedSeries: "",
  currentJob: "",
  pollTimer: null,
  masks: [],
  tasks: []
};

const $ = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) {
    let message = response.statusText;
    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {
      message = await response.text();
    }
    throw new Error(message);
  }
  return response.json();
}

function setProgress(value, label = "") {
  const pct = Math.max(0, Math.min(100, Number(value) || 0));
  $("progressBar").style.width = `${pct}%`;
  $("jobProgress").textContent = `${Math.round(pct)}%`;
  if (label) $("jobState").textContent = label;
}

function setLog(text) {
  $("logBox").textContent = text || "";
  $("logBox").scrollTop = $("logBox").scrollHeight;
}

async function loadStatus() {
  const status = await api("/api/status");
  state.currentPath = status.default_dicom_root;
  $("pathInput").value = status.default_dicom_root;
  const runtime = status.totalsegmentator_exists
    ? `TotalSegmentator: ${status.totalsegmentator}`
    : "TotalSegmentator fehlt: install.ps1 ausfuehren";
  const cuda = status.cuda_available ? `CUDA: ${status.cuda_device}` : "CUDA: nicht aktiv";
  $("runtimeLine").textContent = `${runtime} | ${cuda} | Python: ${status.local_python}`;
  const gpuOption = [...$("deviceSelect").options].find((option) => option.value === "gpu");
  if (gpuOption) {
    gpuOption.disabled = !status.cuda_available;
    if (status.cuda_available) $("deviceSelect").value = "gpu";
  }
  await loadDirectory(state.currentPath);
}

async function loadTasks() {
  const tasks = await api("/api/tasks");
  state.tasks = tasks;
  $("taskSelect").innerHTML = "";
  for (const task of tasks) {
    const option = document.createElement("option");
    option.value = task.id;
    option.textContent = `${task.label} (${task.modality}${task.license === "open" ? "" : ", Lizenz"})`;
    option.title = task.description || "";
    if (task.id === "lung_nodules") option.selected = true;
    $("taskSelect").appendChild(option);
  }
  applyTaskDefaults();
}

function applyTaskDefaults() {
  const task = state.tasks.find((item) => item.id === $("taskSelect").value);
  const supportsFast = task ? task.supports_fast !== false : true;
  $("fastCheck").disabled = !supportsFast;
  if (!supportsFast) $("fastCheck").checked = false;
}

async function loadDirectory(path) {
  const data = await api(`/api/fs/list?path=${encodeURIComponent(path)}`);
  state.currentPath = data.path;
  $("pathInput").value = data.path;
  $("browserPath").textContent = data.path;
  $("upBtn").disabled = !data.parent;
  $("upBtn").dataset.parent = data.parent || "";
  $("dirList").innerHTML = "";
  for (const dir of data.dirs) {
    const button = document.createElement("button");
    button.className = "dir-item";
    button.textContent = dir.name;
    button.title = dir.path;
    button.addEventListener("click", () => loadDirectory(dir.path).catch(showError));
    $("dirList").appendChild(button);
  }
}

function renderSeries(series) {
  $("seriesCount").textContent = `${series.length}`;
  $("seriesBody").innerHTML = "";
  for (const item of series) {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${escapeHtml(item.patient_id || "")}</td>
      <td>${escapeHtml(item.modality || "")}</td>
      <td title="${escapeHtml(item.path)}">${escapeHtml(item.series_description || item.series_uid || "")}</td>
      <td>${item.file_count || 0}</td>
      <td><button>Use</button></td>
    `;
    row.querySelector("button").addEventListener("click", () => {
      state.selectedSeries = item.path;
      $("selectedSeries").textContent = item.path;
    });
    $("seriesBody").appendChild(row);
  }
}

async function scanDicom() {
  const path = $("pathInput").value.trim();
  $("scanBtn").disabled = true;
  $("scanBtn").textContent = "Scan...";
  try {
    const data = await api(`/api/dicom/scan?path=${encodeURIComponent(path)}`);
    renderSeries(data.series);
    if (data.series.length) {
      state.selectedSeries = data.series[0].path;
      $("selectedSeries").textContent = data.series[0].path;
    }
  } finally {
    $("scanBtn").disabled = false;
    $("scanBtn").textContent = "Scannen";
  }
}

async function startJob() {
  if (!state.selectedSeries) {
    throw new Error("Bitte zuerst eine DICOM-Serie auswaehlen.");
  }
  const roi = $("roiInput").value.trim().split(/\s+/).filter(Boolean);
  const payload = {
    dicom_path: state.selectedSeries,
    task: $("taskSelect").value,
    fast: $("fastCheck").checked,
    device: $("deviceSelect").value,
    roi_subset: roi
  };
  $("runBtn").disabled = true;
  const job = await api("/api/jobs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  state.currentJob = job.id;
  pollJob(job.id);
  await loadJobs();
}

async function pollJob(jobId) {
  if (state.pollTimer) clearTimeout(state.pollTimer);
  try {
    const job = await api(`/api/jobs/${jobId}`);
    state.currentJob = job.id;
    setProgress(job.progress, `${job.state}: ${job.stage || ""}`);
    setLog(job.log_tail || "");
    $("runBtn").disabled = ["queued", "preprocessing", "running", "postprocessing"].includes(job.state);
    if (job.state === "completed") {
      await loadViewer(job.id);
      await loadJobs();
      return;
    }
    if (job.state === "failed") {
      await loadJobs();
      return;
    }
    state.pollTimer = setTimeout(() => pollJob(jobId), 1800);
  } catch (error) {
    showError(error);
    $("runBtn").disabled = false;
  }
}

async function loadJobs() {
  const jobs = await api("/api/jobs");
  $("jobList").innerHTML = "";
  for (const job of jobs.slice(0, 12)) {
    const item = document.createElement("button");
    item.className = "job-item";
    item.innerHTML = `
      <strong>${escapeHtml(job.id)}</strong>
      <span class="state-${escapeHtml(job.state)}">${escapeHtml(job.state)} ${job.progress || 0}%</span>
      <span>${escapeHtml(job.input?.task || "")} | ${escapeHtml(job.input?.dicom_path || "")}</span>
    `;
    item.addEventListener("click", async () => {
      state.currentJob = job.id;
      const full = await api(`/api/jobs/${job.id}`);
      setProgress(full.progress, `${full.state}: ${full.stage || ""}`);
      setLog(full.log_tail || "");
      if (full.state === "completed") await loadViewer(job.id);
      if (["queued", "preprocessing", "running", "postprocessing"].includes(full.state)) pollJob(job.id);
    });
    $("jobList").appendChild(item);
  }
}

async function loadViewer(jobId) {
  const data = await api(`/api/jobs/${jobId}/viewer`);
  state.currentJob = jobId;
  state.masks = data.masks || [];
  $("viewerInfo").textContent = `${data.width} x ${data.height} x ${data.slices}`;
  $("sliceRange").max = Math.max(0, data.slices - 1);
  $("sliceRange").value = Math.floor((data.slices - 1) / 2);
  $("maskSelect").innerHTML = "";
  for (const mask of state.masks) {
    const option = document.createElement("option");
    option.value = mask.key;
    option.textContent = mask.nonzero_slices ? `${mask.key} (${mask.first_slice}-${mask.last_slice})` : mask.key;
    $("maskSelect").appendChild(option);
  }
  const preferred = state.masks.find((mask) => mask.key === data.job?.input?.task) || state.masks[0];
  if (preferred) {
    $("maskSelect").value = preferred.key;
  }
  $("exportLink").href = `/api/jobs/${jobId}/volumes.txt`;
  renderVolumes(data.volumes || []);
  jumpToMaskSlice();
}

function jumpToMaskSlice() {
  const mask = state.masks.find((item) => item.key === $("maskSelect").value);
  if (mask && Number.isInteger(mask.first_slice)) {
    $("sliceRange").value = mask.first_slice;
  }
  updateImages();
}

function updateImages() {
  if (!state.currentJob) return;
  const slice = $("sliceRange").value || 0;
  const level = $("levelInput").value || -600;
  const width = $("widthInput").value || 1500;
  const stamp = Date.now();
  $("ctImage").src = `/api/jobs/${state.currentJob}/ct/${slice}.png?level=${level}&width=${width}&_=${stamp}`;
  if ($("maskSelect").value) {
    $("maskImage").src = `/api/jobs/${state.currentJob}/mask/${encodeURIComponent($("maskSelect").value)}/${slice}.png?_=${stamp}`;
  }
}

function renderVolumes(volumes) {
  $("volumesBody").innerHTML = "";
  for (const item of volumes) {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${escapeHtml(item.name)}</td>
      <td>${item.voxels}</td>
      <td>${Number(item.volume_ml).toFixed(3)}</td>
    `;
    $("volumesBody").appendChild(row);
  }
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function showError(error) {
  const message = error instanceof Error ? error.message : String(error);
  setLog(`${$("logBox").textContent}\n${message}`.trim());
}

function wireEvents() {
  $("openPathBtn").addEventListener("click", () => loadDirectory($("pathInput").value).catch(showError));
  $("upBtn").addEventListener("click", () => loadDirectory($("upBtn").dataset.parent).catch(showError));
  $("scanBtn").addEventListener("click", () => scanDicom().catch(showError));
  $("runBtn").addEventListener("click", () => startJob().catch((error) => {
    showError(error);
    $("runBtn").disabled = false;
  }));
  $("refreshJobsBtn").addEventListener("click", () => loadJobs().catch(showError));
  $("taskSelect").addEventListener("change", applyTaskDefaults);
  $("sliceRange").addEventListener("input", updateImages);
  $("maskSelect").addEventListener("change", jumpToMaskSlice);
  $("levelInput").addEventListener("change", updateImages);
  $("widthInput").addEventListener("change", updateImages);
}

async function init() {
  wireEvents();
  await loadTasks();
  await loadStatus();
  await loadJobs();
}

init().catch(showError);

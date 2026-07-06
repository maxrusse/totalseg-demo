const state = {
  currentScene: "",
  currentJob: "",
  pollTimer: null,
  masks: [],
  scenes: []
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
  const runtime = status.local_python_exists
    ? `Python: ${status.local_python}`
    : "Python runtime missing: run install.ps1";
  $("runtimeLine").textContent = `${runtime} | scenes: ${status.scene_count || 0} | demo mode`;
}

function renderScenes(scenes) {
  state.scenes = scenes;
  $("sceneSelect").innerHTML = "";
  for (const scene of scenes) {
    const option = document.createElement("option");
    option.value = scene.id;
    option.textContent = `${scene.label}`;
    option.title = scene.description || "";
    if (scene.recommended) option.selected = true;
    $("sceneSelect").appendChild(option);
  }
  updateSceneSelection();
}

function updateSceneSelection() {
  const scene = state.scenes.find((item) => item.id === $("sceneSelect").value);
  state.currentScene = scene?.id || "";
  $("selectedScene").textContent = scene ? scene.label : "none";
  $("sceneDescription").textContent = scene?.description || "Select a demo scene.";
}

async function loadScenes() {
  const scenes = await api("/api/scenes");
  renderScenes(scenes);
}

async function startJob() {
  if (!state.currentScene) {
    throw new Error("Please choose a demo scene first.");
  }
  const payload = {
    scene_id: state.currentScene,
    fast: $("fastCheck").checked
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
    state.pollTimer = setTimeout(() => pollJob(jobId), 1200);
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
      <span>${escapeHtml(job.input?.scene_id || "")}</span>
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
  const preferred = state.masks[0];
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
  $("runBtn").addEventListener("click", () => startJob().catch((error) => {
    showError(error);
    $("runBtn").disabled = false;
  }));
  $("refreshJobsBtn").addEventListener("click", () => loadJobs().catch(showError));
  $("reloadScenesBtn").addEventListener("click", () => loadScenes().catch(showError));
  $("sceneSelect").addEventListener("change", updateSceneSelection);
  $("sliceRange").addEventListener("input", updateImages);
  $("maskSelect").addEventListener("change", jumpToMaskSlice);
  $("levelInput").addEventListener("change", updateImages);
  $("widthInput").addEventListener("change", updateImages);
}

async function init() {
  wireEvents();
  await loadScenes();
  await loadStatus();
  await loadJobs();
}

init().catch(showError);

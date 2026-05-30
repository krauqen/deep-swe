(function () {
  const data = window.REPO_VIZ_DATA;
  const state = {
    query: "",
    dockerBucket: "all",
    language: "all",
    selectedDocker: null,
    selectedProject: null,
    projectSort: "tasks",
    liveJobs: [],
    liveJob: "",
    liveTrial: "",
    liveTimer: null,
  };

  const palette = ["#147d72", "#cf5b45", "#b7821e", "#6958b7", "#477a3a", "#8b5c2d"];
  const byId = (id) => document.getElementById(id);
  const fmt = new Intl.NumberFormat("en");
  const money = new Intl.NumberFormat("en", { style: "currency", currency: "USD" });

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function textMatchesTask(task) {
    if (!state.query) return true;
    const haystack = [
      task.id,
      task.title,
      task.description,
      task.language,
      task.repo,
      task.dockerfile,
      task.installLabels.join(" "),
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(state.query.toLowerCase());
  }

  function barRows(container, entries, options = {}) {
    const max = Math.max(...entries.map((entry) => entry[1]), 1);
    container.innerHTML = entries
      .map(([label, value], index) => {
        const width = Math.max(4, (value / max) * 100);
        const color = options.color || palette[index % palette.length];
        return `
          <div class="bar-row">
            <div class="bar-label" title="${escapeHtml(label)}">${escapeHtml(label)}</div>
            <div class="bar-track"><div class="bar-fill" style="width:${width}%;background:${color}"></div></div>
            <div class="bar-value">${fmt.format(value)}</div>
          </div>
        `;
      })
      .join("");
  }

  function renderMetrics() {
    const baseImages = Object.keys(data.docker.baseImages).length;
    const metrics = [
      ["Tasks", data.summary.taskCount, "Harbor/Pier task folders"],
      ["Projects", data.summary.projectCount, "Unique GitHub repositories"],
      ["Dockerfiles", data.docker.taskCount, `${baseImages} base image${baseImages === 1 ? "" : "s"}`],
      ["Local Jobs", data.summary.jobCount, "Pier run output folders"],
    ];
    byId("metrics").innerHTML = metrics
      .map(
        ([label, value, hint]) => `
          <article class="metric">
            <span>${escapeHtml(label)}</span>
            <strong>${fmt.format(value)}</strong>
            <small>${escapeHtml(hint)}</small>
          </article>
        `,
      )
      .join("");
  }

  function renderOverview() {
    byId("generatedAt").textContent = `Generated ${new Date(data.generatedAt).toLocaleString()}`;
    renderMetrics();
    barRows(byId("languageBars"), Object.entries(data.summary.languageCounts));
    barRows(byId("fileBars"), Object.entries(data.summary.fileInventory.byTopLevel));
    byId("notes").innerHTML = data.notes
      .map(
        (note) => `
          <article class="note">
            <h3>${escapeHtml(note.title)}</h3>
            <p>${escapeHtml(note.body)}</p>
          </article>
        `,
      )
      .join("");
  }

  function renderDockerStory() {
    const bucketEntries = Object.entries(data.docker.lineBuckets);
    const max = Math.max(...bucketEntries.map((entry) => entry[1]), 1);
    byId("dockerBuckets").innerHTML = bucketEntries
      .map(([label, value], index) => {
        const height = Math.max(12, (value / max) * 138);
        return `
          <div class="bucket">
            <div class="bucket-bar" style="height:${height}px;background:${palette[index]}"></div>
            <div class="bucket-label"><strong>${fmt.format(value)}</strong><br>${escapeHtml(label)}</div>
          </div>
        `;
      })
      .join("");

    barRows(byId("installBars"), Object.entries(data.docker.installPatterns).slice(0, 10));

    const base = Object.keys(data.docker.baseImages)[0] || "unknown";
    byId("dockerCallout").innerHTML = `
      All ${fmt.format(data.docker.taskCount)} task Dockerfiles use <strong>${escapeHtml(base)}</strong>.
      ${fmt.format(data.docker.cloneCount)} clone an upstream repository and ${fmt.format(data.docker.checkoutCount)}
      check out a fixed revision. The dominant recipe is <strong>FROM</strong> shared base,
      <strong>WORKDIR /app</strong>, <strong>git clone && git checkout</strong>, dependency warm-up,
      then <strong>CMD ["/bin/bash"]</strong>.
    `;
  }

  function filteredDockerTasks() {
    return data.tasks.filter((task) => {
      const bucketMatch = state.dockerBucket === "all" || task.dockerLineBucket === state.dockerBucket;
      return bucketMatch && textMatchesTask(task);
    });
  }

  function renderPills(labels) {
    return `<div class="pill-list">${labels.map((label) => `<span class="pill">${escapeHtml(label)}</span>`).join("")}</div>`;
  }

  function selectDocker(taskId) {
    state.selectedDocker = data.tasks.find((task) => task.id === taskId) || data.tasks[0];
    renderDockerSelection();
    document.querySelectorAll("#dockerRows tr").forEach((row) => {
      row.classList.toggle("selected", row.dataset.taskId === state.selectedDocker.id);
    });
  }

  function renderDockerSelection() {
    const task = state.selectedDocker || filteredDockerTasks()[0];
    if (!task) {
      byId("selectedDockerTitle").textContent = "No Dockerfile selected";
      byId("selectedDockerMeta").textContent = "Adjust the search or line-count filter to pick a task.";
      byId("dockerCode").textContent = "";
      return;
    }
    state.selectedDocker = task;
    byId("selectedDockerTitle").textContent = task.id;
    byId("selectedDockerMeta").textContent = `${task.dockerfilePath} · ${task.dockerLineCount} lines · ${task.repo}`;
    byId("dockerCode").innerHTML = escapeHtml(task.dockerfile);
  }

  function renderDockerRows() {
    const tasks = filteredDockerTasks();
    byId("dockerCount").textContent = `${fmt.format(tasks.length)} shown`;
    byId("dockerRows").innerHTML = tasks.length
      ? tasks
          .map(
            (task) => `
              <tr data-task-id="${escapeHtml(task.id)}">
                <td><strong>${escapeHtml(task.id)}</strong><br><span>${escapeHtml(task.title)}</span></td>
                <td>${escapeHtml(task.language)}</td>
                <td>${fmt.format(task.dockerLineCount)}</td>
                <td>${renderPills(task.installLabels)}</td>
              </tr>
            `,
          )
          .join("")
      : '<tr><td colspan="4">No Dockerfiles match the current filters.</td></tr>';

    byId("dockerRows").querySelectorAll("tr").forEach((row) => {
      row.addEventListener("click", () => selectDocker(row.dataset.taskId));
    });

    if (!tasks.some((task) => state.selectedDocker && task.id === state.selectedDocker.id)) {
      state.selectedDocker = tasks[0] || null;
    }
    renderDockerSelection();
    if (state.selectedDocker) {
      const row = byId("dockerRows").querySelector(`[data-task-id="${CSS.escape(state.selectedDocker.id)}"]`);
      if (row) row.classList.add("selected");
    }
  }

  function renderLanguageOptions() {
    byId("languageFilter").innerHTML =
      '<option value="all">All languages</option>' +
      Object.keys(data.summary.languageCounts)
        .map((lang) => `<option value="${escapeHtml(lang)}">${escapeHtml(lang)}</option>`)
        .join("");
  }

  function renderTasks() {
    const tasks = data.tasks
      .filter(textMatchesTask)
      .filter((task) => state.language === "all" || task.language === state.language)
      .slice(0, 60);

    byId("taskGrid").innerHTML = tasks
      .map(
        (task) => `
          <article class="task-card">
            <h3>${escapeHtml(task.title)}</h3>
            <p>${escapeHtml(task.repo)}</p>
            <div class="task-meta">
              <span class="pill">${escapeHtml(task.language)}</span>
              <span class="pill">${escapeHtml(task.category || "uncategorized")}</span>
              <span class="pill">${fmt.format(task.dockerLineCount)} Docker lines</span>
            </div>
          </article>
        `,
      )
      .join("") || '<div class="callout">No tasks match the current filters.</div>';
  }

  function projectMetric(project, key) {
    if (key === "stars") return project.stars || 0;
    if (key === "issues") return project.open_issues || 0;
    return project.task_count || 0;
  }

  function sortedProjects() {
    return [...data.projects]
      .filter((project) => {
        if (!state.query) return true;
        return [project.repo, project.summary, Object.keys(project.dataset_languages || {}).join(" ")]
          .join(" ")
          .toLowerCase()
          .includes(state.query.toLowerCase());
      })
      .sort((a, b) => projectMetric(b, state.projectSort) - projectMetric(a, state.projectSort));
  }

  function selectProject(repo) {
    state.selectedProject = data.projects.find((project) => project.repo === repo) || sortedProjects()[0];
    renderProjects();
  }

  function renderProjectDetail() {
    const project = state.selectedProject || sortedProjects()[0];
    state.selectedProject = project;
    if (!project) {
      byId("projectTitle").textContent = "Project detail";
      byId("projectDetail").innerHTML = "<p>No projects match the current search.</p>";
      return;
    }
    byId("projectTitle").textContent = project.repo;
    const languages = Object.entries(project.dataset_languages || {})
      .map(([lang, count]) => `${lang} (${count})`)
      .join(", ");
    byId("projectDetail").innerHTML = `
      <p>${escapeHtml(project.summary || "No summary available.")}</p>
      <div class="task-meta">
        <span class="pill">${fmt.format(project.task_count || 0)} tasks</span>
        <span class="pill">${escapeHtml(languages || "unknown dataset language")}</span>
        <span class="pill">${fmt.format(project.stars || 0)} stars</span>
        <span class="pill">${fmt.format(project.open_issues || 0)} issues</span>
      </div>
      <ul>
        ${(project.task_titles || []).map((title) => `<li>${escapeHtml(title)}</li>`).join("")}
      </ul>
    `;
  }

  function renderProjects() {
    const projects = sortedProjects().slice(0, 80);
    if (!projects.some((project) => state.selectedProject && project.repo === state.selectedProject.repo)) {
      state.selectedProject = projects[0];
    }
    byId("projectList").innerHTML = projects
      .map((project) => {
        const metric = projectMetric(project, state.projectSort);
        return `
          <div class="project-row ${state.selectedProject && state.selectedProject.repo === project.repo ? "selected" : ""}" data-repo="${escapeHtml(project.repo)}">
            <div>
              <strong>${escapeHtml(project.repo)}</strong><br>
              <span>${escapeHtml(project.github_language || "Unknown")} · ${fmt.format(project.task_count || 0)} task${project.task_count === 1 ? "" : "s"}</span>
            </div>
            <div class="project-score">${fmt.format(metric)}</div>
          </div>
        `;
      })
      .join("");
    byId("projectList").querySelectorAll(".project-row").forEach((row) => {
      row.addEventListener("click", () => selectProject(row.dataset.repo));
    });
    renderProjectDetail();
  }

  function renderJobs() {
    if (!data.jobs.length) {
      byId("jobPanels").innerHTML = '<div class="callout">No local job output found.</div>';
      return;
    }
    byId("jobPanels").innerHTML = data.jobs
      .map((job) => {
        const stats = job.stats || {};
        const statItems = [
          ["Trials", job.totalTrials || 0],
          ["Completed", stats.n_completed_trials || 0],
          ["Errored", stats.n_errored_trials || 0],
          ["Input tokens", stats.n_input_tokens || 0],
          ["Cost", stats.cost_usd == null ? "$0.00" : money.format(stats.cost_usd)],
        ];
        return `
          <article class="job-card">
            <div class="panel-title">
              <div>
                <h3>${escapeHtml(job.name)}</h3>
                <p>${escapeHtml(job.path)}</p>
              </div>
            </div>
            <div class="job-stats">
              ${statItems
                .map(
                  ([label, value]) => `
                    <div class="job-stat">
                      <span>${escapeHtml(label)}</span>
                      <strong>${typeof value === "number" ? fmt.format(value) : escapeHtml(value)}</strong>
                    </div>
                  `,
                )
                .join("")}
            </div>
            <div class="trial-list">
              ${(job.trials || [])
                .map((trial) => {
                  const errored = Boolean(trial.exceptionType);
                  const status = errored ? trial.exceptionType : `reward ${trial.reward ?? "missing"}`;
                  return `
                    <div class="trial">
                      <div>
                        <strong>${escapeHtml(trial.taskName)}</strong><br>
                        <span>${escapeHtml(trial.model || trial.agent || "agent")} · ${fmt.format(trial.steps || 0)} steps · ${money.format(trial.costUsd || 0)}</span>
                      </div>
                      <strong class="${errored ? "status-error" : "status-ok"}">${escapeHtml(status)}</strong>
                    </div>
                  `;
                })
                .join("")}
            </div>
          </article>
        `;
      })
      .join("");
  }

  async function fetchJson(url) {
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
    return response.json();
  }

  function selectedLiveJob() {
    return state.liveJobs.find((job) => job.name === state.liveJob) || state.liveJobs[0];
  }

  function selectedLiveTrial() {
    const job = selectedLiveJob();
    if (!job) return null;
    return (job.trials || []).find((trial) => trial.name === state.liveTrial) || (job.trials || [])[0];
  }

  function renderLiveSelectors() {
    const job = selectedLiveJob();
    byId("liveJobSelect").innerHTML = state.liveJobs
      .map((item) => `<option value="${escapeHtml(item.name)}">${escapeHtml(item.name)}</option>`)
      .join("");
    if (job) {
      byId("liveJobSelect").value = job.name;
      state.liveJob = job.name;
    }

    const trials = job ? job.trials || [] : [];
    const trial = selectedLiveTrial();
    byId("liveTrialSelect").innerHTML = trials
      .map((item) => `<option value="${escapeHtml(item.name)}">${escapeHtml(item.taskName || item.name)}</option>`)
      .join("");
    if (trial) {
      byId("liveTrialSelect").value = trial.name;
      state.liveTrial = trial.name;
    }

    byId("liveTrialMeta").innerHTML = trial
      ? `
        <span><strong>Trial:</strong> ${escapeHtml(trial.name)}</span>
        <span><strong>Status:</strong> ${escapeHtml(trial.exceptionType || (trial.finishedAt ? "finished" : "running or pending"))}</span>
        <span><strong>Reward:</strong> ${escapeHtml(trial.reward ?? "none yet")}</span>
      `
      : "No trials found yet.";
  }

  function renderLiveEvents(payload) {
    const events = payload.events || [];
    byId("liveTitle").textContent = payload.trial || "Trajectory";
    byId("liveSource").textContent = payload.source || "No trajectory/session file yet.";
    byId("liveCount").textContent = `${fmt.format(events.length)} events`;
    byId("liveEvents").innerHTML = events.length
      ? events
          .map((event) => {
            const role = event.role || "event";
            const stamp = event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : `#${event.index}`;
            return `
              <article class="live-event ${escapeHtml(role)}">
                <div class="live-role">
                  <strong>${escapeHtml(role)}</strong><br>
                  <span>${escapeHtml(stamp)}</span><br>
                  <span>${escapeHtml(event.rawType || "")}</span>
                </div>
                <div class="live-body">
                  <h4>${escapeHtml(event.title || role)}</h4>
                  <pre>${escapeHtml(event.text || "")}</pre>
                </div>
              </article>
            `;
          })
          .join("")
      : '<div class="callout">No events are available for this trial yet.</div>';

    const scroller = byId("liveEvents");
    scroller.scrollTop = scroller.scrollHeight;
  }

  async function refreshLiveJobs() {
    try {
      const payload = await fetchJson("/api/live/jobs");
      state.liveJobs = payload.jobs || [];
      if (!state.liveJobs.some((job) => job.name === state.liveJob)) {
        state.liveJob = state.liveJobs[0]?.name || "";
      }
      const job = selectedLiveJob();
      if (job && !(job.trials || []).some((trial) => trial.name === state.liveTrial)) {
        state.liveTrial = (job.trials || [])[0]?.name || "";
      }
      byId("liveStatus").textContent = "Connected";
      renderLiveSelectors();
      await refreshLiveEvents();
    } catch (error) {
      byId("liveStatus").textContent = "Static server";
      byId("liveEvents").innerHTML = `
        <div class="callout">
          Live trajectory endpoints are not available from this server. Start with
          <strong>./analysis/repo-viz/serve.sh</strong> instead of python's plain http.server.
        </div>
      `;
    }
  }

  async function refreshLiveEvents() {
    const job = selectedLiveJob();
    const trial = selectedLiveTrial();
    if (!job || !trial) return;
    const url = `/api/live/events?job=${encodeURIComponent(job.name)}&trial=${encodeURIComponent(trial.name)}&limit=240`;
    const payload = await fetchJson(url);
    renderLiveEvents(payload);
  }

  function setLiveTimer() {
    if (state.liveTimer) {
      clearInterval(state.liveTimer);
      state.liveTimer = null;
    }
    if (byId("liveAutorefresh").checked) {
      state.liveTimer = setInterval(refreshLiveJobs, 1800);
    }
  }

  function renderAll() {
    renderDockerRows();
    renderTasks();
    renderProjects();
  }

  function wireEvents() {
    byId("globalSearch").addEventListener("input", (event) => {
      state.query = event.target.value.trim();
      renderAll();
    });

    document.querySelectorAll("[data-bucket]").forEach((button) => {
      button.addEventListener("click", () => {
        state.dockerBucket = button.dataset.bucket;
        document.querySelectorAll("[data-bucket]").forEach((item) => item.classList.toggle("active", item === button));
        renderDockerRows();
      });
    });

    byId("languageFilter").addEventListener("change", (event) => {
      state.language = event.target.value;
      renderTasks();
    });

    byId("projectSort").addEventListener("change", (event) => {
      state.projectSort = event.target.value;
      renderProjects();
    });

    byId("liveRefresh").addEventListener("click", refreshLiveJobs);
    byId("liveAutorefresh").addEventListener("change", setLiveTimer);
    byId("liveJobSelect").addEventListener("change", async (event) => {
      state.liveJob = event.target.value;
      state.liveTrial = "";
      renderLiveSelectors();
      await refreshLiveEvents();
    });
    byId("liveTrialSelect").addEventListener("change", async (event) => {
      state.liveTrial = event.target.value;
      renderLiveSelectors();
      await refreshLiveEvents();
    });
  }

  renderOverview();
  renderDockerStory();
  renderLanguageOptions();
  renderJobs();
  renderAll();
  wireEvents();
  refreshLiveJobs();
  setLiveTimer();
})();

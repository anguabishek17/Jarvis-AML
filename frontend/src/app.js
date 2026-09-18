/**
 * JARVIS-AML Master Application Controller
 * Connects FastAPI Backend, Graph Canvas, Timeline, DNA Viewer, Analytics Charts,
 * 11 Investigation Tabs, Case Repository, and Dynamic Custom Transaction Ingestion.
 */

document.addEventListener("DOMContentLoaded", () => {
  const API_BASE = window.location.origin.includes("http") ? window.location.origin : "http://127.0.0.1:8089";

  // Initialize Analytics Chart Renderer
  const analyticsChart = new AnalyticsChartRenderer("analyticsOverviewChart", "analyticsTooltip");
  window.analyticsChart = analyticsChart;

  // Initialize Graph Renderer
  const graphRenderer = new GraphCanvasRenderer("graphCanvas", "graphTooltip");
  window.graphRenderer = graphRenderer;

  // Initialize Timeline Controller
  const timelineController = new TimelineController(
    "timelineSlider",
    "timelinePlayBtn",
    "timelineResetBtn",
    "timelineStageLabel",
    "timelineMarkers"
  );

  // Initialize DNA Viewer
  const dnaViewer = new DNAViewer(
    {
      signatureId: "dnaSignatureString",
      hashId: "dnaSha256Short",
      genesGridId: "dnaGenesGrid",
      similarListId: "dnaSimilarCasesList",
      evolutionListId: "dnaEvolutionList",
    },
    {
      modal: document.getElementById("geneEvidenceModal"),
      title: document.getElementById("modalGeneTitle"),
      content: document.getElementById("modalGeneContent"),
      closeBtn: document.getElementById("closeModalBtn"),
    }
  );

  let currentCaseData = null;
  let allScenarios = [];
  let customUploadedFile = null;
  let customValidatedCsvText = "";

  // DOM Elements
  const scenarioSelect = document.getElementById("scenarioSelect");
  const caseQueueList = document.getElementById("caseQueueList");
  const casesTableBody = document.getElementById("casesTableBody");
  const accountSearchInput = document.getElementById("accountSearchInput");
  const searchBtn = document.getElementById("searchBtn");
  const exportPdfBtn = document.getElementById("exportPdfBtn");
  const sidebarExportPdfBtn = document.getElementById("sidebarExportPdfBtn");
  const exportReportBtn = document.getElementById("exportReportBtn");
  const graphModeGroup = document.getElementById("graphModeGroup");
  const resetZoomBtn = document.getElementById("resetZoomBtn");
  const togglePhysicsBtn = document.getElementById("togglePhysicsBtn");

  // Settings Modal DOM Elements
  const settingsModal = document.getElementById("settingsModal");
  const closeSettingsModalBtn = document.getElementById("closeSettingsModalBtn");
  const dismissSettingsBtn = document.getElementById("dismissSettingsBtn");

  // Custom Analysis Modal DOM Elements
  const openCustomAnalysisBtn = document.getElementById("openCustomAnalysisBtn");
  const customAnalysisModal = document.getElementById("customAnalysisModal");
  const closeCustomModalBtn = document.getElementById("closeCustomModalBtn");
  const methodCsvTab = document.getElementById("methodCsvTab");
  const methodPasteTab = document.getElementById("methodPasteTab");
  const methodCsvSection = document.getElementById("methodCsvSection");
  const methodPasteSection = document.getElementById("methodPasteSection");
  const csvDropZone = document.getElementById("csvDropZone");
  const csvFileInput = document.getElementById("csvFileInput");
  const browseFileBtn = document.getElementById("browseFileBtn");
  const fileSelectedInfo = document.getElementById("fileSelectedInfo");
  const selectedFileName = document.getElementById("selectedFileName");
  const selectedFileSize = document.getElementById("selectedFileSize");
  const removeSelectedFileBtn = document.getElementById("removeSelectedFileBtn");
  const pasteCsvTextarea = document.getElementById("pasteCsvTextarea");
  const validatePastedBtn = document.getElementById("validatePastedBtn");
  const clearPastedBtn = document.getElementById("clearPastedBtn");
  const loadSampleCsvBtn = document.getElementById("loadSampleCsvBtn");
  const validationSummaryCard = document.getElementById("validationSummaryCard");
  const valStatusBadge = document.getElementById("valStatusBadge");
  const valTotalRows = document.getElementById("valTotalRows");
  const valValidRows = document.getElementById("valValidRows");
  const valInvalidRows = document.getElementById("valInvalidRows");
  const valTotalVol = document.getElementById("valTotalVol");
  const valWarningsList = document.getElementById("valWarningsList");
  const valErrorsList = document.getElementById("valErrorsList");
  const analyzeTransactionsBtn = document.getElementById("analyzeTransactionsBtn");

  // Tab Manager (Synchronize Sidebar Nav and Horizontal Tab Strip)
  const tabButtons = document.querySelectorAll(".tab-btn");
  const navItemsWithTab = document.querySelectorAll(".nav-item[data-tab]");
  const tabPanes = document.querySelectorAll(".tab-pane");

  function activateTab(tabId) {
    if (!tabId) return;
    
    // Update Horizontal Tab Buttons
    tabButtons.forEach(b => {
      b.classList.toggle("active", b.dataset.tab === tabId);
    });

    // Update Sidebar Nav Items
    document.querySelectorAll(".nav-item").forEach(n => {
      if (n.dataset.tab) {
        n.classList.toggle("active", n.dataset.tab === tabId);
      } else {
        n.classList.remove("active");
      }
    });

    // Update Tab Panes
    tabPanes.forEach(p => {
      p.classList.toggle("active", p.id === tabId);
    });

    // Scroll workspace to top
    const workspaceBody = document.querySelector(".workspace-body");
    if (workspaceBody) workspaceBody.scrollTop = 0;

    // Trigger responsive render if returning to overview or network
    if (tabId === "tab-overview" || tabId === "tab-network") {
      setTimeout(() => {
        if (graphRenderer) graphRenderer.resize();
        if (analyticsChart) analyticsChart.resize();
      }, 50);
    }
  }

  // Bind Tab Click Handlers
  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => activateTab(btn.dataset.tab));
  });

  navItemsWithTab.forEach(item => {
    item.addEventListener("click", () => activateTab(item.dataset.tab));
  });

  // Action Buttons in Sidebar
  document.querySelectorAll(".nav-item[data-action]").forEach(actionBtn => {
    actionBtn.addEventListener("click", () => {
      const action = actionBtn.dataset.action;
      if (action === "open-custom-analysis") {
        if (customAnalysisModal) customAnalysisModal.classList.remove("hidden");
      } else if (action === "open-settings") {
        if (settingsModal) settingsModal.classList.remove("hidden");
      }
    });
  });

  // Settings Modal Handlers
  if (closeSettingsModalBtn) {
    closeSettingsModalBtn.addEventListener("click", () => {
      settingsModal.classList.add("hidden");
    });
  }
  if (dismissSettingsBtn) {
    dismissSettingsBtn.addEventListener("click", () => {
      settingsModal.classList.add("hidden");
    });
  }

  // Drawer Controls
  const accountInspectorDrawer = document.getElementById("accountInspectorDrawer");
  const closeDrawerBtn = document.getElementById("closeDrawerBtn");
  if (closeDrawerBtn) {
    closeDrawerBtn.addEventListener("click", () => {
      accountInspectorDrawer.classList.add("hidden");
    });
  }

  // Graph Modes
  if (graphModeGroup) {
    graphModeGroup.querySelectorAll(".mode-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        graphModeGroup.querySelectorAll(".mode-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        const mode = btn.dataset.mode;
        graphRenderer.setMode(mode);
      });
    });
  }

  if (resetZoomBtn) {
    resetZoomBtn.addEventListener("click", () => {
      graphRenderer.resetView();
    });
  }

  if (togglePhysicsBtn) {
    togglePhysicsBtn.addEventListener("click", () => {
      const isRunning = graphRenderer.togglePhysics();
      togglePhysicsBtn.textContent = isRunning ? "⏸ Freeze" : "▶ Unfreeze";
    });
  }

  // Search Account
  const handleSearch = () => {
    const query = accountSearchInput.value.trim();
    if (!query || !currentCaseData) return;
    const targetNode = graphRenderer.nodes.find(n => n.id.toLowerCase().includes(query.toLowerCase()));
    if (targetNode) {
      graphRenderer.selectedNode = targetNode;
      inspectAccount(targetNode.id);
    } else {
      alert(`Account '${query}' not found in active scenario.`);
    }
  };

  if (searchBtn) searchBtn.addEventListener("click", handleSearch);
  if (accountSearchInput) {
    accountSearchInput.addEventListener("keypress", e => {
      if (e.key === "Enter") handleSearch();
    });
  }

  // Node Click Callback from Graph Canvas
  graphRenderer.onNodeClick = (node) => {
    inspectAccount(node.id);
  };

  // Timeline Stage Change Callback
  timelineController.onStageChange = (stage) => {
    if (!stage) return;
    graphRenderer.setMode("SUSPICIOUS", { pathNodes: stage.accounts_active });
  };

  // Export Forensic Investigation PDF Report Handler
  async function triggerPdfDownload() {
    if (!currentCaseData) {
      alert("No active case to export. Please select or run a case first.");
      return;
    }
    const caseId = currentCaseData.scenario_id || currentCaseData.case_id || "ACTIVE_CASE";
    const originalText = exportPdfBtn ? exportPdfBtn.innerHTML : "📄 Export PDF";
    if (exportPdfBtn) {
      exportPdfBtn.disabled = true;
      exportPdfBtn.textContent = "⏳ Generating PDF...";
    }

    try {
      console.log(`[PDFExport] Requesting PDF report from ${API_BASE}/api/cases/${caseId}/export/pdf`);
      const res = await fetch(`${API_BASE}/api/cases/${caseId}/export/pdf`);
      if (!res.ok) {
        const err = await res.text();
        throw new Error(`Server returned HTTP ${res.status}: ${err}`);
      }

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `JARVIS-AML-${caseId}-Investigation-Report.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
      console.log(`[PDFExport] Successfully downloaded PDF for ${caseId}`);
    } catch (err) {
      console.error("[PDFExport] PDF Export Error:", err);
      alert(`Unable to generate PDF report: ${err.message}`);
    } finally {
      if (exportPdfBtn) {
        exportPdfBtn.disabled = false;
        exportPdfBtn.innerHTML = originalText;
      }
    }
  }

  if (exportPdfBtn) exportPdfBtn.addEventListener("click", triggerPdfDownload);
  if (sidebarExportPdfBtn) sidebarExportPdfBtn.addEventListener("click", triggerPdfDownload);

  // Export Investigation Dossier (JSON)
  if (exportReportBtn) {
    exportReportBtn.addEventListener("click", () => {
      if (!currentCaseData) return;
      const exportPayload = {
        investigation_system: "JARVIS-AML Intelligence Platform",
        scenario_id: currentCaseData.scenario_id,
        timestamp_utc: new Date().toISOString(),
        forensic_integrity_seal: currentCaseData.primary_dna ? currentCaseData.primary_dna.evidence_payload_sha256 : "N/A",
        executive_summary: currentCaseData.narrative_brief,
        money_trail_dna: currentCaseData.primary_dna,
        patterns_detected: currentCaseData.patterns,
        attack_paths: currentCaseData.attack_paths,
        priority_rankings: currentCaseData.priority_rankings,
        account_roles: currentCaseData.roles,
      };

      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(exportPayload, null, 2));
      const downloadAnchor = document.createElement("a");
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `JARVIS_AML_DOSSIER_${currentCaseData.scenario_id}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
    });
  }

  // =========================================================================
  // Custom Transaction Analysis Wiring
  // =========================================================================

  if (openCustomAnalysisBtn) {
    openCustomAnalysisBtn.addEventListener("click", () => {
      customAnalysisModal.classList.remove("hidden");
    });
  }

  if (closeCustomModalBtn) {
    closeCustomModalBtn.addEventListener("click", () => {
      customAnalysisModal.classList.add("hidden");
    });
  }

  window.addEventListener("click", (e) => {
    if (e.target === customAnalysisModal) {
      customAnalysisModal.classList.add("hidden");
    }
    if (e.target === settingsModal) {
      settingsModal.classList.add("hidden");
    }
  });

  // Input Method Switcher
  if (methodCsvTab && methodPasteTab) {
    methodCsvTab.addEventListener("click", () => {
      methodCsvTab.classList.add("active");
      methodPasteTab.classList.remove("active");
      methodCsvSection.classList.add("active");
      methodPasteSection.classList.remove("active");
    });

    methodPasteTab.addEventListener("click", () => {
      methodPasteTab.classList.add("active");
      methodCsvTab.classList.remove("active");
      methodPasteSection.classList.add("active");
      methodCsvSection.classList.remove("active");
    });
  }

  // File Drag & Drop & Browse
  if (browseFileBtn && csvFileInput) {
    browseFileBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      csvFileInput.click();
    });
  }

  if (csvDropZone && csvFileInput) {
    csvDropZone.addEventListener("click", (e) => {
      if (e.target !== browseFileBtn) {
        csvFileInput.click();
      }
    });

    csvDropZone.addEventListener("dragover", (e) => {
      e.preventDefault();
      csvDropZone.classList.add("dragover");
    });

    csvDropZone.addEventListener("dragleave", () => {
      csvDropZone.classList.remove("dragover");
    });

    csvDropZone.addEventListener("drop", (e) => {
      e.preventDefault();
      csvDropZone.classList.remove("dragover");
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        handleFileSelected(e.dataTransfer.files[0]);
      }
    });

    csvFileInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files.length > 0) {
        handleFileSelected(e.target.files[0]);
      }
    });
  }

  async function handleFileSelected(file) {
    if (!file) return;
    try {
      console.log("[CustomAnalysis] File selected:", file.name, file.size);
      customUploadedFile = file;
      selectedFileName.textContent = file.name;
      selectedFileSize.textContent = `(${(file.size / 1024).toFixed(1)} KB)`;
      fileSelectedInfo.classList.remove("hidden");

      const text = await file.text();
      customValidatedCsvText = text;
      if (pasteCsvTextarea) pasteCsvTextarea.value = text;

      if (!text || !text.trim()) {
        renderValidationReport({
          total_rows: 0,
          valid_rows: 0,
          invalid_rows: 0,
          total_volume_inr: 0,
          is_acceptable_for_analysis: false,
          errors: ["CSV file is empty."]
        });
        return;
      }

      await runPreValidation(text, file);
    } catch (err) {
      console.error("[CustomAnalysis] Error reading file:", err);
      renderValidationReport({
        total_rows: 0,
        valid_rows: 0,
        invalid_rows: 0,
        total_volume_inr: 0,
        is_acceptable_for_analysis: false,
        errors: [`Failed to read file: ${err.message}`]
      });
    }
  }

  if (removeSelectedFileBtn) {
    removeSelectedFileBtn.addEventListener("click", () => {
      customUploadedFile = null;
      customValidatedCsvText = "";
      if (csvFileInput) csvFileInput.value = "";
      fileSelectedInfo.classList.add("hidden");
      validationSummaryCard.classList.add("hidden");
      if (analyzeTransactionsBtn) analyzeTransactionsBtn.disabled = true;
    });
  }

  // Load Demo Sample Button
  if (loadSampleCsvBtn) {
    loadSampleCsvBtn.addEventListener("click", async () => {
      try {
        const res = await fetch(`${API_BASE}/api/investigate/sample-csv`);
        const sampleText = await res.text();
        pasteCsvTextarea.value = sampleText;
        methodPasteTab.click();
        customValidatedCsvText = sampleText;
        customUploadedFile = null;
        selectedFileName.textContent = "jarvis_custom_demo.csv";
        selectedFileSize.textContent = `(${sampleText.length} bytes)`;
        fileSelectedInfo.classList.remove("hidden");
        await runPreValidation(sampleText, null);
      } catch (err) {
        console.error("[CustomAnalysis] Failed to load demo sample CSV:", err);
      }
    });
  }

  // Validate Pasted Button
  if (validatePastedBtn) {
    validatePastedBtn.addEventListener("click", async () => {
      const text = pasteCsvTextarea.value.trim();
      if (!text) {
        alert("Please paste CSV transaction records first.");
        return;
      }
      customValidatedCsvText = text;
      customUploadedFile = null;
      await runPreValidation(text, null);
    });
  }

  if (clearPastedBtn) {
    clearPastedBtn.addEventListener("click", () => {
      pasteCsvTextarea.value = "";
      customValidatedCsvText = "";
      customUploadedFile = null;
      fileSelectedInfo.classList.add("hidden");
      validationSummaryCard.classList.add("hidden");
      if (analyzeTransactionsBtn) analyzeTransactionsBtn.disabled = true;
    });
  }

  async function runPreValidation(csvText, fileObj = null) {
    validationSummaryCard.classList.remove("hidden");
    valStatusBadge.textContent = "VALIDATING...";
    valStatusBadge.className = "badge score-med";

    try {
      const payload = {
        csv_text: csvText,
        filename: fileObj ? fileObj.name : "custom_input.csv"
      };

      const res = await fetch(`${API_BASE}/api/investigate/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errText = await res.text();
        renderValidationReport({
          total_rows: 0,
          valid_rows: 0,
          invalid_rows: 0,
          total_volume_inr: 0,
          is_acceptable_for_analysis: false,
          errors: [`Validation service returned HTTP ${res.status}: ${errText}`]
        });
        return;
      }

      const report = await res.json();
      renderValidationReport(report);
    } catch (err) {
      console.error("[CustomAnalysis] Validation network error:", err);
      renderValidationReport({
        total_rows: 0,
        valid_rows: 0,
        invalid_rows: 0,
        total_volume_inr: 0,
        is_acceptable_for_analysis: false,
        errors: [`Network request failed: ${err.message}. Check that the backend server is running.`]
      });
    }
  }

  function renderValidationReport(report) {
    validationSummaryCard.classList.remove("hidden");
    valTotalRows.textContent = report.total_rows || 0;
    valValidRows.textContent = report.valid_rows || 0;
    valInvalidRows.textContent = report.invalid_rows || 0;
    valTotalVol.textContent = `₹${(report.total_volume_inr || 0).toLocaleString('en-IN')}`;

    if (report.is_acceptable_for_analysis) {
      valStatusBadge.textContent = "✓ VALID DATASET";
      valStatusBadge.className = "badge score-low";
      if (analyzeTransactionsBtn) analyzeTransactionsBtn.disabled = false;
    } else {
      valStatusBadge.textContent = "⚠ VALIDATION FAILED";
      valStatusBadge.className = "badge score-high";
      if (analyzeTransactionsBtn) analyzeTransactionsBtn.disabled = true;
    }

    if (report.warnings && report.warnings.length > 0) {
      valWarningsList.classList.remove("hidden");
      valWarningsList.innerHTML = `<b>Warnings:</b><br>${report.warnings.map(w => `• ${w}`).join("<br>")}`;
    } else {
      valWarningsList.classList.add("hidden");
    }

    if (report.errors && report.errors.length > 0) {
      valErrorsList.classList.remove("hidden");
      valErrorsList.innerHTML = `<b>Errors:</b><br>${report.errors.map(e => `• ${e}`).join("<br>")}`;
    } else {
      valErrorsList.classList.add("hidden");
    }
  }

  // Analyze Custom Transactions Button
  if (analyzeTransactionsBtn) {
    analyzeTransactionsBtn.addEventListener("click", async () => {
      if (!customValidatedCsvText || !customValidatedCsvText.trim()) {
        alert("Please provide valid transaction data before running analysis.");
        return;
      }
      analyzeTransactionsBtn.disabled = true;
      analyzeTransactionsBtn.textContent = "⚡ Running JARVIS-AML Pipeline...";

      try {
        const payload = {
          csv_text: customValidatedCsvText,
          dataset_name: selectedFileName.textContent || "Custom Investigation Dataset"
        };

        const res = await fetch(`${API_BASE}/api/investigate/custom`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        if (!res.ok) {
          const errorData = await res.json().catch(() => ({ message: res.statusText }));
          alert(`Analysis Failed: ${JSON.stringify(errorData)}`);
          analyzeTransactionsBtn.disabled = false;
          analyzeTransactionsBtn.textContent = "⚡ Run JARVIS-AML Complete Pipeline";
          return;
        }

        const newCaseData = await res.json();
        customAnalysisModal.classList.add("hidden");
        analyzeTransactionsBtn.disabled = false;
        analyzeTransactionsBtn.textContent = "⚡ Run JARVIS-AML Complete Pipeline";

        await loadScenariosList();
        scenarioSelect.value = newCaseData.scenario_id;
        await loadCase(newCaseData.scenario_id);
        activateTab("tab-overview");
      } catch (err) {
        console.error("[CustomAnalysis] Error running pipeline:", err);
        alert(`Error executing pipeline: ${err.message}. Check server logs.`);
        analyzeTransactionsBtn.disabled = false;
        analyzeTransactionsBtn.textContent = "⚡ Run JARVIS-AML Complete Pipeline";
      }
    });
  }

  // =========================================================================
  // Core Workstation Logic & Scenario Loading
  // =========================================================================

  async function loadScenariosList() {
    try {
      const res = await fetch(`${API_BASE}/api/scenarios`);
      allScenarios = await res.json();
      caseQueueList.innerHTML = "";
      if (casesTableBody) casesTableBody.innerHTML = "";

      scenarioSelect.innerHTML = "";
      allScenarios.forEach(sc => {
        const opt = document.createElement("option");
        opt.value = sc.scenario_id;
        opt.textContent = `${sc.scenario_id} — ${sc.title}`;
        scenarioSelect.appendChild(opt);
      });

      allScenarios.forEach(sc => {
        const isCustom = sc.is_custom || sc.scenario_id.startsWith("CUSTOM-");

        // 1. Sidebar Queue Item
        const item = document.createElement("div");
        item.className = `case-queue-item ${sc.scenario_id === "SCENARIO_G" ? "active" : ""}`;
        item.dataset.id = sc.scenario_id;
        item.innerHTML = `
          <div class="case-item-top">
            <span class="case-item-title">${sc.scenario_id}</span>
            <span class="badge ${isCustom ? "badge-accent" : (sc.difficulty === "HIGH" ? "score-high" : "badge-neutral")}">
              ${isCustom ? "CUSTOM" : sc.difficulty}
            </span>
          </div>
          <div class="case-item-desc">${sc.title}</div>
          <div class="case-item-meta">
            <span>₹${(sc.total_volume_inr / 100000).toFixed(1)}L Vol</span>
            <span>${sc.account_count} Accts</span>
          </div>
        `;
        item.addEventListener("click", () => {
          scenarioSelect.value = sc.scenario_id;
          loadCase(sc.scenario_id);
          activateTab("tab-overview");
        });
        caseQueueList.appendChild(item);

        // 2. Cases Repository Table Row (Tab 2)
        if (casesTableBody) {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td style="font-family:'JetBrains Mono', monospace; font-weight:700; color:#0284c7;">${sc.scenario_id}</td>
            <td style="font-weight:600; color:#0f172a;">${sc.title}</td>
            <td><span class="badge ${isCustom ? "badge-accent" : (sc.difficulty === "HIGH" ? "score-high" : "badge-neutral")}">${isCustom ? "CUSTOM" : sc.difficulty}</span></td>
            <td>₹${(sc.total_volume_inr || 0).toLocaleString('en-IN')}</td>
            <td>${sc.account_count || 0} Accounts</td>
            <td><span class="badge score-low">Active Case</span></td>
            <td><button class="btn btn-sm btn-primary load-case-btn" data-id="${sc.scenario_id}">⚡ Load Case</button></td>
          `;
          tr.querySelector(".load-case-btn").addEventListener("click", (e) => {
            e.stopPropagation();
            scenarioSelect.value = sc.scenario_id;
            loadCase(sc.scenario_id);
            activateTab("tab-overview");
          });
          tr.addEventListener("click", () => {
            scenarioSelect.value = sc.scenario_id;
            loadCase(sc.scenario_id);
            activateTab("tab-overview");
          });
          casesTableBody.appendChild(tr);
        }
      });

      document.getElementById("caseCountBadge").textContent = `${allScenarios.length} Cases`;
    } catch (err) {
      console.error("Failed to fetch scenarios:", err);
    }
  }

  // Load Single Scenario Case
  async function loadCase(scenarioId) {
    const statusText = document.getElementById("systemStatusText");
    if (statusText) statusText.textContent = "PROCESSING...";
    try {
      document.querySelectorAll(".case-queue-item").forEach(el => {
        el.classList.toggle("active", el.dataset.id === scenarioId);
      });

      const res = await fetch(`${API_BASE}/api/cases/${scenarioId}`);
      currentCaseData = await res.json();

      // 1. Update KPI Strip Metrics
      const meta = currentCaseData.metadata || {};
      const patterns = currentCaseData.patterns || [];
      const paths = currentCaseData.attack_paths || [];
      const priorityRankings = currentCaseData.priority_rankings || [];

      document.getElementById("metaVolume").textContent = `₹${(meta.total_volume_inr || 0).toLocaleString('en-IN')}`;
      document.getElementById("patternCountBadge").textContent = `${patterns.length} Clusters`;
      document.getElementById("pathCountBadge").textContent = `${paths.length} Paths`;
      document.getElementById("metaPriorityEntities").textContent = `${priorityRankings.length} Entities`;
      document.getElementById("metaTypology").textContent = meta.primary_typology || "MULTI_STAGE";
      
      const riskSub = document.getElementById("metaNetworkRiskSub");
      if (riskSub) {
        riskSub.textContent = priorityRankings.length > 3 ? "Critical triage required" : "Moderate network risk";
      }

      // 2. Render Main Analytics Chart
      analyticsChart.setData(currentCaseData);

      // 3. Render Pattern Distribution & Priority Table
      renderPatternDistribution(patterns);
      renderPriorityTable(priorityRankings, currentCaseData.roles);

      // 4. Render Graph & Timeline
      graphRenderer.setData(currentCaseData.graph, currentCaseData.roles);
      graphRenderer.resetView();
      timelineController.setStages(currentCaseData.temporal_stages);

      // 5. Render DNA View
      dnaViewer.renderDNA(currentCaseData.primary_dna, currentCaseData.similar_cases);

      // 6. Populate Detail Tabs
      populateOverviewTab(currentCaseData);
      populateAttackPathsTab(currentCaseData);
      populateStorylineTab(currentCaseData);
      populateEntitiesTab(currentCaseData);
      populateNetworkTab(currentCaseData);
      populatePatternsTab(currentCaseData);
      populateEvidenceTab(currentCaseData);
      populateNarrativeTab(currentCaseData);
      populateLeadsTab(currentCaseData);

      if (statusText) statusText.textContent = "ANALYSIS READY";
    } catch (err) {
      console.error("Failed to load scenario case:", err);
      if (statusText) statusText.textContent = "ERROR";
    }
  }

  scenarioSelect.addEventListener("change", (e) => {
    loadCase(e.target.value);
  });

  // Render Pattern Distribution Bars
  function renderPatternDistribution(patterns) {
    const container = document.getElementById("patternBarsContainer");
    if (!container) return;
    container.innerHTML = "";

    const standardPatterns = [
      { name: "Layering", class: "fill-layering" },
      { name: "Circular Transfer", class: "fill-circular" },
      { name: "Rapid Movement", class: "fill-rapid" },
      { name: "Fan-In", class: "fill-fanin" },
      { name: "Fan-Out", class: "fill-fanout" },
      { name: "Structuring", class: "fill-structuring" },
    ];

    const detectedMap = new Map();
    patterns.forEach(p => {
      const titleLower = p.title.toLowerCase();
      let matched = "Layering";
      if (titleLower.includes("circular") || titleLower.includes("round")) matched = "Circular Transfer";
      else if (titleLower.includes("rapid") || titleLower.includes("pass-through")) matched = "Rapid Movement";
      else if (titleLower.includes("fan-in") || titleLower.includes("aggregation")) matched = "Fan-In";
      else if (titleLower.includes("fan-out") || titleLower.includes("dispersion")) matched = "Fan-Out";
      else if (titleLower.includes("structur") || titleLower.includes("smurf")) matched = "Structuring";
      else if (titleLower.includes("layer")) matched = "Layering";
      
      const count = (detectedMap.get(matched) || 0) + 1;
      detectedMap.set(matched, count);
    });

    const maxCount = Math.max(...Array.from(detectedMap.values()), 1);

    standardPatterns.forEach(sp => {
      const count = detectedMap.get(sp.name) || 0;
      const pct = Math.round((count / maxCount) * 85) + (count > 0 ? 15 : 0);
      const isDetected = count > 0;

      const item = document.createElement("div");
      item.className = "pattern-bar-item";
      item.innerHTML = `
        <div class="pattern-bar-header">
          <span style="font-weight:600; color:${isDetected ? '#0f172a' : '#94a3b8'};">${sp.name}</span>
          <span>${count > 0 ? `${count} Detected` : "None"}</span>
        </div>
        <div class="pattern-bar-track">
          <div class="pattern-bar-fill ${sp.class}" style="width: ${count > 0 ? pct : 3}%; opacity: ${count > 0 ? 1 : 0.2};"></div>
        </div>
      `;
      container.appendChild(item);
    });
  }

  // Render Compact Investigation Priority Table
  function renderPriorityTable(priorityRankings, rolesData) {
    const tbody = document.getElementById("overviewPriorityTableBody");
    if (!tbody) return;
    tbody.innerHTML = "";

    if (!priorityRankings || !priorityRankings.length) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:#94a3b8; padding:16px;">No high priority entities flagged.</td></tr>`;
      return;
    }

    priorityRankings.slice(0, 5).forEach(item => {
      const tr = document.createElement("tr");
      const scoreClass = item.priority_score >= 80 ? "score-high" : (item.priority_score >= 50 ? "score-med" : "score-low");
      const role = item.probable_role || "UNKNOWN";
      const conf = Math.round((item.confidence || 0.85) * 100);
      const patternsStr = (item.why_factors && item.why_factors.length) ? item.why_factors[0].replace(/Detected |Suspected /i, '') : "Layering";

      tr.innerHTML = `
        <td class="account-id-text">${item.account_id}</td>
        <td><span class="badge ${scoreClass}">${role}</span></td>
        <td><b>${item.priority_score}</b>/100</td>
        <td>${conf}%</td>
        <td style="color:#64748b; font-size:0.72rem;">${patternsStr}</td>
      `;

      tr.addEventListener("click", () => inspectAccount(item.account_id));
      tbody.appendChild(tr);
    });
  }

  // Tab Population Functions
  function populateOverviewTab(data) {
    const brief = data.narrative_brief || {};
    const briefEl = document.getElementById("overviewBriefingText");
    if (briefEl) {
      briefEl.textContent = brief.executive_summary || "Investigation analysis completed for active scenario.";
    }

    const pList = document.getElementById("overviewPriorityList");
    if (!pList) return;
    pList.innerHTML = "";
    const rankings = data.priority_rankings || [];
    if (!rankings.length) {
      pList.innerHTML = "<p style='color:#64748b; font-size:0.75rem;'>No high-priority accounts identified.</p>";
      return;
    }

    rankings.slice(0, 5).forEach(item => {
      const scoreClass = item.priority_score >= 80 ? "score-high" : (item.priority_score >= 50 ? "score-med" : "score-low");
      const card = document.createElement("div");
      card.className = "priority-item";
      card.innerHTML = `
        <div class="priority-item-header">
          <span class="account-id-text">${item.account_id}</span>
          <span class="badge ${scoreClass}">${item.priority_score}/100</span>
        </div>
        <div style="font-size:0.72rem; color:#475569; margin-top:2px;">Role: <b>${item.probable_role}</b></div>
        <ul class="reasons-list">
          ${item.why_factors.map(f => `<li>${f}</li>`).join("")}
        </ul>
      `;
      card.addEventListener("click", () => inspectAccount(item.account_id));
      pList.appendChild(card);
    });
  }

  function populateAttackPathsTab(data) {
    const paths = data.attack_paths || [];
    const container = document.getElementById("attackPathsList");
    if (!container) return;
    container.innerHTML = "";

    if (!paths.length) {
      container.innerHTML = "<p style='color:#64748b; font-size:0.8rem;'>No high-risk linear paths detected in this dataset.</p>";
      return;
    }

    paths.forEach((p, idx) => {
      const card = document.createElement("div");
      card.className = "path-card";
      card.innerHTML = `
        <div class="path-card-header">
          <span style="font-weight:700; color:#0284c7; font-size:0.88rem;">#${idx+1} ${p.path_id}</span>
          <span class="badge ${p.retention_percentage > 85 ? "score-high" : "score-med"}">${p.retention_percentage}% Retained</span>
        </div>
        <div style="font-family:'JetBrains Mono', monospace; font-size:0.76rem; color:#0f172a; margin:6px 0; font-weight:600;">
          ${p.account_sequence.map(a => a.replace("ACC_", "")).join(" → ")}
        </div>
        <div style="display:flex; justify-content:space-between; font-size:0.74rem; color:#64748b; margin-top:4px;">
          <span>Initial: ₹${p.total_inflow_inr.toLocaleString('en-IN')}</span>
          <span>Final: ₹${p.total_outflow_inr.toLocaleString('en-IN')}</span>
          <span>Transit Time: ${p.elapsed_minutes}m</span>
          <span>Hops: ${p.account_sequence.length}</span>
        </div>
      `;
      card.addEventListener("click", () => {
        graphRenderer.highlightAttackPath(p.account_sequence);
        activateTab("tab-overview");
      });
      container.appendChild(card);
    });
  }

  function populateStorylineTab(data) {
    const container = document.getElementById("chronologicalStorylineList");
    if (!container) return;
    container.innerHTML = "";
    const storyline = data.chronological_storyline || [];
    if (!storyline.length) {
      container.innerHTML = "<p style='color:#64748b; font-size:0.8rem;'>No chronological events recorded.</p>";
      return;
    }

    storyline.forEach(step => {
      const item = document.createElement("div");
      item.className = "storyline-step-item";
      item.innerHTML = `
        <div class="storyline-time">Step ${step.step_index} • ${step.timestamp.replace("T", " ")}</div>
        <div class="storyline-text">${step.narrative}</div>
      `;
      container.appendChild(item);
    });
  }

  function populateEntitiesTab(data) {
    const tbody = document.getElementById("entitiesRoleList");
    if (!tbody) return;
    tbody.innerHTML = "";
    Object.values(data.roles || {}).forEach(r => {
      const tr = document.createElement("tr");
      const role = r.probable_role || "UNKNOWN";
      let roleClass = "score-low";
      if (role === "MULE" || role === "DISPERSER" || role === "ORIGINATOR") roleClass = "score-high";
      else if (role === "AGGREGATOR" || role === "SINK") roleClass = "score-med";

      const priority = r.risk_score || (roleClass === "score-high" ? 88 : 55);

      tr.innerHTML = `
        <td class="account-id-text" style="cursor:pointer; font-weight:700;">${r.account_id}</td>
        <td><span class="badge ${roleClass}">${role}</span></td>
        <td>${Math.round((r.confidence || 0) * 100)}%</td>
        <td><b>${priority}</b>/100</td>
        <td>₹${(r.inflow_total_inr || 0).toLocaleString('en-IN')}</td>
        <td>₹${(r.outflow_total_inr || 0).toLocaleString('en-IN')}</td>
        <td>${Math.round((r.forwarding_ratio || 0) * 100)}%</td>
        <td>${Math.round(r.avg_dwell_time_minutes || 0)}m</td>
        <td><button class="btn btn-sm btn-secondary inspect-btn" data-acc="${r.account_id}">🔍 Inspect</button></td>
      `;

      tr.querySelector(".inspect-btn").addEventListener("click", (e) => {
        e.stopPropagation();
        inspectAccount(r.account_id);
      });
      tr.addEventListener("click", () => inspectAccount(r.account_id));
      tbody.appendChild(tr);
    });
  }

  function populateNetworkTab(data) {
    const container = document.getElementById("communitiesList");
    if (!container) return;
    container.innerHTML = "";
    (data.communities || []).forEach(comm => {
      const item = document.createElement("div");
      item.className = "community-card";
      item.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <span style="font-weight:700; color:#0284c7; font-size:0.88rem;">Community Subgraph ${comm.community_id}</span>
          <span class="badge badge-accent">${comm.size} Members</span>
        </div>
        <div style="font-size:0.75rem; color:#475569; margin:6px 0;">
          Internal Volume: <b style="color:#0f172a;">₹${(comm.internal_volume_inr || 0).toLocaleString('en-IN')}</b> | Density: ${comm.density}
        </div>
        <div style="font-family:'JetBrains Mono', monospace; font-size:0.72rem; color:#0f172a; background:#f1f5f9; padding:6px; border-radius:4px;">
          ${comm.members.join(", ")}
        </div>
      `;
      container.appendChild(item);
    });
  }

  function populatePatternsTab(data) {
    const container = document.getElementById("detectedPatternsList");
    if (!container) return;
    container.innerHTML = "";
    const patterns = data.patterns || [];
    if (!patterns.length) {
      container.innerHTML = "<p style='color:#64748b; font-size:0.85rem;'>No suspicious AML typologies detected.</p>";
      return;
    }

    patterns.forEach(p => {
      const card = document.createElement("div");
      card.className = "pattern-card";
      card.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <span style="font-weight:700; color:#0f172a; font-size:0.88rem;">${p.title}</span>
          <span class="badge ${p.severity === "CRITICAL" ? "score-high" : (p.severity === "HIGH" ? "score-med" : "badge-accent")}">${p.severity}</span>
        </div>
        <div style="font-size:0.78rem; color:#475569; line-height:1.4; margin:6px 0;">${p.description}</div>
        <div style="font-size:0.72rem; color:#64748b; font-family:'JetBrains Mono', monospace;">
          Involved Accounts: ${p.accounts_involved.join(", ")}
        </div>
      `;
      container.appendChild(card);
    });
  }

  function populateEvidenceTab(data) {
    const container = document.getElementById("evidenceChainList");
    if (!container) return;
    container.innerHTML = "";
    const allEvidence = [];
    (data.patterns || []).forEach(p => {
      (p.evidence || []).forEach(e => allEvidence.push(e));
    });

    if (!allEvidence.length) {
      container.innerHTML = "<p style='color:#64748b; font-size:0.85rem;'>No evidence items generated.</p>";
      return;
    }

    allEvidence.forEach(ev => {
      const card = document.createElement("div");
      card.className = "pattern-card";
      card.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <span style="font-weight:700; color:#0284c7; font-size:0.88rem;">${ev.evidence_id}: ${ev.finding_title}</span>
          <span class="badge badge-neutral">Forensic Audit</span>
        </div>
        <div style="font-size:0.78rem; color:#475569; margin:6px 0; line-height:1.4;">${ev.narrative_explanation}</div>
        <div style="display:flex; flex-wrap:wrap; gap:6px; margin-top:6px;">
          ${ev.transaction_ids.map(tx => `<span style="background:#f1f5f9; border:1px solid #e2e8f0; padding:3px 8px; border-radius:4px; font-family:'JetBrains Mono', monospace; font-size:0.72rem; color:#0f766e;">${tx}</span>`).join("")}
        </div>
      `;
      container.appendChild(card);
    });
  }

  function populateNarrativeTab(data) {
    const container = document.getElementById("fullNarrativeView");
    if (!container) return;
    const brief = data.narrative_brief || {};
    container.innerHTML = `
      <div style="font-size:0.85rem; color:#0f172a; line-height:1.6;">
        <h4 style="color:#0284c7; font-size:1.05rem; margin-bottom:10px;">${brief.title || "Intelligence Dossier Briefing"}</h4>
        <p style="margin-bottom:14px;">${brief.executive_summary || "Dossier details ready."}</p>
        
        <div style="margin-top:16px; border-top:1px solid #e2e8f0; padding-top:12px;">
          <h5 style="color:#0f172a; font-size:0.85rem; margin-bottom:8px;">Core Evidence Parameters:</h5>
          <ul style="padding-left:20px; color:#475569; font-size:0.8rem; line-height:1.5;">
            <li><b>Monitored Entities:</b> ${brief.key_metrics ? brief.key_metrics.total_monitored_accounts : "N/A"}</li>
            <li><b>Cumulative Transaction Volume:</b> ₹${brief.key_metrics ? (brief.key_metrics.total_volume_inr || 0).toLocaleString('en-IN') : "N/A"}</li>
            <li><b>Money Trail DNA:</b> <span style="color:#0284c7; font-family:'JetBrains Mono', monospace;">${brief.key_metrics ? brief.key_metrics.dna_fingerprint : "N/A"}</span></li>
          </ul>
        </div>
      </div>
    `;
  }

  function populateLeadsTab(data) {
    const container = document.getElementById("actionableLeadsList");
    if (!container) return;
    container.innerHTML = "";
    const leads = (data.narrative_brief && data.narrative_brief.investigative_leads) || [];
    if (!leads.length) {
      container.innerHTML = "<p style='color:#64748b; font-size:0.85rem;'>No active investigative leads for this dataset.</p>";
      return;
    }

    leads.forEach(lead => {
      const li = document.createElement("li");
      li.textContent = lead;
      container.appendChild(li);
    });
  }

  // 2-Hop Counterfactual Tracing for Selected Account
  async function inspectAccount(accountId) {
    if (!currentCaseData) return;
    try {
      const targetNode = graphRenderer.nodes.find(n => n.id === accountId);
      if (targetNode) {
        graphRenderer.selectedNode = targetNode;
      }

      const res = await fetch(`${API_BASE}/api/trace/${currentCaseData.scenario_id}/${accountId}?depth=2`);
      const trace = await res.json();
      const nodesToHighlight = (trace.neighborhood_2hop && trace.neighborhood_2hop.nodes) || [accountId];
      graphRenderer.highlight2Hop(accountId, nodesToHighlight);

      const drawer = document.getElementById("accountInspectorDrawer");
      const title = document.getElementById("drawerAccountTitle");
      const body = document.getElementById("drawerBodyContent");
      
      if (drawer && title && body) {
        title.textContent = accountId;
        const roleData = (currentCaseData.roles && currentCaseData.roles[accountId]) || {};
        const role = roleData.probable_role || "UNKNOWN";
        const conf = Math.round((roleData.confidence || 0) * 100);
        const inflow = (roleData.inflow_total_inr || 0).toLocaleString('en-IN');
        const outflow = (roleData.outflow_total_inr || 0).toLocaleString('en-IN');
        const fwd = Math.round((roleData.forwarding_ratio || 0) * 100);
        const dwell = Math.round(roleData.avg_dwell_time_minutes || 0);

        body.innerHTML = `
          <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:14px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <span style="font-size:0.75rem; color:#64748b; font-weight:700;">INFERRED ROLE</span>
              <span class="badge score-high">${role} (${conf}%)</span>
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:10px; font-size:0.75rem;">
              <div>Inflow: <b style="color:#0f172a;">₹${inflow}</b></div>
              <div>Outflow: <b style="color:#0f172a;">₹${outflow}</b></div>
              <div>Forwarding: <b style="color:#0284c7;">${fwd}%</b></div>
              <div>Dwell Time: <b style="color:#0f766e;">${dwell}m</b></div>
            </div>
          </div>

          <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:14px;">
            <div style="font-size:0.75rem; font-weight:700; color:#64748b; margin-bottom:6px;">2-HOP CONNECTED NEIGHBORS (${nodesToHighlight.length})</div>
            <div style="font-family:'JetBrains Mono', monospace; font-size:0.72rem; color:#0284c7; display:flex; flex-wrap:wrap; gap:4px;">
              ${nodesToHighlight.map(n => `<span style="background:#ffffff; border:1px solid #cbd5e1; padding:2px 6px; border-radius:4px;">${n}</span>`).join("")}
            </div>
          </div>

          <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:14px;">
            <div style="font-size:0.75rem; font-weight:700; color:#64748b; margin-bottom:6px;">OBSERVABLE EVIDENCE SIGNALS</div>
            <ul style="padding-left:16px; font-size:0.74rem; color:#475569; line-height:1.4;">
              ${(roleData.evidence_signals || ["No anomalous alert signals."]).map(s => `<li>${s}</li>`).join("")}
            </ul>
          </div>
        `;
        drawer.classList.remove("hidden");
      }
    } catch (err) {
      console.error("Failed to trace account:", err);
    }
  }

  // Initial Load
  loadScenariosList().then(() => {
    loadCase("SCENARIO_G");
  });
});

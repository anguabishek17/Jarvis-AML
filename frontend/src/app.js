/**
 * JARVIS-AML Master Application Controller
 * Connects FastAPI Backend, Graph Canvas, Timeline, DNA Viewer, Analytics Charts,
 * 11 Investigation Tabs, Case Repository, and Dynamic Custom Transaction Ingestion.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Support custom environment configuration (e.g. Vercel deployment with Render backend)
  const configuredApiBase = window.__API_BASE_URL__ || 
    (typeof process !== "undefined" && process.env && process.env.VITE_API_BASE_URL) ||
    (typeof window !== "undefined" && window.VITE_API_BASE_URL);

  let API_BASE = configuredApiBase;
  if (!API_BASE) {
    if (window.location && window.location.origin && window.location.origin.startsWith("http")) {
      // If served by live-server or local static server on a different port (e.g. 5500, 3000, 5173), default to backend 8089
      if (window.location.port && ["5500", "5173", "3000", "8080"].includes(window.location.port)) {
        API_BASE = "http://127.0.0.1:8089";
      } else {
        API_BASE = window.location.origin;
      }
    } else {
      API_BASE = "http://127.0.0.1:8089";
    }
  }

  // Update Settings modal input if present
  const settingsInput = document.getElementById("settingsApiUrl");
  if (settingsInput) {
    settingsInput.value = API_BASE;
  }


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
  // Investigation Simulator Controller (What-If Disruption Analysis)
  // =========================================================================
  const simulatorModal = document.getElementById("simulatorModal");
  const openSimulatorBtn = document.getElementById("openSimulatorBtn");
  const sidebarSimulatorBtn = document.getElementById("sidebarSimulatorBtn");
  const graphSimulatorBtn = document.getElementById("graphSimulatorBtn");
  const closeSimulatorModalBtn = document.getElementById("closeSimulatorModalBtn");
  const simTypeAccountBtn = document.getElementById("simTypeAccountBtn");
  const simTypeTxnBtn = document.getElementById("simTypeTxnBtn");
  const simTargetLabel = document.getElementById("simTargetLabel");
  const simTargetSelect = document.getElementById("simTargetSelect");
  const simDirectionSelect = document.getElementById("simDirectionSelect");
  const runSimulationBtn = document.getElementById("runSimulationBtn");
  const simEmptyState = document.getElementById("simEmptyState");
  const simResultsContainer = document.getElementById("simResultsContainer");
  const simHighlightOnGraphBtn = document.getElementById("simHighlightOnGraphBtn");
  const simResetViewBtn = document.getElementById("simResetViewBtn");

  let simCurrentTargetType = "account";
  let simCachedTargets = null;
  let lastSimulationResult = null;

  async function fetchSimulationTargets(scenarioId) {
    if (!scenarioId) return null;
    try {
      console.log("[Simulator] Fetching targets for scenario:", scenarioId);
      const res = await fetch(`${API_BASE}/api/simulate/${scenarioId}/targets`);
      if (!res.ok) {
        console.error("[Simulator] Targets endpoint returned status:", res.status);
        simCachedTargets = null;
        return null;
      }
      simCachedTargets = await res.json();
      console.log("[Simulator] Targets received:", simCachedTargets);
      return simCachedTargets;
    } catch (err) {
      console.error("[Simulator] Error fetching targets:", err);
      simCachedTargets = null;
      return null;
    }
  }

  function populateSimulationTargetsDropdown(selectedTargetId = null) {
    if (!simTargetSelect) return;
    simTargetSelect.innerHTML = "";

    if (!simCachedTargets) {
      const opt = document.createElement("option");
      opt.value = "";
      opt.textContent = "Unable to load investigation targets (API Error).";
      simTargetSelect.appendChild(opt);
      if (runSimulationBtn) runSimulationBtn.disabled = true;
      return;
    }

    if (simCurrentTargetType === "account") {
      if (simTargetLabel) simTargetLabel.textContent = "SELECT TARGET ACCOUNT";
      const accounts = simCachedTargets.accounts || [];

      if (accounts.length === 0) {
        const opt = document.createElement("option");
        opt.value = "";
        opt.textContent = "No accounts available for this investigation.";
        simTargetSelect.appendChild(opt);
        if (runSimulationBtn) runSimulationBtn.disabled = true;
        return;
      }

      // Default placeholder option
      const defaultOpt = document.createElement("option");
      defaultOpt.value = "";
      defaultOpt.textContent = "Select an account...";
      defaultOpt.disabled = true;
      if (!selectedTargetId) defaultOpt.selected = true;
      simTargetSelect.appendChild(defaultOpt);

      accounts.forEach(acc => {
        const opt = document.createElement("option");
        const accId = acc.account_id || acc.id || "UNKNOWN";
        const role = acc.probable_role || acc.role || "UNKNOWN";
        const inflow = typeof acc.inflow_total_inr === "number" ? acc.inflow_total_inr : (acc.inflow || 0);
        const outflow = typeof acc.outflow_total_inr === "number" ? acc.outflow_total_inr : (acc.outflow || 0);
        const vol = (inflow + outflow).toLocaleString('en-IN');
        
        opt.value = accId;
        opt.textContent = `${accId} [${role}] — ₹${vol}`;
        
        if (selectedTargetId && accId === selectedTargetId) {
          opt.selected = true;
          defaultOpt.selected = false;
        }
        simTargetSelect.appendChild(opt);
      });
    } else {
      if (simTargetLabel) simTargetLabel.textContent = "SELECT TARGET TRANSACTION";
      const txns = simCachedTargets.transactions || [];

      if (txns.length === 0) {
        const opt = document.createElement("option");
        opt.value = "";
        opt.textContent = "No transactions available for this investigation.";
        simTargetSelect.appendChild(opt);
        if (runSimulationBtn) runSimulationBtn.disabled = true;
        return;
      }

      // Default placeholder option
      const defaultOpt = document.createElement("option");
      defaultOpt.value = "";
      defaultOpt.textContent = "Select a transaction...";
      defaultOpt.disabled = true;
      if (!selectedTargetId) defaultOpt.selected = true;
      simTargetSelect.appendChild(defaultOpt);

      txns.forEach(tx => {
        const opt = document.createElement("option");
        const txId = tx.transaction_id || tx.id || "TXN";
        const sender = tx.sender_account || tx.sender || "UNKNOWN";
        const receiver = tx.receiver_account || tx.receiver || "UNKNOWN";
        const amt = (tx.amount || 0).toLocaleString('en-IN');
        
        opt.value = txId;
        opt.textContent = `${txId}: ${sender} → ${receiver} (₹${amt})`;
        
        if (selectedTargetId && txId === selectedTargetId) {
          opt.selected = true;
          defaultOpt.selected = false;
        }
        simTargetSelect.appendChild(opt);
      });
    }

    updateSimButtonState();
  }

  function updateSimButtonState() {
    if (runSimulationBtn && simTargetSelect) {
      runSimulationBtn.disabled = !simTargetSelect.value || simTargetSelect.value === "";
    }
  }

  if (simTargetSelect) {
    simTargetSelect.addEventListener("change", updateSimButtonState);
  }

  async function openSimulatorWithTarget(targetType = "account", targetId = null) {
    const activeScenarioId = currentCaseData ? currentCaseData.scenario_id : (scenarioSelect ? scenarioSelect.value : "SCENARIO_G");
    simCurrentTargetType = targetType;

    if (simTypeAccountBtn && simTypeTxnBtn) {
      simTypeAccountBtn.classList.toggle("active", targetType === "account");
      simTypeTxnBtn.classList.toggle("active", targetType === "transaction");
    }

    if (simulatorModal) {
      simulatorModal.classList.remove("hidden");
    }

    // Always fetch fresh targets for the active case to ensure no stale data
    await fetchSimulationTargets(activeScenarioId);
    populateSimulationTargetsDropdown(targetId);

    if (targetId && simTargetSelect && simTargetSelect.value === targetId) {
      runSimulation();
    }
  }

  if (simTypeAccountBtn) {
    simTypeAccountBtn.addEventListener("click", () => {
      simCurrentTargetType = "account";
      simTypeAccountBtn.classList.add("active");
      simTypeTxnBtn.classList.remove("active");
      populateSimulationTargetsDropdown();
    });
  }

  if (simTypeTxnBtn) {
    simTypeTxnBtn.addEventListener("click", () => {
      simCurrentTargetType = "transaction";
      simTypeTxnBtn.classList.add("active");
      simTypeAccountBtn.classList.remove("active");
      populateSimulationTargetsDropdown();
    });
  }

  if (openSimulatorBtn) openSimulatorBtn.addEventListener("click", () => openSimulatorWithTarget("account"));
  if (sidebarSimulatorBtn) sidebarSimulatorBtn.addEventListener("click", () => openSimulatorWithTarget("account"));
  if (graphSimulatorBtn) graphSimulatorBtn.addEventListener("click", () => {
    const selected = graphRenderer.selectedNode ? graphRenderer.selectedNode.id : null;
    openSimulatorWithTarget("account", selected);
  });

  if (closeSimulatorModalBtn) {
    closeSimulatorModalBtn.addEventListener("click", () => {
      if (simulatorModal) simulatorModal.classList.add("hidden");
    });
  }

  if (simResetViewBtn) {
    simResetViewBtn.addEventListener("click", () => {
      if (simulatorModal) simulatorModal.classList.add("hidden");
    });
  }

  async function runSimulation() {
    const activeScenarioId = currentCaseData ? currentCaseData.scenario_id : (scenarioSelect ? scenarioSelect.value : "SCENARIO_G");
    if (!simTargetSelect || !simTargetSelect.value) return;
    
    runSimulationBtn.disabled = true;
    runSimulationBtn.textContent = "⚡ SIMULATING DISRUPTION...";

    try {
      const payload = {
        target_type: simCurrentTargetType,
        target_id: simTargetSelect.value,
        direction: simDirectionSelect ? simDirectionSelect.value : "both"
      };

      const res = await fetch(`${API_BASE}/api/simulate/${activeScenarioId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({ message: res.statusText }));
        alert(`Simulation Failed: ${JSON.stringify(errData)}`);
        runSimulationBtn.disabled = false;
        runSimulationBtn.textContent = "⚡ RUN SIMULATION";
        return;
      }

      const simData = await res.json();
      lastSimulationResult = simData;
      renderSimulationResults(simData);

      runSimulationBtn.disabled = false;
      runSimulationBtn.textContent = "⚡ RUN SIMULATION";
    } catch (err) {
      console.error("[Simulator] Execution error:", err);
      alert(`Simulation Error: ${err.message}`);
      runSimulationBtn.disabled = false;
      runSimulationBtn.textContent = "⚡ RUN SIMULATION";
    }
  }

  if (runSimulationBtn) {
    runSimulationBtn.addEventListener("click", runSimulation);
  }

  function renderSimulationResults(sim) {
    if (simEmptyState) simEmptyState.classList.add("hidden");
    if (simResultsContainer) simResultsContainer.classList.remove("hidden");

    // Robust extraction supporting comparison block
    const comp = sim.comparison || {};
    const before = sim.before || {};
    const after = sim.after || {};
    const impact = sim.impact || {};

    // 1. Comparison KPIs
    const bPaths = comp.attack_paths ? comp.attack_paths.before : ((before.attack_paths || []).length);
    const aPaths = comp.attack_paths ? comp.attack_paths.after : ((after.attack_paths || []).length);
    const pathImpact = sim.path_impact || impact.affected_paths || [];
    const brokenCount = pathImpact.filter(p => p.status === "BROKEN" || p.status === "SEVERED").length;

    document.getElementById("simBeforePaths").textContent = bPaths;
    document.getElementById("simAfterPaths").textContent = aPaths;
    document.getElementById("simDiffPathsText").textContent = brokenCount > 0 ? `-${brokenCount} broken` : "0 broken";

    const bNodes = comp.suspicious_nodes ? comp.suspicious_nodes.before : (before.metrics ? before.metrics.total_accounts : 0);
    const aNodes = comp.suspicious_nodes ? comp.suspicious_nodes.after : (after.metrics ? after.metrics.total_accounts : 0);
    document.getElementById("simBeforeNodes").textContent = bNodes;
    document.getElementById("simAfterNodes").textContent = aNodes;
    const diffNodes = bNodes - aNodes;
    document.getElementById("simDiffNodesText").textContent = diffNodes > 0 ? `-${diffNodes} nodes` : "0 diff";

    const bVol = comp.total_volume_inr ? comp.total_volume_inr.before : (before.metrics ? before.metrics.total_volume_inr : 0);
    const aVol = comp.total_volume_inr ? comp.total_volume_inr.after : (after.metrics ? after.metrics.total_volume_inr : 0);
    document.getElementById("simBeforeVol").textContent = `₹${(bVol / 100000).toFixed(1)}L`;
    document.getElementById("simAfterVol").textContent = `₹${(aVol / 100000).toFixed(1)}L`;
    const volDiff = bVol - aVol;
    document.getElementById("simDiffVolText").textContent = volDiff > 0 ? `-₹${(volDiff / 100000).toFixed(1)}L` : "₹0";

    const bHops = comp.max_hop_depth ? comp.max_hop_depth.before : (before.metrics ? before.metrics.max_hop_depth : 0);
    const aHops = comp.max_hop_depth ? comp.max_hop_depth.after : (after.metrics ? after.metrics.max_hop_depth : 0);
    document.getElementById("simBeforeHops").textContent = bHops;
    document.getElementById("simAfterHops").textContent = aHops;
    document.getElementById("simDiffHopsText").textContent = aHops < bHops ? `Reduced by ${bHops - aHops}` : "Unchanged";

    const bRet = comp.max_retention_pct ? Math.round(comp.max_retention_pct.before) : Math.round((before.metrics ? before.metrics.flow_retention_ratio : 0) * 100);
    const aRet = comp.max_retention_pct ? Math.round(comp.max_retention_pct.after) : Math.round((after.metrics ? after.metrics.flow_retention_ratio : 0) * 100);
    document.getElementById("simBeforeRet").textContent = `${bRet}%`;
    document.getElementById("simAfterRet").textContent = `${aRet}%`;
    document.getElementById("simDiffRetText").textContent = `${aRet - bRet}% delta`;

    const bPrio = comp.case_priority_score ? Math.round(comp.case_priority_score.before) : Math.round(before.priority || 0);
    const aPrio = comp.case_priority_score ? Math.round(comp.case_priority_score.after) : Math.round(after.priority || 0);
    document.getElementById("simBeforePriority").textContent = bPrio;
    document.getElementById("simAfterPriority").textContent = aPrio;
    const prioDiff = aPrio - bPrio;
    document.getElementById("simDiffPriorityText").textContent = prioDiff < 0 ? `${prioDiff} pts` : `+${prioDiff} pts`;

    // 2. Money Trail DNA Shift
    const dnaImpact = sim.dna_impact || {};
    const bDnaSig = comp.primary_dna_signature ? comp.primary_dna_signature.before : (dnaImpact.signature_before || (before.dna ? before.dna.signature : "N/A"));
    const aDnaSig = comp.primary_dna_signature ? comp.primary_dna_signature.after : (dnaImpact.signature_after || (after.dna ? after.dna.signature : "N/A"));
    document.getElementById("simOriginalDnaSig").textContent = bDnaSig || "N/A";
    document.getElementById("simSimulatedDnaSig").textContent = aDnaSig || "N/A";

    const genesCompContainer = document.getElementById("simDnaGenesComparison");
    if (genesCompContainer) {
      genesCompContainer.innerHTML = "";
      const dnaDiffs = (dnaImpact.genes) || impact.dna_comparison || {};
      const geneKeys = ["typology", "velocity", "dispersion", "retention", "channel", "topology", "role_sequence"];

      geneKeys.forEach(gk => {
        const geneInfo = dnaDiffs[gk] || { before: "N/A", after: "N/A", changed: false };
        const card = document.createElement("div");
        card.className = `sim-gene-card ${geneInfo.changed ? "mutated" : ""}`;
        card.innerHTML = `
          <div class="sim-gene-name">${gk.replace('_', ' ')}</div>
          <div class="sim-gene-diff">
            <span style="color:#64748b;">${geneInfo.before}</span>
            <span style="color:#0284c7;">→</span>
            <b style="color:${geneInfo.changed ? '#b45309' : '#0f172a'};">${geneInfo.after}</b>
          </div>
        `;
        genesCompContainer.appendChild(card);
      });
    }

    // 3. Attack Paths Impact List
    const pathsList = document.getElementById("simAttackPathsList");
    const brokenBadge = document.getElementById("simBrokenPathsCountBadge");
    if (pathsList) {
      pathsList.innerHTML = "";
      const pathComparisons = sim.path_impact || impact.affected_paths || [];
      if (brokenBadge) brokenBadge.textContent = `${brokenCount} Broken`;

      if (pathComparisons.length === 0) {
        pathsList.innerHTML = `<div style="font-size:0.75rem; color:#64748b; padding:4px;">No attack paths disrupted by this removal.</div>`;
      } else {
        pathComparisons.forEach(p => {
          const isBroken = p.status === "BROKEN" || p.status === "SEVERED";
          const row = document.createElement("div");
          row.className = `sim-item-row ${isBroken ? "broken" : ""}`;
          const nodesStr = Array.isArray(p.nodes) ? p.nodes.join(" ➔ ") : (p.path_sequence ? p.path_sequence.join(" ➔ ") : (p.account_sequence ? p.account_sequence.join(" ➔ ") : ""));
          row.innerHTML = `
            <div>
              <b style="color:${isBroken ? '#b91c1c' : '#0284c7'};">${p.path_id}</b>: ${nodesStr}
              <div style="font-size:0.68rem; color:${isBroken ? '#7f1d1d' : '#64748b'}; margin-top:2px;">${p.reason || p.status}</div>
            </div>
            <span class="badge ${isBroken ? 'score-high' : 'score-low'}">${p.status || 'ACTIVE'}</span>
          `;
          pathsList.appendChild(row);
        });
      }
    }

    // 4. Pattern Disruption List
    const patternsList = document.getElementById("simPatternsImpactList");
    if (patternsList) {
      patternsList.innerHTML = "";
      const patImpact = sim.pattern_impact || impact.affected_patterns || {};
      const removedPats = patImpact.removed || [];
      const persistedPats = patImpact.persisted || [];
      const newPats = patImpact.newly_detected || [];

      if (removedPats.length === 0 && persistedPats.length === 0 && newPats.length === 0) {
        patternsList.innerHTML = `<div style="font-size:0.75rem; color:#64748b; padding:4px;">No pattern changes detected.</div>`;
      } else {
        removedPats.forEach(p => {
          const row = document.createElement("div");
          row.className = "sim-item-row removed";
          row.innerHTML = `<span><b>${p.pattern_type || p.title}</b></span> <span class="badge score-high">REMOVED</span>`;
          patternsList.appendChild(row);
        });
        persistedPats.forEach(p => {
          const row = document.createElement("div");
          row.className = "sim-item-row persisted";
          row.innerHTML = `<span><b>${p.pattern_type || p.title}</b></span> <span class="badge score-low">PERSISTED</span>`;
          patternsList.appendChild(row);
        });
        newPats.forEach(p => {
          const row = document.createElement("div");
          row.className = "sim-item-row new";
          row.innerHTML = `<span><b>${p.pattern_type || p.title}</b></span> <span class="badge badge-accent">NEW DETECTED</span>`;
          patternsList.appendChild(row);
        });
      }
    }

    // 5. Role Shifts List
    const roleList = document.getElementById("simRoleShiftsList");
    if (roleList) {
      roleList.innerHTML = "";
      const roleShifts = sim.role_impact || impact.role_shifts || [];
      if (roleShifts.length === 0) {
        roleList.innerHTML = `<div style="font-size:0.75rem; color:#64748b; padding:4px;">No downstream role re-assignments occurred.</div>`;
      } else {
        roleShifts.forEach(r => {
          const row = document.createElement("div");
          row.className = "sim-item-row";
          const rBefore = r.role_before || r.original_role || "UNKNOWN";
          const rAfter = r.role_after || r.simulated_role || "UNKNOWN";
          const confB = Math.round((r.confidence_before || r.original_confidence || 0) * 100);
          const confA = Math.round((r.confidence_after || r.simulated_confidence || 0) * 100);
          row.innerHTML = `
            <div>
              <b>${r.account_id}</b>
              <div style="font-size:0.68rem; color:#64748b;">${rBefore} (${confB}%) ➔ ${rAfter} (${confA}%)</div>
            </div>
            <span class="badge score-low">Role Shift</span>
          `;
          roleList.appendChild(row);
        });
      }
    }

    // 6. Temporal Storyline List
    const timelineList = document.getElementById("simTemporalStorylineList");
    if (timelineList) {
      timelineList.innerHTML = "";
      const tempStages = sim.temporal_impact || (impact.temporal_impact ? impact.temporal_impact.simulated_stages : []) || [];
      if (tempStages.length === 0) {
        timelineList.innerHTML = `<div style="font-size:0.75rem; color:#64748b; padding:4px;">No temporal stage changes.</div>`;
      } else {
        tempStages.forEach(s => {
          const row = document.createElement("div");
          row.className = "sim-item-row";
          row.innerHTML = `
            <div>
              <b style="color:#0284c7;">${s.stage_name}</b>
              <div style="font-size:0.68rem; color:#64748b;">${s.status || ''} (Risk Score: ${s.after_risk_score ?? s.stage_risk_score ?? 0})</div>
            </div>
            <span class="badge ${s.status === 'DISRUPTED' ? 'score-high' : 'score-low'}">${s.status || 'ACTIVE'}</span>
          `;
          timelineList.appendChild(row);
        });
      }
    }

    // 7. "Why This Matters" Forensic Explanation
    const whyMatters = document.getElementById("simWhyMattersText");
    if (whyMatters) {
      whyMatters.textContent = sim.why_this_matters || impact.why_this_matters || "Mathematical topology comparison shows the removal of this entity or transaction changes the network structure and behavioural risk signature.";
    }
  }

  // Highlight Simulation on Cytoscape / Canvas Graph
  if (simHighlightOnGraphBtn) {
    simHighlightOnGraphBtn.addEventListener("click", () => {
      if (!lastSimulationResult) return;
      simulatorModal.classList.add("hidden");
      graphRenderer.setSimulationMode(lastSimulationResult);
      activateTab("tab-overview");
    });
  }

  // Tab Manager Action Listeners for Simulator
  document.querySelectorAll("[data-action='open-simulator']").forEach(btn => {
    btn.addEventListener("click", () => openSimulatorWithTarget("account"));
  });

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

      // 7. Sync Copilot Active Context
      const copilotCtxLabel = document.getElementById("copilotCaseContextLabel");
      if (copilotCtxLabel) {
        copilotCtxLabel.textContent = `Context: ${scenarioId}`;
      }
      resetCopilotChatStream(scenarioId);

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
          <div style="margin-bottom:12px;">
            <button id="drawerSimulateWhatIfBtn" class="btn btn-primary" style="width:100%; font-weight:700; font-size:0.8rem; padding:8px 12px; background:linear-gradient(135deg, #0284c7 0%, #0369a1 100%);">
              🔬 SIMULATE WHAT-IF REMOVAL
            </button>
          </div>

          <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:14px; margin-bottom:12px;">
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

          <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:14px; margin-bottom:12px;">
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

        const drawerSimBtn = document.getElementById("drawerSimulateWhatIfBtn");
        if (drawerSimBtn) {
          drawerSimBtn.addEventListener("click", () => {
            drawer.classList.add("hidden");
            openSimulatorWithTarget("account", accountId);
          });
        }

        drawer.classList.remove("hidden");
      }
    } catch (err) {
      console.error("Failed to trace account:", err);
    }
  }

  // =========================================================================
  // Investigation Copilot Controller (AI Assistant & Action Dispatcher)
  // =========================================================================
  const copilotDrawer = document.getElementById("copilotDrawer");
  const openCopilotBtn = document.getElementById("openCopilotBtn");
  const sidebarCopilotBtn = document.getElementById("sidebarCopilotBtn");
  const closeCopilotDrawerBtn = document.getElementById("closeCopilotDrawerBtn");
  const copilotForm = document.getElementById("copilotForm");
  const copilotInput = document.getElementById("copilotInput");
  const copilotSendBtn = document.getElementById("copilotSendBtn");
  const copilotChatStream = document.getElementById("copilotChatStream");

  function openCopilot() {
    if (copilotDrawer) {
      copilotDrawer.classList.remove("hidden");
      if (copilotInput) copilotInput.focus();
    }
  }

  function closeCopilot() {
    if (copilotDrawer) {
      copilotDrawer.classList.add("hidden");
    }
  }

  if (openCopilotBtn) {
    openCopilotBtn.addEventListener("click", openCopilot);
  }

  if (sidebarCopilotBtn) {
    sidebarCopilotBtn.addEventListener("click", openCopilot);
  }

  if (closeCopilotDrawerBtn) {
    closeCopilotDrawerBtn.addEventListener("click", closeCopilot);
  }

  // Bind any element with data-action="open-copilot"
  document.querySelectorAll("[data-action='open-copilot']").forEach(btn => {
    btn.addEventListener("click", openCopilot);
  });

  // Prompt Chips Handler
  document.querySelectorAll(".copilot-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const query = chip.dataset.query || chip.textContent.trim();
      if (copilotInput) {
        copilotInput.value = query;
      }
      submitCopilotQuery(query);
    });
  });

  if (copilotForm) {
    copilotForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const q = copilotInput.value.trim();
      if (q) {
        submitCopilotQuery(q);
      }
    });
  }

  function resetCopilotChatStream(scenarioId) {
    if (!copilotChatStream) return;
    copilotChatStream.innerHTML = `
      <div class="copilot-msg copilot-msg-system">
        <div class="copilot-msg-avatar">✨</div>
        <div class="copilot-msg-content">
          <p><b>JARVIS Investigation Copilot Online.</b></p>
          <p style="margin-top:4px; font-size:0.75rem; color:#475569;">
            Active Context: <b>${scenarioId}</b>. Ask any natural language question or select a quick query above.
          </p>
        </div>
      </div>
    `;
  }

  async function submitCopilotQuery(queryText) {
    if (!queryText || !currentCaseData) return;

    // 1. Render User Message
    appendUserMessage(queryText);
    if (copilotInput) copilotInput.value = "";
    if (copilotSendBtn) copilotSendBtn.disabled = true;

    // 2. Render Thinking Placeholder
    const thinkingId = "copilot-thinking-" + Date.now();
    appendThinkingMessage(thinkingId);
    scrollCopilotToBottom();

    try {
      const res = await fetch(`${API_BASE}/api/copilot/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scenario_id: currentCaseData.scenario_id,
          question: queryText
        })
      });

      const data = await res.json();
      removeThinkingMessage(thinkingId);

      if (!res.ok) {
        appendBotMessage({
          answer: `Error (${res.status}): ${data.detail || "Failed to process query."}`,
          confidence: "LOW",
          why: [],
          evidence: [],
          actions: []
        });
      } else {
        appendBotMessage(data);
      }
    } catch (err) {
      console.error("[Copilot] Query error:", err);
      removeThinkingMessage(thinkingId);
      appendBotMessage({
        answer: `Network connection error: ${err.message}. Ensure backend is running.`,
        confidence: "LOW",
        why: [],
        evidence: [],
        actions: []
      });
    } finally {
      if (copilotSendBtn) copilotSendBtn.disabled = false;
      scrollCopilotToBottom();
    }
  }

  function appendUserMessage(text) {
    if (!copilotChatStream) return;
    const msgDiv = document.createElement("div");
    msgDiv.className = "copilot-msg copilot-msg-user";
    msgDiv.innerHTML = `
      <div class="copilot-msg-content">
        <p>${escapeHtml(text)}</p>
      </div>
    `;
    copilotChatStream.appendChild(msgDiv);
  }

  function appendThinkingMessage(id) {
    if (!copilotChatStream) return;
    const msgDiv = document.createElement("div");
    msgDiv.className = "copilot-msg copilot-msg-bot thinking";
    msgDiv.id = id;
    msgDiv.innerHTML = `
      <div class="copilot-msg-avatar">✨</div>
      <div class="copilot-msg-content">
        <p style="font-style:italic; color:#0284c7;">Analyzing investigation topology & evidence...</p>
      </div>
    `;
    copilotChatStream.appendChild(msgDiv);
  }

  function removeThinkingMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }

  function appendBotMessage(data) {
    if (!copilotChatStream) return;
    const msgDiv = document.createElement("div");
    msgDiv.className = "copilot-msg copilot-msg-bot";

    // Why section
    let whyHtml = "";
    if (data.why && data.why.length > 0) {
      whyHtml = `
        <div class="copilot-why-box">
          <div class="copilot-why-title">Why This Matters:</div>
          <ul class="copilot-why-list">
            ${data.why.map(w => `<li>${escapeHtml(w)}</li>`).join("")}
          </ul>
        </div>
      `;
    }

    // Evidence Section
    let evidenceHtml = "";
    if (data.evidence && data.evidence.length > 0) {
      evidenceHtml = `
        <div class="copilot-evidence-box">
          <div class="copilot-evidence-title">Evidence Citations:</div>
          <div class="copilot-evidence-pills">
            ${data.evidence.map(e => `<span class="copilot-evidence-pill">${escapeHtml(e)}</span>`).join("")}
          </div>
        </div>
      `;
    }

    // Actions Section
    let actionsHtml = "";
    if (data.actions && data.actions.length > 0) {
      actionsHtml = `
        <div class="copilot-actions-bar">
          ${data.actions.map((act, idx) => {
            return `
              <button class="copilot-action-btn" data-act-type="${escapeHtml(act.type)}" data-act-target="${escapeHtml(act.target || '')}">
                ${escapeHtml(act.label || 'Take Action')}
              </button>
            `;
          }).join("")}
        </div>
      `;
    }

    const confBadge = data.confidence ? `<span class="badge ${data.confidence === 'HIGH' ? 'score-low' : (data.confidence === 'MEDIUM' ? 'score-med' : 'score-high')}" style="font-size:0.65rem; padding:1px 5px;">${data.confidence} CONFIDENCE</span>` : "";

    msgDiv.innerHTML = `
      <div class="copilot-msg-avatar">✨</div>
      <div class="copilot-msg-content">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
          <span style="font-size:0.7rem; font-weight:700; color:#0284c7;">JARVIS INTELLIGENCE</span>
          ${confBadge}
        </div>
        <p style="white-space:pre-line;">${formatMarkdownLite(data.answer)}</p>
        ${whyHtml}
        ${evidenceHtml}
        ${actionsHtml}
      </div>
    `;

    // Bind action buttons inside this message
    msgDiv.querySelectorAll(".copilot-action-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        executeCopilotAction(btn.dataset.actType, btn.dataset.actTarget);
      });
    });

    copilotChatStream.appendChild(msgDiv);
  }

  function executeCopilotAction(type, target) {
    console.log("[Copilot Action]", type, target);
    switch (type) {
      case "focus_node":
        if (target) {
          inspectAccount(target);
          activateTab("tab-overview");
        }
        break;

      case "trace_path":
        if (target && currentCaseData && currentCaseData.attack_paths) {
          const path = currentCaseData.attack_paths.find(p => p.path_id === target);
          if (path && path.path_sequence) {
            graphRenderer.activePathNodeIds = new Set(path.path_sequence);
            graphRenderer.activePathEdges = new Set();
            for (let i = 0; i < path.path_sequence.length - 1; i++) {
              graphRenderer.activePathEdges.add(`${path.path_sequence[i]}->${path.path_sequence[i+1]}`);
            }
            graphRenderer.mode = "MONEY_TRAIL";
            activateTab("tab-overview");
            graphRenderer.draw();
          }
        }
        break;

      case "open_simulator":
        openSimulatorWithTarget("account", target || null);
        break;

      case "navigate_tab":
        if (target) {
          activateTab(target);
        }
        break;

      case "focus_simulation":
        openSimulatorWithTarget("account", target || null);
        break;

      default:
        console.warn("Unknown copilot action:", type);
    }
  }

  function scrollCopilotToBottom() {
    if (copilotChatStream) {
      copilotChatStream.scrollTop = copilotChatStream.scrollHeight;
    }
  }

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function formatMarkdownLite(str) {
    if (!str) return "";
    // Bold **text**
    let formatted = escapeHtml(str);
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
    return formatted;
  }

  // Initial Load
  loadScenariosList().then(() => {
    loadCase("SCENARIO_G");
  });
});


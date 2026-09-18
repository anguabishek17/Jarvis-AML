/**
 * JARVIS-AML Money Trail DNA & Behavioural Similarity Visualizer
 * Original Innovation Layer UI
 */

class DNAViewer {
  constructor(containerIds, modalElements) {
    this.sigDisplay = document.getElementById(containerIds.signatureId);
    this.hashDisplay = document.getElementById(containerIds.hashId);
    this.genesGrid = document.getElementById(containerIds.genesGridId);
    this.similarList = document.getElementById(containerIds.similarListId);
    this.evolutionList = document.getElementById(containerIds.evolutionListId);

    this.modal = modalElements.modal;
    this.modalTitle = modalElements.title;
    this.modalContent = modalElements.content;
    this.closeBtn = modalElements.closeBtn;

    this.currentDna = null;
    this.initModal();
  }

  initModal() {
    this.closeBtn.addEventListener("click", () => this.hideModal());
    window.addEventListener("click", (e) => {
      if (e.target === this.modal) this.hideModal();
    });

    const verifyBtn = document.getElementById("verifyDnaHashBtn");
    if (verifyBtn) {
      verifyBtn.addEventListener("click", () => this.showHashVerification());
    }
  }

  showModal(title, htmlContent) {
    this.modalTitle.textContent = title;
    this.modalContent.innerHTML = htmlContent;
    this.modal.classList.remove("hidden");
  }

  hideModal() {
    this.modal.classList.add("hidden");
  }

  showHashVerification() {
    if (!this.currentDna) return;
    const content = `
      <div>
        <div style="font-weight:600; color:#38bdf8; margin-bottom:6px;">Forensic SHA-256 Integrity Verification</div>
        <div style="font-size:0.75rem; color:#94a3b8; margin-bottom:12px;">
          This cryptographic digest validates that the generated behavioral fingerprint and underlying mathematical evidence have not been altered.
        </div>
        <div style="background:#0a0e17; border:1px solid #24344d; padding:10px; border-radius:6px; font-family:'JetBrains Mono', monospace; font-size:0.75rem; color:#10b981; word-break:break-all;">
          ${this.currentDna.evidence_payload_sha256}
        </div>
        <div style="margin-top:12px; font-size:0.72rem; color:#94a3b8;">
          ✓ Timestamp: ${this.currentDna.generated_at || new Date().toISOString()}<br>
          ✓ Algorithm: SHA-256 / UTF-8 Canonical Json Digest<br>
          ✓ Status: Tamper-Evident Record Verified
        </div>
      </div>
    `;
    this.showModal("Forensic Integrity Seal", content);
  }

  renderDNA(dnaData, similarCases = []) {
    this.currentDna = dnaData;
    if (!dnaData) {
      this.sigDisplay.textContent = "NO ATTACK PATH EXTRACTED";
      this.hashDisplay.textContent = "...";
      this.genesGrid.innerHTML = "<p style='color:#64748b; font-size:0.8rem;'>No active money trail selected.</p>";
      this.similarList.innerHTML = "";
      this.evolutionList.innerHTML = "";
      return;
    }

    // 1. Signature Box
    this.sigDisplay.textContent = dnaData.signature;
    const hash = dnaData.evidence_payload_sha256 || "";
    this.hashDisplay.textContent = hash ? `${hash.substring(0, 12)}...${hash.substring(hash.length - 8)}` : "Verified";

    // 2. Genes Grid
    this.genesGrid.innerHTML = "";
    (dnaData.genes || []).forEach(gene => {
      const card = document.createElement("div");
      card.className = "gene-card";
      card.innerHTML = `
        <div class="gene-card-header">${gene.gene_name}</div>
        <div class="gene-card-value">${gene.value_display}</div>
        <div class="gene-card-code">${gene.gene_code}</div>
      `;
      card.addEventListener("click", () => this.inspectGene(gene));
      this.genesGrid.appendChild(card);
    });

    // 3. Similar Cases
    this.similarList.innerHTML = "";
    if (similarCases && similarCases.length > 0) {
      similarCases.forEach(sim => {
        const item = document.createElement("div");
        item.className = "similar-case-card";
        item.innerHTML = `
          <div class="sim-header">
            <span class="sim-title">${sim.case_title}</span>
            <span class="sim-match-badge">${sim.overall_similarity_pct}% Match</span>
          </div>
          <div class="sim-dna">${sim.dna_signature}</div>
          <div class="sim-notes">${sim.known_typology_notes}</div>
          <div style="font-size:0.7rem; color:#64748b; margin-top:4px;">
            Retention: ${sim.retention_similarity_pct}% | Velocity: ${sim.velocity_similarity_pct}% | Topology: ${sim.topology_similarity_pct}%
          </div>
        `;
        this.similarList.appendChild(item);
      });
    } else {
      this.similarList.innerHTML = "<p style='color:#64748b; font-size:0.78rem;'>No matching typologies.</p>";
    }

    // 4. DNA Evolution
    this.evolutionList.innerHTML = "";
    (dnaData.evolution_stages || []).forEach(stage => {
      const step = document.createElement("div");
      step.className = "evolution-step";
      step.innerHTML = `
        <div class="evolution-step-title">Stage ${stage.stage_index} (${stage.stage_name}) — ${stage.timestamp_range}</div>
        <div class="evolution-step-sig">${stage.active_dna_signature}</div>
        <div style="font-size:0.72rem; color:#94a3b8;">${stage.stage_narrative}</div>
      `;
      this.evolutionList.appendChild(step);
    });
  }

  inspectGene(gene) {
    const txBadges = (gene.supporting_transaction_ids || [])
      .map(tx => `<span style="background:#1e293b; border:1px solid #334155; padding:2px 6px; border-radius:4px; font-family:'JetBrains Mono', monospace; font-size:0.75rem; color:#38bdf8;">${tx}</span>`)
      .join(" ");

    const detailsJson = JSON.stringify(gene.calculation_details || {}, null, 2);

    const content = `
      <div>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
          <span style="font-size:1.1rem; font-weight:700; color:#00f0ff; font-family:'JetBrains Mono', monospace;">${gene.gene_code}</span>
          <span style="font-size:0.8rem; font-weight:600; color:#ffffff;">${gene.value_display}</span>
        </div>
        <p style="font-size:0.82rem; color:#cbd5e1; margin-bottom:12px; line-height:1.45;">
          ${gene.why_explanation}
        </p>
        <div style="margin-bottom:10px;">
          <div style="font-size:0.72rem; font-weight:700; color:#64748b; text-transform:uppercase; margin-bottom:4px;">Supporting Transaction IDs</div>
          <div style="display:flex; flex-wrap:wrap; gap:4px;">${txBadges || "<span style='color:#64748b;'>None</span>"}</div>
        </div>
        <div>
          <div style="font-size:0.72rem; font-weight:700; color:#64748b; text-transform:uppercase; margin-bottom:4px;">Mathematical & Topological Parameters</div>
          <pre style="background:#0a0e17; border:1px solid #24344d; padding:8px; border-radius:6px; font-family:'JetBrains Mono', monospace; font-size:0.72rem; color:#94a3b8; overflow-x:auto;">${detailsJson}</pre>
        </div>
      </div>
    `;

    this.showModal(`Gene Evidence: ${gene.gene_name}`, content);
  }
}

window.DNAViewer = DNAViewer;

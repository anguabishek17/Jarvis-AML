/**
 * JARVIS-AML Analytics Chart Renderer
 * Renders modern, responsive SaaS charts for Suspicious Activity Overview
 * and Pattern Distribution without external heavy libraries.
 */

class AnalyticsChartRenderer {
  constructor(canvasId, tooltipId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext("2d");
    this.tooltip = document.getElementById(tooltipId);
    this.dataPoints = [];
    this.hoveredIndex = -1;

    this.initEvents();
    this.resize();
    window.addEventListener("resize", () => {
      this.resize();
      this.render();
    });
  }

  resize() {
    if (!this.canvas) return;
    const rect = this.canvas.parentElement.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    this.width = rect.width;
    this.height = Math.max(rect.height, 220);
    this.canvas.width = this.width * dpr;
    this.canvas.height = this.height * dpr;
    this.ctx.scale(dpr, dpr);
  }

  initEvents() {
    if (!this.canvas) return;
    this.canvas.addEventListener("mousemove", (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      if (!this.dataPoints.length) return;
      const paddingLeft = 50;
      const paddingRight = 30;
      const graphWidth = this.width - paddingLeft - paddingRight;
      const step = graphWidth / Math.max(this.dataPoints.length - 1, 1);

      let closestIdx = -1;
      let minDistance = Infinity;

      this.dataPoints.forEach((pt, i) => {
        const px = paddingLeft + i * step;
        const dist = Math.abs(mouseX - px);
        if (dist < minDistance && dist < step * 0.75) {
          minDistance = dist;
          closestIdx = i;
        }
      });

      if (closestIdx !== this.hoveredIndex) {
        this.hoveredIndex = closestIdx;
        this.render();
        this.updateTooltip(e.clientX, e.clientY);
      }
    });

    this.canvas.addEventListener("mouseleave", () => {
      this.hoveredIndex = -1;
      this.render();
      if (this.tooltip) this.tooltip.classList.add("hidden");
    });
  }

  updateTooltip(clientX, clientY) {
    if (!this.tooltip || this.hoveredIndex < 0 || !this.dataPoints[this.hoveredIndex]) {
      if (this.tooltip) this.tooltip.classList.add("hidden");
      return;
    }

    const pt = this.dataPoints[this.hoveredIndex];
    this.tooltip.innerHTML = `
      <div style="font-weight:700; color:#0f172a; margin-bottom:4px; font-size:0.8rem;">${pt.label}</div>
      <div style="font-size:0.75rem; color:#475569;">Risk Score: <b style="color:#ef4444;">${pt.riskScore}/100</b></div>
      <div style="font-size:0.75rem; color:#475569;">Volume: <b style="color:#0284c7;">₹${(pt.volume || 0).toLocaleString('en-IN')}</b></div>
      <div style="font-size:0.7rem; color:#64748b; margin-top:2px;">${pt.activeAccounts || 0} active accounts</div>
    `;
    this.tooltip.classList.remove("hidden");
    this.tooltip.style.left = `${clientX + 12}px`;
    this.tooltip.style.top = `${clientY - 20}px`;
  }

  setData(caseData) {
    if (!caseData) return;
    const stages = caseData.temporal_stages || [];
    const totalVol = (caseData.metadata && caseData.metadata.total_volume_inr) || 1000000;

    if (stages.length > 0) {
      this.dataPoints = stages.map((s, idx) => {
        const fraction = (idx + 1) / stages.length;
        const stageVol = Math.round(totalVol * (s.accounts_active ? s.accounts_active.length / 10 : 0.2));
        const risk = idx === 0 ? 45 : (idx === 1 ? 70 : (idx === 2 ? 95 : (idx === 3 ? 88 : 65)));
        return {
          label: s.stage_name || `Stage ${idx + 1}`,
          time: s.time_range_display || `T+${idx * 15}m`,
          riskScore: s.stage_risk_score || risk,
          volume: stageVol,
          activeAccounts: (s.accounts_active && s.accounts_active.length) || 3
        };
      });
    } else {
      // Fallback baseline points
      this.dataPoints = [
        { label: "Injection (09:00)", riskScore: 35, volume: totalVol * 0.3, activeAccounts: 2 },
        { label: "Dispersion (09:15)", riskScore: 72, volume: totalVol * 0.45, activeAccounts: 5 },
        { label: "Layering (09:30)", riskScore: 94, volume: totalVol * 0.8, activeAccounts: 8 },
        { label: "Convergence (09:45)", riskScore: 86, volume: totalVol * 0.6, activeAccounts: 4 },
        { label: "Exit Sink (10:00)", riskScore: 60, volume: totalVol * 0.25, activeAccounts: 2 },
      ];
    }

    this.resize();
    this.render();
  }

  render() {
    if (!this.ctx || !this.width) return;
    const ctx = this.ctx;
    const w = this.width;
    const h = this.height;

    ctx.clearRect(0, 0, w, h);

    if (!this.dataPoints || this.dataPoints.length === 0) {
      ctx.fillStyle = "#94a3b8";
      ctx.font = "12px Inter, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("No temporal activity data available for active case", w / 2, h / 2);
      return;
    }

    const padLeft = 45;
    const padRight = 30;
    const padTop = 25;
    const padBottom = 35;
    const plotW = w - padLeft - padRight;
    const plotH = h - padTop - padBottom;

    // Draw Background Grid Lines
    ctx.strokeStyle = "#f1f5f9";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = padTop + (plotH / 4) * i;
      ctx.beginPath();
      ctx.moveTo(padLeft, y);
      ctx.lineTo(w - padRight, y);
      ctx.stroke();

      // Y-axis labels (Risk Score 0-100)
      ctx.fillStyle = "#94a3b8";
      ctx.font = "10px Inter, sans-serif";
      ctx.textAlign = "right";
      ctx.fillText(`${100 - i * 25}%`, padLeft - 8, y + 3);
    }

    const stepX = plotW / Math.max(this.dataPoints.length - 1, 1);
    const coords = this.dataPoints.map((pt, i) => {
      const x = padLeft + i * stepX;
      const normalizedY = (pt.riskScore || 0) / 100;
      const y = padTop + plotH - (normalizedY * plotH);
      return { x, y, pt };
    });

    // 1. Draw Gradient Area Fill for Risk
    ctx.beginPath();
    ctx.moveTo(coords[0].x, padTop + plotH);
    coords.forEach((c) => ctx.lineTo(c.x, c.y));
    ctx.lineTo(coords[coords.length - 1].x, padTop + plotH);
    ctx.closePath();

    const areaGradient = ctx.createLinearGradient(0, padTop, 0, padTop + plotH);
    areaGradient.addColorStop(0, "rgba(239, 68, 68, 0.28)");
    areaGradient.addColorStop(0.5, "rgba(2, 132, 199, 0.18)");
    areaGradient.addColorStop(1, "rgba(2, 132, 199, 0.02)");
    ctx.fillStyle = areaGradient;
    ctx.fill();

    // 2. Draw Smooth Risk Curve
    ctx.beginPath();
    ctx.moveTo(coords[0].x, coords[0].y);
    for (let i = 0; i < coords.length - 1; i++) {
      const c1 = coords[i];
      const c2 = coords[i + 1];
      const mx = (c1.x + c2.x) / 2;
      ctx.bezierCurveTo(mx, c1.y, mx, c2.y, c2.x, c2.y);
    }
    ctx.strokeStyle = "#0284c7";
    ctx.lineWidth = 2.5;
    ctx.stroke();

    // 3. Draw Nodes and Labels
    coords.forEach((c, idx) => {
      const isHovered = idx === this.hoveredIndex;
      const risk = c.pt.riskScore || 0;
      const dotColor = risk >= 80 ? "#ef4444" : (risk >= 50 ? "#f59e0b" : "#0284c7");

      // Vertical guide line when hovered
      if (isHovered) {
        ctx.beginPath();
        ctx.moveTo(c.x, padTop);
        ctx.lineTo(c.x, padTop + plotH);
        ctx.strokeStyle = "#cbd5e1";
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 4]);
        ctx.stroke();
        ctx.setLineDash([]);
      }

      // Outer ring
      ctx.beginPath();
      ctx.arc(c.x, c.y, isHovered ? 6 : 4, 0, 2 * Math.PI);
      ctx.fillStyle = "#ffffff";
      ctx.fill();
      ctx.strokeStyle = dotColor;
      ctx.lineWidth = 2.5;
      ctx.stroke();

      // X-axis label
      ctx.fillStyle = isHovered ? "#0f172a" : "#64748b";
      ctx.font = isHovered ? "600 11px Inter, sans-serif" : "11px Inter, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(c.pt.label, c.x, padTop + plotH + 20);
    });
  }
}

window.AnalyticsChartRenderer = AnalyticsChartRenderer;

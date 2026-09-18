/**
 * JARVIS-AML Graph Canvas Renderer
 * High-performance 2D force-directed graph with particle pulse animations,
 * role-based node color coding, directed transaction arrows, pan/zoom, and mode filtering.
 */

class GraphCanvasRenderer {
  constructor(canvasId, tooltipId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext("2d");
    this.tooltip = document.getElementById(tooltipId);

    this.nodes = [];
    this.edges = [];
    this.roles = {};
    this.activeMode = "FULL";
    this.activePathNodeIds = new Set();
    this.active2HopNodeIds = new Set();
    this.selectedNode = null;
    this.hoveredNode = null;

    // Viewport transform
    this.scale = 1.0;
    this.panX = 0;
    this.panY = 0;
    this.isDragging = false;
    this.dragStartX = 0;
    this.dragStartY = 0;
    this.isPhysicsRunning = true;

    // Animation particles along edges
    this.particles = [];
    this.particleTimer = 0;

    this.initEvents();
    this.resize();
    window.addEventListener("resize", () => this.resize());
    this.animate();
  }

  resize() {
    const rect = this.canvas.parentElement.getBoundingClientRect();
    this.canvas.width = rect.width * window.devicePixelRatio;
    this.canvas.height = rect.height * window.devicePixelRatio;
    this.ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    this.logicalWidth = rect.width;
    this.logicalHeight = rect.height;
    if (this.panX === 0 && this.panY === 0) {
      this.panX = this.logicalWidth / 2;
      this.panY = this.logicalHeight / 2;
    }
  }

  setData(graphData, rolesData = {}) {
    this.roles = rolesData;
    const rawNodes = graphData.nodes || [];
    const rawEdges = graphData.edges || [];

    // Map existing positions if reloading
    const posMap = new Map();
    this.nodes.forEach(n => posMap.set(n.id, { x: n.x, y: n.y, vx: n.vx, vy: n.vy }));

    const radius = Math.min(this.logicalWidth, this.logicalHeight) * 0.35;
    const count = rawNodes.length;

    this.nodes = rawNodes.map((n, i) => {
      const angle = (i / Math.max(count, 1)) * 2 * Math.PI;
      const prev = posMap.get(n.id);
      return {
        ...n,
        x: prev ? prev.x : Math.cos(angle) * radius + (Math.random() * 20 - 10),
        y: prev ? prev.y : Math.sin(angle) * radius + (Math.random() * 20 - 10),
        vx: prev ? prev.vx : 0,
        vy: prev ? prev.vy : 0,
        radius: 18,
      };
    });

    this.edges = rawEdges.map(e => ({
      ...e,
      sourceNode: this.nodes.find(n => n.id === e.source),
      targetNode: this.nodes.find(n => n.id === e.target),
    })).filter(e => e.sourceNode && e.targetNode);

    // Initialize flow particles
    this.particles = [];
    this.edges.forEach((e, idx) => {
      this.particles.push({
        edge: e,
        progress: (idx * 0.2) % 1.0,
        speed: 0.008 + (Math.random() * 0.004),
      });
    });
  }

  setMode(mode, contextData = {}) {
    this.activeMode = mode;
    if (contextData.pathNodes) {
      this.activePathNodeIds = new Set(contextData.pathNodes);
    }
    if (contextData.twoHopNodes) {
      this.active2HopNodeIds = new Set(contextData.twoHopNodes);
    }
  }

  highlightAttackPath(accountSequence) {
    this.activePathNodeIds = new Set(accountSequence);
    this.activeMode = "MONEY_TRAIL";
  }

  highlight2Hop(focusAccount, nodesList) {
    this.selectedNode = this.nodes.find(n => n.id === focusAccount) || null;
    this.active2HopNodeIds = new Set(nodesList);
    this.activeMode = "2HOP";
  }

  resetView() {
    this.scale = 1.0;
    this.panX = this.logicalWidth / 2;
    this.panY = this.logicalHeight / 2;
    this.activeMode = "FULL";
    this.activePathNodeIds.clear();
    this.active2HopNodeIds.clear();
    this.selectedNode = null;
  }

  togglePhysics() {
    this.isPhysicsRunning = !this.isPhysicsRunning;
    return this.isPhysicsRunning;
  }

  initEvents() {
    this.canvas.addEventListener("mousedown", e => {
      const pos = this.getCanvasCoords(e);
      const clickedNode = this.getNodeAt(pos.x, pos.y);
      if (clickedNode) {
        this.selectedNode = clickedNode;
        if (this.onNodeClick) this.onNodeClick(clickedNode);
      } else {
        this.isDragging = true;
        this.dragStartX = e.clientX - this.panX;
        this.dragStartY = e.clientY - this.panY;
      }
    });

    window.addEventListener("mousemove", e => {
      if (this.isDragging) {
        this.panX = e.clientX - this.dragStartX;
        this.panY = e.clientY - this.dragStartY;
        return;
      }
      const pos = this.getCanvasCoords(e);
      const hovered = this.getNodeAt(pos.x, pos.y);
      this.hoveredNode = hovered;
      this.updateTooltip(hovered, e.clientX, e.clientY);
    });

    window.addEventListener("mouseup", () => {
      this.isDragging = false;
    });

    this.canvas.addEventListener("wheel", e => {
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
      this.scale = Math.min(Math.max(this.scale * zoomFactor, 0.3), 3.0);
    });
  }

  getCanvasCoords(e) {
    const rect = this.canvas.getBoundingClientRect();
    const rawX = e.clientX - rect.left;
    const rawY = e.clientY - rect.top;
    return {
      x: (rawX - this.panX) / this.scale,
      y: (rawY - this.panY) / this.scale,
    };
  }

  getNodeAt(x, y) {
    for (const node of this.nodes) {
      const dx = node.x - x;
      const dy = node.y - y;
      if (Math.sqrt(dx * dx + dy * dy) <= node.radius + 6) {
        return node;
      }
    }
    return null;
  }

  updateTooltip(node, clientX, clientY) {
    if (!node) {
      this.tooltip.classList.add("hidden");
      return;
    }
    const roleInfo = this.roles[node.id] || {};
    const probableRole = roleInfo.probable_role || "ANALYZING";
    const confidence = roleInfo.confidence ? `${Math.round(roleInfo.confidence * 100)}%` : "N/A";

    this.tooltip.innerHTML = `
      <div style="font-weight:700; color:#38bdf8; margin-bottom:4px;">${node.id}</div>
      <div style="font-size:0.75rem; color:#94a3b8;">${node.label || node.id}</div>
      <div style="margin-top:6px; font-size:0.72rem;">
        <div>Role Hypothesis: <b style="color:#ffffff;">${probableRole}</b> (${confidence})</div>
        <div>Inflow: <span style="color:#10b981;">₹${(node.inflow_total || 0).toLocaleString('en-IN')}</span></div>
        <div>Outflow: <span style="color:#f59e0b;">₹${(node.outflow_total || 0).toLocaleString('en-IN')}</span></div>
        <div>Forwarding: <b>${Math.round((node.forwarding_ratio || 0)*100)}%</b></div>
        <div>Dwell Latency: <b>${node.avg_dwell_minutes || 0}m</b></div>
      </div>
    `;
    this.tooltip.style.left = `${clientX + 15}px`;
    this.tooltip.style.top = `${clientY + 15}px`;
    this.tooltip.classList.remove("hidden");
  }

  updatePhysics() {
    if (!this.isPhysicsRunning) return;

    // Repulsion between nodes
    for (let i = 0; i < this.nodes.length; i++) {
      for (let j = i + 1; j < this.nodes.length; j++) {
        const n1 = this.nodes[i];
        const n2 = this.nodes[j];
        const dx = n2.x - n1.x;
        const dy = n2.y - n1.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        if (dist < 220) {
          const force = (220 - dist) / dist * 0.08;
          n1.vx -= dx * force;
          n1.vy -= dy * force;
          n2.vx += dx * force;
          n2.vy += dy * force;
        }
      }
    }

    // Spring attraction along edges
    for (const edge of this.edges) {
      const u = edge.sourceNode;
      const v = edge.targetNode;
      const dx = v.x - u.x;
      const dy = v.y - u.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const targetDist = 130;
      const force = (dist - targetDist) * 0.015;
      u.vx += (dx / dist) * force;
      u.vy += (dy / dist) * force;
      v.vx -= (dx / dist) * force;
      v.vy -= (dy / dist) * force;
    }

    // Center gravity & velocity dampening
    for (const node of this.nodes) {
      node.vx += (-node.x) * 0.002;
      node.vy += (-node.y) * 0.002;
      node.vx *= 0.85;
      node.vy *= 0.85;
      node.x += node.vx;
      node.y += node.vy;
    }
  }

  getNodeColor(node) {
    const roleInfo = this.roles[node.id];
    const role = roleInfo ? roleInfo.probable_role : "LEGITIMATE";
    switch (role) {
      case "ORIGINATOR": return "#3b82f6";
      case "MULE": return "#f59e0b";
      case "DISPERSER": return "#a855f7";
      case "AGGREGATOR": return "#06b6d4";
      case "SINK": return "#ef4444";
      case "LEGITIMATE": default: return "#10b981";
    }
  }

  isNodeVisible(node) {
    if (this.activeMode === "FULL") return true;
    if (this.activeMode === "MONEY_TRAIL") return this.activePathNodeIds.has(node.id);
    if (this.activeMode === "2HOP") return this.active2HopNodeIds.has(node.id);
    if (this.activeMode === "SUSPICIOUS") {
      const r = this.roles[node.id];
      return r && r.probable_role !== "LEGITIMATE";
    }
    return true;
  }

  setSimulationMode(simData) {
    if (!simData) {
      this.simulationActive = false;
      this.simRemovedNodeId = null;
      this.simRemovedTxnId = null;
      this.simBrokenEdges = new Set();
      this.simAffectedNodeIds = new Set();
      return;
    }

    this.simulationActive = true;
    this.simRemovedNodeId = simData.target_type === "account" ? simData.target_id : null;
    this.simRemovedTxnId = simData.target_type === "transaction" ? simData.target_id : null;
    
    this.simAffectedNodeIds = new Set(simData.impact ? simData.impact.affected_entities || [] : []);
    this.simBrokenEdges = new Set(simData.impact ? (simData.impact.removed_edges || []).map(e => `${e.sender}->${e.receiver}`) : []);
  }

  animate() {
    this.updatePhysics();
    this.render();
    requestAnimationFrame(() => this.animate());
  }

  render() {
    this.ctx.clearRect(0, 0, this.logicalWidth, this.logicalHeight);
    this.ctx.save();
    this.ctx.translate(this.panX, this.panY);
    this.ctx.scale(this.scale, this.scale);

    // Draw Edges
    for (const edge of this.edges) {
      const isSrcVis = this.isNodeVisible(edge.sourceNode);
      const isTgtVis = this.isNodeVisible(edge.targetNode);
      const isPathEdge = this.activePathNodeIds.has(edge.sourceNode.id) && this.activePathNodeIds.has(edge.targetNode.id);
      
      const edgeKey = `${edge.sourceNode.id}->${edge.targetNode.id}`;
      const isSimBroken = this.simulationActive && (
        this.simBrokenEdges.has(edgeKey) || 
        edge.sourceNode.id === this.simRemovedNodeId || 
        edge.targetNode.id === this.simRemovedNodeId ||
        edge.transaction_id === this.simRemovedTxnId
      );

      let alpha = (!isSrcVis || !isTgtVis) ? 0.08 : (isPathEdge ? 0.95 : 0.45);
      let strokeColor = isPathEdge ? "#00f0ff" : "#475569";
      let lineWidth = isPathEdge ? 2.5 : 1.2;

      if (isSimBroken) {
        strokeColor = "#ef4444";
        lineWidth = 2.0;
        alpha = 0.8;
      }

      this.drawDirectedEdge(edge.sourceNode, edge.targetNode, edge, strokeColor, alpha, lineWidth, isSimBroken);
    }

    // Draw Flow Particles along path edges
    for (const p of this.particles) {
      if (!this.isNodeVisible(p.edge.sourceNode) || !this.isNodeVisible(p.edge.targetNode)) continue;
      const isPath = this.activePathNodeIds.has(p.edge.sourceNode.id) && this.activePathNodeIds.has(p.edge.targetNode.id);
      
      const edgeKey = `${p.edge.sourceNode.id}->${p.edge.targetNode.id}`;
      if (this.simulationActive && (this.simBrokenEdges.has(edgeKey) || p.edge.sourceNode.id === this.simRemovedNodeId || p.edge.targetNode.id === this.simRemovedNodeId)) {
        continue; // Do not flow particles through simulated broken edges
      }

      p.progress = (p.progress + p.speed) % 1.0;

      const px = p.edge.sourceNode.x + (p.edge.targetNode.x - p.edge.sourceNode.x) * p.progress;
      const py = p.edge.sourceNode.y + (p.edge.targetNode.y - p.edge.sourceNode.y) * p.progress;

      this.ctx.beginPath();
      this.ctx.arc(px, py, isPath ? 3.5 : 2, 0, 2 * Math.PI);
      this.ctx.fillStyle = isPath ? "#00f0ff" : "rgba(56, 189, 248, 0.6)";
      this.ctx.fill();
    }

    // Draw Nodes
    for (const node of this.nodes) {
      const isVis = this.isNodeVisible(node);
      const isSelected = this.selectedNode && this.selectedNode.id === node.id;
      const isHovered = this.hoveredNode && this.hoveredNode.id === node.id;
      const isPathNode = this.activePathNodeIds.has(node.id);
      const isSimRemoved = this.simulationActive && (node.id === this.simRemovedNodeId);
      const isSimAffected = this.simulationActive && this.simAffectedNodeIds.has(node.id);

      let color = this.getNodeColor(node);
      let alpha = isVis ? 1.0 : 0.15;

      if (isSimRemoved) {
        color = "#ef4444";
        alpha = 0.4;
      } else if (isSimAffected) {
        color = "#f59e0b";
      }

      // Glow effect for selected or path node or simulated removed
      if (isSelected || isPathNode || isSimRemoved) {
        this.ctx.beginPath();
        this.ctx.arc(node.x, node.y, node.radius + 8, 0, 2 * Math.PI);
        this.ctx.fillStyle = isSimRemoved ? "rgba(239, 68, 68, 0.3)" : (isPathNode ? "rgba(0, 240, 255, 0.25)" : "rgba(59, 130, 246, 0.3)");
        this.ctx.fill();
      }

      // Outer border
      this.ctx.beginPath();
      this.ctx.arc(node.x, node.y, node.radius, 0, 2 * Math.PI);
      this.ctx.fillStyle = isVis ? (isSimRemoved ? "#3b1219" : "#162032") : "#0d131f";
      this.ctx.fill();
      this.ctx.strokeStyle = color;
      this.ctx.globalAlpha = alpha;
      this.ctx.lineWidth = isSimRemoved ? 2.5 : (isSelected ? 3.5 : (isHovered ? 2.5 : 2.0));
      
      if (isSimRemoved) {
        this.ctx.setLineDash([4, 4]);
      } else {
        this.ctx.setLineDash([]);
      }
      this.ctx.stroke();
      this.ctx.setLineDash([]);

      // Node Inner Dot or Strike-through
      this.ctx.beginPath();
      this.ctx.arc(node.x, node.y, node.radius * 0.45, 0, 2 * Math.PI);
      this.ctx.fillStyle = color;
      this.ctx.fill();

      if (isSimRemoved) {
        this.ctx.beginPath();
        this.ctx.moveTo(node.x - node.radius * 0.5, node.y - node.radius * 0.5);
        this.ctx.lineTo(node.x + node.radius * 0.5, node.y + node.radius * 0.5);
        this.ctx.strokeStyle = "#ffffff";
        this.ctx.lineWidth = 2;
        this.ctx.stroke();
      }

      // Label Text
      this.ctx.font = isSelected ? "bold 11px 'JetBrains Mono', monospace" : "10px 'JetBrains Mono', monospace";
      this.ctx.fillStyle = isSimRemoved ? "#ef4444" : (isVis ? "#f1f5f9" : "#475569");
      this.ctx.textAlign = "center";
      const labelText = isSimRemoved ? `[REMOVED] ${node.id.replace("ACC_", "")}` : node.id.replace("ACC_", "");
      this.ctx.fillText(labelText, node.x, node.y + node.radius + 14);
      this.ctx.globalAlpha = 1.0;
    }

    this.ctx.restore();
  }

  drawDirectedEdge(u, v, edgeData, strokeColor, alpha, lineWidth) {
    const dx = v.x - u.x;
    const dy = v.y - u.y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    if (dist === 0) return;

    // Offset line to account for node radii
    const startX = u.x + (dx / dist) * u.radius;
    const startY = u.y + (dy / dist) * u.radius;
    const endX = v.x - (dx / dist) * (v.radius + 6);
    const endY = v.y - (dy / dist) * (v.radius + 6);

    this.ctx.save();
    this.ctx.globalAlpha = alpha;
    this.ctx.strokeStyle = strokeColor;
    this.ctx.lineWidth = lineWidth;

    // Line
    this.ctx.beginPath();
    this.ctx.moveTo(startX, startY);
    this.ctx.lineTo(endX, endY);
    this.ctx.stroke();

    // Arrow Head
    const angle = Math.atan2(dy, dx);
    const arrowLen = 7;
    this.ctx.beginPath();
    this.ctx.moveTo(endX, endY);
    this.ctx.lineTo(endX - arrowLen * Math.cos(angle - Math.PI / 6), endY - arrowLen * Math.sin(angle - Math.PI / 6));
    this.ctx.lineTo(endX - arrowLen * Math.cos(angle + Math.PI / 6), endY - arrowLen * Math.sin(angle + Math.PI / 6));
    this.ctx.closePath();
    this.ctx.fillStyle = strokeColor;
    this.ctx.fill();

    // Edge Amount Label (if zoomed in or in path)
    if (this.scale >= 0.85 && alpha >= 0.4) {
      const midX = (startX + endX) / 2;
      const midY = (startY + endY) / 2;
      this.ctx.font = "9px 'JetBrains Mono', monospace";
      this.ctx.fillStyle = "#38bdf8";
      this.ctx.textAlign = "center";
      const amtStr = `₹${(edgeData.amount / 100000).toFixed(1)}L`;
      this.ctx.fillText(amtStr, midX, midY - 4);
    }

    this.ctx.restore();
  }
}

window.GraphCanvasRenderer = GraphCanvasRenderer;

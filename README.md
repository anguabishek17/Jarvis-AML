# JARVIS-AML — AI-Powered Financial Crime Investigation & Money Trail Intelligence System

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3119/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.2-009688.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-89%20passed-success.svg)](https://pytest.org/)
[![Vercel](https://img.shields.io/badge/Frontend-Vercel-black?logo=vercel)](https://jarvis-aml.vercel.app)
[![Render](https://img.shields.io/badge/Backend-Render-46E3B7?logo=render)](https://jarvis-aml.onrender.com)

**JARVIS-AML** is an explainable graph-based Anti-Money Laundering (AML) intelligence platform and financial crime investigation operations center. It provides end-to-end topological money trail reconstruction, deterministic typology detection, account role inference, 6-gene Money Trail DNA™ fingerprinting with cryptographic integrity verification, temporal risk evolution, custom CSV dataset ingestion, interactive What-If scenario simulation, a zero-hallucination Investigation Copilot, and dynamic forensic PDF dossier export.

---

## 🌐 Live Production Deployments

- **Frontend (Vercel)**: [https://jarvis-aml.vercel.app](https://jarvis-aml.vercel.app)
- **Backend API (Render)**: [https://jarvis-aml.onrender.com](https://jarvis-aml.onrender.com)
- **Interactive API Documentation**: [https://jarvis-aml.onrender.com/docs](https://jarvis-aml.onrender.com/docs)
- **Health Check**: [https://jarvis-aml.onrender.com/health](https://jarvis-aml.onrender.com/health)

---

## 🚀 Key Features

1. **Deterministic Typology Detectors**:
   - **Layering Trails**: Rapid, high-retention multi-hop transit sequences.
   - **Circular Transfers**: Closed-loop round-tripping flows.
   - **Rapid Movement**: Low dwell-time pass-through transactions (mule accounts).
   - **Fan-Out (Structuring / Smurfing)**: Single source dispersing to multiple intermediary accounts.
   - **Fan-In (Funnel Aggregation)**: Multiple intermediary accounts funneling funds into a single terminal sink.

2. **Money Trail DNA™ — Behavioural Fingerprinting**:
   - Deterministic 6-gene sequence: `TYPOLOGY`, `RETENTION`, `VELOCITY`, `DISPERSION`, `TOPOLOGY`, `ROLE SEQUENCE`.
   - Historical typology similarity matching with vector cosine similarity.
   - Tamper-evident SHA-256 cryptographic forensic integrity seal.

3. **Topological Graph Engine & Interactive Visualizer**:
   - 2D force-directed layout with particle flow along directed transaction edges.
   - Multi-mode filtering: `FULL NETWORK`, `SUSPICIOUS ONLY`, `MONEY TRAIL`, `ROLE VIEW`, `2-HOP TRACE`, `PATTERNS`.
   - Interactive 5-stage temporal timeline scrubber (`Injection` $\to$ `Dispersion` $\to$ `Layering` $\to$ `Convergence` $\to$ `Sink`).

4. **Investigation Copilot (AI Intelligence Layer)**:
   - Zero-hallucination explainability engine grounded strictly in active case dossier facts.
   - Deep entity explainability (`Why is ACC_GATEKEEPER_MULE important?`).
   - Longest attack path analysis, pattern triage, Money Trail DNA breakdown, and court evidence briefings.
   - Interactive UI directives: highlight on graph, trace attack trail, and launch counterfactual simulations.

5. **Investigation Simulator (What-If Disruptions)**:
   - Counterfactual graph disruption engine to simulate hypothetical entity or transaction removal.
   - Before-versus-after network metrics, disrupted attack paths, broken typologies, and role-shift analytics.

6. **Entity Intelligence & Role Inference**:
   - Heuristic classification: `ORIGINATOR`, `MULE`, `DISPERSER`, `AGGREGATOR`, `SINK`, `LEGITIMATE`.
   - Quantitative signals: Forwarding ratio, dwell time, betweenness centrality, degree distribution, and in/outflow asymmetry.
   - Slide-over right drawer account inspector with 2-hop neighborhood exploration.

7. **Custom Ingestion Pipeline**:
   - Upload custom transaction CSV files or paste raw transaction records.
   - Real-time pre-validation (`/api/investigate/validate`) with error/warning diagnostics.
   - Complete execution of graph builder, detectors, DNA generator, and report synthesis.

8. **Dynamic Forensic PDF Dossier Export**:
   - Multi-page ReportLab PDF export with 14 comprehensive audit sections.
   - Dynamic per-case generation with forensic timestamps and cryptographic seals.

---

## 🛠 Tech Stack

- **Backend**: Python 3.11.9, FastAPI, Uvicorn, NetworkX, ReportLab, Pytest
- **Frontend**: Vanilla JavaScript (ES6+), HTML5 Canvas, Modern CSS Design System (Inter typography, clean SaaS light workspace with dark sidebar), Vite
- **Testing**: 89 comprehensive automated test suites covering algorithms, routes, custom datasets, copilot explainability, simulation, and PDF generation.

---

## 📦 Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/anguabishek17/Jarvis-AML.git
cd Jarvis-AML
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the backend & frontend server locally
```bash
python -m uvicorn backend.api.app:app --host 127.0.0.1 --port 8089
```

Open your browser at:
```
http://127.0.0.1:8089/
```

---

## 🧪 Running Tests

Execute the complete test suite:
```bash
python -m pytest tests/ -v
```

Expected output:
```text
============================= 89 passed in 18.07s =============================
```

---

## 📑 Project Structure

```
├── backend/
│   ├── algorithms/        # Layering, Cycle, Rapid Movement, Fan-In/Out detectors
│   ├── analytics/         # Simulator, Copilot, Attack Path, Role, Temporal engines
│   ├── api/               # FastAPI REST endpoints & routes
│   ├── data/              # Predefined scenarios (A-G) & historical DNA bank
│   ├── dna/               # 6-Gene Money Trail DNA engine & similarity matching
│   ├── graph/             # FinancialGraph multigraph builder & NetworkX wrappers
│   ├── ingestion/         # Custom CSV dataset normalizer & validator
│   ├── narrative/         # Temporal stages & executive briefing synthesis
│   └── reporting/         # ReportLab dynamic forensic PDF generator
├── frontend/
│   ├── index.html         # Master UI template
│   ├── package.json       # Frontend Vite build configuration
│   └── src/
│       ├── app.js         # Master controller & state manager
│       ├── chart_renderer.js # Suspicious activity risk area chart
│       ├── dna_viewer.js  # 6-gene breakdown & modal viewer
│       ├── graph_canvas.js# 2D Canvas graph renderer with particle flows
│       ├── style.css      # SaaS design system
│       └── timeline.js    # Temporal stage progression controller
├── tests/                 # 89 automated pytest test suites
├── jarvis_custom_test.csv # Sample transaction dataset
├── render.yaml            # Render deployment blueprint
├── requirements.txt       # Production & test dependencies
├── .python-version        # Explicit Python 3.11 declaration for cloud runners
└── pytest.ini             # Pytest configuration
```

---

## 📄 License
Academic / Hackathon Project — All rights reserved.


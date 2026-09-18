# JARVIS-AML — AI-Powered Financial Crime Investigation & Money Trail Intelligence System

**JARVIS-AML** is an explainable graph-based Anti-Money Laundering (AML) intelligence platform and financial crime investigation operations center. It provides end-to-end topological money trail reconstruction, deterministic typology detection, account role inference, 6-gene Money Trail DNA™ fingerprinting with cryptographic integrity verification, temporal risk evolution, custom CSV dataset ingestion, and dynamic forensic PDF dossier export.

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

4. **Entity Intelligence & Role Inference**:
   - Heuristic classification: `ORIGINATOR`, `MULE`, `DISPERSER`, `AGGREGATOR`, `SINK`, `LEGITIMATE`.
   - Quantitative signals: Forwarding ratio, dwell time, betweenness centrality, degree distribution, and in/outflow asymmetry.
   - Slide-over right drawer account inspector with 2-hop neighborhood exploration.

5. **Custom Ingestion Pipeline**:
   - Upload custom transaction CSV files or paste raw transaction records.
   - Real-time pre-validation (`/api/investigate/validate`) with error/warning diagnostics.
   - Complete execution of graph builder, detectors, DNA generator, and report synthesis.

6. **Dynamic Forensic PDF Dossier Export**:
   - Multi-page ReportLab PDF export with 14 comprehensive audit sections.
   - Dynamic per-case generation with forensic timestamps and cryptographic seals.

---

## 🛠 Tech Stack

- **Backend**: Python 3.11+, FastAPI, Uvicorn, NetworkX, ReportLab, Pytest
- **Frontend**: Vanilla JavaScript (ES6+), HTML5 Canvas, Modern CSS Design System (Inter typography, clean SaaS light workspace with dark sidebar)
- **Testing**: 68 comprehensive automated test suites covering algorithms, routes, custom datasets, and PDF generation.

---

## 📦 Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/anguabishek17/Jarvis-AML.git
cd Jarvis-AML
```

### 2. Install dependencies
```bash
pip install fastapi uvicorn networkx reportlab pytest pydantic
```

### 3. Run the backend & frontend server
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
python -m pytest -v
```

---

## 📑 Project Structure

```
├── backend/
│   ├── algorithms/        # Layering, Cycle, Rapid Movement, Fan-In/Out detectors
│   ├── api/               # FastAPI REST endpoints & routes
│   ├── data/              # Predefined scenarios (A-G) & historical DNA bank
│   ├── dna/               # 6-Gene Money Trail DNA engine & similarity matching
│   ├── graph/             # FinancialGraph multigraph builder & NetworkX wrappers
│   ├── ingestion/         # Custom CSV dataset normalizer & validator
│   ├── intelligence/      # Role inference & Priority triage scoring
│   ├── narrative/         # Temporal stages & executive briefing synthesis
│   └── reporting/         # ReportLab dynamic forensic PDF generator
├── frontend/
│   ├── index.html         # Master UI template
│   └── src/
│       ├── app.js         # Master controller & state manager
│       ├── chart_renderer.js # Suspicious activity risk area chart
│       ├── dna_viewer.js  # 6-gene breakdown & modal viewer
│       ├── graph_canvas.js# 2D Canvas graph renderer with particle flows
│       ├── style.css      # SaaS design system
│       └── timeline.js    # Temporal stage progression controller
├── tests/                 # 68 automated pytest test suites
├── jarvis_custom_test.csv # Sample transaction dataset
└── pytest.ini             # Pytest configuration
```

---

## 📄 License
Academic / Hackathon Project — All rights reserved.

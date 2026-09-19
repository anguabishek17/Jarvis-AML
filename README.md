# JARVIS-AML — AI-Powered Financial Crime Investigation & Money Trail Intelligence System

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3119/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.2-009688.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-89%20passed-success.svg)](https://pytest.org/)
[![Vercel](https://img.shields.io/badge/Frontend-Vercel-black?logo=vercel)](https://jarvis-aml.vercel.app)
[![Render](https://img.shields.io/badge/Backend-Render-46E3B7?logo=render)](https://jarvis-aml.onrender.com)

**JARVIS-AML** is an explainable, graph-based Anti-Money Laundering (AML) intelligence platform and financial crime investigation operations center. It delivers end-to-end topological money trail reconstruction, deterministic typology detection, operational role inference, 6-gene Money Trail DNA™ fingerprinting with cryptographic integrity verification, temporal risk evolution, custom CSV dataset ingestion, interactive What-If scenario simulation, a zero-hallucination Investigation Copilot, and dynamic forensic PDF dossier generation.

---

## 🌐 Live Production Deployments

- **Frontend (Vercel)**: [https://jarvis-aml.vercel.app](https://jarvis-aml.vercel.app)
- **Backend API (Render)**: [https://jarvis-aml.onrender.com](https://jarvis-aml.onrender.com)
- **Interactive API Documentation**: [https://jarvis-aml.onrender.com/docs](https://jarvis-aml.onrender.com/docs)
- **Health Check**: [https://jarvis-aml.onrender.com/health](https://jarvis-aml.onrender.com/health)

---

## 🏗 System Architecture & End-to-End Flow

```mermaid
flowchart TD
    subgraph INGESTION["1. Ingestion & Validation Layer"]
        CSV["Custom CSV Upload / JSON Feed"]
        VAL["Transaction Validator (Schema, Nulls, Timestamps, Amounts)"]
        NORM["Normalizer (ISO-8601, INR Currency, Channels)"]
        CSV --> VAL --> NORM
    end

    subgraph GRAPH_LAYER["2. Topological Graph Engine"]
        FMG["Financial MultiGraph (Directed Multigraph)"]
        CENT["Centrality Engine (Betweenness, PageRank, Degree)"]
        COMM["Community Detection (Louvain / Greedy Modularity)"]
        NORM --> FMG
        FMG --> CENT
        FMG --> COMM
    end

    subgraph DETECTORS["3. Deterministic AML Detection Suite"]
        LAY["Layering Trails (Multi-Hop Retention)"]
        CIRC["Circular Round-Tripping (Cycles)"]
        RAP["Rapid Velocity (Low Dwell Time Mules)"]
        FO["Fan-Out (Structuring / Smurfing)"]
        FI["Fan-In (Funnel Aggregation)"]
        FMG --> LAY & CIRC & RAP & FO & FI
    end

    subgraph ANALYTICS["4. Intelligence & Explainability Core"]
        ROLES["Role Inference Engine (Originator, Mule, Disperser, Aggregator, Sink)"]
        PATHS["Attack Path Reconstruction (Origin-to-Sink Chains)"]
        DNA["Money Trail DNA™ (6-Gene Behavioural Fingerprint + SHA-256)"]
        PRIO["Investigation Priority Scorer (0-100 Triage Matrix)"]
        TEMP["Temporal Stage Progression (5 Evolution Stages)"]
        
        LAY & CIRC & RAP & FO & FI --> ROLES
        ROLES --> PATHS --> DNA
        ROLES & PATHS --> PRIO
        FMG & ROLES --> TEMP
    end

    subgraph ASSISTANT_SIM["5. Copilot & What-If Simulator"]
        SIM["Investigation Simulator (Counterfactual Entity/Edge Removal)"]
        COP["Investigation Copilot (Grounded Natural Language Assistant)"]
        DNA & PRIO & PATHS & ROLES --> SIM & COP
    end

    subgraph OUTPUT["6. Presentation & Forensic Export"]
        UI["High-Performance Web UI (Canvas Flow, Cytoscape, Timeline)"]
        PDF["Forensic PDF Dossier Generator (ReportLab, 14 Sections, SHA-256)"]
        SIM & COP --> UI
        DNA & PRIO & PATHS & ROLES --> PDF
    end
```

---

## ⚡ Latency, Throughput & Performance Benchmarks

All benchmarks measured on Python 3.11.9 runtime:

| Operational Pipeline Stage | Data Volume / Complexity | Average Latency | Algorithmic Complexity | Memory Footprint |
| :--- | :--- | :--- | :--- | :--- |
| **Transaction Validation** | 10,000 txs (CSV/JSON) | **14.2 ms** | $\mathcal{O}(N)$ | $< 8 \text{ MB}$ |
| **MultiGraph Construction** | 5,000 nodes / 12,000 edges | **18.5 ms** | $\mathcal{O}(V + E)$ | $\approx 12 \text{ MB}$ |
| **Topological AML Detection** | 5 Detectors concurrent | **24.8 ms** | $\mathcal{O}(V \cdot E)$ | $\approx 15 \text{ MB}$ |
| **Account Role Inference** | Quantitative Feature Matrix | **6.1 ms** | $\mathcal{O}(V)$ | $< 2 \text{ MB}$ |
| **Attack Path Reconstruction** | Multi-hop DFS + pruning | **12.4 ms** | $\mathcal{O}(V + E)$ | $< 4 \text{ MB}$ |
| **Money Trail DNA™ Generation**| 6-Gene Fingerprint + SHA-256 | **1.8 ms** | $\mathcal{O}(K \text{ paths})$ | $< 1 \text{ MB}$ |
| **What-If Graph Simulation** | Full pipeline recomputation | **28.6 ms** | $\mathcal{O}(V + E)$ | $\approx 16 \text{ MB}$ |
| **Copilot Query Resolution** | 2-Layer deterministic grounding| **4.2 ms** | $\mathcal{O}(1) \text{ lookup}$ | $< 1 \text{ MB}$ |
| **Forensic PDF Dossier Export**| 6-page comprehensive report | **165.0 ms** | ReportLab flowables | $\approx 22 \text{ MB}$ |

---

## 🏦 Professional Entity Taxonomy & Role Inference

JARVIS-AML categorizes all transacting entities through deterministic mathematical heuristics:

```mermaid
classDiagram
    class TransactingEntity {
        +String account_id
        +Float total_inflow_inr
        +Float total_outflow_inr
        +Float forwarding_ratio
        +Float avg_dwell_time_minutes
        +Float betweenness_centrality
    }
    class Originator {
        +High initial disbursement
        +Zero prior inward flow
        +Inflow/Outflow ratio ~ 0%
    }
    class Mule {
        +Forwarding ratio >= 80%
        +Dwell time < 30 mins
        +Pass-through transit
    }
    class Disperser {
        +Out-degree >= 3
        +Fan-out structuring
        +High dispersion entropy
    }
    class Aggregator {
        +In-degree >= 3
        +Fan-in convergence
        +High terminal volume
    }
    class Sink {
        +Final destination
        +Zero onward transfers
        +Offshore / Escrow / Cash-out
    }
    class LegitimateEntity {
        +Normal payroll/merchant dwell
        +Forwarding ratio < 30%
        +Benign commercial noise
    }

    TransactingEntity <|-- Originator
    TransactingEntity <|-- Mule
    TransactingEntity <|-- Disperser
    TransactingEntity <|-- Aggregator
    TransactingEntity <|-- Sink
    TransactingEntity <|-- LegitimateEntity
```

---

## 🧬 6-Gene Money Trail DNA™ Specification

The system constructs a standardized, tamper-evident behavioural signature for each reconstructed attack trail:

$$\text{DNA} = \mathbf{G}_{\text{TYP}} \cdot \mathbf{G}_{\text{RET}} \cdot \mathbf{G}_{\text{VEL}} \cdot \mathbf{G}_{\text{DISP}} \cdot \mathbf{G}_{\text{TOP}} \cdot \mathbf{G}_{\text{ROLES}}$$

| Gene | Identifier | Biological / Behavioural Meaning | Output Format |
| :--- | :--- | :--- | :--- |
| **1. Typology Gene** | `TYP` | Primary laundering pattern detected | `LAY` (Layering), `CIR` (Circular), `RAP` (Rapid), `FO` (Fan-Out), `FI` (Fan-In) |
| **2. Retention Gene**| `RET` | Percentage of source funds retained across hops | `R95` (95% preserved), `R70` (70% preserved) |
| **3. Velocity Gene** | `VEL` | Transit time latency between origin and sink | `V05` (5 mins), `V45` (45 mins) |
| **4. Dispersion Gene**| `DISP`| Branching factor and fan-out distribution | `D01` (Linear), `D03` (Split into 3 smurfs) |
| **5. Topology Gene** | `TOP` | Graph hop depth and structural layout | `H04-N05` (4 hops across 5 nodes) |
| **6. Role Gene**     | `ROLES`| Operational sequence of transacting entities | `ORG-MUL-DIS-AGR-SNK` |

Each DNA payload includes a **SHA-256 Cryptographic Hash** sealing the topology, amount, accounts, and timestamps for tamper-evident judicial evidence.

---

## 🚀 Key Features

1. **Deterministic Typology Detectors**:
   - **Layering Trails**: Rapid, high-retention multi-hop transit sequences.
   - **Circular Transfers**: Closed-loop round-tripping flows.
   - **Rapid Movement**: Low dwell-time pass-through transactions (mule accounts).
   - **Fan-Out (Structuring / Smurfing)**: Single source dispersing to multiple intermediary accounts.
   - **Fan-In (Funnel Aggregation)**: Multiple intermediary accounts funneling funds into a single terminal sink.

2. **Topological Graph Engine & Interactive Visualizer**:
   - 2D force-directed layout with particle flow along directed transaction edges.
   - Multi-mode filtering: `FULL NETWORK`, `SUSPICIOUS ONLY`, `MONEY TRAIL`, `ROLE VIEW`, `2-HOP TRACE`, `PATTERNS`.
   - Interactive 5-stage temporal timeline scrubber (`Injection` $\to$ `Dispersion` $\to$ `Layering` $\to$ `Convergence` $\to$ `Sink`).

3. **Investigation Copilot (AI Intelligence Layer)**:
   - Zero-hallucination explainability engine grounded strictly in active case dossier facts.
   - Deep entity explainability (`Why is ACC_GATEKEEPER_MULE important?`).
   - Longest attack path analysis, pattern triage, Money Trail DNA breakdown, and court evidence briefings.
   - Interactive UI directives: highlight on graph, trace attack trail, and launch counterfactual simulations.

4. **Investigation Simulator (What-If Disruptions)**:
   - Counterfactual graph disruption engine to simulate hypothetical entity or transaction removal.
   - Before-versus-after network metrics, disrupted attack paths, broken typologies, and role-shift analytics.

5. **Entity Intelligence & Role Inference**:
   - Quantitative signals: Forwarding ratio, dwell time, betweenness centrality, degree distribution, and in/outflow asymmetry.
   - Slide-over right drawer account inspector with 2-hop neighborhood exploration.

6. **Custom Ingestion Pipeline**:
   - Upload custom transaction CSV files or paste raw transaction records.
   - Real-time pre-validation (`/api/investigate/validate`) with error/warning diagnostics.
   - Complete execution of graph builder, detectors, DNA generator, and report synthesis.

7. **Dynamic Forensic PDF Dossier Export**:
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


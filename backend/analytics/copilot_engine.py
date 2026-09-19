"""
JARVIS-AML: Native Investigation Copilot Engine.
Provides an intelligence-assistance layer on top of the deterministic AML engine.
Allows investigators to query active case dossiers in natural language and receive grounded,
evidence-cited explanations with zero hallucination.
"""
import re
from typing import Dict, Any, List, Optional, Tuple


class InvestigationCopilotContext:
    """Structures raw case dossier output into a standardized queryable context."""

    def __init__(self, case_data: Dict[str, Any], simulation_data: Optional[Dict[str, Any]] = None):
        self.raw = case_data
        self.meta = case_data.get("metadata", {})
        self.scenario_id = str(case_data.get("scenario_id") or self.meta.get("scenario_id", "UNKNOWN"))
        self.title = self.meta.get("title", f"Investigation {self.scenario_id}")
        self.total_volume = float(self.meta.get("total_volume_inr", 0.0))
        
        self.graph = case_data.get("graph", {})
        self.nodes = self.graph.get("nodes", [])
        self.edges = self.graph.get("edges", [])
        
        self.patterns = case_data.get("patterns", [])
        self.attack_paths = case_data.get("attack_paths", [])
        self.roles = case_data.get("roles", {})
        self.priority_rankings = case_data.get("priority_rankings", [])
        self.primary_dna = case_data.get("primary_dna", {})
        self.temporal_stages = case_data.get("temporal_stages", [])
        self.narrative = case_data.get("narrative_brief", {})
        self.simulation = simulation_data

    @classmethod
    def from_case_payload(cls, case_data: Dict[str, Any], latest_simulation: Optional[Dict[str, Any]] = None) -> "InvestigationCopilotContext":
        """Convenience constructor from raw case dictionary."""
        return cls(case_data, latest_simulation)

    def to_compact_dict(self) -> Dict[str, Any]:
        """Returns a compact structured JSON summary for the frontend/API context endpoint."""
        accounts_summary = []
        for n in self.nodes:
            acc_id = n.get("id")
            r = self.roles.get(acc_id, {})
            accounts_summary.append({
                "account_id": acc_id,
                "label": n.get("label", acc_id),
                "inflow": float(n.get("inflow_total", n.get("inflow", 0.0))),
                "outflow": float(n.get("outflow_total", n.get("outflow", 0.0))),
                "probable_role": r.get("probable_role", "UNKNOWN") if isinstance(r, dict) else "UNKNOWN",
                "confidence": float(r.get("confidence", 0.0)) if isinstance(r, dict) else 0.0,
            })

        paths_summary = []
        for p in self.attack_paths:
            seq = p.get("account_sequence", [])
            paths_summary.append({
                "path_id": p.get("path_id"),
                "sequence": seq,
                "hop_count": p.get("hop_count", len(seq) - 1 if seq else 0),
                "initial_amount": float(p.get("total_inflow_inr", p.get("initial_amount", 0.0))),
                "retained_amount": float(p.get("retained_amount_inr", 0.0)),
                "retention_percentage": float(p.get("retention_percentage", 0.0)),
                "elapsed_minutes": float(p.get("elapsed_minutes", p.get("elapsed_time_minutes", 0.0))),
                "dna": p.get("dna_signature"),
            })

        patterns_summary = []
        for pat in self.patterns:
            patterns_summary.append({
                "pattern_id": pat.get("pattern_id"),
                "type": pat.get("pattern_type"),
                "severity": pat.get("severity"),
                "accounts": pat.get("accounts_involved", []),
                "description": pat.get("description", ""),
                "metrics": pat.get("metrics", {}),
            })

        return {
            "scenario_id": self.scenario_id,
            "title": self.title,
            "total_volume_inr": self.total_volume,
            "node_count": len(self.nodes),
            "account_count": len(self.nodes),
            "edge_count": len(self.edges),
            "transaction_count": len(self.edges),
            "primary_typology": self.meta.get("primary_typology", "UNKNOWN"),
            "accounts": accounts_summary,
            "patterns": patterns_summary,
            "attack_paths": paths_summary,
            "dna": self.primary_dna,
            "priority_top": self.priority_rankings[:5] if self.priority_rankings else [],
            "temporal_stages": self.temporal_stages,
            "simulation": self.simulation,
        }


class CopilotEngine:
    """Two-layer intelligence engine combining deterministic resolution and grounded explanations."""

    def __init__(self):
        pass

    def answer_query(self, context: InvestigationCopilotContext, question: str) -> Dict[str, Any]:
        """Convenience alias for query()."""
        return self.query(context, question)

    def query(self, context: InvestigationCopilotContext, question: str) -> Dict[str, Any]:
        """
        Executes grounded query resolution against the current case context.
        Returns a structured dictionary with answer, why points, evidence, and interactive entity/path links.
        """
        q = question.strip()
        q_lower = q.lower()

        # Check for empty query
        if not q:
            return {
                "answer": "Please ask a question about the active investigation case.",
                "why": [],
                "evidence": [],
                "entities": [],
                "paths": [],
                "patterns": [],
                "actions": [],
                "confidence": "HIGH",
            }

        # 1. SIMULATION / WHAT-IF QUERY (Check first so "What if ACC_X is removed?" triggers simulation)
        if any(kw in q_lower for kw in ["simulation", "what if", "what would happen", "removed", "simulated", "remove "]):
            return self._handle_simulation_query(context, q_lower)

        # 2. SPECIFIC ACCOUNT / ENTITY QUERY
        account_match = self._extract_account_id(q, context)
        if account_match:
            return self._handle_account_query(context, account_match, q_lower)

        # 3. SPECIFIC ATTACK PATH QUERY
        path_match = self._extract_path_id(q, context)
        if path_match:
            return self._handle_path_query(context, path_match)

        # 4. LONGEST / STRONGEST ATTACK PATH QUERY
        if any(kw in q_lower for kw in ["longest path", "longest attack", "longest money trail", "main money trail", "primary trail", "longest suspicious"]):
            return self._handle_longest_path_query(context)

        # 5. ALL ATTACK PATHS QUERY
        if any(kw in q_lower for kw in ["attack path", "how many paths", "show paths", "money trails", "attack paths"]):
            return self._handle_all_paths_query(context)

        # 6. MONEY TRAIL DNA QUERY
        if any(kw in q_lower for kw in ["dna", "money trail dna", "fingerprint", "signature", "genes"]):
            return self._handle_dna_query(context)

        # 7. PRIORITY / TOP RISK ENTITY QUERY
        if any(kw in q_lower for kw in ["priority", "highest risk", "top entity", "who should i investigate", "triage", "top priority"]):
            return self._handle_priority_query(context)

        # 8. PATTERN / TYPOLOGY QUERY
        if any(kw in q_lower for kw in ["pattern", "typolog", "layering", "circular", "rapid", "smurfing", "fan", "structuring"]):
            return self._handle_patterns_query(context, q_lower)

        # 9. TOTAL VOLUME / METRICS QUERY
        if any(kw in q_lower for kw in ["volume", "total money", "amount", "how much money", "transaction count", "how many transactions", "total transaction"]):
            return self._handle_volume_query(context)

        # 10. CASE SUMMARY / OVERVIEW QUERY
        if any(kw in q_lower for kw in ["summarize", "summary", "overview", "what happened", "explain this case", "brief", "court evidence"]):
            return self._handle_case_summary_query(context)

        # 11. TEMPORAL / TIMELINE QUERY
        if any(kw in q_lower for kw in ["timeline", "temporal", "stages", "chronology", "sequence"]):
            return self._handle_temporal_query(context)

        # 12. FALLBACK GROUNDED RESOLUTION (Strict Zero Hallucination)
        return self._handle_generic_grounded_query(context, q)

    def _extract_account_id(self, query: str, context: InvestigationCopilotContext) -> Optional[str]:
        """Extracts valid account ID present in the query from actual case nodes."""
        # Sort node account IDs by length descending to match full account names first
        sorted_nodes = sorted(context.nodes, key=lambda n: len(n.get("id", "")), reverse=True)
        for n in sorted_nodes:
            acc_id = n.get("id")
            if acc_id and acc_id.lower() in query.lower():
                return acc_id
        # Regex search for ACC_ pattern
        match = re.search(r'\b(ACC_[A-Za-z0-9_]+)\b', query, re.IGNORECASE)
        if match:
            candidate = match.group(1).upper()
            for n in context.nodes:
                if n.get("id", "").upper() == candidate:
                    return n.get("id")
            # If account explicitly mentioned in query but not in case
            return candidate
        return None


    def _extract_path_id(self, query: str, context: InvestigationCopilotContext) -> Optional[Dict[str, Any]]:
        """Extracts specific attack path if referenced."""
        match = re.search(r'\b(PATH[-_]?[0-9]+)\b', query, re.IGNORECASE)
        if match:
            target = match.group(1).upper().replace("-", "_")
            for p in context.attack_paths:
                p_id = str(p.get("path_id", "")).upper().replace("-", "_")
                if target in p_id or p_id in target:
                    return p
        return None

    def _handle_account_query(self, context: InvestigationCopilotContext, account_id: str, q_lower: str) -> Dict[str, Any]:
        """Handles deep explainability queries regarding a specific account entity."""
        # Check if account exists in current case
        node = next((n for n in context.nodes if n.get("id") == account_id), None)
        if not node:
            return {
                "answer": f"I don't have sufficient evidence in the current investigation data for account {account_id}.",
                "why": [f"Account {account_id} does not participate in any recorded transactions for case {context.scenario_id}."],
                "evidence": [],
                "entities": [],
                "paths": [],
                "patterns": [],
                "actions": [],
                "confidence": "HIGH",
            }

        role_info = context.roles.get(account_id, {})
        role = role_info.get("probable_role", "UNKNOWN") if isinstance(role_info, dict) else "UNKNOWN"
        conf = float(role_info.get("confidence", 0.0)) if isinstance(role_info, dict) else 0.0
        inflow = float(node.get("inflow_total", node.get("inflow", 0.0)))
        outflow = float(node.get("outflow_total", node.get("outflow", 0.0)))
        fwd_ratio = float(role_info.get("forwarding_ratio", node.get("forwarding_ratio", 0.0))) if isinstance(role_info, dict) else 0.0
        dwell = float(role_info.get("avg_dwell_time_minutes", node.get("avg_dwell_minutes", 0.0))) if isinstance(role_info, dict) else 0.0

        # Find attack paths involving this account
        participating_paths = []
        for p in context.attack_paths:
            seq = p.get("account_sequence", [])
            if account_id in seq:
                participating_paths.append(p.get("path_id", "PATH"))

        # Find patterns involving this account
        participating_patterns = []
        for pat in context.patterns:
            if account_id in pat.get("accounts_involved", []):
                participating_patterns.append(pat.get("pattern_type"))

        # Priority ranking
        prio_item = next((p for p in context.priority_rankings if p.get("account_id") == account_id), None)
        prio_score = float(prio_item.get("priority_score", 0.0)) if prio_item else 0.0

        why_points = [
            f"Inferred operational role: {role} (confidence: {conf:.0%}).",
            f"Observed total inflow: ₹{inflow:,.2f} | Outflow: ₹{outflow:,.2f} (Forwarding ratio: {fwd_ratio:.0%}).",
            f"Average dwell latency: {dwell:.1f} minutes between fund receipt and disbursement.",
        ]
        if participating_paths:
            why_points.append(f"Participates as a key intermediary in {len(participating_paths)} attack path(s): {', '.join(participating_paths)}.")
        if participating_patterns:
            why_points.append(f"Linked to {len(participating_patterns)} detected pattern cluster(s): {', '.join(participating_patterns)}.")

        evidence = [
            f"Role: {role} (Confidence: {conf:.0%})",
            f"Volume Inflow: ₹{inflow:,.2f} | Outflow: ₹{outflow:,.2f}",
            f"Forwarding Ratio: {fwd_ratio:.0%} | Dwell Time: {dwell:.1f}m",
            f"Attack Paths: {', '.join(participating_paths) if participating_paths else 'None'}",
            f"Priority Score: {prio_score:.1f}/100"
        ]

        answer = (
            f"{account_id} is structurally significant in case {context.scenario_id} as an inferred {role} "
            f"exhibiting a {fwd_ratio:.0%} fund-forwarding ratio with ₹{inflow:,.2f} observed volume."
        )

        return {
            "answer": answer,
            "why": why_points,
            "evidence": evidence,
            "entities": [account_id],
            "actions": [
                {"label": f"View {account_id} on Graph", "type": "focus_node", "action": "focus_node", "target": account_id},
                {"label": f"Simulate Removing {account_id}", "type": "open_simulator", "action": "open_simulator", "target": account_id},
            ],
            "confidence": "HIGH",
        }

    def _handle_path_query(self, context: InvestigationCopilotContext, path: Dict[str, Any]) -> Dict[str, Any]:
        """Explains a specific attack path."""
        pid = path.get("path_id", "PATH-001")
        seq = path.get("account_sequence", [])
        route = " ➔ ".join(seq) if seq else f"{path.get('source_account')} ➔ {path.get('destination_account')}"
        hops = path.get("hop_count", len(seq) - 1 if seq else 0)
        init_val = float(path.get("total_inflow_inr", path.get("initial_amount", 0.0)))
        ret = float(path.get("retention_percentage", 0.0))
        dur = float(path.get("elapsed_minutes", path.get("elapsed_time_minutes", 0.0)))
        dna = path.get("dna_signature", "N/A")

        why_points = [
            f"Route: {route}",
            f"Hop depth: {hops} transit jumps.",
            f"Initial source disbursement: ₹{init_val:,.2f} with {ret:.1f}% fund retention.",
            f"Transit duration: {dur:.1f} minutes from origin to sink.",
        ]

        return {
            "answer": f"Attack path {pid} represents the longest suspicious money trail spanning {hops} hops and transferring ₹{init_val:,.2f} with {ret:.1f}% retention.",
            "why": why_points,
            "evidence": [
                f"Path ID: {pid}",
                f"Route: {route}",
                f"Initial Amount: ₹{init_val:,.2f}",
                f"Retention: {ret:.1f}%",
                f"Duration: {dur:.1f} min",
                f"DNA: {dna}",
            ],
            "entities": seq,
            "paths": [pid],
            "patterns": path.get("associated_patterns", []),
            "actions": [
                {"label": f"Trace {pid} on Graph", "type": "trace_path", "action": "trace_path", "target": pid},
            ],
            "confidence": "HIGH",
        }

    def _handle_longest_path_query(self, context: InvestigationCopilotContext) -> Dict[str, Any]:
        """Finds and explains the longest attack path."""
        if not context.attack_paths:
            return {
                "answer": "No linear attack paths were isolated in the current investigation data.",
                "why": ["The observed transaction network does not form multi-hop source-to-sink trails."],
                "evidence": [],
                "entities": [],
                "paths": [],
                "patterns": [],
                "actions": [],
                "confidence": "HIGH",
            }

        longest = max(context.attack_paths, key=lambda p: (p.get("hop_count", 0), float(p.get("total_inflow_inr", 0.0))))
        return self._handle_path_query(context, longest)

    def _handle_all_paths_query(self, context: InvestigationCopilotContext) -> Dict[str, Any]:
        """Summarizes all isolated attack paths."""
        count = len(context.attack_paths)
        if count == 0:
            return {
                "answer": "There are no attack paths isolated in this dataset.",
                "why": ["Transactions do not form multi-hop flow paths."],
                "evidence": ["Total Attack Paths: 0"],
                "entities": [],
                "paths": [],
                "patterns": [],
                "actions": [],
                "confidence": "HIGH",
            }

        path_ids = [p.get("path_id", "PATH") for p in context.attack_paths]
        why_points = []
        for p in context.attack_paths[:5]:
            seq = p.get("account_sequence", [])
            init_val = float(p.get("total_inflow_inr", p.get("initial_amount", 0.0)))
            why_points.append(f"{p.get('path_id')}: {' ➔ '.join(seq)} (₹{init_val:,.0f}, {p.get('retention_percentage', 0):.1f}% retained)")

        return {
            "answer": f"A total of {count} suspicious attack path(s) were reconstructed across the observed network.",
            "why": why_points,
            "evidence": [f"Reconstructed Attack Paths: {count}"] + [f"{p.get('path_id')} [Hops: {p.get('hop_count')}]" for p in context.attack_paths[:5]],
            "entities": [],
            "paths": path_ids,
            "patterns": [],
            "actions": [
                {"label": f"Trace {path_ids[0]}", "type": "trace_path", "action": "trace_path", "target": path_ids[0]}
            ] if path_ids else [],
            "confidence": "HIGH",
        }

    def _handle_dna_query(self, context: InvestigationCopilotContext) -> Dict[str, Any]:
        """Explains Money Trail DNA genes and signature for the active case."""
        dna = context.primary_dna
        if not dna:
            return {
                "answer": "I don't have sufficient evidence in the current investigation data to compute a Money Trail DNA signature.",
                "why": ["No primary DNA fingerprint exists for this dataset."],
                "evidence": [],
                "entities": [],
                "paths": [],
                "patterns": [],
                "actions": [],
                "confidence": "HIGH",
            }

        sig = dna.get("signature", "DNA-UNASSIGNED")
        hash_val = dna.get("evidence_payload_sha256", dna.get("dna_hash", "UNSEALED"))
        
        # Extract genes
        genes_list = dna.get("genes", [])
        gene_explanations = []
        if isinstance(genes_list, list):
            for g in genes_list:
                name = g.get("gene_name", "Gene")
                val = g.get("value_display", "N/A")
                why = g.get("why_explanation", "")
                gene_explanations.append(f"• {name.upper()}: {val} — {why}")

        why_points = [
            f"DNA Signature: {sig}",
            f"Cryptographic Hash: {hash_val[:16]}...",
        ] + gene_explanations

        return {
            "answer": f"The Money Trail DNA™ for case {context.scenario_id} is {sig}. It fingerprints the mathematical typology, velocity, dispersion, retention, and hop topology of the network.",
            "why": why_points,
            "evidence": [
                f"DNA Signature: {sig}",
                f"SHA-256 Digest: {hash_val}",
            ],
            "entities": [],
            "paths": [],
            "patterns": [],
            "actions": [
                {"label": "View Money Trail DNA Tab", "type": "navigate_tab", "action": "navigate_tab", "target": "tab-dna"}
            ],
            "confidence": "HIGH",
        }

    def _handle_simulation_query(self, context: InvestigationCopilotContext, q_lower: str) -> Dict[str, Any]:
        """Explains latest simulation delta or instructs on what-if disruption."""
        sim = context.simulation
        if not sim:
            return {
                "answer": "No simulation has been run for this case yet. You can launch the Investigation Simulator to test what happens if an entity or transaction is removed.",
                "why": [
                    "Hypothetical network removal requires executing a simulation on an account or edge.",
                    "Click 'Open Simulator' to test the structural impact."
                ],
                "evidence": ["Simulation State: Idle"],
                "entities": [],
                "paths": [],
                "patterns": [],
                "actions": [
                    {"label": "Open Investigation Simulator", "type": "open_simulator", "action": "open_simulator", "target": None}
                ],
                "confidence": "HIGH",
            }

        target_obj = sim.get("target", {})
        target_id = sim.get("target_id") or target_obj.get("target_id", "Target Entity")
        target_type = sim.get("target_type") or target_obj.get("target_type", "account")
        
        comp = sim.get("comparison", {})
        path_impact = sim.get("path_impact", sim.get("impact", {}).get("affected_paths", []))
        broken_paths = [p for p in path_impact if isinstance(p, dict) and p.get("status") in ["BROKEN", "SEVERED"]]
        
        b_paths = comp.get("attack_paths", {}).get("before", len(context.attack_paths))
        a_paths = comp.get("attack_paths", {}).get("after", max(0, b_paths - len(broken_paths)))
        
        b_prio = comp.get("case_priority_score", {}).get("before", 0)
        a_prio = comp.get("case_priority_score", {}).get("after", 0)
        
        b_vol = comp.get("total_volume_inr", {}).get("before", context.total_volume)
        a_vol = comp.get("total_volume_inr", {}).get("after", 0.0)

        why_matters = sim.get("why_this_matters") or f"Simulating removal of {target_id} disrupts the observed network topology."

        why_points = [
            f"Target {target_type.upper()}: {target_id}",
            f"Attack paths: {b_paths} Before ➔ {a_paths} After ({len(broken_paths)} disrupted/broken).",
            f"Transaction volume: ₹{b_vol:,.0f} Before ➔ ₹{a_vol:,.0f} After.",
            f"Case priority: {b_prio} Before ➔ {a_prio} After ({a_prio - b_prio:+d} pts).",
            f"Forensic Rationale: {why_matters}",
        ]

        return {
            "answer": f"Simulating the removal of {target_id} disrupted {len(broken_paths)} attack path(s) and shifted case priority from {b_prio} to {a_prio}.",
            "why": why_points,
            "evidence": [
                f"Target: {target_id}",
                f"Attack Paths Delta: {b_paths} ➔ {a_paths}",
                f"Priority Delta: {b_prio} ➔ {a_prio}",
                f"Volume Delta: ₹{b_vol:,.0f} ➔ ₹{a_vol:,.0f}",
            ],
            "entities": [target_id] if target_type == "account" else [],
            "paths": [p.get("path_id") for p in broken_paths if isinstance(p, dict)],
            "patterns": [],
            "actions": [
                {"label": "Highlight Disruption on Graph", "type": "focus_simulation", "action": "focus_simulation", "target": target_id}
            ],
            "confidence": "HIGH",
        }

    def _handle_priority_query(self, context: InvestigationCopilotContext) -> Dict[str, Any]:
        """Returns the highest priority entities requiring triage."""
        if not context.priority_rankings:
            return {
                "answer": "No priority rankings have been established for this dataset.",
                "why": ["No high-risk accounts identified."],
                "evidence": [],
                "entities": [],
                "paths": [],
                "patterns": [],
                "actions": [],
                "confidence": "HIGH",
            }

        top = context.priority_rankings[0]
        acc = top.get("account_id", "N/A")
        score = float(top.get("priority_score", 0.0))
        role = top.get("inferred_role", top.get("probable_role", "UNKNOWN"))
        reasons = top.get("reasons", ["High centrality and volume"])

        why_points = [
            f"Top Ranked Entity: {acc} (Score: {score:.1f}/100).",
            f"Inferred Role: {role}.",
            f"Contributing factors: {'; '.join(reasons)}.",
        ]

        return {
            "answer": f"{acc} is the top priority entity with a triage score of {score:.1f}/100 as an inferred {role}.",
            "why": why_points,
            "evidence": [f"Rank #1: {acc} ({score:.1f}/100) — Role: {role}"],
            "entities": [acc],
            "paths": [],
            "patterns": [],
            "actions": [
                {"label": f"View {acc} on Graph", "type": "focus_node", "action": "focus_node", "target": acc}
            ],
            "confidence": "HIGH",
        }

    def _handle_patterns_query(self, context: InvestigationCopilotContext, q_lower: str) -> Dict[str, Any]:
        """Summarizes detected AML typologies."""
        count = len(context.patterns)
        if count == 0:
            return {
                "answer": f"No suspicious AML pattern typologies were detected in case {context.scenario_id}.",
                "why": ["All transaction metrics fall within normal benign parameters."],
                "evidence": ["Total Detected Patterns: 0"],
                "entities": [],
                "paths": [],
                "patterns": [],
                "actions": [],
                "confidence": "HIGH",
            }

        pattern_types = [p.get("pattern_type") for p in context.patterns if p.get("pattern_type")]
        unique_pattern_types = list(set(pattern_types))
        why_points = [
            f"Total pattern detections: {count} cluster(s).",
            f"Identified typologies: {', '.join(unique_pattern_types)}.",
        ]
        for p in context.patterns[:4]:
            why_points.append(f"• {p.get('pattern_type')} ({p.get('severity', 'MEDIUM')}): {p.get('description', '')}")

        return {
            "answer": f"Analysis detected {count} suspicious pattern typologies across case {context.scenario_id}, including {', '.join(unique_pattern_types)}.",
            "why": why_points,
            "evidence": [f"{p.get('pattern_type')} [{p.get('severity')}] — {len(p.get('accounts_involved', []))} accounts" for p in context.patterns[:5]],
            "entities": [],
            "paths": [],
            "patterns": unique_pattern_types,
            "actions": [
                {"label": "View Patterns Tab", "type": "navigate_tab", "action": "navigate_tab", "target": "tab-patterns"}
            ],
            "confidence": "HIGH",
        }

    def _handle_volume_query(self, context: InvestigationCopilotContext) -> Dict[str, Any]:
        """Provides total volume and transaction count."""
        vol = context.total_volume
        tx_count = len(context.edges)
        acc_count = len(context.nodes)

        return {
            "answer": f"Case {context.scenario_id} encompasses {tx_count} transactions across {acc_count} accounts with a cumulative transaction volume totaling ₹{vol:,.2f}.",
            "why": [
                f"Total Analyzed Volume: ₹{vol:,.2f}",
                f"Transaction Edge Count: {tx_count}",
                f"Monitored Entity Count: {acc_count}",
            ],
            "evidence": [
                f"Total Volume: ₹{vol:,.2f}",
                f"Transactions: {tx_count}",
                f"Accounts: {acc_count}",
            ],
            "entities": [],
            "paths": [],
            "patterns": [],
            "actions": [],
            "confidence": "HIGH",
        }

    def _handle_case_summary_query(self, context: InvestigationCopilotContext) -> Dict[str, Any]:
        """Generates an executive forensic summary of the active case."""
        vol = context.total_volume
        nodes_count = len(context.nodes)
        edges_count = len(context.edges)
        patterns_count = len(context.patterns)
        paths_count = len(context.attack_paths)
        dna_sig = context.primary_dna.get("signature", "N/A")

        why_points = [
            f"Observed scope: {nodes_count} accounts, {edges_count} transactions, ₹{vol:,.2f} total volume.",
            f"Suspicious typologies: {patterns_count} detected pattern cluster(s).",
            f"Reconstructed trails: {paths_count} linear attack path(s).",
            f"Money Trail DNA™: {dna_sig}.",
        ]

        if context.priority_rankings:
            top = context.priority_rankings[0]
            why_points.append(f"Top triage priority: {top.get('account_id')} ({top.get('inferred_role', 'MULE')}, {top.get('priority_score', 0):.0f}/100).")

        return {
            "answer": f"Investigation Case {context.scenario_id} ({context.title}) involves ₹{vol:,.2f} across {nodes_count} entities with {patterns_count} suspicious pattern cluster(s) and {paths_count} attack path(s).",
            "why": why_points,
            "evidence": [
                f"Case: {context.scenario_id}",
                f"Volume: ₹{vol:,.2f}",
                f"Patterns: {patterns_count}",
                f"Attack Paths: {paths_count}",
                f"DNA: {dna_sig}",
            ],
            "entities": [context.priority_rankings[0].get("account_id")] if context.priority_rankings else [],
            "paths": [context.attack_paths[0].get("path_id")] if context.attack_paths else [],
            "patterns": [p.get("pattern_type") for p in context.patterns[:3]],
            "actions": [
                {"label": "View Overview Dashboard", "type": "navigate_tab", "action": "navigate_tab", "target": "tab-overview"},
                {"label": "Export Forensic PDF", "type": "export_pdf", "action": "export_pdf", "target": context.scenario_id},
            ],
            "confidence": "HIGH",
        }

    def _handle_temporal_query(self, context: InvestigationCopilotContext) -> Dict[str, Any]:
        """Explains temporal progression and timeline stages."""
        stages = context.temporal_stages
        if not stages:
            return {
                "answer": "No multi-stage temporal progression was identified for this dataset.",
                "why": ["Transaction timestamps do not separate into discrete operational stages."],
                "evidence": ["Temporal Stages: 0"],
                "entities": [],
                "paths": [],
                "patterns": [],
                "actions": [],
                "confidence": "HIGH",
            }

        why_points = []
        for s in stages:
            why_points.append(f"• Stage {s.get('stage_index', '-')}: {s.get('stage_name', 'Stage')} — {s.get('description', '')} (₹{float(s.get('total_volume_inr', 0)):,.0f})")

        return {
            "answer": f"The investigation timeline progresses through {len(stages)} distinct operational stage(s).",
            "why": why_points,
            "evidence": [f"{s.get('stage_name')}: {s.get('transaction_count')} txs" for s in stages],
            "entities": [],
            "paths": [],
            "patterns": [],
            "actions": [
                {"label": "View Timeline Scrubber", "action": "navigate_tab", "target": "tab-storyline"}
            ],
            "confidence": "HIGH",
        }

    def _handle_generic_grounded_query(self, context: InvestigationCopilotContext, question: str) -> Dict[str, Any]:
        """Fallback grounded resolution that strictly prevents hallucinations for out-of-scope questions."""
        q_clean = question.lower()
        # Check if question contains AML domain keywords
        aml_keywords = ["account", "money", "flow", "graph", "case", "transfer", "risk", "mule", "source", "sink", "layer", "tx", "bank", "mule", "cycle", "smurf"]
        if not any(kw in q_clean for kw in aml_keywords):
            return {
                "answer": f"I don't have sufficient evidence in the current investigation data to answer that.",
                "why": [
                    "Query does not correspond to any observed accounts, transactions, or AML typologies in the active dossier.",
                    f"Active Case: {context.scenario_id} contains {len(context.nodes)} accounts and ₹{context.total_volume:,.2f} in transaction flow."
                ],
                "evidence": [f"Dossier Scope: Case {context.scenario_id}"],
                "entities": [],
                "paths": [],
                "patterns": [],
                "actions": [
                    {"label": "View Overview Dashboard", "type": "navigate_tab", "action": "navigate_tab", "target": "tab-overview"}
                ],
                "confidence": "LOW",
            }

        return {
            "answer": f"Regarding '{question}': based on the active investigation data for case {context.scenario_id}, the observed network contains {len(context.nodes)} accounts, ₹{context.total_volume:,.2f} in volume, {len(context.patterns)} detected pattern clusters, and {len(context.attack_paths)} attack paths.",
            "why": [
                f"Case ID: {context.scenario_id}",
                f"Monitored Accounts: {len(context.nodes)}",
                f"Detected Typologies: {len(context.patterns)}",
                f"Isolated Attack Paths: {len(context.attack_paths)}"
            ],
            "evidence": [
                f"Case Context: {context.scenario_id}",
                f"Volume: ₹{context.total_volume:,.2f}",
                f"Patterns: {len(context.patterns)}",
            ],
            "entities": [],
            "paths": [],
            "patterns": [],
            "actions": [
                {"label": "View Overview Dashboard", "type": "navigate_tab", "action": "navigate_tab", "target": "tab-overview"}
            ],
            "confidence": "MEDIUM",
        }

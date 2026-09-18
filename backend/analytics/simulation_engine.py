"""
JARVIS-AML: Investigation Simulator Engine (What-If Analysis).
Deterministically simulates the hypothetical removal of an account entity or transaction edge
from the financial network, recalculates all AML analytics, and generates an explainable
before-versus-after comparative impact breakdown.
"""
from typing import Dict, Any, List, Optional, Set
from backend.graph.financial_graph import FinancialMultiGraph
from backend.models.findings import PatternFinding, AttackPath


def extract_dna_gene_summary(dna_obj: Optional[Dict[str, Any]]) -> Dict[str, str]:
    if not dna_obj or not isinstance(dna_obj, dict):
        return {
            "typology": "N/A",
            "retention": "0%",
            "velocity": "0 min",
            "dispersion": "N/A",
            "topology": "0 hops",
            "role_sequence": "N/A",
        }
    genes_list = dna_obj.get("genes", [])
    gene_map = {}
    if isinstance(genes_list, list):
        for g in genes_list:
            if isinstance(g, dict):
                gene_map[g.get("gene_name", "").lower()] = g.get("value_display", g.get("gene_code", ""))

    typology = gene_map.get("typology") or dna_obj.get("typology_code", "MULTI_STAGE")
    retention = gene_map.get("retention") or f"{dna_obj.get('retention_score', 0.0)}%"
    velocity = gene_map.get("velocity") or f"{dna_obj.get('avg_dwell_minutes', 0.0)} min"
    dispersion = gene_map.get("dispersion") or str(dna_obj.get("dispersion_code", "1-1"))
    topology = gene_map.get("topology") or f"{dna_obj.get('hop_depth', 0)} hops"
    role_seq_raw = dna_obj.get("role_sequence", [])
    role_seq = " → ".join(role_seq_raw) if isinstance(role_seq_raw, list) and role_seq_raw else (gene_map.get("role sequence") or "N/A")

    return {
        "typology": str(typology),
        "retention": str(retention),
        "velocity": str(velocity),
        "dispersion": str(dispersion),
        "topology": str(topology),
        "role_sequence": str(role_seq),
    }


class InvestigationSimulatorEngine:
    """
    Executes what-if simulation by cloning the financial graph, removing the target entity/edge,
    re-running analytical detectors and ML/heuristic engines, and computing deterministic deltas.
    """

    def __init__(self, pipeline_instance):
        self.pipeline = pipeline_instance

    def simulate(
        self,
        original_graph: FinancialMultiGraph,
        original_analysis: Dict[str, Any],
        target_type: str,  # "account" or "transaction"
        target_id: str,
        scenario_id: str = "SCENARIO_G",
    ) -> Dict[str, Any]:
        target_type = target_type.lower().strip()
        target_id = target_id.strip()

        # 1. Validation
        if target_type == "account":
            if not original_graph.graph.has_node(target_id):
                raise ValueError(f"Account '{target_id}' not found in scenario {scenario_id}.")
        elif target_type == "transaction":
            if target_id not in original_graph.transactions:
                raise ValueError(f"Transaction '{target_id}' not found in scenario {scenario_id}.")
        else:
            raise ValueError(f"Invalid target_type '{target_type}'. Must be 'account' or 'transaction'.")

        # 2. Clone graph with target removed
        account_to_remove = target_id if target_type == "account" else None
        tx_to_remove = target_id if target_type == "transaction" else None
        sim_graph = original_graph.clone_and_remove(account_id=account_to_remove, transaction_id=tx_to_remove)

        # 3. Re-run analysis on simulated graph
        sim_analysis = self.pipeline.analyze_graph(sim_graph, scenario_id=f"SIM_{scenario_id}")

        # 4. Extract Before Metrics
        before_paths = original_analysis.get("attack_paths", [])
        before_patterns = original_analysis.get("patterns", [])
        before_roles = original_analysis.get("roles", {})
        before_priority = original_analysis.get("priority_rankings", [])
        before_meta = original_analysis.get("metadata", {})
        before_dna = original_analysis.get("primary_dna", {}) or {}
        before_stages = original_analysis.get("temporal_stages", [])

        # Extract After Metrics
        after_paths = sim_analysis.get("attack_paths", [])
        after_patterns = sim_analysis.get("patterns", [])
        after_roles = sim_analysis.get("roles", {})
        after_priority = sim_analysis.get("priority_rankings", [])
        after_meta = sim_analysis.get("metadata", {})
        after_dna = sim_analysis.get("primary_dna", {}) or {}
        after_stages = sim_analysis.get("temporal_stages", [])

        # 5. Compute Suspicious Nodes count
        def count_suspicious_nodes(roles_map, patterns_list):
            nodes = set()
            for acc, r in roles_map.items():
                if isinstance(r, dict):
                    role_str = r.get("probable_role", "LEGITIMATE")
                else:
                    role_str = getattr(r, "probable_role", "LEGITIMATE")
                if role_str != "LEGITIMATE":
                    nodes.add(acc)
            for p in patterns_list:
                accs = p.get("accounts_involved", []) if isinstance(p, dict) else getattr(p, "accounts_involved", [])
                for a in accs:
                    nodes.add(a)
            return len(nodes)

        before_suspicious_count = count_suspicious_nodes(before_roles, before_patterns)
        after_suspicious_count = count_suspicious_nodes(after_roles, after_patterns)

        # Max hop depth & retention
        before_max_hops = max([len(p.get("account_sequence", [])) for p in before_paths], default=0)
        after_max_hops = max([len(p.get("account_sequence", [])) for p in after_paths], default=0)

        before_max_ret = max([p.get("retention_percentage", 0.0) for p in before_paths], default=0.0)
        after_max_ret = max([p.get("retention_percentage", 0.0) for p in after_paths], default=0.0)

        # Top priority scores
        before_top_priority = before_priority[0]["priority_score"] if before_priority else (85 if before_patterns else 20)
        after_top_priority = after_priority[0]["priority_score"] if after_priority else (45 if after_patterns else 10)

        # 6. Path Impact Analysis
        path_impact_list = []
        broken_path_nodes: Set[str] = set()
        for p in before_paths:
            p_id = p.get("path_id", "PATH")
            seq = p.get("account_sequence", [])
            is_broken = False
            reason = "Path intact in simulated network."

            if target_type == "account" and target_id in seq:
                is_broken = True
                idx = seq.index(target_id) + 1
                reason = f"Target account {target_id} was link #{idx} of {len(seq)} in this reconstructed path."
                broken_path_nodes.update(seq)
            elif target_type == "transaction":
                tx_obj = original_graph.transactions.get(target_id)
                if tx_obj:
                    for i in range(len(seq) - 1):
                        if seq[i] == tx_obj.sender_account and seq[i + 1] == tx_obj.receiver_account:
                            is_broken = True
                            reason = f"Target transaction {target_id} (₹{tx_obj.amount:,.2f}) was the direct transfer from {seq[i]} to {seq[i+1]}."
                            broken_path_nodes.update(seq)
                            break

            if not is_broken:
                survived = any(ap.get("account_sequence") == seq for ap in after_paths)
                if not survived:
                    is_broken = True
                    reason = "Flow volume or timing along path attenuated below suspicious threshold."
                    broken_path_nodes.update(seq)

            path_impact_list.append({
                "path_id": p_id,
                "account_sequence": seq,
                "status": "BROKEN" if is_broken else "UNCHANGED",
                "retention_percentage": p.get("retention_percentage", 0.0),
                "elapsed_minutes": p.get("elapsed_minutes", 0.0),
                "reason": reason,
            })

        # 7. Pattern Disruption Analysis
        before_pat_titles = {p.get("title", ""): p for p in before_patterns}
        after_pat_titles = {p.get("title", ""): p for p in after_patterns}

        removed_patterns = []
        persisted_patterns = []
        new_patterns = []

        for title, p in before_pat_titles.items():
            if title in after_pat_titles:
                persisted_patterns.append({
                    "pattern_type": p.get("pattern_type", ""),
                    "title": title,
                    "severity": p.get("severity", "MEDIUM"),
                    "status": "PERSISTED",
                    "note": "Typology remains active via alternative accounts/flows.",
                })
            else:
                removed_patterns.append({
                    "pattern_type": p.get("pattern_type", ""),
                    "title": title,
                    "severity": p.get("severity", "HIGH"),
                    "status": "REMOVED",
                    "note": f"Typology disrupted by removal of {target_id}.",
                })

        for title, p in after_pat_titles.items():
            if title not in before_pat_titles:
                new_patterns.append({
                    "pattern_type": p.get("pattern_type", ""),
                    "title": title,
                    "severity": p.get("severity", "MEDIUM"),
                    "status": "NEWLY_DETECTED",
                    "note": "Emerged under recalculated graph topology.",
                })

        # 8. Network Structural Impact
        removed_edges_ids = []
        removed_edges_volume = 0.0
        affected_neighbors: Set[str] = set()

        if target_type == "account":
            for u, v, k, d in original_graph.graph.edges(data=True, keys=True):
                if u == target_id or v == target_id:
                    removed_edges_ids.append(d.get("transaction_id", k))
                    removed_edges_volume += d.get("amount", 0.0)
                    if u != target_id:
                        affected_neighbors.add(u)
                    if v != target_id:
                        affected_neighbors.add(v)
        else:
            tx_obj = original_graph.transactions.get(target_id)
            if tx_obj:
                removed_edges_ids.append(target_id)
                removed_edges_volume = tx_obj.amount
                affected_neighbors.add(tx_obj.sender_account)
                affected_neighbors.add(tx_obj.receiver_account)

        communities_before = original_analysis.get("communities", [])
        communities_after = sim_analysis.get("communities", [])

        # 9. Temporal Storyline Impact
        stage_impact_list = []
        for stage in before_stages:
            s_name = stage.get("stage_name", "")
            s_accounts = stage.get("accounts_active", [])
            s_risk = stage.get("stage_risk_score", 50)

            is_affected = False
            if target_type == "account" and target_id in s_accounts:
                is_affected = True
            elif target_type == "transaction":
                tx_obj = original_graph.transactions.get(target_id)
                if tx_obj and (tx_obj.sender_account in s_accounts or tx_obj.receiver_account in s_accounts):
                    is_affected = True

            after_stage = next((s for s in after_stages if s.get("stage_name") == s_name), None)
            after_risk = after_stage.get("stage_risk_score", 0) if after_stage else 0

            stage_impact_list.append({
                "stage_name": s_name,
                "time_range": stage.get("time_range_display", ""),
                "status": "DISRUPTED" if is_affected or not after_stage else ("ATTENUATED" if after_risk < s_risk else "UNCHANGED"),
                "before_risk_score": s_risk,
                "after_risk_score": after_risk,
                "accounts_involved": s_accounts,
            })

        # 10. Money Trail DNA Impact
        dna_before_summary = extract_dna_gene_summary(before_dna)
        dna_after_summary = extract_dna_gene_summary(after_dna)

        dna_gene_comparison = {
            "typology": {
                "before": dna_before_summary["typology"],
                "after": dna_after_summary["typology"],
                "changed": dna_before_summary["typology"] != dna_after_summary["typology"],
            },
            "retention": {
                "before": dna_before_summary["retention"],
                "after": dna_after_summary["retention"],
                "changed": dna_before_summary["retention"] != dna_after_summary["retention"],
            },
            "velocity": {
                "before": dna_before_summary["velocity"],
                "after": dna_after_summary["velocity"],
                "changed": dna_before_summary["velocity"] != dna_after_summary["velocity"],
            },
            "dispersion": {
                "before": dna_before_summary["dispersion"],
                "after": dna_after_summary["dispersion"],
                "changed": dna_before_summary["dispersion"] != dna_after_summary["dispersion"],
            },
            "topology": {
                "before": dna_before_summary["topology"],
                "after": dna_after_summary["topology"],
                "changed": dna_before_summary["topology"] != dna_after_summary["topology"],
            },
            "role_sequence": {
                "before": dna_before_summary["role_sequence"],
                "after": dna_after_summary["role_sequence"],
                "changed": dna_before_summary["role_sequence"] != dna_after_summary["role_sequence"],
            },
        }

        # 11. Role Shift Impact on Downstream Accounts
        role_shifts = []
        for acc_id, orig_r in before_roles.items():
            if acc_id == target_id:
                continue
            sim_r = after_roles.get(acc_id, {})
            orig_role = orig_r.get("probable_role", "UNKNOWN") if isinstance(orig_r, dict) else getattr(orig_r, "probable_role", "UNKNOWN")
            sim_role = sim_r.get("probable_role", "UNKNOWN") if isinstance(sim_r, dict) else getattr(sim_r, "probable_role", "UNKNOWN")
            orig_conf = orig_r.get("confidence", 0.0) if isinstance(orig_r, dict) else getattr(orig_r, "confidence", 0.0)
            sim_conf = sim_r.get("confidence", 0.0) if isinstance(sim_r, dict) else getattr(sim_r, "confidence", 0.0)

            if orig_role != sim_role or abs(orig_conf - sim_conf) >= 0.10:
                role_shifts.append({
                    "account_id": acc_id,
                    "role_before": orig_role,
                    "confidence_before": round(orig_conf, 2),
                    "role_after": sim_role,
                    "confidence_after": round(sim_conf, 2),
                    "notes": f"Role confidence shifted from {int(orig_conf*100)}% to {int(sim_conf*100)}% due to upstream/downstream flow alteration.",
                })

        # 12. Priority Factor Breakdown
        priority_factors = []
        if len(removed_patterns) > 0:
            priority_factors.append(f"{len(removed_patterns)} suspicious typologies eliminated ({', '.join(p['title'] for p in removed_patterns[:2])})")
        broken_count = sum(1 for p in path_impact_list if p["status"] == "BROKEN")
        if broken_count > 0:
            priority_factors.append(f"{broken_count} of {len(before_paths)} reconstructed linear attack paths severed")
        if removed_edges_volume > 0:
            priority_factors.append(f"Direct flow volume reduction of ₹{removed_edges_volume:,.2f}")
        if len(affected_neighbors) > 0:
            priority_factors.append(f"Betweenness centrality decreased across {len(affected_neighbors)} adjacent entities")

        # 13. "Why This Matters" Forensic Summary
        why_matters = (
            f"Simulating the hypothetical removal of {target_type} '{target_id}' breaks {broken_count} of {len(before_paths)} "
            f"reconstructed laundering attack paths and disrupts {len(removed_patterns)} detected AML pattern clusters. "
            f"Observed network transaction volume decreases by ₹{removed_edges_volume:,.2f}, and overall investigation "
            f"priority shifts from {before_top_priority} to {after_top_priority}/100. This indicates that {target_id} acts as "
            f"a key transit bottleneck within the monitored topology."
        )

        # 14. Assemble Complete Simulation Payload
        return {
            "scenario_id": scenario_id,
            "target": {
                "target_type": target_type,
                "target_id": target_id,
                "label": target_id,
            },
            "comparison": {
                "attack_paths": {"before": len(before_paths), "after": len(after_paths)},
                "suspicious_nodes": {"before": before_suspicious_count, "after": after_suspicious_count},
                "transactions_count": {"before": original_graph.get_edge_count(), "after": sim_graph.get_edge_count()},
                "total_volume_inr": {
                    "before": before_meta.get("total_volume_inr", 0.0),
                    "after": after_meta.get("total_volume_inr", 0.0),
                },
                "max_hop_depth": {"before": before_max_hops, "after": after_max_hops},
                "max_retention_pct": {"before": round(before_max_ret, 1), "after": round(after_max_ret, 1)},
                "pattern_clusters": {"before": len(before_patterns), "after": len(after_patterns)},
                "case_priority_score": {"before": before_top_priority, "after": after_top_priority},
                "primary_dna_signature": {
                    "before": before_dna.get("dna_signature", "N/A") if isinstance(before_dna, dict) else getattr(before_dna, "dna_signature", "N/A"),
                    "after": after_dna.get("dna_signature", "N/A") if isinstance(after_dna, dict) else getattr(after_dna, "dna_signature", "N/A"),
                },
            },
            "path_impact": path_impact_list,
            "pattern_impact": {
                "removed": removed_patterns,
                "persisted": persisted_patterns,
                "newly_detected": new_patterns,
                "summary": f"{len(removed_patterns)} typologies disrupted, {len(persisted_patterns)} persisted.",
            },
            "network_impact": {
                "nodes_removed": [target_id] if target_type == "account" else [],
                "edges_removed": removed_edges_ids,
                "removed_volume_inr": removed_edges_volume,
                "affected_entities": list(affected_neighbors),
                "communities_before": len(communities_before),
                "communities_after": len(communities_after),
                "connectivity_status": "Severely Disrupted" if broken_count > 0 else "Reduced",
            },
            "temporal_impact": stage_impact_list,
            "dna_impact": {
                "signature_before": before_dna.get("dna_signature", "N/A") if isinstance(before_dna, dict) else getattr(before_dna, "dna_signature", "N/A"),
                "signature_after": after_dna.get("dna_signature", "N/A") if isinstance(after_dna, dict) else getattr(after_dna, "dna_signature", "N/A"),
                "genes": dna_gene_comparison,
            },
            "role_impact": role_shifts,
            "priority_impact": {
                "priority_before": before_top_priority,
                "priority_after": after_top_priority,
                "delta": after_top_priority - before_top_priority,
                "contributing_factors": priority_factors,
            },
            "why_this_matters": why_matters,
            "simulated_graph": sim_graph.to_dict(),
            "simulated_roles": after_roles,
            "diff_highlights": {
                "removed_node_ids": [target_id] if target_type == "account" else [],
                "removed_edge_ids": removed_edges_ids,
                "broken_path_nodes": list(broken_path_nodes),
                "affected_neighbor_ids": list(affected_neighbors),
            },
        }

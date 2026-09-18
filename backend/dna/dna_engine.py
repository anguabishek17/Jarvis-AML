"""
Financial Behavioural Fingerprint & Money Trail DNA Engine.
Extracts explainable, deterministic DNA signatures from money-flow attack paths.
Every gene is backed by mathematical derivations and exact supporting transaction IDs.
Includes local SHA-256 tamper-evident verification hashing.
"""
import hashlib
import json
from typing import List, Dict, Any, Optional
from backend.graph.financial_graph import FinancialMultiGraph
from backend.models.findings import AttackPath, AccountRoleHypothesis, PatternFinding
from backend.models.dna import MoneyTrailDNA, DNAGene, DNAEvolutionStage


class MoneyTrailDNAEngine:
    """
    Constructs deterministic, evidence-linked Financial Behavioural DNA fingerprints:
    DNA-TYPOLOGY-RETENTION-VELOCITY-DISPERSION-TOPOLOGY
    Example: DNA-LAY4-RAP98-RET93-VEL14-DISP3-H5
    """

    def generate_dna_for_path(
        self,
        path: AttackPath,
        graph: FinancialMultiGraph,
        roles: Dict[str, AccountRoleHypothesis],
        findings: List[PatternFinding] = None,
    ) -> MoneyTrailDNA:
        if findings is None:
            findings = []

        # 1. GENE 1: TYPOLOGY
        typology_gene = self._build_typology_gene(path, findings)

        # 2. GENE 2: RETENTION
        retention_gene = self._build_retention_gene(path, graph)

        # 3. GENE 3: VELOCITY
        velocity_gene = self._build_velocity_gene(path, graph)

        # 4. GENE 4: DISPERSION
        dispersion_gene = self._build_dispersion_gene(path, graph)

        # 5. GENE 5: TOPOLOGY
        topology_gene = self._build_topology_gene(path)

        # 6. GENE 6: ROLE SEQUENCE
        role_sequence_gene, role_names = self._build_role_sequence_gene(path, roles)

        genes = [
            typology_gene,
            retention_gene,
            velocity_gene,
            dispersion_gene,
            topology_gene,
            role_sequence_gene,
        ]

        # Construct deterministic compact signature
        sig_parts = [
            "DNA",
            typology_gene.gene_code,
            retention_gene.gene_code,
            velocity_gene.gene_code,
            dispersion_gene.gene_code,
            topology_gene.gene_code,
        ]
        signature = "-".join(sig_parts)

        # Build evolution stages
        evolution = self._build_evolution_stages(path, graph, genes, signature)

        # Generate tamper-evident SHA-256 evidence hash
        evidence_payload = {
            "path_id": path.path_id,
            "signature": signature,
            "account_sequence": path.account_sequence,
            "transaction_ids": path.transaction_ids,
            "retention_score": retention_gene.calculation_details.get("retention_percentage", 0.0),
            "avg_dwell_minutes": velocity_gene.calculation_details.get("avg_dwell_minutes", 0.0),
            "hop_depth": path.hop_count,
            "genes": [g.model_dump() for g in genes],
        }
        payload_bytes = json.dumps(evidence_payload, sort_keys=True, default=str).encode("utf-8")
        evidence_hash = hashlib.sha256(payload_bytes).hexdigest()

        return MoneyTrailDNA(
            dna_id=f"DNA_{path.path_id}",
            path_id=path.path_id,
            signature=signature,
            genes=genes,
            typology_code=typology_gene.gene_code,
            retention_score=path.retention_percentage,
            velocity_score=max(100.0 - min(velocity_gene.calculation_details.get("avg_dwell_minutes", 0.0), 100.0), 0.0),
            avg_dwell_minutes=velocity_gene.calculation_details.get("avg_dwell_minutes", 0.0),
            dispersion_code=dispersion_gene.gene_code,
            hop_depth=path.hop_count,
            role_sequence=role_names,
            evidence_payload_sha256=evidence_hash,
            evolution_stages=evolution,
        )

    def _build_typology_gene(self, path: AttackPath, findings: List[PatternFinding]) -> DNAGene:
        # Check active patterns
        active_codes = []
        supporting_txs = []
        for f in findings:
            if any(acc in path.account_sequence for acc in f.accounts_involved):
                supporting_txs.extend(f.transaction_ids)
                p_type = f.pattern_type.value
                if p_type == "LAYERING" and "LAY" not in active_codes:
                    active_codes.append(f"LAY{path.hop_count}")
                elif p_type == "RAPID_MOVEMENT" and "RAP" not in active_codes:
                    active_codes.append("RAP")
                elif p_type == "CIRCULAR_TRANSFER" and "CYC" not in active_codes:
                    active_codes.append("CYC")
                elif p_type in ("FAN_IN", "FAN_OUT") and "FAN" not in active_codes:
                    active_codes.append("FAN")

        if not active_codes:
            active_codes.append(f"LAY{path.hop_count}")

        code = "-".join(active_codes)
        display_val = " → ".join(active_codes)

        return DNAGene(
            gene_name="Typology",
            gene_code=code,
            value_display=display_val,
            why_explanation=f"Reconstructed money flow manifests {len(active_codes)} distinct AML pattern typologies across {path.hop_count} transit hops.",
            supporting_transaction_ids=list(set(supporting_txs if supporting_txs else path.transaction_ids)),
            calculation_details={"observed_patterns": active_codes, "hop_count": path.hop_count},
        )

    def _build_retention_gene(self, path: AttackPath, graph: FinancialMultiGraph) -> DNAGene:
        initial_amt = path.total_inflow_inr
        final_amt = path.total_outflow_inr
        ret_pct = round((final_amt / initial_amt) * 100.0, 1) if initial_amt > 0 else 100.0
        ret_int = int(round(ret_pct))

        gene_code = f"RET{ret_int}"
        display_val = f"{ret_pct}% Retained"

        return DNAGene(
            gene_name="Retention",
            gene_code=gene_code,
            value_display=display_val,
            why_explanation=(
                f"Initial path disbursement was ₹{initial_amt:,.2f} and final terminal receipt was ₹{final_amt:,.2f}, "
                f"resulting in a {ret_pct}% fund retention rate (₹{initial_amt - final_amt:,.2f} transit fee/leakage)."
            ),
            supporting_transaction_ids=path.transaction_ids,
            calculation_details={
                "initial_amount_inr": initial_amt,
                "final_amount_inr": final_amt,
                "retained_amount_inr": initial_amt - final_amt,
                "retention_percentage": ret_pct,
            },
        )

    def _build_velocity_gene(self, path: AttackPath, graph: FinancialMultiGraph) -> DNAGene:
        # Calculate average dwell time across intermediate hops
        tx_objs = [graph.transactions[tx_id] for tx_id in path.transaction_ids if tx_id in graph.transactions]
        tx_objs = sorted(tx_objs, key=lambda x: x.timestamp)

        dwells = []
        if len(tx_objs) > 1:
            for i in range(len(tx_objs) - 1):
                diff = (tx_objs[i+1].timestamp - tx_objs[i].timestamp).total_seconds() / 60.0
                dwells.append(diff)

        avg_dwell = round(sum(dwells) / len(dwells), 1) if dwells else 0.0
        dwell_int = int(round(avg_dwell))

        gene_code = f"VEL{dwell_int}"
        velocity_rating = "HIGH" if avg_dwell <= 15.0 else ("MEDIUM" if avg_dwell <= 60.0 else "LOW")
        display_val = f"{avg_dwell} mins ({velocity_rating})"

        return DNAGene(
            gene_name="Velocity",
            gene_code=gene_code,
            value_display=display_val,
            why_explanation=f"Average dwell latency between intermediary transfer hops is {avg_dwell} minutes ({velocity_rating} velocity forwarding).",
            supporting_transaction_ids=path.transaction_ids,
            calculation_details={
                "avg_dwell_minutes": avg_dwell,
                "total_elapsed_minutes": path.elapsed_minutes,
                "velocity_rating": velocity_rating,
            },
        )

    def _build_dispersion_gene(self, path: AttackPath, graph: FinancialMultiGraph) -> DNAGene:
        src = path.source_account
        sink = path.destination_account
        src_out = len(graph.get_outgoing_transactions(src))
        sink_in = len(graph.get_incoming_transactions(sink))
        mid_count = len(path.intermediate_accounts)

        disp_code = f"DISP{src_out}-{max(mid_count, 1)}-{sink_in}"
        short_code = f"DISP{src_out}"

        return DNAGene(
            gene_name="Dispersion",
            gene_code=short_code,
            value_display=f"{src_out} → {max(mid_count, 1)} → {sink_in}",
            why_explanation=f"Fan-out branching factor of {src_out} outgoing channels converging across {mid_count} intermediate nodes into {sink_in} feeder streams.",
            supporting_transaction_ids=path.transaction_ids,
            calculation_details={"source_out_degree": src_out, "intermediate_nodes": mid_count, "sink_in_degree": sink_in},
        )

    def _build_topology_gene(self, path: AttackPath) -> DNAGene:
        code = f"H{path.hop_count}"
        display_val = f"{path.hop_count} Hops ({len(path.account_sequence)} Accounts)"

        return DNAGene(
            gene_name="Topology",
            gene_code=code,
            value_display=display_val,
            why_explanation=f"Graph path depth spanning {path.hop_count} sequential transfers across {len(path.account_sequence)} distinct financial entities.",
            supporting_transaction_ids=path.transaction_ids,
            calculation_details={"hop_count": path.hop_count, "account_count": len(path.account_sequence)},
        )

    def _build_role_sequence_gene(self, path: AttackPath, roles: Dict[str, AccountRoleHypothesis]) -> (DNAGene, List[str]):
        role_sequence = []
        for acc in path.account_sequence:
            r = roles.get(acc)
            role_sequence.append(r.probable_role.value if r else "MULE")

        display_val = " → ".join(role_sequence)
        code = "-".join([r[:3] for r in role_sequence])

        gene = DNAGene(
            gene_name="Role Sequence",
            gene_code=code,
            value_display=display_val,
            why_explanation=f"Inferred operational path topology progressing through: {display_val}.",
            supporting_transaction_ids=path.transaction_ids,
            calculation_details={"role_sequence": role_sequence},
        )
        return gene, role_sequence

    def _build_evolution_stages(
        self,
        path: AttackPath,
        graph: FinancialMultiGraph,
        genes: List[DNAGene],
        final_sig: str,
    ) -> List[DNAEvolutionStage]:
        stages: List[DNAEvolutionStage] = []
        tx_objs = [graph.transactions[tx_id] for tx_id in path.transaction_ids if tx_id in graph.transactions]
        tx_objs = sorted(tx_objs, key=lambda x: x.timestamp)

        if not tx_objs:
            return stages

        stage_names = ["INJECTION", "DISPERSION", "LAYERING", "CONVERGENCE", "SINK"]
        step_count = min(len(tx_objs), len(stage_names))
        
        cumulative_sig_parts = ["DNA"]
        
        for i in range(step_count):
            tx = tx_objs[i]
            stage_name = stage_names[i] if i < len(stage_names) else f"TRANSIT_{i+1}"
            
            # Progressively add gene codes
            if i == 0:
                cumulative_sig_parts.append(f"LAY1")
                new_gene = "LAY1"
            elif i == 1:
                cumulative_sig_parts.append(genes[2].gene_code)  # Velocity
                new_gene = genes[2].gene_code
            elif i == 2:
                cumulative_sig_parts.append(genes[1].gene_code)  # Retention
                new_gene = genes[1].gene_code
            elif i == 3:
                cumulative_sig_parts.append(genes[3].gene_code)  # Dispersion
                new_gene = genes[3].gene_code
            else:
                cumulative_sig_parts.append(genes[4].gene_code)  # Topology
                new_gene = genes[4].gene_code

            sig_str = "-".join(cumulative_sig_parts)
            
            stages.append(
                DNAEvolutionStage(
                    stage_index=i + 1,
                    stage_name=stage_name,
                    timestamp_range=tx.timestamp.strftime("%H:%M IST"),
                    active_dna_signature=sig_str,
                    new_genes_added=[new_gene],
                    volume_inr_at_stage=tx.amount,
                    accounts_active=[tx.sender_account, tx.receiver_account],
                    stage_narrative=f"Stage {i+1} ({stage_name}): Transferred ₹{tx.amount:,.2f} from {tx.sender_account} to {tx.receiver_account}.",
                )
            )

        return stages

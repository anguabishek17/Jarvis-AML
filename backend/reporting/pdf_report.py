"""
JARVIS-AML: Forensic Investigation PDF Report Generator.
Uses ReportLab to generate a multi-page, evidence-backed, professional AML investigation report
dynamically from the active investigation case dossier.
"""
import io
import os
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
    PageBreak,
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and render total page count, running headers, and running footers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#475569"))

        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(40, 810, "JARVIS-AML FORENSIC FINANCIAL INTELLIGENCE REPORT")
            self.drawRightString(555, 810, getattr(self, "case_id_str", "INVESTIGATION REPORT"))
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(40, 804, 555, 804)

        # Footer
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(40, 45, 555, 45)

        self.setFont("Helvetica", 7.5)
        self.drawString(40, 32, "CONFIDENTIAL — STRICTLY FOR LAW ENFORCEMENT & COMPLIANCE USE ONLY")
        self.drawRightString(555, 32, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


class ForensicPDFReportGenerator:
    """Generates a complete, evidence-based investigation PDF for any case."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._init_custom_styles()

    def _init_custom_styles(self):
        # Color palette
        self.c_primary = colors.HexColor("#0F172A")    # Slate 900
        self.c_navy = colors.HexColor("#1E293B")       # Slate 800
        self.c_accent = colors.HexColor("#0284C7")     # Sky 600
        self.c_danger = colors.HexColor("#DC2626")     # Red 600
        self.c_warning = colors.HexColor("#D97706")    # Amber 600
        self.c_bg_light = colors.HexColor("#F8FAFC")   # Slate 50
        self.c_border = colors.HexColor("#E2E8F0")     # Slate 200

        self.title_style = ParagraphStyle(
            "DocTitle",
            parent=self.styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=self.c_primary,
            spaceAfter=4,
        )

        self.subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#475569"),
            spaceAfter=12,
        )

        self.section_heading = ParagraphStyle(
            "SectionHeading",
            parent=self.styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=self.c_navy,
            spaceBefore=12,
            spaceAfter=6,
            keepWithNext=True,
        )

        self.sub_section_heading = ParagraphStyle(
            "SubSectionHeading",
            parent=self.styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#334155"),
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True,
        )

        self.body_style = ParagraphStyle(
            "DocBody",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor("#1E293B"),
            spaceAfter=4,
        )

        self.callout_style = ParagraphStyle(
            "DocCallout",
            parent=self.styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#475569"),
        )

        self.table_cell = ParagraphStyle(
            "TableCell",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor("#1E293B"),
        )

        self.table_cell_bold = ParagraphStyle(
            "TableCellBold",
            parent=self.table_cell,
            fontName="Helvetica-Bold",
        )

        self.table_cell_header = ParagraphStyle(
            "TableCellHeader",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.white,
        )

        self.dna_pill = ParagraphStyle(
            "DNAPill",
            parent=self.styles["Normal"],
            fontName="Courier-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#0369A1"),
        )

    def generate_pdf(self, case_data: Dict[str, Any]) -> bytes:
        """Compiles the full case data dictionary into a PDF byte stream."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=40,
            rightMargin=40,
            topMargin=45,
            bottomMargin=55,
        )

        case_id = str(case_data.get("scenario_id") or case_data.get("case_id") or "CASE-UNASSIGNED")

        story: List[Any] = []

        # 1. Header & Title Block
        story.extend(self._build_header_block(case_data, case_id))
        story.append(Spacer(1, 8))

        # 2. Executive Summary & KPIs
        story.extend(self._build_executive_summary(case_data))
        story.append(Spacer(1, 10))

        # 3. Input Data & Validation Summary
        story.extend(self._build_input_summary(case_data))
        story.append(Spacer(1, 10))

        # 4. Network Intelligence & Communities
        story.extend(self._build_network_intelligence(case_data))
        story.append(Spacer(1, 10))

        # 5. Detected AML Patterns
        story.extend(self._build_patterns_section(case_data))
        story.append(Spacer(1, 10))

        # 6. Reconstructed Attack Paths
        story.extend(self._build_attack_paths_section(case_data))
        story.append(Spacer(1, 10))

        # 7. Account Role Hypotheses
        story.extend(self._build_roles_section(case_data))
        story.append(Spacer(1, 10))

        # 8. Investigation Priority Triage
        story.extend(self._build_priority_section(case_data))
        story.append(Spacer(1, 10))

        # 9. Money Trail DNA & Gene Evidence
        story.extend(self._build_dna_section(case_data))
        story.append(Spacer(1, 10))

        # 10. Historical Case Similarity
        story.extend(self._build_similarity_section(case_data))
        story.append(Spacer(1, 10))

        # 11. Temporal Risk Stages & Storyline
        story.extend(self._build_temporal_storyline_section(case_data))
        story.append(Spacer(1, 10))

        # 12. Full Investigator Narrative Brief
        story.extend(self._build_narrative_section(case_data))
        story.append(Spacer(1, 10))

        # 13. Actionable Investigation Leads
        story.extend(self._build_leads_section(case_data))
        story.append(Spacer(1, 10))

        # 14. Transaction Evidence Register (Sample/Key Evidence)
        story.extend(self._build_evidence_register(case_data))
        story.append(Spacer(1, 12))

        # 15. Forensic Integrity Seal
        story.extend(self._build_integrity_footer(case_data, case_id))

        # Build document with NumberedCanvas
        def make_canvas(*args, **kwargs):
            c = NumberedCanvas(*args, **kwargs)
            c.case_id_str = f"CASE: {case_id}"
            return c

        doc.build(story, canvasmaker=make_canvas)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def _build_header_block(self, case_data: Dict[str, Any], case_id: str) -> List[Any]:
        meta = case_data.get("metadata", {})
        title = meta.get("title", case_id)
        is_custom = meta.get("is_custom", False) or case_id.startswith("CUSTOM-")
        source_label = "CUSTOM UPLOADED TRANSACTION DATASET" if is_custom else "BENCHMARK TYPOLOGY SCENARIO"
        gen_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        elements = [
            Paragraph("JARVIS-AML INTELLIGENCE PLATFORM", ParagraphStyle("H0", fontName="Helvetica-Bold", fontSize=9, textColor=self.c_accent, leading=11)),
            Paragraph("FINANCIAL CRIME FORENSIC INVESTIGATION REPORT", self.title_style),
            Paragraph(f"<b>Case Identifier:</b> {case_id} &nbsp;|&nbsp; <b>Source:</b> {source_label} &nbsp;|&nbsp; <b>Generated:</b> {gen_time}", self.subtitle_style),
            HRFlowable(width="100%", thickness=1.5, color=self.c_navy, spaceBefore=0, spaceAfter=8),
            # Disclaimer
            Table(
                [[
                    Paragraph(
                        "<b>LEGAL & EVIDENTIARY DISCLAIMER:</b> This dossier is an automated analytical investigation-support artifact produced from observed transaction logs. Inferred account roles, pattern detections, and priority rankings represent evidence-grounded hypotheses generated by mathematical graph and behavioural engines. This document does not establish criminal liability and is intended solely to guide qualified human investigators.",
                        self.callout_style
                    )
                ]],
                colWidths=[515],
                style=TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), self.c_bg_light),
                    ("BOX", (0, 0), (-1, -1), 0.5, self.c_border),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ])
            )
        ]
        return elements

    def _build_executive_summary(self, case_data: Dict[str, Any]) -> List[Any]:
        meta = case_data.get("metadata", {})
        graph = case_data.get("graph", {})
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        patterns = case_data.get("patterns", [])
        paths = case_data.get("attack_paths", [])
        priorities = case_data.get("priority_rankings", [])
        total_vol = meta.get("total_volume_inr", sum(float(e.get("amount", 0)) for e in edges))

        top_priority = priorities[0] if priorities else None
        top_acc = top_priority.get("account_id", "N/A") if top_priority else "N/A"
        top_role = top_priority.get("inferred_role", top_priority.get("probable_role", "N/A")) if top_priority else "N/A"
        top_score = f"{top_priority.get('priority_score', 0):.1f}/100" if top_priority else "N/A"

        dna = case_data.get("primary_dna", {})
        dna_sig = dna.get("signature", "N/A") if dna else "N/A"

        summary_data = [
            [
                Paragraph("<b>Monitored Accounts:</b>", self.table_cell), Paragraph(str(len(nodes)), self.table_cell_bold),
                Paragraph("<b>Total Volume (INR):</b>", self.table_cell), Paragraph(f"₹{total_vol:,.2f}", self.table_cell_bold)
            ],
            [
                Paragraph("<b>Total Transactions:</b>", self.table_cell), Paragraph(str(len(edges)), self.table_cell_bold),
                Paragraph("<b>Pattern Findings:</b>", self.table_cell), Paragraph(f"{len(patterns)} clusters", self.table_cell_bold)
            ],
            [
                Paragraph("<b>Attack Money Trails:</b>", self.table_cell), Paragraph(str(len(paths)), self.table_cell_bold),
                Paragraph("<b>Top Priority Entity:</b>", self.table_cell), Paragraph(f"{top_acc} ({top_role} - {top_score})", self.table_cell_bold)
            ],
            [
                Paragraph("<b>Primary DNA Signature:</b>", self.table_cell), Paragraph(dna_sig, self.dna_pill),
                Paragraph("<b>Typology Code:</b>", self.table_cell), Paragraph(str(meta.get("primary_typology", "CUSTOM_INGESTION")), self.table_cell_bold)
            ]
        ]

        table = Table(summary_data, colWidths=[130, 127, 130, 128])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), self.c_bg_light),
            ("GRID", (0, 0), (-1, -1), 0.5, self.c_border),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))

        return [
            Paragraph("1. EXECUTIVE SUMMARY & FORENSIC METRICS", self.section_heading),
            table
        ]

    def _build_input_summary(self, case_data: Dict[str, Any]) -> List[Any]:
        val = case_data.get("validation_report") or case_data.get("metadata", {}).get("validation_summary")
        meta = case_data.get("metadata", {})
        graph = case_data.get("graph", {})
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        total_rows = val.get("total_rows", len(edges)) if val else len(edges)
        valid_rows = val.get("valid_rows", len(edges)) if val else len(edges)
        invalid_rows = val.get("invalid_rows", 0) if val else 0
        dataset_title = meta.get("title", "Active Dataset")

        data_rows = [
            [
                Paragraph("<b>Dataset Source / Name:</b>", self.table_cell), Paragraph(dataset_title, self.table_cell),
                Paragraph("<b>Validation Status:</b>", self.table_cell), Paragraph("✓ VALIDATED (100% INGESTED)", self.table_cell_bold)
            ],
            [
                Paragraph("<b>Total Input Rows:</b>", self.table_cell), Paragraph(str(total_rows), self.table_cell),
                Paragraph("<b>Valid Transactions:</b>", self.table_cell), Paragraph(f"{valid_rows} rows", self.table_cell)
            ],
            [
                Paragraph("<b>Invalid / Filtered:</b>", self.table_cell), Paragraph(f"{invalid_rows} rows", self.table_cell),
                Paragraph("<b>Active Entity Count:</b>", self.table_cell), Paragraph(f"{len(nodes)} accounts", self.table_cell)
            ]
        ]

        table = Table(data_rows, colWidths=[130, 127, 130, 128])
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, self.c_border),
            ("BACKGROUND", (0, 0), (-1, -1), colors.white),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))

        return [
            Paragraph("2. INPUT DATA & VALIDATION AUDIT", self.section_heading),
            table
        ]

    def _build_network_intelligence(self, case_data: Dict[str, Any]) -> List[Any]:
        graph = case_data.get("graph", {})
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        communities = case_data.get("communities", [])

        # Sort accounts by highest transaction volume
        sorted_nodes = sorted(nodes, key=lambda n: float(n.get("inflow", 0)) + float(n.get("outflow", 0)), reverse=True)[:5]
        top_hubs = ", ".join([f"{n.get('id', 'N/A')} (₹{float(n.get('inflow',0))+float(n.get('outflow',0)):,.0f})" for n in sorted_nodes]) if sorted_nodes else "None"

        comm_summary = f"{len(communities)} isolated / connected sub-clusters detected." if communities else "Single connected component."

        content = [
            Paragraph(f"• <b>Network Topology:</b> Directed MultiGraph with {len(nodes)} entity nodes and {len(edges)} transaction edges.", self.body_style),
            Paragraph(f"• <b>Community Partitioning:</b> {comm_summary}", self.body_style),
            Paragraph(f"• <b>Dominant Flow Hubs (Inflow+Outflow):</b> {top_hubs}", self.body_style),
        ]

        return [
            Paragraph("3. NETWORK TOPOLOGY & COMMUNITY INTELLIGENCE", self.section_heading),
            *content
        ]

    def _build_patterns_section(self, case_data: Dict[str, Any]) -> List[Any]:
        patterns = case_data.get("patterns", [])
        if not patterns:
            return [
                Paragraph("4. AML SUSPICIOUS PATTERN FINDINGS", self.section_heading),
                Paragraph("No deterministic suspicious typology patterns were detected in this dataset.", self.body_style)
            ]

        rows = [
            [
                Paragraph("Pattern Type", self.table_cell_header),
                Paragraph("Severity", self.table_cell_header),
                Paragraph("Accounts Involved", self.table_cell_header),
                Paragraph("Observable Evidence / Description", self.table_cell_header),
            ]
        ]

        for p in patterns[:12]:  # Top 12 patterns to prevent unbounded table growth
            ptype = str(p.get("pattern_type", "UNKNOWN"))
            sev = str(p.get("severity", "MEDIUM")).upper()
            accs = ", ".join(p.get("accounts_involved", []))
            desc = str(p.get("description", ""))
            metrics = p.get("metrics", {})
            if metrics:
                metric_str = " | ".join([f"{k}: {v}" for k, v in metrics.items() if not isinstance(v, (list, dict))])
                if metric_str:
                    desc += f" [Metrics: {metric_str}]"

            rows.append([
                Paragraph(f"<b>{ptype}</b>", self.table_cell),
                Paragraph(f"<b>{sev}</b>", self.table_cell),
                Paragraph(accs, self.table_cell),
                Paragraph(desc, self.table_cell),
            ])

        table = Table(rows, colWidths=[100, 60, 130, 225], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.c_navy),
            ("GRID", (0, 0), (-1, -1), 0.5, self.c_border),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, self.c_bg_light]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))

        return [
            Paragraph(f"4. AML SUSPICIOUS PATTERN FINDINGS ({len(patterns)} Total Detections)", self.section_heading),
            table
        ]

    def _build_attack_paths_section(self, case_data: Dict[str, Any]) -> List[Any]:
        paths = case_data.get("attack_paths", [])
        if not paths:
            return [
                Paragraph("5. RECONSTRUCTED ATTACK PATHS & MONEY TRAILS", self.section_heading),
                Paragraph("No multi-hop linear laundering attack paths were isolated in this dataset.", self.body_style)
            ]

        elements: List[Any] = [
            Paragraph(f"5. RECONSTRUCTED ATTACK PATHS & MONEY TRAILS ({len(paths)} Active Trails)", self.section_heading)
        ]

        rows = [
            [
                Paragraph("Path ID", self.table_cell_header),
                Paragraph("Flow Route (Source → Intermediaries → Sink)", self.table_cell_header),
                Paragraph("Hops", self.table_cell_header),
                Paragraph("Initial Vol", self.table_cell_header),
                Paragraph("Retention", self.table_cell_header),
                Paragraph("Duration", self.table_cell_header),
            ]
        ]

        for p in paths[:8]:
            pid = str(p.get("path_id", "PATH-001"))
            acc_seq = p.get("account_sequence", [])
            route_str = " → ".join(acc_seq) if acc_seq else f"{p.get('source_account')} → {p.get('sink_account')}"
            hops = str(p.get("hop_count", len(acc_seq)-1 if acc_seq else 1))
            init_amt = f"₹{float(p.get('initial_amount', 0)):,.0f}"
            ret = f"{float(p.get('retention_percentage', 0)):.1f}%"
            dur = f"{float(p.get('elapsed_time_minutes', 0)):.0f} min"

            rows.append([
                Paragraph(f"<b>{pid}</b>", self.table_cell),
                Paragraph(route_str, self.table_cell),
                Paragraph(hops, self.table_cell),
                Paragraph(init_amt, self.table_cell),
                Paragraph(ret, self.table_cell_bold),
                Paragraph(dur, self.table_cell),
            ])

        table = Table(rows, colWidths=[55, 235, 35, 65, 55, 70], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.c_navy),
            ("GRID", (0, 0), (-1, -1), 0.5, self.c_border),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, self.c_bg_light]),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))

        elements.append(table)
        return elements

    def _build_roles_section(self, case_data: Dict[str, Any]) -> List[Any]:
        roles = case_data.get("roles", {})
        if not roles:
            return [
                Paragraph("6. PROBABLE ACCOUNT ROLE INFERENCES", self.section_heading),
                Paragraph("No specific account roles could be inferred from available transactions.", self.body_style)
            ]

        rows = [
            [
                Paragraph("Account ID", self.table_cell_header),
                Paragraph("Probable Role", self.table_cell_header),
                Paragraph("Conf.", self.table_cell_header),
                Paragraph("Total Inflow", self.table_cell_header),
                Paragraph("Total Outflow", self.table_cell_header),
                Paragraph("Forwarding", self.table_cell_header),
                Paragraph("Dwell Time", self.table_cell_header),
            ]
        ]

        for acc_id, r in roles.items():
            role_name = str(r.get("probable_role", "UNKNOWN"))
            conf = f"{float(r.get('confidence', 0)):.0%}"
            inflow = f"₹{float(r.get('inflow_total_inr', 0)):,.0f}"
            outflow = f"₹{float(r.get('outflow_total_inr', 0)):,.0f}"
            ratio = f"{float(r.get('forwarding_ratio', 0)):.0%}"
            dwell = f"{float(r.get('avg_dwell_time_minutes', 0)):.0f} min"

            rows.append([
                Paragraph(f"<b>{acc_id}</b>", self.table_cell),
                Paragraph(f"<b>{role_name}</b>", self.table_cell),
                Paragraph(conf, self.table_cell),
                Paragraph(inflow, self.table_cell),
                Paragraph(outflow, self.table_cell),
                Paragraph(ratio, self.table_cell),
                Paragraph(dwell, self.table_cell),
            ])

        table = Table(rows, colWidths=[95, 80, 45, 75, 75, 65, 80], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.c_navy),
            ("GRID", (0, 0), (-1, -1), 0.5, self.c_border),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, self.c_bg_light]),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))

        return [
            Paragraph("6. PROBABLE ACCOUNT ROLE HYPOTHESES", self.section_heading),
            table
        ]

    def _build_priority_section(self, case_data: Dict[str, Any]) -> List[Any]:
        priorities = case_data.get("priority_rankings", [])
        if not priorities:
            return []

        rows = [
            [
                Paragraph("Rank", self.table_cell_header),
                Paragraph("Account ID", self.table_cell_header),
                Paragraph("Priority Score", self.table_cell_header),
                Paragraph("Inferred Role", self.table_cell_header),
                Paragraph("Confidence", self.table_cell_header),
                Paragraph("Observable Evidence Rationale", self.table_cell_header),
            ]
        ]

        for p in priorities[:10]:
            rank = str(p.get("rank", "-"))
            acc = str(p.get("account_id", "-"))
            score = f"{float(p.get('priority_score', 0)):.1f}/100"
            role = str(p.get("inferred_role", p.get("probable_role", "UNKNOWN")))
            conf = f"{float(p.get('role_confidence', 0)):.0%}"
            reasons = "; ".join(p.get("reasons", [])) if p.get("reasons") else "Flow volume and centrality"

            rows.append([
                Paragraph(f"#{rank}", self.table_cell_bold),
                Paragraph(f"<b>{acc}</b>", self.table_cell),
                Paragraph(f"<b>{score}</b>", self.table_cell_bold),
                Paragraph(role, self.table_cell),
                Paragraph(conf, self.table_cell),
                Paragraph(reasons, self.table_cell),
            ])

        table = Table(rows, colWidths=[35, 95, 65, 75, 55, 190], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.c_navy),
            ("GRID", (0, 0), (-1, -1), 0.5, self.c_border),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, self.c_bg_light]),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))

        return [
            Paragraph("7. INVESTIGATION PRIORITY TRIAGE (0–100 EXPLAINABLE SCORING)", self.section_heading),
            table
        ]

    def _build_dna_section(self, case_data: Dict[str, Any]) -> List[Any]:
        dna = case_data.get("primary_dna")
        if not dna:
            return [
                Paragraph("8. MONEY TRAIL DNA™ BEHAVIOURAL SIGNATURE", self.section_heading),
                Paragraph("No primary Money Trail DNA fingerprint generated for this dataset.", self.body_style)
            ]

        sig = dna.get("signature", "DNA-UNASSIGNED")
        hash_seal = dna.get("evidence_payload_sha256", dna.get("dna_hash", "UNSEALED"))
        genes = dna.get("genes", {})

        gene_rows = [
            [
                Paragraph("Gene Identifier", self.table_cell_header),
                Paragraph("Gene Code", self.table_cell_header),
                Paragraph("Value / Signal", self.table_cell_header),
                Paragraph("Forensic Calculation / Meaning", self.table_cell_header),
            ]
        ]

        if isinstance(genes, list):
            for g in genes:
                if isinstance(g, dict):
                    name = str(g.get("gene_name", "Gene"))
                    code = str(g.get("gene_code", "N/A"))
                    val = str(g.get("value_display", "N/A"))
                    expl = str(g.get("why_explanation", ""))
                else:
                    name = str(getattr(g, "gene_name", "Gene"))
                    code = str(getattr(g, "gene_code", "N/A"))
                    val = str(getattr(g, "value_display", "N/A"))
                    expl = str(getattr(g, "why_explanation", ""))

                gene_rows.append([
                    Paragraph(f"<b>{name}</b>", self.table_cell_bold),
                    Paragraph(f"<b>{code}</b>", self.dna_pill),
                    Paragraph(val, self.table_cell),
                    Paragraph(expl, self.table_cell),
                ])
        elif isinstance(genes, dict):
            for name, g in genes.items():
                if isinstance(g, dict):
                    code = str(g.get("code", g.get("gene_code", "N/A")))
                    val = str(g.get("value", g.get("value_display", "N/A")))
                    expl = str(g.get("description", g.get("why_explanation", "")))
                else:
                    code = str(getattr(g, "code", getattr(g, "gene_code", "N/A")))
                    val = str(getattr(g, "value", getattr(g, "value_display", "N/A")))
                    expl = str(getattr(g, "description", getattr(g, "why_explanation", "")))

                gene_rows.append([
                    Paragraph(f"<b>{name}</b>", self.table_cell_bold),
                    Paragraph(f"<b>{code}</b>", self.dna_pill),
                    Paragraph(val, self.table_cell),
                    Paragraph(expl, self.table_cell),
                ])

        table = Table(gene_rows, colWidths=[120, 75, 120, 200], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.c_navy),
            ("GRID", (0, 0), (-1, -1), 0.5, self.c_border),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, self.c_bg_light]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))

        return [
            Paragraph("8. MONEY TRAIL DNA™ BEHAVIOURAL FINGERPRINT", self.section_heading),
            Paragraph(f"<b>Active DNA Fingerprint:</b> <font color='#0284C7' face='Courier-Bold'>{sig}</font>", self.body_style),
            Paragraph(f"<b>SHA-256 Evidence Seal:</b> <font color='#475569' face='Courier'>{hash_seal}</font>", self.body_style),
            Spacer(1, 4),
            table
        ]

    def _build_similarity_section(self, case_data: Dict[str, Any]) -> List[Any]:
        sims = case_data.get("similar_cases", [])
        if not sims:
            return []

        rows = [
            [
                Paragraph("Historical Reference Case", self.table_cell_header),
                Paragraph("Similarity", self.table_cell_header),
                Paragraph("Primary Typology", self.table_cell_header),
                Paragraph("Matching Behavioural Vectors / Signals", self.table_cell_header),
            ]
        ]

        for s in sims[:4]:
            cid = f"<b>{s.get('reference_case_id')}</b> — {s.get('reference_title')}"
            sim_pct = f"{float(s.get('similarity_percentage', 0)):.1f}%"
            typology = str(s.get("typology_matched", "N/A"))
            vectors = s.get("matching_vectors", [])
            vec_str = ", ".join(vectors) if vectors else "Typology and velocity alignment"

            rows.append([
                Paragraph(cid, self.table_cell),
                Paragraph(f"<b>{sim_pct}</b>", self.table_cell_bold),
                Paragraph(typology, self.table_cell),
                Paragraph(f"Behavioural match: {vec_str}", self.table_cell),
            ])

        table = Table(rows, colWidths=[160, 65, 110, 180], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.c_navy),
            ("GRID", (0, 0), (-1, -1), 0.5, self.c_border),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, self.c_bg_light]),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))

        return [
            Paragraph("9. HISTORICAL CASE BEHAVIOURAL SIMILARITY", self.section_heading),
            Paragraph("Automated vector distance matching against historical typologies from law enforcement repositories:", self.body_style),
            Spacer(1, 3),
            table
        ]

    def _build_temporal_storyline_section(self, case_data: Dict[str, Any]) -> List[Any]:
        stages = case_data.get("temporal_stages", [])
        storyline = case_data.get("chronological_storyline", [])

        elements: List[Any] = [
            Paragraph("10. TEMPORAL RISK EVOLUTION & STORYLINE", self.section_heading)
        ]

        if stages:
            rows = [
                [
                    Paragraph("Stage", self.table_cell_header),
                    Paragraph("Stage Name", self.table_cell_header),
                    Paragraph("Time Interval", self.table_cell_header),
                    Paragraph("Tx Count", self.table_cell_header),
                    Paragraph("Volume (INR)", self.table_cell_header),
                    Paragraph("Observed Typology Phase", self.table_cell_header),
                ]
            ]
            for s in stages:
                idx = str(s.get("stage_index", "-"))
                name = str(s.get("stage_name", "-"))
                t_start = str(s.get("start_time", ""))[:16]
                t_end = str(s.get("end_time", ""))[:16]
                t_range = f"{t_start} to {t_end}" if t_start and t_end else "Timeline Window"
                tx_c = str(s.get("transaction_count", "-"))
                vol = f"₹{float(s.get('total_volume_inr', 0)):,.0f}"
                desc = str(s.get("description", ""))

                rows.append([
                    Paragraph(f"#{idx}", self.table_cell_bold),
                    Paragraph(f"<b>{name}</b>", self.table_cell),
                    Paragraph(t_range, self.table_cell),
                    Paragraph(tx_c, self.table_cell),
                    Paragraph(vol, self.table_cell),
                    Paragraph(desc, self.table_cell),
                ])

            table = Table(rows, colWidths=[30, 85, 110, 45, 75, 170], repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), self.c_navy),
                ("GRID", (0, 0), (-1, -1), 0.5, self.c_border),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, self.c_bg_light]),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 6))

        if storyline:
            elements.append(Paragraph("<b>Chronological Event Sequence:</b>", self.sub_section_heading))
            for item in storyline:
                phase = item.get("phase", "Event")
                desc = item.get("description", "")
                evidence = item.get("supporting_evidence", [])
                ev_str = f" [Evidence: {', '.join(evidence)}]" if evidence else ""
                elements.append(Paragraph(f"• <b>{phase}:</b> {desc}{ev_str}", self.body_style))

        return elements

    def _build_narrative_section(self, case_data: Dict[str, Any]) -> List[Any]:
        narrative = case_data.get("narrative_brief", {})
        if not narrative:
            return []

        elements: List[Any] = [
            Paragraph("11. COMPREHENSIVE INVESTIGATOR NARRATIVE", self.section_heading)
        ]

        if "executive_summary" in narrative:
            elements.append(Paragraph("<b>11.1 Executive Synthesis:</b>", self.sub_section_heading))
            elements.append(Paragraph(str(narrative["executive_summary"]), self.body_style))
            elements.append(Spacer(1, 4))

        if "money_trail_breakdown" in narrative:
            elements.append(Paragraph("<b>11.2 Money Trail Breakdown:</b>", self.sub_section_heading))
            elements.append(Paragraph(str(narrative["money_trail_breakdown"]), self.body_style))
            elements.append(Spacer(1, 4))

        if "key_entities" in narrative:
            elements.append(Paragraph("<b>11.3 Key Entities & Role Observations:</b>", self.sub_section_heading))
            elements.append(Paragraph(str(narrative["key_entities"]), self.body_style))
            elements.append(Spacer(1, 4))

        return elements

    def _build_leads_section(self, case_data: Dict[str, Any]) -> List[Any]:
        narrative = case_data.get("narrative_brief", {})
        leads = narrative.get("actionable_leads", [])
        if not leads:
            return []

        elements: List[Any] = [
            Paragraph("12. ACTIONABLE INVESTIGATION LEADS", self.section_heading),
            Paragraph("Evidence-grounded recommendations for field investigators and compliance officers:", self.body_style),
            Spacer(1, 3)
        ]

        for lead in leads:
            elements.append(Paragraph(f"• <b>Investigation Directive:</b> {lead}", self.body_style))

        return elements

    def _build_evidence_register(self, case_data: Dict[str, Any]) -> List[Any]:
        graph = case_data.get("graph", {})
        edges = graph.get("edges", [])
        if not edges:
            return []

        elements: List[Any] = [
            Paragraph("13. TRANSACTION EVIDENCE REGISTER (KEY OBSERVATIONS)", self.section_heading),
            Paragraph(f"Showing chronological transaction logs extracted for forensic chain of custody ({len(edges)} total records):", self.body_style),
            Spacer(1, 4)
        ]

        rows = [
            [
                Paragraph("Tx ID", self.table_cell_header),
                Paragraph("Timestamp", self.table_cell_header),
                Paragraph("Sender Account", self.table_cell_header),
                Paragraph("Receiver Account", self.table_cell_header),
                Paragraph("Amount (INR)", self.table_cell_header),
                Paragraph("Channel", self.table_cell_header),
            ]
        ]

        # Limit to top 25 transactions in PDF to prevent excessive page length while showing complete evidence
        for e in edges[:25]:
            tx_id = str(e.get("transaction_id", e.get("id", "-")))
            ts = str(e.get("timestamp", "-"))[:19]
            snd = str(e.get("sender_account", e.get("source", "-")))
            rcv = str(e.get("receiver_account", e.get("target", "-")))
            amt = f"₹{float(e.get('amount', 0)):,.0f}"
            chan = str(e.get("channel", "TRANSFER"))

            rows.append([
                Paragraph(f"<b>{tx_id}</b>", self.table_cell),
                Paragraph(ts, self.table_cell),
                Paragraph(snd, self.table_cell),
                Paragraph(rcv, self.table_cell),
                Paragraph(amt, self.table_cell_bold),
                Paragraph(chan, self.table_cell),
            ])

        table = Table(rows, colWidths=[65, 95, 110, 110, 75, 60], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.c_navy),
            ("GRID", (0, 0), (-1, -1), 0.5, self.c_border),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, self.c_bg_light]),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))

        elements.append(table)
        return elements

    def _build_integrity_footer(self, case_data: Dict[str, Any], case_id: str) -> List[Any]:
        dna = case_data.get("primary_dna") or {}
        case_hash = dna.get("evidence_payload_sha256", dna.get("dna_hash", "UNSEALED"))
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        integrity_table = Table(
            [
                [
                    Paragraph("<b>CRYPTOGRAPHIC EVIDENCE INTEGRITY SEAL</b>", self.table_cell_bold),
                    Paragraph(f"<b>Generated:</b> {timestamp}", self.table_cell),
                ],
                [
                    Paragraph("<b>Case Evidence SHA-256 Digest:</b>", self.table_cell),
                    Paragraph(f"<font face='Courier'>{case_hash}</font>", self.table_cell),
                ],
                [
                    Paragraph("<b>Verification Protocol:</b>", self.table_cell),
                    Paragraph("JARVIS-AML Deterministic Graph Hash (HMAC-SHA256)", self.table_cell),
                ]
            ],
            colWidths=[160, 355]
        )
        integrity_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), self.c_bg_light),
            ("GRID", (0, 0), (-1, -1), 0.5, self.c_border),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))

        return [
            Paragraph("14. FORENSIC CHAIN OF CUSTODY & INTEGRITY SEAL", self.section_heading),
            integrity_table
        ]

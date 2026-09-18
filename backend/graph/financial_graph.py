"""
Financial MultiGraph Engine using NetworkX MultiDiGraph.
Preserves multiple directed transactions between accounts with full metadata,
temporal filtering, upstream/downstream BFS exploration, and centrality calculations.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional, Set, Tuple
import networkx as nx
from backend.models.transaction import Transaction, Account, PaymentChannel, TransactionType, TransactionStatus


class FinancialMultiGraph:
    """
    High-performance directed multigraph representation of financial accounts and transactions.
    """

    def __init__(self):
        self.graph: nx.MultiDiGraph = nx.MultiDiGraph()
        self.transactions: Dict[str, Transaction] = {}
        self.accounts: Dict[str, Account] = {}

    def add_account(self, account: Account) -> None:
        """Register account node."""
        self.accounts[account.account_id] = account
        if not self.graph.has_node(account.account_id):
            self.graph.add_node(
                account.account_id,
                account_holder_name=account.account_holder_name or account.account_id,
                account_type=account.account_type or "SAVINGS",
                bank_name=account.bank_name or "HDFC Bank",
                ifsc_code=account.ifsc_code or "HDFC0001234",
                kyc_status=account.kyc_status or "VERIFIED",
                created_date=account.created_date,
                total_inflow=0.0,
                total_outflow=0.0,
            )

    def add_transaction(self, tx: Transaction) -> None:
        """Add a directed transaction edge between sender and receiver."""
        self.transactions[tx.transaction_id] = tx

        # Ensure sender node exists
        if not self.graph.has_node(tx.sender_account):
            self.add_account(Account(account_id=tx.sender_account))

        # Ensure receiver node exists
        if not self.graph.has_node(tx.receiver_account):
            self.add_account(Account(account_id=tx.receiver_account))

        # Update node inflow/outflow totals
        self.graph.nodes[tx.sender_account]["total_outflow"] = (
            self.graph.nodes[tx.sender_account].get("total_outflow", 0.0) + tx.amount
        )
        self.graph.nodes[tx.receiver_account]["total_inflow"] = (
            self.graph.nodes[tx.receiver_account].get("total_inflow", 0.0) + tx.amount
        )

        # Add directed multigraph edge
        self.graph.add_edge(
            tx.sender_account,
            tx.receiver_account,
            key=tx.transaction_id,
            transaction_id=tx.transaction_id,
            timestamp=tx.timestamp,
            amount=tx.amount,
            currency=tx.currency,
            channel=tx.channel.value if isinstance(tx.channel, PaymentChannel) else str(tx.channel),
            transaction_type=tx.transaction_type.value if isinstance(tx.transaction_type, TransactionType) else str(tx.transaction_type),
            status=tx.status.value if isinstance(tx.status, TransactionStatus) else str(tx.status),
            remarks=tx.remarks or "",
            metadata=tx.metadata or {},
        )

    def load_transactions(self, transactions: List[Transaction], accounts: Optional[List[Account]] = None) -> None:
        """Bulk load transactions and optional accounts."""
        if accounts:
            for acc in accounts:
                self.add_account(acc)
        for tx in transactions:
            self.add_transaction(tx)

    def get_node_count(self) -> int:
        return self.graph.number_of_nodes()

    def get_edge_count(self) -> int:
        return self.graph.number_of_edges()

    def get_accounts(self) -> List[str]:
        return list(self.graph.nodes())

    def get_all_transactions(self) -> List[Transaction]:
        return list(self.transactions.values())

    def get_incoming_transactions(self, account_id: str) -> List[Transaction]:
        """Get list of transactions where account is receiver, sorted chronologically."""
        if not self.graph.has_node(account_id):
            return []
        tx_list = []
        for u, v, key, data in self.graph.in_edges(account_id, data=True, keys=True):
            tx_id = data.get("transaction_id") or key
            if tx_id in self.transactions:
                tx_list.append(self.transactions[tx_id])
        return sorted(tx_list, key=lambda x: x.timestamp)

    def get_outgoing_transactions(self, account_id: str) -> List[Transaction]:
        """Get list of transactions where account is sender, sorted chronologically."""
        if not self.graph.has_node(account_id):
            return []
        tx_list = []
        for u, v, key, data in self.graph.out_edges(account_id, data=True, keys=True):
            tx_id = data.get("transaction_id") or key
            if tx_id in self.transactions:
                tx_list.append(self.transactions[tx_id])
        return sorted(tx_list, key=lambda x: x.timestamp)

    def get_account_metrics(self, account_id: str) -> Dict[str, Any]:
        """Calculate in-degree, out-degree, total amounts, dwell times, and forwarding ratio."""
        if not self.graph.has_node(account_id):
            return {
                "in_degree": 0, "out_degree": 0, "inflow_total": 0.0,
                "outflow_total": 0.0, "forwarding_ratio": 0.0, "avg_dwell_minutes": 0.0
            }

        in_txs = self.get_incoming_transactions(account_id)
        out_txs = self.get_outgoing_transactions(account_id)

        inflow_total = sum(tx.amount for tx in in_txs)
        outflow_total = sum(tx.amount for tx in out_txs)

        forwarding_ratio = (outflow_total / inflow_total) if inflow_total > 0 else 0.0

        # Calculate average dwell time between earliest in and earliest out
        dwell_times = []
        for in_tx in in_txs:
            for out_tx in out_txs:
                if out_tx.timestamp >= in_tx.timestamp:
                    diff_mins = (out_tx.timestamp - in_tx.timestamp).total_seconds() / 60.0
                    dwell_times.append(diff_mins)
                    break

        avg_dwell = sum(dwell_times) / len(dwell_times) if dwell_times else 0.0

        return {
            "in_degree": len(in_txs),
            "out_degree": len(out_txs),
            "inflow_total": inflow_total,
            "outflow_total": outflow_total,
            "forwarding_ratio": min(forwarding_ratio, 1.0),
            "avg_dwell_minutes": round(avg_dwell, 2),
        }

    def compute_centrality_metrics(self) -> Dict[str, Dict[str, float]]:
        """Compute betweenness, degree, and closeness centralities on simple directed projection."""
        if self.graph.number_of_nodes() == 0:
            return {}

        # Build simple directed graph for centrality
        simple_digraph = nx.DiGraph()
        for u, v, data in self.graph.edges(data=True):
            w = data.get("amount", 1.0)
            if simple_digraph.has_edge(u, v):
                simple_digraph[u][v]["weight"] += w
            else:
                simple_digraph.add_edge(u, v, weight=w)

        # Betweenness centrality
        betweenness = nx.betweenness_centrality(simple_digraph, normalized=True)
        in_deg_cent = nx.in_degree_centrality(simple_digraph)
        out_deg_cent = nx.out_degree_centrality(simple_digraph)

        metrics = {}
        for node in self.graph.nodes():
            metrics[node] = {
                "betweenness": round(betweenness.get(node, 0.0), 4),
                "in_degree_centrality": round(in_deg_cent.get(node, 0.0), 4),
                "out_degree_centrality": round(out_deg_cent.get(node, 0.0), 4),
            }
        return metrics

    def trace_upstream(self, target_account: str, max_depth: int = 3) -> Dict[str, Any]:
        """Bounded BFS backwards in time to trace upstream sources of funds."""
        if not self.graph.has_node(target_account):
            return {"nodes": [], "edges": []}

        visited_nodes: Set[str] = {target_account}
        collected_edges: List[Dict[str, Any]] = []
        queue: List[Tuple[str, int]] = [(target_account, 0)]

        while queue:
            curr_acc, depth = queue.pop(0)
            if depth >= max_depth:
                continue

            for u, v, key, data in self.graph.in_edges(curr_acc, data=True, keys=True):
                collected_edges.append({
                    "from": u,
                    "to": v,
                    "transaction_id": data.get("transaction_id", key),
                    "amount": data.get("amount", 0.0),
                    "timestamp": data.get("timestamp").isoformat() if isinstance(data.get("timestamp"), datetime) else str(data.get("timestamp")),
                    "channel": data.get("channel", "IMPS"),
                })
                if u not in visited_nodes:
                    visited_nodes.add(u)
                    queue.append((u, depth + 1))

        return {
            "focus_account": target_account,
            "direction": "UPSTREAM",
            "nodes": list(visited_nodes),
            "edges": collected_edges,
        }

    def trace_downstream(self, source_account: str, max_depth: int = 3) -> Dict[str, Any]:
        """Bounded BFS forwards in time to trace downstream destinations of funds."""
        if not self.graph.has_node(source_account):
            return {"nodes": [], "edges": []}

        visited_nodes: Set[str] = {source_account}
        collected_edges: List[Dict[str, Any]] = []
        queue: List[Tuple[str, int]] = [(source_account, 0)]

        while queue:
            curr_acc, depth = queue.pop(0)
            if depth >= max_depth:
                continue

            for u, v, key, data in self.graph.out_edges(curr_acc, data=True, keys=True):
                collected_edges.append({
                    "from": u,
                    "to": v,
                    "transaction_id": data.get("transaction_id", key),
                    "amount": data.get("amount", 0.0),
                    "timestamp": data.get("timestamp").isoformat() if isinstance(data.get("timestamp"), datetime) else str(data.get("timestamp")),
                    "channel": data.get("channel", "IMPS"),
                })
                if v not in visited_nodes:
                    visited_nodes.add(v)
                    queue.append((v, depth + 1))

        return {
            "focus_account": source_account,
            "direction": "DOWNSTREAM",
            "nodes": list(visited_nodes),
            "edges": collected_edges,
        }

    def extract_2hop_neighborhood(self, account_id: str) -> Dict[str, Any]:
        """Extract all 2-hop upstream and downstream accounts and connecting edges."""
        if not self.graph.has_node(account_id):
            return {"nodes": [], "edges": []}

        upstream = self.trace_upstream(account_id, max_depth=2)
        downstream = self.trace_downstream(account_id, max_depth=2)

        all_nodes = list(set(upstream["nodes"] + downstream["nodes"]))
        edge_map = {}
        for edge in upstream["edges"] + downstream["edges"]:
            edge_map[edge["transaction_id"]] = edge

        return {
            "focus_account": account_id,
            "nodes": all_nodes,
            "edges": list(edge_map.values()),
        }

    def detect_communities(self) -> List[Dict[str, Any]]:
        """Detect connected components and dense clusters on the undirected projection."""
        if self.graph.number_of_nodes() == 0:
            return []

        undirected = self.graph.to_undirected()
        components = list(nx.connected_components(undirected))
        
        communities = []
        for idx, comp in enumerate(components, 1):
            members = list(comp)
            subgraph = self.graph.subgraph(members)
            internal_vol = sum(d.get("amount", 0.0) for u, v, d in subgraph.edges(data=True))
            
            # External volume
            external_vol = 0.0
            for node in members:
                for u, v, d in self.graph.in_edges(node, data=True):
                    if u not in comp:
                        external_vol += d.get("amount", 0.0)
                for u, v, d in self.graph.out_edges(node, data=True):
                    if v not in comp:
                        external_vol += d.get("amount", 0.0)

            n = len(members)
            possible_edges = n * (n - 1) if n > 1 else 1
            density = round(subgraph.number_of_edges() / max(possible_edges, 1), 3)

            communities.append({
                "community_id": f"COMM_{idx:02d}",
                "members": members,
                "internal_volume_inr": round(internal_vol, 2),
                "external_volume_inr": round(external_vol, 2),
                "density": density,
                "size": len(members),
            })

        return sorted(communities, key=lambda x: x["internal_volume_inr"], reverse=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to rich structured JSON representation for UI and API."""
        centrality = self.compute_centrality_metrics()
        
        nodes_list = []
        for node_id, data in self.graph.nodes(data=True):
            metrics = self.get_account_metrics(node_id)
            cent = centrality.get(node_id, {})
            nodes_list.append({
                "id": node_id,
                "label": data.get("account_holder_name", node_id),
                "type": data.get("account_type", "SAVINGS"),
                "bank": data.get("bank_name", "HDFC Bank"),
                "ifsc": data.get("ifsc_code", "HDFC0001234"),
                "kyc_status": data.get("kyc_status", "VERIFIED"),
                "inflow_total": metrics["inflow_total"],
                "outflow_total": metrics["outflow_total"],
                "in_degree": metrics["in_degree"],
                "out_degree": metrics["out_degree"],
                "forwarding_ratio": metrics["forwarding_ratio"],
                "avg_dwell_minutes": metrics["avg_dwell_minutes"],
                "betweenness": cent.get("betweenness", 0.0),
            })

        edges_list = []
        for u, v, key, data in self.graph.edges(data=True, keys=True):
            ts = data.get("timestamp")
            edges_list.append({
                "id": data.get("transaction_id", key),
                "source": u,
                "target": v,
                "amount": data.get("amount", 0.0),
                "currency": data.get("currency", "INR"),
                "channel": data.get("channel", "IMPS"),
                "type": data.get("transaction_type", "TRANSFER"),
                "status": data.get("status", "COMPLETED"),
                "timestamp": ts.isoformat() if isinstance(ts, datetime) else str(ts),
                "remarks": data.get("remarks", ""),
            })

        return {
            "nodes": nodes_list,
            "edges": edges_list,
            "node_count": len(nodes_list),
            "edge_count": len(edges_list),
        }

    def clone_and_remove(
        self,
        account_id: Optional[str] = None,
        transaction_id: Optional[str] = None
    ) -> 'FinancialMultiGraph':
        """
        Create a clean copy of the financial graph with an account (and its incident edges)
        or a specific transaction edge removed for what-if simulation purposes.
        """
        sim_graph = FinancialMultiGraph()
        for acc_id, acc in self.accounts.items():
            if account_id and acc_id == account_id:
                continue
            sim_graph.add_account(Account(
                account_id=acc.account_id,
                account_holder_name=acc.account_holder_name,
                account_type=acc.account_type,
                bank_name=acc.bank_name,
                ifsc_code=acc.ifsc_code,
                kyc_status=acc.kyc_status,
                created_date=acc.created_date,
            ))
        for tx in self.transactions.values():
            if transaction_id and tx.transaction_id == transaction_id:
                continue
            if account_id and (tx.sender_account == account_id or tx.receiver_account == account_id):
                continue
            sim_graph.add_transaction(tx)
        return sim_graph


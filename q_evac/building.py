"""
Building simulation model for Q-Evac.
Defines the building topology, corridor junctions, emergency exits,
distance values, congestion metrics, and corridor block statuses.
"""

from typing import Dict, List, Tuple, Any, Optional
import networkx as nx


class Corridor:
    """Represents a corridor connecting two junctions in the building."""
    def __init__(
        self,
        id_: str,
        name: str,
        u: str,
        v: str,
        distance: float,
        congestion: float = 1.0,
        is_blocked: bool = False
    ):
        self.id = id_
        self.name = name
        self.u = u
        self.v = v
        self.distance = float(distance)
        self.congestion = float(congestion)  # scale 0 to 10
        self.is_blocked = bool(is_blocked)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "u": self.u,
            "v": self.v,
            "distance": self.distance,
            "congestion": self.congestion,
            "is_blocked": self.is_blocked,
        }


class Building:
    """Fictional 8-junction building graph with 3 emergency exits."""

    # Default node definitions: (id, label, type, (x, y))
    DEFAULT_NODES = [
        ("LOBBY", "Main Lobby", "start", (1.0, 3.0)),
        ("HALL_A", "Hallway Alpha", "junction", (3.0, 4.5)),
        ("ATRIUM", "Central Atrium", "junction", (3.0, 2.5)),
        ("HALL_B", "Hallway Beta", "junction", (3.0, 0.5)),
        ("WING_E", "East Wing", "junction", (5.5, 3.8)),
        ("WING_W", "West Wing", "junction", (5.5, 1.2)),
        ("EXIT_A", "Exit North (A)", "exit", (8.0, 4.8)),
        ("EXIT_B", "Exit East (B)", "exit", (8.0, 2.5)),
        ("EXIT_C", "Exit South (C)", "exit", (8.0, 0.2)),
    ]

    # Default corridors: (id, name, u, v, distance_meters, default_congestion)
    DEFAULT_CORRIDORS = [
        ("C1", "Lobby - Hall Alpha", "LOBBY", "HALL_A", 15.0, 2.0),
        ("C2", "Lobby - Central Atrium", "LOBBY", "ATRIUM", 12.0, 4.0),
        ("C3", "Lobby - Hall Beta", "LOBBY", "HALL_B", 18.0, 1.0),
        ("C4", "Hall Alpha - East Wing", "HALL_A", "WING_E", 14.0, 2.0),
        ("C5", "Atrium - East Wing", "ATRIUM", "WING_E", 10.0, 5.0),
        ("C6", "Atrium - West Wing", "ATRIUM", "WING_W", 10.0, 3.0),
        ("C7", "Hall Beta - West Wing", "HALL_B", "WING_W", 16.0, 1.0),
        ("C8", "Hall Alpha - Exit North", "HALL_A", "EXIT_A", 12.0, 1.0),
        ("C9", "East Wing - Exit North", "WING_E", "EXIT_A", 15.0, 2.0),
        ("C10", "East Wing - Exit East", "WING_E", "EXIT_B", 11.0, 3.0),
        ("C11", "West Wing - Exit East", "WING_W", "EXIT_B", 13.0, 2.0),
        ("C12", "West Wing - Exit South", "WING_W", "EXIT_C", 10.0, 1.0),
        ("C13", "Hall Beta - Exit South", "HALL_B", "EXIT_C", 14.0, 2.0),
        ("C14", "Hall Alpha - Atrium Link", "HALL_A", "ATRIUM", 8.0, 3.0),
        ("C15", "Atrium - Hall Beta Link", "ATRIUM", "HALL_B", 8.0, 2.0),
    ]

    def __init__(self, congestion_weight: float = 1.0):
        self.congestion_weight = float(congestion_weight)
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.corridors: Dict[str, Corridor] = {}
        self._init_default_layout()

    def _init_default_layout(self) -> None:
        """Initializes default node coordinates and corridor connections."""
        self.nodes = {
            id_: {
                "id": id_,
                "label": label,
                "type": type_,
                "pos": pos
            }
            for id_, label, type_, pos in self.DEFAULT_NODES
        }
        self.corridors = {
            c[0]: Corridor(c[0], c[1], c[2], c[3], c[4], c[5], False)
            for c in self.DEFAULT_CORRIDORS
        }

    def reset_to_default(self) -> None:
        """Resets all corridors to unblocked and default congestion levels."""
        self._init_default_layout()

    def set_corridor_blocked(self, corridor_id: str, blocked: bool) -> None:
        """Sets blocked state for a corridor by its ID."""
        if corridor_id in self.corridors:
            self.corridors[corridor_id].is_blocked = blocked

    def set_corridor_congestion(self, corridor_id: str, level: float) -> None:
        """Sets congestion score (0 to 10) for a corridor."""
        if corridor_id in self.corridors:
            self.corridors[corridor_id].congestion = max(0.0, min(10.0, float(level)))

    def apply_preset(self, preset_name: str) -> None:
        """Applies predefined demonstration scenarios for quick testing and judges."""
        self.reset_to_default()
        if preset_name == "All Clear (Normal)":
            pass  # Default state
        elif preset_name == "Shortest Exit Blocked":
            # Direct path to Exit North via Hallway Alpha is blocked
            self.set_corridor_blocked("C8", True)
        elif preset_name == "Heavy Atrium & North Congestion":
            # Atrium and North route crowded, pushing traffic to Hallway Beta -> South
            self.set_corridor_congestion("C1", 9.0)
            self.set_corridor_congestion("C2", 9.0)
            self.set_corridor_congestion("C8", 8.0)
        elif preset_name == "Full Isolation (No Reachable Exit)":
            # All exit-adjacent corridors blocked
            self.set_corridor_blocked("C8", True)
            self.set_corridor_blocked("C9", True)
            self.set_corridor_blocked("C10", True)
            self.set_corridor_blocked("C11", True)
            self.set_corridor_blocked("C12", True)
            self.set_corridor_blocked("C13", True)
        elif preset_name == "Single Viable Exit (Exit South Only)":
            # Block exits A and B
            self.set_corridor_blocked("C8", True)
            self.set_corridor_blocked("C9", True)
            self.set_corridor_blocked("C10", True)
            self.set_corridor_blocked("C11", True)

    def get_corridor_between(self, u: str, v: str) -> Optional[Corridor]:
        """Finds the corridor connecting nodes u and v."""
        for c in self.corridors.values():
            if (c.u == u and c.v == v) or (c.u == v and c.v == u):
                return c
        return None

    def get_candidate_routes(self) -> List[Dict[str, Any]]:
        """
        Defines exactly 4 key candidate evacuation routes from LOBBY to exits.
        These are encoded as 2-qubit states:
          |00> -> Route A (North Express)
          |01> -> Route B (Atrium East)
          |10> -> Route C (Beta South)
          |11> -> Route D (Cross Wing East)
        """
        raw_candidates = [
            {
                "bitstring": "00",
                "label": "Route 0 (|00⟩): North Express",
                "description": "Lobby -> Hallway Alpha -> Exit North (A)",
                "target_exit": "EXIT_A",
                "path": ["LOBBY", "HALL_A", "EXIT_A"],
            },
            {
                "bitstring": "01",
                "label": "Route 1 (|01⟩): Atrium East",
                "description": "Lobby -> Central Atrium -> East Wing -> Exit East (B)",
                "target_exit": "EXIT_B",
                "path": ["LOBBY", "ATRIUM", "WING_E", "EXIT_B"],
            },
            {
                "bitstring": "10",
                "label": "Route 2 (|10⟩): Beta South",
                "description": "Lobby -> Hallway Beta -> Exit South (C)",
                "target_exit": "EXIT_C",
                "path": ["LOBBY", "HALL_B", "EXIT_C"],
            },
            {
                "bitstring": "11",
                "label": "Route 3 (|11⟩): Cross Atrium South",
                "description": "Lobby -> Central Atrium -> West Wing -> Exit South (C)",
                "target_exit": "EXIT_C",
                "path": ["LOBBY", "ATRIUM", "WING_W", "EXIT_C"],
            },
        ]

        evaluated = []
        for cand in raw_candidates:
            path = cand["path"]
            tot_dist = 0.0
            tot_cong = 0.0
            is_blocked = False
            blocked_reasons = []

            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                corr = self.get_corridor_between(u, v)
                if corr is None:
                    is_blocked = True
                    blocked_reasons.append(f"No corridor {u}-{v}")
                else:
                    tot_dist += corr.distance
                    tot_cong += corr.congestion
                    if corr.is_blocked:
                        is_blocked = True
                        blocked_reasons.append(f"{corr.name} is blocked")

            cost = tot_dist + (self.congestion_weight * tot_cong)
            evaluated.append({
                "bitstring": cand["bitstring"],
                "index": int(cand["bitstring"], 2),
                "label": cand["label"],
                "description": cand["description"],
                "target_exit": cand["target_exit"],
                "path": path,
                "distance": round(tot_dist, 1),
                "congestion": round(tot_cong, 1),
                "is_blocked": is_blocked,
                "is_available": not is_blocked,
                "cost": round(cost, 2),
                "blocked_reasons": blocked_reasons,
            })

        return evaluated

    def to_networkx(self) -> nx.Graph:
        """
        Builds a NetworkX graph representation of the building.
        Available corridors have edge weight = distance + (congestion_weight * congestion).
        Blocked corridors are either excluded or flagged.
        """
        G = nx.Graph()
        for node_id, data in self.nodes.items():
            G.add_node(
                node_id,
                label=data["label"],
                type=data["type"],
                pos=data["pos"]
            )

        for c in self.corridors.values():
            cost = c.distance + (self.congestion_weight * c.congestion)
            G.add_edge(
                c.u,
                c.v,
                id=c.id,
                name=c.name,
                distance=c.distance,
                congestion=c.congestion,
                is_blocked=c.is_blocked,
                cost=cost,
                weight=cost if not c.is_blocked else float("inf")
            )

        return G

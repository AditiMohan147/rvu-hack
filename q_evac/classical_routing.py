"""
Classical route selection algorithm for Q-Evac using NetworkX Dijkstra shortest path.
Calculates available paths to all emergency exits and identifies the lowest-cost evacuation path.
"""

from typing import Dict, List, Optional, Any
import networkx as nx
from building import Building


def find_optimal_evacuation_route(
    building: Building,
    start_node: str = "LOBBY"
) -> Dict[str, Any]:
    """
    Finds the lowest-cost available evacuation path from start_node to any emergency exit.

    Formula:
      Route Cost = Total Distance + (Congestion Weight * Total Congestion Penalty)

    Returns:
      Dictionary containing:
        - success (bool): True if at least one exit is reachable.
        - selected_route (dict): The lowest-cost route details or None.
        - all_exit_routes (dict): Routes found for each exit.
        - formula_explanation (str): Human-friendly explanation.
        - disclaimer (str): Educational simulation notice.
    """
    G = building.to_networkx()

    # Create sub-graph with only unblocked corridors
    available_edges = [
        (u, v, d) for u, v, d in G.edges(data=True) if not d.get("is_blocked", False)
    ]
    G_available = nx.Graph()
    for n, d in G.nodes(data=True):
        G_available.add_node(n, **d)
    G_available.add_edges_from(available_edges)

    exit_nodes = [
        n for n, d in G.nodes(data=True) if d.get("type") == "exit"
    ]

    all_exit_routes = {}
    best_route: Optional[Dict[str, Any]] = None
    lowest_cost = float("inf")

    for exit_node in exit_nodes:
        if nx.has_path(G_available, start_node, exit_node):
            try:
                # Dijkstra shortest path using edge cost (distance + congestion_weight * congestion)
                path = nx.shortest_path(
                    G_available,
                    source=start_node,
                    target=exit_node,
                    weight="weight"
                )

                # Compute exact metrics along path
                total_distance = 0.0
                total_congestion = 0.0
                edge_breakdown = []

                for i in range(len(path) - 1):
                    u, v = path[i], path[i + 1]
                    edge_data = G[u][v]
                    dist = edge_data["distance"]
                    cong = edge_data["congestion"]
                    cost = dist + (building.congestion_weight * cong)
                    total_distance += dist
                    total_congestion += cong
                    edge_breakdown.append({
                        "from": u,
                        "to": v,
                        "name": edge_data["name"],
                        "distance": dist,
                        "congestion": cong,
                        "cost": cost
                    })

                total_cost = total_distance + (building.congestion_weight * total_congestion)

                route_info = {
                    "exit_node": exit_node,
                    "exit_label": G.nodes[exit_node]["label"],
                    "path": path,
                    "path_labels": [G.nodes[n]["label"] for n in path],
                    "total_distance": round(total_distance, 1),
                    "total_congestion": round(total_congestion, 1),
                    "congestion_weight": building.congestion_weight,
                    "total_cost": round(total_cost, 2),
                    "edge_breakdown": edge_breakdown,
                    "reachable": True
                }
                all_exit_routes[exit_node] = route_info

                if total_cost < lowest_cost:
                    lowest_cost = total_cost
                    best_route = route_info

            except nx.NetworkXNoPath:
                all_exit_routes[exit_node] = {
                    "exit_node": exit_node,
                    "exit_label": G.nodes[exit_node]["label"],
                    "reachable": False,
                    "error": "No reachable path due to corridor blockage."
                }
        else:
            all_exit_routes[exit_node] = {
                "exit_node": exit_node,
                "exit_label": G.nodes[exit_node]["label"],
                "reachable": False,
                "error": "No reachable path due to corridor blockage."
            }

    success = best_route is not None

    formula_exp = (
        f"Route Cost = Total Distance ({best_route['total_distance'] if best_route else 0}m) "
        f"+ [Congestion Weight ({building.congestion_weight}) × Total Congestion ({best_route['total_congestion'] if best_route else 0})]. "
        "Lower cost means a route is shorter and less overcrowded."
    )

    disclaimer = (
        "Educational Simulation Only: The selected route is the lowest-cost path "
        "under the mathematical weights of this simulation. It does not replace "
        "official architectural evacuation codes or emergency personnel guidance."
    )

    return {
        "success": success,
        "start_node": start_node,
        "selected_route": best_route,
        "all_exit_routes": all_exit_routes,
        "lowest_cost": lowest_cost if success else None,
        "formula_explanation": formula_exp,
        "disclaimer": disclaimer,
    }

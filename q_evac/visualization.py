"""
Visualization module for Q-Evac.
Provides publication-quality Matplotlib figures for:
1. Interactive Building Map with corridor statuses, congestion, and highlighted routes.
2. Quantum Measurement Results histogram with marked-state highlights.
3. Qiskit Quantum Circuit diagram.
"""

from typing import Dict, List, Optional, Any
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import networkx as nx
from qiskit import QuantumCircuit
from building import Building


def plot_building_map(
    building: Building,
    selected_path: Optional[List[str]] = None,
    title: Optional[str] = None,
    figsize: tuple = (11, 7)
) -> plt.Figure:
    """
    Renders the simulated building network graph with distinct visual cues
    for start location, exits, junctions, blocked passages, congestion levels,
    and the optimal evacuation route.

    Args:
        building: Building simulation model.
        selected_path: List of node IDs along the chosen evacuation route (e.g. ['LOBBY', 'HALL_A', 'EXIT_A']).
        title: Optional custom figure title.
        figsize: Figure dimensions.

    Returns:
        matplotlib.figure.Figure: The complete building map figure.
    """
    fig, ax = plt.subplots(figsize=figsize, facecolor="#0f172a")
    ax.set_facecolor("#0f172a")

    # Extract positions from building nodes
    pos = {n_id: data["pos"] for n_id, data in building.nodes.items()}

    # Separate corridors into categories
    unblocked_corridors = [c for c in building.corridors.values() if not c.is_blocked]
    blocked_corridors = [c for c in building.corridors.values() if c.is_blocked]

    # Draw unblocked corridors with color and width reflecting congestion
    for c in unblocked_corridors:
        p1 = pos[c.u]
        p2 = pos[c.v]
        # Congestion color gradient: low (green) -> medium (amber) -> high (orange/red)
        if c.congestion <= 2.0:
            edge_color = "#22c55e"  # Emerald green
            lw = 2.5
        elif c.congestion <= 5.0:
            edge_color = "#f59e0b"  # Amber
            lw = 3.5
        else:
            edge_color = "#f97316"  # Orange
            lw = 4.5

        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=edge_color, linewidth=lw, alpha=0.85, zorder=2)

        # Corridor label: distance and congestion
        mid_x = (p1[0] + p2[0]) / 2.0
        mid_y = (p1[1] + p2[1]) / 2.0
        ax.text(
            mid_x, mid_y,
            f"{c.distance:.0f}m | c:{c.congestion:.0f}",
            fontsize=8,
            color="#cbd5e1",
            ha="center",
            va="center",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="#1e293b", edgecolor="#334155", alpha=0.85),
            zorder=3
        )

    # Draw blocked corridors (thick dashed red line with 'X' markers)
    for c in blocked_corridors:
        p1 = pos[c.u]
        p2 = pos[c.v]
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="#ef4444", linewidth=3.5, linestyle="--", alpha=0.9, zorder=2)
        mid_x = (p1[0] + p2[0]) / 2.0
        mid_y = (p1[1] + p2[1]) / 2.0
        ax.scatter([mid_x], [mid_y], marker="X", s=180, color="#ef4444", edgecolors="#ffffff", linewidths=1.5, zorder=4)
        ax.text(
            mid_x, mid_y - 0.22,
            f"BLOCKED\n({c.distance:.0f}m)",
            fontsize=7.5,
            fontweight="bold",
            color="#fca5a5",
            ha="center",
            va="top",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="#450a0a", edgecolor="#ef4444", alpha=0.9),
            zorder=4
        )

    # Highlight selected evacuation route if provided
    if selected_path and len(selected_path) > 1:
        path_xs = [pos[nid][0] for nid in selected_path]
        path_ys = [pos[nid][1] for nid in selected_path]
        # Glowing cyan / gold path
        ax.plot(path_xs, path_ys, color="#06b6d4", linewidth=7.0, alpha=0.5, zorder=5)
        ax.plot(path_xs, path_ys, color="#38bdf8", linewidth=3.5, linestyle="-", alpha=0.95, zorder=6)

    # Draw Nodes: Start, Junctions, Exits
    for n_id, data in building.nodes.items():
        x, y = data["pos"]
        node_type = data["type"]
        label = data["label"]

        if node_type == "start":
            node_color = "#10b981"  # Vibrant green
            border_color = "#ecfdf5"
            size = 1200
            shape = "o"
            badge = "START"
        elif node_type == "exit":
            node_color = "#f43f5e"  # Rose / red
            border_color = "#fff1f2"
            size = 1400
            shape = "s"
            badge = "EXIT"
        else:
            node_color = "#3b82f6"  # Slate Blue
            border_color = "#eff6ff"
            size = 900
            shape = "o"
            badge = None

        if shape == "s":
            ax.scatter([x], [y], s=size, c=node_color, marker="s", edgecolors=border_color, linewidths=2.5, zorder=7)
        else:
            ax.scatter([x], [y], s=size, c=node_color, marker="o", edgecolors=border_color, linewidths=2.5, zorder=7)

        # Label inside or next to node
        offset_y = 0.32 if node_type != "exit" else 0.35
        display_text = f"{label}\n[{badge}]" if badge else label
        ax.text(
            x, y + offset_y,
            display_text,
            fontsize=8.5,
            fontweight="bold",
            color="#ffffff",
            ha="center",
            va="bottom",
            bbox=dict(boxstyle="round,pad=0.25", facecolor="#1e293b", edgecolor=node_color, alpha=0.9),
            zorder=8
        )

    # Custom Legend
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label='Start Location (Lobby)',
               markerfacecolor='#10b981', markeredgecolor='#ffffff', markersize=12),
        Line2D([0], [0], marker='s', color='w', label='Emergency Exit',
               markerfacecolor='#f43f5e', markeredgecolor='#ffffff', markersize=12),
        Line2D([0], [0], marker='o', color='w', label='Corridor Junction',
               markerfacecolor='#3b82f6', markeredgecolor='#ffffff', markersize=10),
        Line2D([0], [0], color='#22c55e', lw=3, label='Clear Corridor (Low Congestion)'),
        Line2D([0], [0], color='#f59e0b', lw=3.5, label='Congested Corridor'),
        Line2D([0], [0], color='#ef4444', lw=3, linestyle='--', label='Blocked Corridor (X)'),
    ]
    if selected_path:
        legend_elements.append(
            Line2D([0], [0], color='#38bdf8', lw=4, label='Selected Evacuation Route')
        )

    leg = ax.legend(
        handles=legend_elements,
        loc="upper left",
        facecolor="#1e293b",
        edgecolor="#334155",
        fontsize=8.5,
        labelcolor="#e2e8f0",
        framealpha=0.95
    )
    leg.get_frame().set_linewidth(1.0)

    # Margins and axes styling
    ax.set_xlim(0.0, 9.2)
    ax.set_ylim(-0.8, 5.8)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    default_title = "Building Topology & Emergency Evacuation Graph"
    ax.set_title(title or default_title, fontsize=13, fontweight="bold", color="#f8fafc", pad=15)
    plt.tight_layout()
    return fig


def plot_quantum_counts(
    counts: Dict[str, int],
    marked_bitstrings: List[str],
    shots: int = 1024,
    title: Optional[str] = None,
    figsize: tuple = (9, 5)
) -> plt.Figure:
    """
    Renders an informative histogram of Qiskit Aer simulator measurement results.
    Highlights marked candidate routes with distinct colors and displays
    exact counts and percentage probabilities atop each bar.

    Args:
        counts: Dictionary of bitstring counts (e.g. {'00': 1024, '01': 0, ...}).
        marked_bitstrings: List of bitstrings satisfying search conditions.
        shots: Total measurement shots executed on Aer.
        title: Optional figure title.
        figsize: Figure dimensions.

    Returns:
        matplotlib.figure.Figure: The measurement bar chart.
    """
    fig, ax = plt.subplots(figsize=figsize, facecolor="#0f172a")
    ax.set_facecolor("#0f172a")

    states = ["00", "01", "10", "11"]
    route_names = {
        "00": "Route 0: North Exp (Exit A)",
        "01": "Route 1: Atrium East (Exit B)",
        "10": "Route 2: Beta South (Exit C)",
        "11": "Route 3: Cross South (Exit C)",
    }

    values = [counts.get(s, 0) for s in states]
    percentages = [(v / shots) * 100.0 for v in values]

    # Bar colors: Emerald for marked, Slate for unmarked
    bar_colors = []
    bar_edges = []
    for s in states:
        if s in marked_bitstrings:
            bar_colors.append("#10b981")  # Vibrant Green for marked
            bar_edges.append("#34d399")
        else:
            bar_colors.append("#334155")  # Dark Slate for unmarked
            bar_edges.append("#64748b")

    bars = ax.bar(range(len(states)), values, color=bar_colors, edgecolor=bar_edges, linewidth=1.5, width=0.55, zorder=3)

    # Reference baseline: uniform 25% (shots / 4)
    uniform_val = shots / 4.0
    ax.axhline(
        uniform_val,
        color="#94a3b8",
        linestyle=":",
        linewidth=1.5,
        alpha=0.75,
        label=f"Uniform Baseline (25% = {int(uniform_val)} shots)",
        zorder=2
    )

    # Bar labels
    max_val = max(values) if values else 1
    y_limit = max(shots * 1.05, max_val * 1.18)
    ax.set_ylim(0, y_limit)

    for i, bar in enumerate(bars):
        h = bar.get_height()
        pct = percentages[i]
        state = states[i]
        status = "★ MARKED" if state in marked_bitstrings else "UNMARKED"
        label_color = "#34d399" if state in marked_bitstrings else "#cbd5e1"

        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            h + (y_limit * 0.02),
            f"{int(h)} ({pct:.1f}%)\n{status}",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="bold",
            color=label_color,
            zorder=4
        )

    # X-Axis custom tick labels
    x_labels = [f"|{s}⟩\n{route_names[s]}" for s in states]
    ax.set_xticks(range(len(states)))
    ax.set_xticklabels(x_labels, fontsize=8.5, color="#e2e8f0", fontweight="medium")

    # Grid and Spines
    ax.yaxis.grid(True, linestyle="--", alpha=0.2, color="#94a3b8", zorder=1)
    ax.xaxis.grid(False)
    for spine in ax.spines.values():
        spine.set_color("#334155")

    ax.set_ylabel("Measurement Counts (Shots)", fontsize=10, color="#94a3b8", labelpad=8)
    ax.tick_params(axis="y", colors="#94a3b8", labelsize=9)

    leg = ax.legend(
        loc="upper right",
        facecolor="#1e293b",
        edgecolor="#334155",
        fontsize=8.5,
        labelcolor="#cbd5e1"
    )
    leg.get_frame().set_linewidth(1.0)

    num_marked = len(marked_bitstrings)
    sub = f"Shots = {shots} | Marked Candidates: {num_marked}/4 ({', '.join(marked_bitstrings) if marked_bitstrings else 'None'})"
    full_title = f"{title or 'Qiskit Aer Grover Search Measurement Counts'}\n({sub})"
    ax.set_title(full_title, fontsize=11.5, fontweight="bold", color="#f8fafc", pad=12)

    plt.tight_layout()
    return fig


def plot_quantum_circuit(
    circuit: QuantumCircuit,
    figsize: tuple = (10, 3.5)
) -> plt.Figure:
    """
    Renders the quantum circuit using Qiskit's Matplotlib drawer.

    Args:
        circuit: The QuantumCircuit object.
        figsize: Figure dimensions.

    Returns:
        matplotlib.figure.Figure: The rendered circuit figure.
    """
    try:
        fig = circuit.draw(output="mpl", style="iqp")
        return fig
    except Exception:
        # Fallback to standard mpl drawer
        try:
            fig = circuit.draw(output="mpl")
            return fig
        except Exception:
            # Fallback figure with text representation
            fig, ax = plt.subplots(figsize=figsize, facecolor="#0f172a")
            ax.set_facecolor("#0f172a")
            ax.text(
                0.5, 0.5,
                str(circuit.draw(output="text")),
                family="monospace",
                fontsize=9,
                color="#38bdf8",
                ha="center",
                va="center",
                wrap=True
            )
            ax.axis("off")
            ax.set_title("Quantum Search Circuit (Grover)", color="#ffffff", fontsize=11, fontweight="bold")
            return fig

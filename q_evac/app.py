"""
Q-Evac: Quantum-Based Emergency Exit Selection
Interactive Streamlit Dashboard
RV University Qiskit Quantum Computing Hackathon
"""

import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from building import Building
from classical_routing import find_optimal_evacuation_route
from quantum_search import run_quantum_search
from visualization import plot_building_map, plot_quantum_counts, plot_quantum_circuit

# Page Configuration
st.set_page_config(
    page_title="Q-Evac | Quantum Emergency Exit Selection",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Hackathon UI
st.markdown("""
<style>
    /* Dark glassmorphism & accent styling */
    .metric-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
        border: 1px solid rgba(56, 189, 248, 0.25);
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
        margin-bottom: 12px;
    }
    .metric-title {
        color: #94a3b8;
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .metric-value {
        color: #38bdf8;
        font-size: 1.55rem;
        font-weight: 700;
    }
    .metric-sub {
        color: #64748b;
        font-size: 0.78rem;
        margin-top: 2px;
    }
    .disclaimer-banner {
        background: linear-gradient(90deg, rgba(234, 88, 12, 0.15) 0%, rgba(220, 38, 38, 0.15) 100%);
        border-left: 4px solid #f97316;
        padding: 10px 16px;
        border-radius: 4px;
        margin-bottom: 20px;
        color: #fdba74;
        font-size: 0.86rem;
    }
    .badge-clear {
        background-color: #14532d;
        color: #86efac;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-blocked {
        background-color: #7f1d1d;
        color: #fca5a5;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-quantum {
        background-color: #1e1b4b;
        color: #a5b4fc;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# Session State Initialization
if "building" not in st.session_state:
    st.session_state.building = Building()

if "preset_selected" not in st.session_state:
    st.session_state.preset_selected = "All Clear (Normal)"


# Helper Callbacks
def apply_preset_callback():
    preset = st.session_state.preset_choice
    st.session_state.building.apply_preset(preset)
    st.session_state.preset_selected = preset


def reset_callback():
    st.session_state.building.reset_to_default()
    st.session_state.preset_selected = "All Clear (Normal)"


# SIDEBAR CONTROLS
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/quantum-computing.png", width=64)
    st.title("Emergency Controls")
    st.caption("RV University Qiskit Hackathon Prototype")

    st.markdown("---")
    st.subheader("🎯 Scenario Presets")
    preset_options = [
        "All Clear (Normal)",
        "Shortest Exit Blocked",
        "Heavy Atrium & North Congestion",
        "Single Viable Exit (Exit South Only)",
        "Full Isolation (No Reachable Exit)",
    ]

    current_idx = preset_options.index(st.session_state.preset_selected) if st.session_state.preset_selected in preset_options else 0
    st.selectbox(
        "Load Emergency Preset:",
        options=preset_options,
        index=current_idx,
        key="preset_choice",
        on_change=apply_preset_callback,
        help="Quickly demonstrate key emergency and algorithm behaviors for hackathon judges."
    )

    if st.button("🔄 Reset Building to Default", use_container_width=True, on_click=reset_callback):
        st.success("Building topology reset to default clear conditions.")

    st.markdown("---")
    st.subheader("⚙️ Routing Parameters")
    
    start_node = st.selectbox(
        "Evacuation Start Location:",
        options=list(st.session_state.building.nodes.keys()),
        index=0,
        format_func=lambda x: f"{x} - {st.session_state.building.nodes[x]['label']}"
    )

    congestion_weight = st.slider(
        "Congestion Penalty Weight (w):",
        min_value=0.0,
        max_value=3.0,
        value=float(st.session_state.building.congestion_weight),
        step=0.1,
        help="Multiplier for corridor congestion in the cost formula: Cost = Distance + (w * Congestion)"
    )
    st.session_state.building.congestion_weight = congestion_weight

    st.markdown("---")
    st.subheader("⚛️ Quantum Simulator Settings")
    
    shots = st.select_slider(
        "Qiskit Aer Shots:",
        options=[256, 512, 1024, 2048, 4096],
        value=1024,
        help="Number of circuit measurement repetitions executed on Qiskit AerSimulator."
    )

    auto_threshold = st.checkbox("Auto-tune Cost Threshold", value=True, help="Automatically sets threshold to find the lowest available route.")
    
    # Calculate candidate costs for reference
    current_candidates = st.session_state.building.get_candidate_routes()
    avail_costs = [c["cost"] for c in current_candidates if c["is_available"]]
    min_avail_cost = min(avail_costs) if avail_costs else 30.0

    if auto_threshold:
        cost_threshold = float(min_avail_cost)
        st.caption(f"Active Oracle Threshold: **≤ {cost_threshold:.1f}**")
    else:
        cost_threshold = st.slider(
            "Oracle Cost Threshold (C_max):",
            min_value=15.0,
            max_value=60.0,
            value=float(min_avail_cost),
            step=1.0,
            help="Candidate routes with cost <= threshold and not blocked are marked by the Grover oracle."
        )

    st.markdown("---")
    with st.expander("🚧 Individual Corridor Controls"):
        st.caption("Manually toggle blockages and adjust congestion for each passage.")
        for cid, corr in sorted(st.session_state.building.corridors.items()):
            col_b, col_c = st.columns([1, 2])
            with col_b:
                is_bl = st.checkbox(
                    f"{cid} Blocked",
                    value=corr.is_blocked,
                    key=f"blk_{cid}",
                    help=f"{corr.name} ({corr.distance}m)"
                )
                st.session_state.building.set_corridor_blocked(cid, is_bl)
            with col_c:
                c_val = st.slider(
                    f"{cid} Congestion",
                    min_value=0.0,
                    max_value=10.0,
                    value=float(corr.congestion),
                    step=1.0,
                    key=f"cng_{cid}"
                )
                st.session_state.building.set_corridor_congestion(cid, c_val)


# RUN CORE ENGINES
building = st.session_state.building
classical_res = find_optimal_evacuation_route(building, start_node=start_node)
quantum_res = run_quantum_search(building, cost_threshold=cost_threshold, shots=shots, seed=42)

# MAIN CONTENT
st.title("🚨 Q-Evac: Quantum-Based Emergency Exit Selection")
st.markdown("### Intelligent Evacuation Routing via NetworkX Shortest Path & Qiskit Grover Search")

# Mandatory Safety Disclaimer Banner
st.markdown(
    '<div class="disclaimer-banner">'
    '<strong>⚠️ Educational Hackathon Prototype:</strong> This software is a conceptual simulation developed for the '
    'RV University Qiskit Quantum Computing Hackathon. It demonstrates quantum candidate search algorithms and classical graph routing. '
    'It does not guarantee real-world evacuation safety and must never replace certified building fire safety protocols or emergency services.'
    '</div>',
    unsafe_allow_html=True
)

# TOP METRICS DASHBOARD
mcol1, mcol2, mcol3, mcol4 = st.columns(4)

with mcol1:
    if classical_res["success"]:
        opt_route = classical_res["selected_route"]
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Classical Optimal Exit</div>
            <div class="metric-value">{opt_route['exit_label']}</div>
            <div class="metric-sub">Via {' → '.join(opt_route['path'])}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-title">Classical Optimal Exit</div>
            <div class="metric-value" style="color: #ef4444;">NO EXIT REACHABLE</div>
            <div class="metric-sub">All exit paths severed by blockages</div>
        </div>
        """, unsafe_allow_html=True)

with mcol2:
    if classical_res["success"]:
        opt_route = classical_res["selected_route"]
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Optimal Route Cost</div>
            <div class="metric-value">{opt_route['total_cost']:.1f}</div>
            <div class="metric-sub">Dist: {opt_route['total_distance']:.0f}m | Congestion Pen: {opt_route['total_congestion']:.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-title">Optimal Route Cost</div>
            <div class="metric-value" style="color: #94a3b8;">∞ (Blocked)</div>
            <div class="metric-sub">Graph disconnected from exits</div>
        </div>
        """, unsafe_allow_html=True)

with mcol3:
    n_marked = len(quantum_res["marked_bitstrings"])
    marked_str = ", ".join(quantum_res["marked_bitstrings"]) if n_marked > 0 else "None"
    color_marked = "#38bdf8" if n_marked == 1 else ("#f59e0b" if n_marked > 1 else "#ef4444")
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Quantum Marked Routes (M)</div>
        <div class="metric-value" style="color: {color_marked};">{n_marked} of 4</div>
        <div class="metric-sub">Marked: [{marked_str}] | C_max ≤ {cost_threshold:.1f}</div>
    </div>
    """, unsafe_allow_html=True)

with mcol4:
    top_bs = quantum_res["top_measured_bitstring"]
    top_pct = (quantum_res["counts"][top_bs] / quantum_res["shots"]) * 100
    top_marked = top_bs in quantum_res["marked_bitstrings"]
    val_color = "#22c55e" if top_marked else "#e2e8f0"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Top Quantum Measurement</div>
        <div class="metric-value" style="color: {val_color};">|{top_bs}⟩ ({top_pct:.1f}%)</div>
        <div class="metric-sub">{quantum_res['top_measured_route']['label']}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# MAIN INTERACTIVE TABS
tabs = st.tabs([
    "🏢 Building Map & Evacuation",
    "⚡ Classical Routing Analysis",
    "⚛️ Quantum Grover Experiment",
    "📊 Classical vs Quantum Comparison",
    "🔍 Limitations & Future Scope",
    "🏆 Judge Walkthrough & Pitch"
])

# TAB 1: BUILDING MAP
with tabs[0]:
    st.subheader("🏢 Building Map & Real-time Evacuation Paths")
    st.write(
        "Interactive simulation of an 8-junction building layout with 3 dedicated emergency exits: "
        "**Exit North (A)**, **Exit East (B)**, and **Exit South (C)**. "
        "Corridor colors indicate traffic congestion, dashed red lines indicate hazardous blockages, "
        "and the highlighted cyan trace represents the recommended evacuation path."
    )

    selected_path = classical_res["selected_route"]["path"] if classical_res["success"] else None
    
    col_map, col_info = st.columns([2.2, 1.0])
    with col_map:
        fig_map = plot_building_map(
            building=building,
            selected_path=selected_path,
            title=f"Building Evacuation Topology ({st.session_state.preset_selected})"
        )
        st.pyplot(fig_map, use_container_width=True)
        plt.close(fig_map)

    with col_info:
        st.markdown("#### 🚪 Emergency Exit Status")
        for exit_id in ["EXIT_A", "EXIT_B", "EXIT_C"]:
            route_data = classical_res["all_exit_routes"].get(exit_id, {})
            label = building.nodes[exit_id]["label"]
            if route_data.get("reachable", False):
                cost = route_data["total_cost"]
                dist = route_data["total_distance"]
                st.markdown(f"""
                <div style="background:#1e293b; padding:10px; border-radius:8px; margin-bottom:8px; border-left:4px solid #22c55e;">
                    <strong>{label}</strong> <span class="badge-clear">AVAILABLE</span><br>
                    <span style="font-size:0.82rem; color:#94a3b8;">Path: {' → '.join(route_data['path'])}</span><br>
                    <span style="font-size:0.85rem; color:#38bdf8;">Cost: <b>{cost:.1f}</b> (Dist: {dist:.0f}m, Cong: {route_data['total_congestion']:.0f})</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background:#1e293b; padding:10px; border-radius:8px; margin-bottom:8px; border-left:4px solid #ef4444;">
                    <strong>{label}</strong> <span class="badge-blocked">UNREACHABLE</span><br>
                    <span style="font-size:0.82rem; color:#fca5a5;">Corridor access blocked by hazard</span>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("#### 📋 2-Qubit Candidate Routes")
        candidates = building.get_candidate_routes()
        for cand in candidates:
            status_badge = '<span class="badge-clear">CLEAR</span>' if cand["is_available"] else '<span class="badge-blocked">BLOCKED</span>'
            st.markdown(f"""
            <div style="background:#0f172a; padding:8px 12px; border-radius:6px; margin-bottom:6px; border:1px solid #334155;">
                <span style="font-family:monospace; color:#38bdf8; font-weight:bold;">|{cand['bitstring']}⟩</span> <b>{cand['label'].split(':')[1]}</b> {status_badge}<br>
                <span style="font-size:0.78rem; color:#94a3b8;">{cand['description']}</span><br>
                <span style="font-size:0.80rem; color:#cbd5e1;">Cost: <b>{cand['cost']:.1f}</b> (Dist: {cand['distance']:.0f}m | Cong: {cand['congestion']:.0f})</span>
            </div>
            """, unsafe_allow_html=True)

# TAB 2: CLASSICAL ROUTING ANALYSIS
with tabs[1]:
    st.subheader("⚡ Classical Shortest-Path Evacuation Engine (Dijkstra)")
    st.write(
        "The classical routing engine evaluates the building graph using **NetworkX Dijkstra's algorithm**. "
        "Corridors flagged as blocked are pruned from the graph. Edge weights are computed using the formula below."
    )

    st.info(f"📐 **Cost Formula:** `{classical_res['formula_explanation']}`")

    if classical_res["success"]:
        opt = classical_res["selected_route"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Selected Emergency Exit", opt["exit_label"])
        c2.metric("Total Route Cost", f"{opt['total_cost']:.2f}")
        c3.metric("Total Travel Distance", f"{opt['total_distance']:.1f} meters")

        st.markdown("#### 🛤️ Detailed Route Breakdown")
        df_edges = pd.DataFrame(opt["edge_breakdown"])
        df_edges.columns = ["From Junction", "To Junction", "Corridor Name", "Distance (m)", "Congestion (0-10)", "Edge Cost"]
        st.dataframe(df_edges, use_container_width=True, hide_index=True)

        st.success(
            f"✅ **Route Summary:** The classical routing algorithm identified `{ ' → '.join(opt['path_labels']) }` "
            f"as the optimal path to reach safety with the lowest evaluated cost under the current settings."
        )
    else:
        st.error(
            "🚨 **Evacuation Route Failure:** No emergency exit is reachable from the starting location under the current "
            "corridor blockage conditions. All evacuation corridors leading to exits A, B, and C are compromised. "
            "Occupants must shelter in place until emergency responders clear a designated safe passage."
        )

# TAB 3: QUANTUM GROVER SEARCH EXPERIMENT
with tabs[2]:
    st.subheader("⚛️ Genuine 2-Qubit Quantum Search Experiment (Qiskit & Qiskit Aer)")
    st.write(
        "To evaluate quantum algorithms for candidate exit selection, we encode 4 potential evacuation routes "
        "into a 2-qubit computational basis state $|q_1 q_0\\rangle$. Grover's search algorithm accelerates unstructured "
        "search by marking states satisfying safety constraints and amplifying their measurement probability."
    )

    st.markdown(r"""
    | Basis State | Candidate Route Name | Destination Exit | Corridor Path |
    | :---: | :--- | :--- | :--- |
    | **|00⟩** | Route 0 (North Express) | Exit North (A) | Lobby → Hallway Alpha → Exit North |
    | **|01⟩** | Route 1 (Atrium East) | Exit East (B) | Lobby → Central Atrium → East Wing → Exit East |
    | **|10⟩** | Route 2 (Beta South) | Exit South (C) | Lobby → Hallway Beta → Exit South |
    | **|11⟩** | Route 3 (Cross Atrium) | Exit South (C) | Lobby → Central Atrium → West Wing → Exit South |
    """)

    st.markdown("---")
    qc_col1, qc_col2 = st.columns([1.3, 1.0])

    with qc_col1:
        st.markdown("#### 🔬 Qiskit Quantum Circuit Architecture")
        fig_circ = plot_quantum_circuit(quantum_res["circuit"])
        st.pyplot(fig_circ, use_container_width=True)
        plt.close(fig_circ)

        st.markdown(
            "**Circuit Components:**\n"
            "1. **State Prep (Hadamard):** Creates an equal superposition $|s\\rangle = \\frac{1}{2}(|00\\rangle + |01\\rangle + |10\\rangle + |11\\rangle)$.\n"
            "2. **Phase Oracle ($O_f$):** Flips the phase $(-1)$ of basis states corresponding to unblocked routes with $\\text{Cost} \\le C_{\\text{max}}$.\n"
            "3. **Grover Diffuser ($2|s\\rangle\\langle s| - I$):** Performs inversion about the mean amplitude, amplifying marked states.\n"
            "4. **Measurement:** Collapses the quantum state into classical register bits measured via Qiskit Aer."
        )

    with qc_col2:
        st.markdown("#### 📊 Qiskit AerSimulator Measurement Results")
        fig_counts = plot_quantum_counts(
            counts=quantum_res["counts"],
            marked_bitstrings=quantum_res["marked_bitstrings"],
            shots=quantum_res["shots"]
        )
        st.pyplot(fig_counts, use_container_width=True)
        plt.close(fig_counts)

    st.markdown("---")
    st.markdown("#### 🧠 Quantum Dynamics & Case Analysis")
    
    st.info(f"**Grover Dynamics Analysis:** {quantum_res['case_analysis']}")
    
    with st.expander("📖 Step-by-Step Mathematical Explanation"):
        st.text(quantum_res["mathematical_explanation"])

# TAB 4: CLASSICAL VS QUANTUM COMPARISON
with tabs[3]:
    st.subheader("📊 Systematic Classical vs Quantum Comparison")
    st.write(
        "A rigorous, scientific comparison between NetworkX classical Dijkstra pathfinding "
        "and Qiskit Aer Grover quantum route candidate search."
    )

    comp_data = [
        {
            "Metric / Dimension": "Algorithmic Approach",
            "Classical Routing (Dijkstra)": "Graph Shortest Path on weighted directed/undirected graph",
            "Quantum Search (Grover)": "Amplitude amplification over unstructured candidate database"
        },
        {
            "Metric / Dimension": "Time Complexity",
            "Classical Routing (Dijkstra)": "O(V log V + E) using Fibonacci / binary heap",
            "Quantum Search (Grover)": "O(√N) database search queries (quadratic speedup)"
        },
        {
            "Metric / Dimension": "Nature of Output",
            "Classical Routing (Dijkstra)": "Deterministic single minimum-cost path",
            "Quantum Search (Grover)": "Probabilistic quantum measurement collapse across candidates"
        },
        {
            "Metric / Dimension": "Handling of Constraints",
            "Classical Routing (Dijkstra)": "Corridors pruned directly prior to graph traversal",
            "Quantum Search (Grover)": "Phase oracle evaluates validity conditions dynamically"
        },
        {
            "Metric / Dimension": "System Role",
            "Classical Routing (Dijkstra)": "Calculates exact end-to-end navigational path",
            "Quantum Search (Grover)": "Demonstrates rapid filtering of viable exit options"
        },
        {
            "Metric / Dimension": "Hardware Feasibility",
            "Classical Routing (Dijkstra)": "Runs in milliseconds on low-power edge CPUs / microcontrollers",
            "Quantum Search (Grover)": "Simulated via Qiskit Aer; requires fault-tolerant quantum hardware for real scale"
        }
    ]
    st.dataframe(pd.DataFrame(comp_data), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("#### ⚖️ Scientific Findings & Nuances")
    c_a, c_b = st.columns(2)
    with c_a:
        st.markdown("""
        **Where Classical Excels:**
        - **Arbitrary Graph Scale:** Dijkstra effortlessly routes across thousands of building corridors in milliseconds.
        - **Deterministic Guarantees:** 100% deterministic path selection without probabilistic variance.
        - **Deployment Ready:** Runs immediately on existing fire alarm microcontrollers and smartphone apps without cryogenic hardware.
        """)
    with c_b:
        st.markdown("""
        **What the Quantum Experiment Demonstrates:**
        - **Quadratic Speedup Principle:** For $N$ candidate routes, Grover scales as $O(\\sqrt{N})$ compared to classical brute force $O(N)$.
        - **Oracle Encoding:** Shows how safety constraints (unblocked corridors and acceptable congestion limits) map to quantum phase shifts.
        - **Over-rotation Insights:** Highlighted that when 50% ($M=2$) of states are marked, standard Grover requires fractional-phase tuning to avoid over-rotation.
        """)

# TAB 5: LIMITATIONS & FUTURE SCOPE
with tabs[4]:
    st.subheader("🔍 Project Limitations & Future Research Horizons")

    st.markdown("""
    ### Honest Assessment of Limitations
    1. **Small Search Space ($N=4$):** 
       With only 4 candidate routes (2 qubits), classical search requires only 4 comparisons, making the classical implementation vastly faster in practice than compiling and simulating quantum circuits.
    2. **Oracle Compilation Overhead:**
       In real-world quantum computing, constructing the oracle circuit for dynamic building data requires quantum memory (QRAM) or classical preprocessing overhead.
    3. **NISQ Device Noise:**
       On real Noisy Intermediate-Scale Quantum (NISQ) processors, two-qubit CZ/CX gate errors and decoherence reduce Grover's peak measurement fidelity.
    4. **Educational Prototype Scope:**
       The model assumes static corridor snapshots during an emergency and does not simulate real-time human panic, smoke diffusion, or thermal dynamics.

    ---
    ### Future Research Horizons
    - **QAOA for Dynamic Evacuation Scheduling:**
      Formulate multi-person evacuation as a Quantum Approximate Optimization Algorithm (QAOA) quadratic unconstrained binary optimization (QUBO) problem to minimize corridor stampedes.
    - **Execution on Real IBM Quantum Hardware:**
      Deploy the 2-qubit and 4-qubit circuits to IBM Quantum Heron/Eagle processors via IBM Quantum Platform to analyze actual device error mitigation techniques.
    - **Integration with IoT Sensors:**
      Link corridor congestion and blockage states to real-time LoRaWAN smoke and infrared crowd-density sensors.
    """)

# TAB 6: JUDGE WALKTHROUGH & PRESENTATION
with tabs[5]:
    st.subheader("🏆 Hackathon Judge Demonstration Script (3-Minute Pitch)")
    st.write("Use this structured script to present Q-Evac to RV University Hackathon evaluators.")

    with st.expander("⏱️ Minute 1: The Problem & The Architecture", expanded=True):
        st.markdown("""
        - **Hook:** *"During building emergencies, evacuees reflexively rush to the main exit, often walking straight into blocked corridors or deadly stampedes."*
        - **Solution:** *"Q-Evac pairs classical graph-theory pathfinding with a genuine Qiskit quantum search experiment."*
        - **Demo Action:** Point to the **Building Map** on Tab 1, explaining the Lobby, Hallway Alpha/Beta, Atrium, and Exits A, B, C.
        """)

    with st.expander("⏱️ Minute 2: Interactive Scenarios & Quantum Grover Search", expanded=True):
        st.markdown("""
        - **Demo Action:** Open the sidebar, switch the preset to **'Shortest Exit Blocked'** or **'Heavy Atrium Congestion'**.
        - **Show Reaction:** Watch the classical optimal path dynamically reroute to Exit South, and watch the Qiskit Grover oracle update its marked bitstrings.
        - **Explain Quantum Circuit:** Switch to Tab 3. Explain the Hadamard preparation, the Phase Oracle $O_f$, the Grover diffuser reflection about the mean, and the measurement on Qiskit Aer.
        - **Showcase Result:** Point to the 100% peak measurement of the valid candidate state in the Aer histogram!
        """)

    with st.expander("⏱️ Minute 3: Comparison, Realism & Limitations", expanded=True):
        st.markdown("""
        - **No Fluff / Honest Quantum Assessment:** *"We do not claim quantum supremacy on a 2-qubit toy graph. Instead, we prove that safety and congestion constraints can be mapped to quantum phase oracles with quadratic Grover acceleration."*
        - **Safety First:** Reiterate the educational disclaimer—this is a computational exploration, not a substitute for certified evacuation systems.
        - **Closing:** Open for judge questions!
        """)

# FOOTER
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #64748b; font-size: 0.82rem;'>"
    "Q-Evac Prototype | Developed for RV University Qiskit Quantum Computing Hackathon | Built with Python, Qiskit 2.3, Qiskit Aer, NetworkX, and Streamlit"
    "</div>",
    unsafe_allow_html=True
)

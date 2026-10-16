# Q-Evac 🚨 — Quantum-Based Emergency Exit Selection
> **RV University Qiskit Quantum Computing Hackathon Prototype**  
> Educational prototype comparing classical graph pathfinding with genuine Qiskit Grover quantum search for emergency egress selection.

---

## ⚠️ Important Educational Safety Disclaimer
**This project is strictly an educational and scientific demonstration.** It simulates simplified building topologies and quantum candidate selection algorithms. It does **not** replace certified building architectural codes, fire alarm systems, life-safety evacuation protocols, or instructions from emergency first responders.

---

## 1. Problem Statement & Motivation
During a structure emergency (e.g., fire, gas leak, power outage), building occupants typically rush toward the primary exit they entered through. This instinctive behavior frequently causes severe corridor overcrowding, bottlenecks, and trampling, or leads evacuees directly into passages that are already blocked by fire or structural debris.

Traditional static exit signage fails to adapt to dynamic real-time hazard conditions. A modern intelligent evacuation system must quickly evaluate corridor distances, active blockage states, and crowd congestion to recommend viable, low-risk egress routes.

---

## 2. Proposed Solution
**Q-Evac** is an end-to-end software simulation combining:
1. **Classical Route Finding (NetworkX Dijkstra):** Determines the lowest-cost, available path across the full building topology, accounting for physical corridor distance and real-time congestion penalties.
2. **Quantum Search Candidate Selection (Qiskit & Qiskit Aer):** Maps 4 key candidate evacuation routes onto a 2-qubit register ($|00\rangle, |01\rangle, |10\rangle, |11\rangle$) and applies Grover's Search Algorithm to mark and amplify routes that are both unblocked and below a safety cost threshold.
3. **Interactive Streamlit Dashboard:** Provides real-time map visualization, emergency scenario presets (e.g. fire blocking North exit, heavy atrium crowd), dynamic sliders, quantum circuit diagrams, and Aer measurement histograms.

---

## 3. Technology Stack
- **Python 3.10+ / 3.13**
- **Qiskit (>=1.0.0, tested on 2.3.1):** Quantum circuit synthesis, Hadamard layers, controlled-Z phase oracles, Grover diffuser reflections.
- **Qiskit Aer (>=0.14.0, tested on 0.17.2):** High-performance local quantum simulator (`AerSimulator`).
- **NetworkX (>=3.0):** Graph representation of corridor junctions, edge cost evaluation, and Dijkstra shortest path routing.
- **Streamlit (>=1.30.0):** Responsive web interface, real-time controls, and scenario presets.
- **Matplotlib (>=3.7.0):** High-contrast publication-ready building maps, quantum circuit rendering, and measurement count charts.
- **NumPy (>=1.24.0):** Numerical utilities.

---

## 4. Project File Structure
```
q_evac/
├── app.py                  # Main Streamlit interactive web dashboard
├── building.py             # Building network topology, corridors, and 2-qubit candidate definitions
├── classical_routing.py    # NetworkX Dijkstra shortest-path routing algorithm
├── quantum_search.py       # Qiskit 2-qubit Grover search circuit and Qiskit Aer runner
├── visualization.py        # Matplotlib visualization routines (building map, counts, circuit)
├── requirements.txt        # Python dependency manifest
├── README.md               # Complete project documentation & guide
└── .streamlit/
    └── config.toml         # Streamlit dark theme configuration
```

---

## 5. System Architecture & Workflow

```mermaid
graph TD
    A[Emergency Sensor Input / User Preset] --> B[Building Topology Graph]
    B --> C1[Classical Routing Engine: NetworkX Dijkstra]
    B --> C2[Quantum Candidate Encoder: 2 Qubits / 4 Routes]
    
    C1 --> D1[Optimal Evacuation Path & Cost]
    
    C2 --> E1[State Prep: H gates |s>]
    E1 --> E2[Phase Oracle: O_f flips marked states]
    E2 --> E3[Diffuser: Inversion about mean amplitude]
    E3 --> E4[Qiskit AerSimulator: 1024 shots]
    
    D1 --> F[Streamlit Interactive Dashboard]
    E4 --> F
```

---

## 6. Mathematical Formulations

### Classical Routing Cost Function
For an available path $P$ consisting of corridors $e_1, e_2, \dots, e_k$:
$$\text{Cost}(P) = \sum_{e \in P} \text{Distance}(e) + w \cdot \sum_{e \in P} \text{Congestion}(e)$$
- $\text{Distance}(e)$: Corridor length in meters.
- $\text{Congestion}(e)$: Congestion index on a scale from 0 (empty) to 10 (gridlock).
- $w$: Congestion penalty weight multiplier (default $w = 1.0$).
- Blocked corridors are assigned $\text{Cost} = \infty$ and excluded from traversal.

### Quantum Grover Search Encoding
We encode 4 candidate evacuation paths into 2 qubits $|q_1 q_0\rangle$:
| State | Candidate Route | Destination |
| :---: | :--- | :--- |
| $\|00\rangle$ | Route 0 (North Express) | Exit North (A) |
| $\|01\rangle$ | Route 1 (Atrium East) | Exit East (B) |
| $\|10\rangle$ | Route 2 (Beta South) | Exit South (C) |
| $\|11\rangle$ | Route 3 (Cross Atrium) | Exit South (C) |

**Oracle Condition:**
A basis state $|x\rangle$ is marked by flipping its phase $(-1)$ if:
1. $\text{Route}(x)$ is unblocked ($\text{is\_available} = \text{True}$)
2. $\text{Cost}(\text{Route}(x)) \le C_{\text{max}}$

**Amplitude Amplification:**
For $N=4$ states and $M=1$ marked target, a single Grover iteration ($R \approx \frac{\pi}{4}\sqrt{\frac{N}{M}} = 1$) rotates the state vector directly onto the marked target with theoretical **100% probability**.

---

## 7. Installation & Quick Start

### 1. Prerequisites
Ensure Python 3.10 to 3.13 is installed on your system.

### 2. Setup Virtual Environment (Optional but recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
cd q_evac
pip install -r requirements.txt
```

### 4. Run the Streamlit Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 8. Example Demonstration Scenarios

| Scenario Preset | Blockages / Congestion | Classical Result | Quantum Search Result |
| :--- | :--- | :--- | :--- |
| **All Clear (Normal)** | No corridors blocked. Normal traffic. | Selects Route 0 (Exit North, Cost: 29.0). | Qiskit marks $\|00\rangle$, Aer measures $\|00\rangle$ with ~100% confidence. |
| **Shortest Exit Blocked** | Corridor C8 (Alpha to Exit North) blocked by hazard. | Reroutes to Exit East (B) or Exit South (C). | State $\|00\rangle$ excluded by oracle. New best candidate amplified. |
| **Heavy Atrium Congestion** | Central corridors C1, C2 at congestion level 9/10. | Reroutes traffic through Hallway Beta to Exit South (C). | High-cost routes filtered out. State $\|10\rangle$ amplified. |
| **Single Viable Exit** | Corridors leading to North and East exits severed. | Selects Exit South (C). | Exactly 1 valid candidate marked and amplified to 100%. |
| **Full Isolation** | All exit-adjacent corridors blocked. | Flags "NO EXIT REACHABLE". Recommends shelter-in-place. | Oracle marks 0 states ($M=0$). Measurement returns uniform ~25% noise across all states. |

---

## 9. Classical vs Quantum Comparison Summary

| Attribute | Classical Routing (Dijkstra) | Quantum Search (Grover) |
| :--- | :--- | :--- |
| **Core Problem** | Shortest path across graph network | Amplitude amplification in database of route candidates |
| **Algorithmic Complexity** | $O(V \log V + E)$ | $O(\sqrt{N})$ search queries |
| **Determinism** | 100% deterministic exact minimum | Probabilistic quantum measurement sampling |
| **Practical Utility** | Immediate deployment on standard IoT microcontrollers | Demonstrates algorithmic acceleration for combinatorial candidate evaluation |
| **Current Readiness** | Commercial standard | Experimental prototype simulated on Qiskit Aer |

---

## 10. Acknowledgments & References
- **IBM Qiskit Documentation & Tutorials:** [https://docs.quantum.ibm.com/](https://docs.quantum.ibm.com/)
- **Michael A. Nielsen & Isaac L. Chuang:** *Quantum Computation and Quantum Information* (Cambridge University Press).
- **NetworkX Graph Library:** [https://networkx.org/](https://networkx.org/)
- **Streamlit Framework:** [https://streamlit.io/](https://streamlit.io/)
- Developed for the **RV University Qiskit Quantum Computing Hackathon**.

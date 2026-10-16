# Q-Evac: Presentation & Pitch Outline
## RV University Qiskit Quantum Computing Hackathon (2026)

---

### Slide 1: Title & Hook
- **Title:** Q-Evac: Quantum-Based Emergency Exit Selection
- **Subtitle:** Pairing NetworkX Graph Routing with Qiskit Grover Search for Dynamic Building Evacuation
- **Presenter:** Hackathon Team
- **Hook:** In an emergency, occupants instinctively stampede toward the entrance they know best—often running directly into lethal blockages and overcrowding. How can quantum and classical algorithms coordinate to guide people toward the safest, lowest-cost exits?

---

### Slide 2: The Problem Statement
- **Dynamic Hazards:** Corridors become blocked by fire, structural damage, or smoke.
- **Congestion Spikes:** Nearest exits become choked with bottleneck traffic.
- **Limitation of Static Signage:** Fixed exit signs cannot adapt to real-time corridor statuses.

---

### Slide 3: The Proposed Solution
- **Dual-Engine Architecture:**
  1. **Classical Engine:** NetworkX Dijkstra algorithm calculating exact shortest paths with congestion penalties.
  2. **Quantum Search Engine:** Qiskit Grover's algorithm demonstrating quadratic amplitude amplification to filter viable route candidates under safety thresholds.
- **Interactive UI:** Streamlit dashboard with real-time corridor blockage toggles and congestion sliders.

---

### Slide 4: Building Topology Simulation
- **Graph Structure:** 8 corridor junctions (`LOBBY`, `HALL_A`, `ATRIUM`, `HALL_B`, `WING_E`, `WING_W`) connecting to 3 designated exits:
  - Exit North (A)
  - Exit East (B)
  - Exit South (C)
- **Edge Cost Formula:**
  $$\text{Cost} = \text{Distance} + w \cdot \text{Congestion}$$

---

### Slide 5: Classical Route Selection
- **Algorithm:** Dijkstra shortest-path with blocked edge removal.
- **Safety Handling:** When all egress corridors are severed, the system cleanly triggers an emergency warning: *"No Exit Reachable — Shelter in Place"*.

---

### Slide 6: Quantum Grover Search Experiment
- **Encoding:** 4 candidate egress routes mapped to a 2-qubit register:
  - $|00\rangle \to$ Route 0 (North Express)
  - $|01\rangle \to$ Route 1 (Atrium East)
  - $|10\rangle \to$ Route 2 (Beta South)
  - $|11\rangle \to$ Route 3 (Cross Atrium)
- **Phase Oracle:** Evaluates $\text{Unblocked} \land (\text{Cost} \le C_{\text{max}})$, applying a $-1$ phase flip to valid candidate states.
- **Grover Diffuser:** Inversion about the mean amplitude rotates the quantum state towards target routes.
- **Execution:** Simulated on `Qiskit AerSimulator` with 1024 measurement shots.

---

### Slide 7: Experimental Results & Observations
- **Single Target ($M=1$):** Achieves theoretical 100% amplification to the optimal route.
- **Two Targets ($M=2$):** Demonstrates balanced 50/50 probability distribution (over-rotation dynamics in Grover math).
- **Zero Targets ($M=0$):** Oracle applies no phase shifts, preserving uniform 25% superposition noise (signaling complete isolation).

---

### Slide 8: Classical vs Quantum Comparison
- **Classical Strengths:** Production-ready, deterministic, scales effortlessly to thousands of nodes on low-power microcontrollers.
- **Quantum Strengths:** Provides $O(\sqrt{N})$ query acceleration for combinatorial candidate evaluation across vast route spaces.

---

### Slide 9: Limitations & Future Horizons
- **Honest Limitations:** 2-qubit scale on NISQ simulators; classical preprocessing required for dynamic oracles.
- **Future Work:**
  - Formulating multi-agent crowd flow as a QAOA (Quantum Approximate Optimization Algorithm) QUBO problem.
  - Deploying and benchmarking on physical IBM Quantum hardware (e.g., IBM Heron processor).
  - Interfacing with IoT building sensor networks (smoke/infrared).

---

### Slide 10: Conclusion & Q&A
- **Key Takeaway:** Q-Evac demonstrates how quantum computing concepts can intersect with classical urban safety infrastructure.
- **Questions & Discussion.**

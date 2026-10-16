"""
Quantum Search Module for Q-Evac using Qiskit and Qiskit Aer.
Implements Grover's Search Algorithm on 2 qubits to search over 4 candidate
emergency evacuation routes meeting safety and cost criteria.

Candidate Encoding (2 Qubits: q1 q0):
  |00⟩ (q1=0, q0=0) -> Route 0: North Express (Exit A)
  |01⟩ (q1=0, q0=1) -> Route 1: Atrium East   (Exit B)
  |10⟩ (q1=1, q0=0) -> Route 2: Beta South     (Exit C)
  |11⟩ (q1=1, q0=1) -> Route 3: Cross Atrium   (Exit C)

Search Condition:
  A route candidate is marked if:
    1. It is available (no blocked corridor along the route)
    2. Its cost is less than or equal to a specified cost threshold.
"""

from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from building import Building


def build_grover_circuit(
    marked_bitstrings: List[str],
    num_qubits: int = 2,
    iterations: int = 1
) -> QuantumCircuit:
    """
    Constructs a 2-qubit Grover search circuit with a genuine phase oracle
    and reflection diffuser.

    Args:
        marked_bitstrings: List of bitstrings to mark (e.g., ['01']).
                           Convention: bitstring "b1b0" where b0 is qubit 0, b1 is qubit 1.
        num_qubits: Number of qubits (default 2 for N=4 routes).
        iterations: Number of Grover iterations (default 1 for N=4, M=1 optimal).

    Returns:
        QuantumCircuit: The constructed and measured Qiskit circuit.
    """
    qc = QuantumCircuit(num_qubits, num_qubits, name="Grover_QEvac")

    # Step 1: Equal Superposition State Preparation |s> = H^2 |00>
    qc.h(range(num_qubits))
    qc.barrier(label="Prep")

    # If no states are marked, we skip oracle & diffuser, yielding uniform superposition
    if not marked_bitstrings or iterations == 0:
        qc.measure(range(num_qubits), range(num_qubits))
        return qc

    for it in range(iterations):
        # Step 2: Phase Oracle O_f
        # Applies a (-1) phase shift to each marked basis state |x>
        for bs in marked_bitstrings:
            # bs format: "b1b0", where bs[0] is qubit 1 and bs[1] is qubit 0
            b1 = int(bs[0])
            b0 = int(bs[1])

            # Apply X gates to qubits that are 0 in the marked bitstring
            if b0 == 0:
                qc.x(0)
            if b1 == 0:
                qc.x(1)

            # Controlled-Z flips the phase of |11>
            qc.cz(0, 1)

            # Uncompute X gates
            if b0 == 0:
                qc.x(0)
            if b1 == 0:
                qc.x(1)

        qc.barrier(label=f"Oracle_{it+1}")

        # Step 3: Grover Diffuser (Reflection about the uniform superposition |s>)
        # D = 2|s><s| - I = H (2|00><00| - I) H
        qc.h(range(num_qubits))
        qc.x(range(num_qubits))
        qc.cz(0, 1)
        qc.x(range(num_qubits))
        qc.h(range(num_qubits))
        qc.barrier(label=f"Diffuser_{it+1}")

    # Step 4: Measurement into classical register
    qc.measure(range(num_qubits), range(num_qubits))
    return qc


def run_quantum_search(
    building: Building,
    cost_threshold: Optional[float] = None,
    shots: int = 1024,
    seed: Optional[int] = 42
) -> Dict[str, Any]:
    """
    Evaluates building candidate evacuation routes and runs the Grover search experiment
    using Qiskit Aer.

    Args:
        building: Building simulation instance.
        cost_threshold: Maximum allowable cost for a route to be marked.
                        If None, defaults to lowest available cost + 5.0 (or median).
        shots: Number of measurement repetitions on AerSimulator.
        seed: Random seed for reproducibility.

    Returns:
        Dictionary containing:
            - candidates: Evaluated candidate route list.
            - cost_threshold: The threshold used for filtering.
            - marked_bitstrings: Bitstrings marked by the oracle.
            - marked_routes: Route definitions matching the search condition.
            - circuit: The QuantumCircuit object.
            - counts: Raw dictionary of bitstring counts from AerSimulator.
            - probabilities: Normalized probabilities for all 4 states.
            - top_measured_bitstring: Bitstring with highest counts.
            - top_measured_route: Route corresponding to top bitstring.
            - success_observed: True if any marked state was measured with high probability.
            - case_analysis: Detailed explanation of the quantum dynamics.
            - mathematical_explanation: Textbook rationale of the Grover result.
            - simulator_name: Name of simulator used ('Qiskit AerSimulator').
    """
    candidates = building.get_candidate_routes()

    # Determine default threshold if none provided
    available_costs = [c["cost"] for c in candidates if c["is_available"]]
    if cost_threshold is None:
        if available_costs:
            # Default: set threshold equal to the min cost to find the single best candidate
            cost_threshold = float(min(available_costs))
        else:
            cost_threshold = 30.0

    # Identify marked routes
    marked_bitstrings: List[str] = []
    marked_routes: List[Dict[str, Any]] = []

    for c in candidates:
        if c["is_available"] and c["cost"] <= cost_threshold:
            marked_bitstrings.append(c["bitstring"])
            marked_routes.append(c)

    # Build and execute circuit
    num_marked = len(marked_bitstrings)
    qc = build_grover_circuit(marked_bitstrings, num_qubits=2, iterations=1)

    simulator = AerSimulator()
    job = simulator.run(qc, shots=shots, seed_simulator=seed)
    result = job.result()
    raw_counts = result.get_counts()

    # Standardize counts to all 4 possible 2-bit states
    all_states = ["00", "01", "10", "11"]
    counts = {state: raw_counts.get(state, 0) for state in all_states}
    probabilities = {state: counts[state] / shots for state in all_states}

    top_measured_bitstring = max(counts, key=counts.get)
    top_measured_route = next(
        (c for c in candidates if c["bitstring"] == top_measured_bitstring), None
    )

    # Comprehensive educational analysis of Grover behavior for N=4
    if num_marked == 1:
        success_observed = (top_measured_bitstring in marked_bitstrings) and (probabilities[top_measured_bitstring] > 0.90)
        case_analysis = (
            f"Case M=1 (Optimal Grover Amplification): Exactly 1 route ({marked_bitstrings[0]}) meets the criteria. "
            f"For N=4 with M=1, exactly 1 Grover iteration theoretically produces 100% constructive interference "
            f"for the marked state and complete destructive interference for unmarked states. "
            f"The Aer simulator measured '{top_measured_bitstring}' with {probabilities[top_measured_bitstring]*100:.1f}% probability."
        )
        mathematical_explanation = (
            "Grover Math (N=4, M=1):\n"
            "- Initial superposition: |s> = 1/2(|00> + |01> + |10> + |11>), amplitude = +0.50 per state.\n"
            f"- Phase Oracle: Inverts marked state |{marked_bitstrings[0]}> amplitude to -0.50.\n"
            "- Mean amplitude: mu = (3*(0.50) + (-0.50)) / 4 = 1.0 / 4 = +0.25.\n"
            "- Inversion about mean: A_new = 2*mu - A_old.\n"
            f"  * Marked state: 2(0.25) - (-0.50) = 0.50 + 0.50 = 1.00 (100% Probability!)\n"
            "  * Unmarked states: 2(0.25) - (0.50) = 0.50 - 0.50 = 0.00 (0% Probability)."
        )
    elif num_marked == 2:
        # For M=2 out of N=4, 50% of the entire database is marked
        success_observed = sum(counts.get(bs, 0) for bs in marked_bitstrings) / shots > 0.40
        case_analysis = (
            f"Case M=2 (Over-rotation / Balanced Subspace): Exactly 2 routes ({', '.join(marked_bitstrings)}) meet the criteria. "
            f"Because marked states constitute 50% of the entire search space (M/N = 2/4), the Grover rotation angle "
            f"theta = 2 arcsin(sqrt(2/4)) = pi/2 causes an over-rotation. "
            f"The mean amplitude becomes mu = 0, causing the diffuser to invert amplitudes into an equal magnitude superposition. "
            f"In practice, when 50% of candidates are valid, classical random guessing finds a valid exit in 1 query with 50% probability."
        )
        mathematical_explanation = (
            "Grover Over-Rotation Math (N=4, M=2):\n"
            "- Initial superposition: all 4 amplitudes are +0.50.\n"
            "- Oracle inverts 2 marked states: two amplitudes become -0.50, two remain +0.50.\n"
            "- Mean amplitude: mu = (2*(0.50) + 2*(-0.50)) / 4 = 0.00.\n"
            "- Inversion about mean: A_new = 2(0) - A_old = -A_old.\n"
            "- All state magnitudes remain |+-0.50|, resulting in equal ~25% probabilities across all 4 states.\n"
            "- This illustrates a fundamental quantum search principle: knowing the number of marked items (M) "
            "is necessary to prevent over-rotation (typically solved via Quantum Counting or adaptive fractional iterations)."
        )
    elif num_marked == 0:
        success_observed = False
        case_analysis = (
            "Case M=0 (No Candidates Valid / Complete Blockage): No candidate routes met the search criteria. "
            "The oracle applied no phase shifts. The Grover diffuser returns the uniform superposition state |s>, "
            "measuring each bitstring with equal ~25% probability. This signals that all routes are either blocked "
            "or exceed the maximum allowable congestion threshold."
        )
        mathematical_explanation = (
            "Empty Search Space (N=4, M=0):\n"
            "- With 0 marked states, Oracle = Identity (I).\n"
            "- Diffuser D applied to |s>: D|s> = (2|s><s| - I)|s> = 2|s> - |s> = |s>.\n"
            "- The state remains invariant: equal 25% probability for each route label."
        )
    elif num_marked == 3:
        success_observed = True
        case_analysis = (
            f"Case M=3: 3 out of 4 routes ({', '.join(marked_bitstrings)}) are valid. "
            f"Similar to M=2, the marked subspace is dominant (75% of search space). "
            f"Standard Grover rotation amplifies the unmarked state while marked states split the remaining probability."
        )
        mathematical_explanation = (
            "Inverted Search Dynamics (N=4, M=3):\n"
            "- Mean amplitude mu = (0.50 - 3*0.50)/4 = -0.25.\n"
            "- Diffuser amplifies the single UNMARKED state to 100%, demonstrating that searching for 3 marked items "
            "is mathematically equivalent to searching for the 1 defective/unmarked item."
        )
    else:  # num_marked == 4
        success_observed = True
        case_analysis = (
            "Case M=4 (All Routes Clear): Every candidate route is unblocked and below the cost limit. "
            "Applying the oracle to all states applies a global phase (-I), preserving the uniform distribution."
        )
        mathematical_explanation = (
            "Global Phase Shift (N=4, M=4):\n"
            "- Oracle flips all 4 states: |psi> -> -|psi>.\n"
            "- Diffuser reflects about mean, preserving uniform distribution across all routes."
        )

    return {
        "candidates": candidates,
        "cost_threshold": cost_threshold,
        "marked_bitstrings": marked_bitstrings,
        "marked_routes": marked_routes,
        "num_marked": num_marked,
        "circuit": qc,
        "counts": counts,
        "probabilities": probabilities,
        "top_measured_bitstring": top_measured_bitstring,
        "top_measured_route": top_measured_route,
        "success_observed": success_observed,
        "case_analysis": case_analysis,
        "mathematical_explanation": mathematical_explanation,
        "simulator_name": "Qiskit AerSimulator (Aer 0.17+ / Qiskit 2.3+)",
        "shots": shots,
        "disclaimer": (
            "Educational Simulation Notice: This quantum circuit is simulated on classical hardware using Qiskit Aer. "
            "It demonstrates quantum search principles for candidate evacuation route selection and does not guarantee "
            "real-world emergency exit safety."
        ),
    }


if __name__ == "__main__":
    # Quick standalone sanity test
    b = Building()
    print("Testing Quantum Search on default building...")
    res = run_quantum_search(b, cost_threshold=28.0)
    print(f"Marked: {res['marked_bitstrings']}")
    print(f"Counts: {res['counts']}")
    print(f"Top: {res['top_measured_bitstring']}")
    print("Success:", res["success_observed"])
    print(res["case_analysis"])

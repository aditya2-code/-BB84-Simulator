import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

simulator = AerSimulator()

def encode_message(bits, bases):
    """Alice encodes her classical bits into qubits using chosen bases."""
    circuits = []
    for bit, basis in zip(bits, bases):
        qc = QuantumCircuit(1, 1)
        # Prepare state |1> if bit is 1
        if bit == 1:
            qc.x(0)
        # Switch to X-basis (diagonal) using Hadamard gate if basis is 1
        if basis == 1:
            qc.h(0)
        qc.barrier()
        circuits.append(qc)
    return circuits

def intercept_message(circuits, eve_bases):
    """Eve intercepts, measures in her random basis, and resends the collapsed qubit."""
    intercepted_circuits = []
    for qc, basis in zip(circuits, eve_bases):
        # Measure in Eve's basis
        if basis == 1:
            qc.h(0)
        qc.measure(0, 0)
        
        # Run simulation to get Eve's measured bit
        compiled = transpile(qc, simulator)
        result = simulator.run(compiled, shots=1, memory=True).result()
        measured_bit = int(result.get_memory()[0])
        
        # Eve prepares a fresh qubit based on what she measured to send to Bob
        new_qc = QuantumCircuit(1, 1)
        if measured_bit == 1:
            new_qc.x(0)
        if basis == 1:
            new_qc.h(0)
        new_qc.barrier()
        intercepted_circuits.append(new_qc)
        
    return intercepted_circuits

def measure_message(circuits, bases):
    """Bob measures the incoming qubits using his randomly chosen bases."""
    measurements = []
    for qc, basis in zip(circuits, bases):
        if basis == 1:
            qc.h(0)
        qc.measure(0, 0)
        
        compiled = transpile(qc, simulator)
        result = simulator.run(compiled, shots=1, memory=True).result()
        measured_bit = int(result.get_memory()[0])
        measurements.append(measured_bit)
    return measurements

def sift_keys(alice_bases, bob_bases, alice_bits, bob_bits):
    """Keep only the bits where Alice and Bob used the exact same basis."""
    alice_key = []
    bob_key = []
    matching_indices = []
    
    for i in range(len(alice_bases)):
        if alice_bases[i] == bob_bases[i]:
            alice_key.append(alice_bits[i])
            bob_key.append(bob_bits[i])
            matching_indices.append(i)
            
    return alice_key, bob_key, matching_indices

def run_bb84_simulation(num_qubits=20, eve_present=False):
    # 0 = Z-basis (+), 1 = X-basis (×)
    alice_bits = np.random.randint(2, size=num_qubits)
    alice_bases = np.random.randint(2, size=num_qubits)
    bob_bases = np.random.randint(2, size=num_qubits)
    
    # 1. Alice encodes qubits
    circuits = encode_message(alice_bits, alice_bases)
    
    # 2. Eve intercepts (optional)
    eve_bases = None
    if eve_present:
        eve_bases = np.random.randint(2, size=num_qubits)
        circuits = intercept_message(circuits, eve_bases)
        
    # 3. Bob measures qubits
    bob_bits = measure_message(circuits, bob_bases)
    
    # 4. Sift keys
    alice_key, bob_key, matching_indices = sift_keys(
        alice_bases, bob_bases, alice_bits, bob_bits
    )
    
    # 5. Calculate Quantum Bit Error Rate (QBER)
    errors = sum(1 for a, b in zip(alice_key, bob_key) if a != b)
    qber = (errors / len(alice_key) * 100) if len(alice_key) > 0 else 0.0
    
    return {
        "alice_bits": alice_bits,
        "alice_bases": alice_bases,
        "eve_bases": eve_bases,
        "bob_bases": bob_bases,
        "bob_bits": bob_bits,
        "alice_key": alice_key,
        "bob_key": bob_key,
        "matching_indices": matching_indices,
        "qber": qber,
        "sample_circuit": circuits[0] if circuits else None
    }
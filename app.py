import streamlit as st
import pandas as pd
from quantum_bb84 import run_bb84_simulation

st.set_page_config(page_title="BB84 QKD Simulator", page_icon="🔐", layout="wide")

st.title("🔐 BB84 Quantum Key Distribution (QKD) Simulator")
st.markdown(
    "Simulate quantum key exchange between **Alice** and **Bob**, and observe how "
    "quantum mechanics detects an eavesdropper (**Eve**) via state disturbance."
)

# Sidebar Controls
st.sidebar.header("Simulation Parameters")
num_qubits = st.sidebar.slider("Number of Qubits Transmitted", min_value=10, max_value=100, value=25, step=5)
eve_present = st.sidebar.toggle("Enable Eavesdropper (Eve)", value=False)
run_btn = st.sidebar.button("Run Quantum Transmission", type="primary", use_container_width=True)

# Run Simulation
results = run_bb84_simulation(num_qubits=num_qubits, eve_present=eve_present)

# Top Metrics Row
col1, col2, col3, col4 = st.columns(4)
col1.metric("Qubits Sent", num_qubits)
col2.metric("Sifted Key Length", f"{len(results['alice_key'])} bits")
col3.metric("Quantum Bit Error Rate (QBER)", f"{results['qber']:.1f}%")

if results["qber"] > 10.0:
    col4.error("🚨 Eavesdropper Detected! Key Discarded.")
else:
    col4.success("✅ Channel Secure! Key Established.")

st.divider()

# Key Comparison Display
st.subheader("🔑 Final Sifted Keys (Matching Bases Only)")
k_col1, k_col2 = st.columns(2)
k_col1.code(f"Alice's Key: {''.join(map(str, results['alice_key']))}", language="text")
k_col2.code(f"Bob's Key:   {''.join(map(str, results['bob_key']))}", language="text")

# Transmission Breakdown Table
st.subheader("📊 Qubit-by-Qubit Transmission Log")
basis_map = {0: "+ (Z)", 1: "× (X)"}

table_data = []
for i in range(num_qubits):
    basis_match = results["alice_bases"][i] == results["bob_bases"][i]
    bit_match = results["alice_bits"][i] == results["bob_bits"][i]
    
    status = "Discarded (Basis Mismatch)"
    if basis_match:
        status = "✅ Kept (Match)" if bit_match else "❌ Kept (ERROR - Eve Interference)"
        
    row = {
        "Qubit #": i + 1,
        "Alice Bit": results["alice_bits"][i],
        "Alice Basis": basis_map[results["alice_bases"][i]],
        "Bob Basis": basis_map[results["bob_bases"][i]],
        "Bob Measured": results["bob_bits"][i],
        "Status": status
    }
    if eve_present:
        row["Eve Basis"] = basis_map[results["eve_bases"][i]]
    table_data.append(row)

df = pd.DataFrame(table_data)
st.dataframe(df, use_container_width=True, hide_index=True)

# Circuit Visualization
st.subheader("⚛️ Sample Single-Qubit Circuit (Qubit #1)")
if results["sample_circuit"]:
    st.code(results["sample_circuit"].draw(output="text"), language="text")
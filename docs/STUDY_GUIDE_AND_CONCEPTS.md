# Master Study Guide & Conceptual Breakdown — MRPL PS 26117
> **Technical Architecture & Engineering Foundation Guide**  
> *Master these concepts step-by-step to understand 100% of the sovereign system.*

---

## 1. Executive Concepts & Architectural Thesis

### A. What is "Harness Engineering"?
In modern AI systems engineering, models (LLMs/SLMs) are non-deterministic, interchangeable commodities. An **AI Harness** is the deterministic, typed software scaffolding built around the model. It governs:
1. **Input boundaries:** Semantic routing and schema validation (`pydantic`).
2. **Execution safety:** Sandboxed subprocess runners with strict timeouts.
3. **State memory:** Directed Acyclic Graphs (DAGs) storing structured data rather than conversation history.
4. **Reliability:** Automated circuit breakers and error re-injection loops.

### B. Why State Graph DAGs Beat Conversational Chains
- **Conversational Agents (LangChain / CrewAI):** Store history as a long text transcript. As context grows, token latency spikes, hallucinations increase, and malformed outputs break the pipeline.
- **Deterministic State Graph DAG:** Decouples state into a typed Pydantic object (`WorkbenchState`). The model only executes atomic actions (e.g. `PLAN`, `SYNTHESIZE_CODE`), and deterministic Python code handles state transitions.

---

## 2. Industrial Refinery Domain Knowledge (MRPL & ASME Standards)

### A. Who is MRPL?
- **Mangalore Refinery and Petrochemicals Limited (MRPL)** is a premier Category 1 Miniratna PSU and a subsidiary of ONGC, operating a massive 15 Million Metric Tonne (MMTPA) crude oil refinery in Mangalore, Karnataka.
- Plant equipment operates under extreme temperatures ($>400^\circ\text{C}$) and pressures ($>40\text{ bar}$).

### B. What is a P&ID (Piping & Instrumentation Diagram)?
- The master engineering schematic of a processing plant showing piping, valves, instruments, safety interlocks, and control loops.
- Key tags:
  - `PT-1044`: Pressure Transmitter #1044.
  - `TT-1082`: Temperature Transmitter #1082.
  - `FCV-1021`: Flow Control Valve.
  - `XV-1001`: Emergency Shutoff Valve.

### C. What is Ultrasonic Thickness Testing (NDT)?
- Non-destructive testing (NDT) using high-frequency sound waves to measure the remaining wall thickness of steel pipes and boiler tubes without shutting down the plant.
- Over time, hot crude oil corrodes pipe walls. If the wall drops below a critical threshold, the pipe can rupture catastrophically.

### D. The ASME B31.3 Engineering Formula
The minimum required pipe wall thickness under internal pressure is governed by **ASME B31.3 (Process Piping Code)**:

$$t_{\text{min}} = \frac{P \cdot D}{2(S \cdot E + P \cdot Y)} + c$$

Where:
- $P$: Internal design pressure (e.g. $4.0\text{ MPa} = 40\text{ bar}$)
- $D$: Pipe outside diameter (e.g. $219.1\text{ mm}$ for an 8-inch nominal pipe)
- $S$: Allowable material stress (e.g. $137.0\text{ MPa}$ for ASTM A106 Grade B carbon steel)
- $E$: Longitudinal weld joint quality factor ($1.0$ for seamless pipe)
- $Y$: Temperature coefficient factor ($0.4$ for ferritic steel $<482^\circ\text{C}$)
- $c$: Corrosion allowance ($3.0\text{ mm}$ safety margin)

**Remaining Operational Life Equation:**
$$\text{Remaining Safe Life (Years)} = \frac{t_{\text{actual}} - t_{\text{min}}}{\text{Annual Corrosion Rate (mm/year)}}$$

---

## 3. Systems, Security & Air-Gap Mechanics

### A. How the Air-Gap Network Sniffer Works (`harness/network_monitor.py`)
- Uses Python's `psutil.net_connections(kind='inet')` to inspect all open TCP/UDP sockets.
- Evaluates destination IP addresses against RFC 1918 private subnets:
  - Allowed: `127.0.0.1` (localhost loopback), `192.168.0.0/16`, `10.0.0.0/8`, `172.16.0.0/12`.
  - Violations: Any public Internet routable IP (e.g. `8.8.8.8`, OpenAI IP ranges).
- Proves cryptographically to judges that no data leaves the physical laptop.

### B. Distributed LAN Compute Topology
- Connects Master Edge Station (Client Laptop) $\leftrightarrow$ Local Compute Pod (LAN GPU Node) over private Wi-Fi/Ethernet (`192.168.1.X`).
- Replicates an industrial refinery control-room network communicating with a local server-room GPU rack.

---

## 4. Codebase Reference Map

| Component | Path | Key Function |
| :--- | :--- | :--- |
| **Pydantic Schemas** | [`harness/types.py`](../harness/types.py) | Defines `WorkbenchState`, `TaskIntent`, `PSUApprovalNote` data contracts. |
| **Semantic Router** | [`harness/semantic_router.py`](../harness/semantic_router.py) | Sub-10ms intent classifier selecting specialized SLMs (Code, Vision, Reasoner). |
| **Math Sandbox** | [`harness/sandbox.py`](../harness/sandbox.py) | Subprocess runner executing ASME B31.3 math with 5s timeout. |
| **State Machine DAG**| [`harness/state_graph.py`](../harness/state_graph.py) | Multi-step DAG orchestrator with 3-retry circuit breaker. |
| **Sovereign RAG** | [`harness/sovereign_rag.py`](../harness/sovereign_rag.py) | On-premise BM25 keyword and vector retrieval over MRPL SOP manuals. |
| **Multimodal Parser**| [`harness/multimodal_parser.py`](../harness/multimodal_parser.py) | Parses input `.xlsx` ultrasonic logs and P&ID JSON metadata. |
| **Deliverable Engine**| [`harness/deliverable_engine.py`](../harness/deliverable_engine.py) | Generates official Microsoft Word (`.docx`) and Excel (`.xlsx`) deliverables. |
| **Air-Gap Sniffer** | [`harness/network_monitor.py`](../harness/network_monitor.py) | Live socket sniffer verifying 0 outbound WAN egress. |
| **FastAPI Backend** | [`api/server.py`](../api/server.py) | REST API hosting the Cyber Dark UI dashboard at `http://127.0.0.1:8000`. |
| **CLI Demo Runner** | [`cli/demo.py`](../cli/demo.py) | Interactive ANSI terminal runner stepping through the 4 Grand Finale flows. |

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

## 4. Cryptographic Proofs & Merkle DAG Mechanics

### A. Why Conventional Auditing Fails
Standard software logging outputs flat text files (e.g. `app.log`). In an industrial PSU setting:
1. Log entries can be retroactively edited with a text editor.
2. Flat logs provide no mathematical proof that an ASME B31.3 calculation wasn't tampered with after human review.
3. If an equipment failure triggers a judicial or safety inquiry, flat logs offer zero non-repudiation.

### B. SHA-256 Merkle Block Transition Model (`harness/audit_ledger.py`)
Our system binds every DAG node transition into a cryptographic block chain:
```text
Genesis Root (Block 0)
       │
       ▼
Block 1 (Intent & Model Binding) ──► SHA256(Block 0 Hash + Input + Output)
       │
       ▼
Block 2 (Step Planner DAG)       ──► SHA256(Block 1 Hash + Input + Output)
       │
       ▼
Block 3 (Sandbox Math Execution) ──► SHA256(Block 2 Hash + Input + Output)
       │
       ▼
Block 4 (Safety Critic Circuit)  ──► SHA256(Block 3 Hash + Input + Output)
       │
       ▼
Block 5 (Office Deliverables)    ──► SHA256(Block 4 Hash + Binary File Hashes)
       │
       ▼
   Merkle Root (Exported to QR Code Proof & Verification Certificate)
```

### C. Physical File Hash Verification (`verify_disk_artifacts`)
Even if the database ledger is preserved, an attacker could modify the generated `.docx` memo or `.xlsx` workbook on the Windows/Linux filesystem.  
The workbench calculates binary SHA-256 digests directly from disk storage:
$$\text{Digest} = \text{SHA-256}(\text{read\_bytes}("deliverables/Approval\_Note.docx"))$$
If even one character or font weight is altered on disk, the physical hash deviates from Block 5's cryptographic receipt, immediately flagging a tamper breach (`🚨 MERKLE FORGERY DETECTED`).

---

## 5. Sovereign RAG: BM25 + Dense Semantic Hybrid Retrieval

### A. Why Cloud Vector DBs (Pinecone, Weaviate Cloud) Are Banned
Transmitting internal Standard Operating Procedures (SOPs), emergency shutdown sequences, and Delegation of Power manuals to a remote vector database breaches on-premise air-gap requirements.

### B. Air-Gapped Hybrid Indexing (`harness/sovereign_rag.py`)
1. **Inverted BM25 Index:** Tokenizes documents locally using frequency-inverse document frequency weighting. Ensures 100% recall on technical equipment tags (e.g., `B-101`, `CDU-1`, `DOP Schedule 4.1`) where dense semantic embeddings often experience semantic drift.
2. **Dense Semantic Matching:** Encodes chunks locally without internet access.
3. **Reciprocal Rank Fusion (RRF):** Blends keyword and semantic scores:
   $$RRF(d) = \sum_{m \in M} \frac{1}{60 + r_m(d)}$$
4. **Grounded Source Attribution:** Every generated sentence in the RAG Studio links back to verifiable paragraph chunks with exact line numbers.

---

## 6. Codebase Reference Map

| Component | Path | Key Function |
| :--- | :--- | :--- |
| **Pydantic Schemas** | [`harness/types.py`](../harness/types.py) | Defines `WorkbenchState`, `TaskIntent`, `PSUApprovalNote` data contracts. |
| **Semantic Router** | [`harness/semantic_router.py`](../harness/semantic_router.py) | Sub-10ms intent classifier selecting specialized SLMs (Code, Vision, Reasoner). |
| **Model Adapter** | [`harness/model_adapter.py`](../harness/model_adapter.py) | Pluggable local inference layer supporting Ollama, llama.cpp, and LAN pods. |
| **Math Sandbox** | [`harness/sandbox.py`](../harness/sandbox.py) | Subprocess runner executing ASME B31.3 math with 5s timeout. |
| **State Machine DAG**| [`harness/state_graph.py`](../harness/state_graph.py) | Multi-step DAG orchestrator with 3-retry circuit breaker. |
| **Merkle Audit Ledger**| [`harness/audit_ledger.py`](../harness/audit_ledger.py) | Cryptographic block DAG & physical on-disk file binary hash auditor. |
| **Sovereign RAG** | [`harness/sovereign_rag.py`](../harness/sovereign_rag.py) | On-premise BM25 keyword and dense semantic retrieval over MRPL SOP manuals. |
| **Multimodal Parser**| [`harness/multimodal_parser.py`](../harness/multimodal_parser.py) | Parses input `.xlsx` ultrasonic logs and P&ID JSON metadata. |
| **Deliverable Engine**| [`harness/deliverable_engine.py`](../harness/deliverable_engine.py) | Generates official Microsoft Word (`.docx`) and Excel (`.xlsx`) deliverables. |
| **Certificate Generator**| [`harness/certificate_generator.py`](../harness/certificate_generator.py) | Renders printable PDF/PNG compliance certificates with scannable QR proof. |
| **Air-Gap Sniffer** | [`harness/network_monitor.py`](../harness/network_monitor.py) | Live socket sniffer verifying 0 outbound WAN egress. |
| **FastAPI Backend** | [`api/server.py`](../api/server.py) | REST API hosting the Cyber Dark UI dashboard at `http://127.0.0.1:8000`. |
| **CLI Demo Runner** | [`cli/demo.py`](../cli/demo.py) | Interactive ANSI terminal runner stepping through the 4 Grand Finale flows. |


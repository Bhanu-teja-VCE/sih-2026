# SIH 2026 — Team Orchestration & AGENTS Blueprint (MRPL PS 26117)
> **Master Context:** Linked to Bhanu Teja's primary context [`AGENTS.md`](file:///C:/Users/bhanu/OneDrive/Desktop/second%20year/AGENTS.md) and [`PROBLEM_STATEMENT_GROUND_TRUTH.md`](file:///c:/Users/bhanu/OneDrive/Desktop/sih%202026/PROBLEM_STATEMENT_GROUND_TRUTH.md).

---

## 🔒 IMMUTABLE GROUND TRUTH ANCHOR (MRPL PS 26117)

### Background:
Refineries, PSUs, defence-linked manufacturing units and government offices generate a lot of routine but sensitive knowledge work. Approval notes, board presentations, engineering calculations, code for internal tools, review of scanned drawings and inspection reports. None of this can go through cloud AI assistants like Claude or Codex because the underlying data is confidential: Piping & Instrument Diagrams, financials, vendor negotiations, unreleased designs, internal correspondence, confidential business strategies etc. Company policy keeps this data on premises, so people either do the work manually resulting in productivity loss, or they quietly paste confidential material into public tools anyway. Open weight large reasoning models have reached a point where a genuinely useful assistant built on them is realistic. But nothing deployable exists today that industrial users can actually work with the way they use Claude or Codex.

### Description:
The idea is a self-hosted, air gapped AI workbench running entirely on the organization's own GPU server. Nothing leaves the premises. The backend should not be locked to one model. It needs to support multiple open weight models at once and automatically pick the right one for a given task based on what that task needs, a coding request handled differently from a document summary request. New open weight models should be addable later without redesigning the system, since this space is moving fast.

The assistant also needs to actually act like an agent. Plan out multi step work, call local tools such as file read and write, code execution in a sandbox, spreadsheet work, internal document search, and iterate on a task instead of answering once and stopping. It needs to handle more than text too: scanned PDFs, handwritten notes, engineering drawings, photographs, read through on device OCR and vision models. Output should be real deliverables, approval notes, PPT/Word/Excel files, working code, calculations with steps shown, not just chat replies. And it needs to ground itself in the organization's own manuals, SOPs and past correspondence through a local knowledge base connector, again with nothing going external.

### Expected Solution & Demonstrable Evaluation Criteria:
A working local deployment, demonstrable on a single workstation or server with a mid range GPU (use a smaller open weight model if 120B class hardware isn't available at the venue), that shows:
1. **Model auto selection** across at least two different task types.
2. **An agentic task carried through end to end**, for example reading a scanned inspection report, pulling out key findings and drafting an approval note as a Word file.
3. **A coding task** run and verified in a sandbox.
4. **A multimodal task** involving image or scanned document understanding (P&IDs, drawings, handwritten notes).
5. **Visible Network Monitor / Egress Proof**: The system should also show, through logs or a visible network monitor, that no external calls are made at any point. That's the actual proof of the sovereign claim, not just a statement of it.

---

## 1. What the Ideal Solution Looks Like (Our North Star Benchmark)

To score highest in SIH 2026 evaluations, our system satisfies all five criteria with mathematical rigor:

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               SOVEREIGN INDUSTRIAL WORKBENCH                           │
│                                                                                        │
│  [User Intent / Scanned Document]                                                      │
│               │                                                                        │
│               ▼                                                                        │
│  1. POLY-MODEL ROUTER ──────► Qwen-Coder-7B (Code) | Qwen2-VL (P&ID) | DeepSeek-R1     │
│               │                                                                        │
│               ▼                                                                        │
│  2. DETERMINISTIC STATE DAG ──► Step Planner ──► Sandboxed Executor ──► Self-Healing   │
│               │                                                                        │
│               ▼                                                                        │
│  3. LOCAL TOOL SUITE ───────► Python Sandbox (ASME Math) + Tesseract OCR + Local RAG   │
│               │                                                                        │
│               ▼                                                                        │
│  4. INDUSTRIAL DELIVERABLE ─► Microsoft Word .docx (PSU Note) & Excel .xlsx Sheet      │
│               │                                                                        │
│               ▼                                                                        │
│  5. AIR-GAP VERIFICATION ───► Live Network Sniffer (0 WAN Packets Logged)              │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

1. **Deterministic Guarantees**: Raw LLM output is untrusted. All calculations are executed in Python subprocess sandboxes.
2. **Pluggable Poly-Model Layer**: Switching from a 3B model to a 70B model requires modifying only a single config entry.
3. **Formal PSU Formatting**: Generates Word documents matching MRPL's exact approval structure.
4. **Verifiable Egress Proof**: Real-time packet sniffer proves zero internet packets leave the machine.

---

## 2. System Directory Blueprint

```text
sih 2026/
├── .gitignore                          # Clean git ignore for Python/Venv/Node/GGUF
├── README.md                           # Master project documentation & live demo guide
├── AGENTS.md                           # Master context, ideal specs & learning invariants
├── PROBLEM_STATEMENT_GROUND_TRUTH.md   # Official MRPL requirements anchor
├── IMPLEMENTATION_SPEC.md              # Technical specification
│
├── harness/                            # Core Deterministic Harness Engine
│   ├── __init__.py
│   ├── types.py                        # Pydantic schemas for state, intent, and tool contracts
│   ├── semantic_router.py              # Fast intent classifier & Poly-Model selector
│   ├── model_adapter.py                # Pluggable inference layer (Ollama / Local HTTP / GGUF)
│   ├── sandbox.py                      # Subprocess calculation runner with circuit breaker
│   ├── state_graph.py                  # Deterministic Agentic DAG (Plan -> Tool -> Verify -> Output)
│   ├── network_monitor.py              # Real-time socket sniffer proving 0 external packets
│   └── deliverable_engine.py           # PSU-formatted Word (.docx) & Excel (.xlsx) generator
│
├── data/                               # Sample Industrial Ground Truth Datasets
│   ├── sample_inspection_report.txt    # Scanned boiler ultrasonic thickness test data
│   ├── sample_pid_metadata.json        # P&ID valve and line specification data
│   └── refinery_sop_handbook.txt       # MRPL standard operating procedures for RAG
│
├── deliverables/                       # Output artifact directory for generated .docx / .xlsx
│
└── tests/                              # Evals-as-Code & Automated Verification Suite
    ├── __init__.py
    ├── test_router.py                  # Verifies model auto-routing across task types
    ├── test_sandbox.py                 # Tests formula execution & circuit breaker recovery
    ├── test_state_graph.py             # Verifies end-to-end agentic workflow
    ├── test_network_monitor.py         # Verifies air-gap 0-egress detection
    └── test_deliverables.py            # Verifies valid .docx and .xlsx generation
```

---

## 3. Role Architecture & Learning Contract

- **Team Lead (Bhanu Teja)**: **Sole Technical Builder & AI Harness Architect**
  - Owns 100% of the technical implementation, state graph mechanics, backend, frontend, and verification harness.
  - Learning Invariant: **Understand every single line, mechanism, and state transition before running it.** No black-box cargo culting.
  - Architectural Thesis: The project's strength is **The Harness Around the LLM**. Models are cheap, interchangeable commodities; the harness is the defensible intellectual property.

- **Virtual AI Partner (Antigravity)**: **Relentless Pair-Programmer & Conceptual Tutor**
  - Explains the intuition, mathematical invariants, data structures, and trade-offs before writing code.
  - Builds clean, modular, transparent Python & TypeScript code.

---

## 4. Realistic Team Delegation Matrix (Zero-Code Friction)

| Member | Assigned Responsibility | Concrete High-Leverage Deliverables |
| :--- | :--- | :--- |
| **Bhanu Teja (Lead)** | **Full System Architecture & Engineering** | State Graph DAG, Poly-Model Router, Sandboxed Calculator, Air-Gap Monitor, Deliverable Exporter |
| **Member 2** | **SIH Pitch Deck & Storyboarding** | Official AICTE/MRPL slide deck format, problem framing, workflow graphics |
| **Member 3** | **Industrial Sample Dataset Sourcing** | Gathering open-source P&ID diagrams, sample refinery boiler inspection reports, PSU SOP documents |
| **Member 4** | **Ground Truth Verification & Math Auditing**| Hand-verifying engineering formulas (e.g. ASME B31.3 Barlow's equation) against generated outputs |
| **Member 5** | **PSU Approval Note Formatting & Templates** | Designing standard MRPL Word `.docx` templates (Subject, Background, Implication, Recommendation) |
| **Member 6** | **Live Pitch Rehearsal & Hardware Setup** | Managing local LAN/Wi-Fi router setup, backup laptop tethering, timing pitch delivery |

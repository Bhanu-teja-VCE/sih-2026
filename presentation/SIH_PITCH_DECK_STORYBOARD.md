# Smart India Hackathon 2026 — Master Pitch Deck Storyboard
## Problem Statement ID: 26117 | Organization: Mangalore Refinery and Petrochemicals Limited (MRPL)
### Title: Sovereign On-Premise Agentic AI Workbench for Confidential Industrial Work
**Team Lead & AI Harness Architect:** Bhanu Teja

---

## 🎯 Slide 1: Title & Executive Identity
- **Header:** Sovereign Industrial AI Workbench
- **Sub-Header:** 100% Air-Gapped, Poly-Model Agentic Assistant for Confidential PSU Knowledge Work
- **Problem Statement ID:** `26117` | **Theme:** Smart Automation | **Category:** Software
- **Ministry / PSU Sponsor:** Mangalore Refinery and Petrochemicals Limited (MRPL)
- **Key Message:** *"Eliminating data leaks by bringing verifiable reasoning models to on-premise industrial hardware."*

---

## 🏭 Slide 2: The Industrial Dilemma (The Critical Gap)
- **The Reality in Indian Refineries & PSUs:**
  - Engineers handle confidential P&IDs, ultrasonic boiler inspection logs, vendor negotiations, and financial approval notes daily.
  - **The Compliance Barrier:** Cloud AI (Claude, ChatGPT, Codex) is banned on premises due to data sovereignty and defense/PSU security mandates.
  - **The Current Pain:** Engineers either perform tedious manual calculations or quietly leak proprietary data into public tools.
- **The Core Solution:** A self-hosted, air-gapped agentic workbench running on enterprise GPU/CPU servers where zero bytes leave the organization.

---

## 🧠 Slide 3: Poly-Model Semantic Auto-Routing
- **The Architectural Flaw of Competitors:** Single 70B models are slow, expensive, and fail across mixed task modalities.
- **Our Innovation:** A lightweight **Semantic Router** running in $<10\text{ms}$ on CPU:
  - `CODE_ANALYSIS` $\rightarrow$ **Qwen2.5-Coder-7B** (ASME script generation & simulation)
  - `VISION_INSPECTION` $\rightarrow$ **Qwen2-VL-7B / MiniCPM-V** (P&ID diagrams, scanned logs)
  - `APPROVAL_MEMO` $\rightarrow$ **DeepSeek-R1-Distill-8B** (Formal PSU administrative reasoning)
- **Pluggable Architecture:** Dropping any new `.gguf` open-weight model into the registry works seamlessly without system redesign.

---

## ⚡ Slide 4: Deterministic State Graph DAG vs. Chatbot Wrappers
- **Why Chatbots Fail in PSUs:** Non-deterministic LLM chains crash on unexpected JSON or hallucinations.
- **Our Deterministic State Machine:**
  ```text
  [Ingest Report] ──► [DAG Planner] ──► [Sandbox Tool] ──► [Critic Verifier] ──► [PSU Deliverable]
                             ▲                                    │ (On Error: Retry <= 3)
                             └────────────────────────────────────┘
  ```
- **Circuit Breaker:** Automatic error capture, stack trace re-injection, and bounded self-correction (3 retries max).

---

## 📐 Slide 5: Sandboxed Math & ASME B31.3 Safety Code Verification
- **Zero Calculation Hallucinations:** The model is strictly forbidden from doing arithmetic in text.
- **The Mechanism:** The model writes pure Python code for ASME B31.3 modified Barlow equation:
  $$t_{\text{req}} = \frac{P \cdot D}{2(S \cdot E + P \cdot Y)} + c$$
- **Isolated Subprocess:** Runs inside a sandboxed Python runtime with a 5-second timeout boundary, capturing exact mathematical margins and safe operational life.

---

## 📑 Slide 6: Multimodal Ingestion & Sovereign Local RAG
- **Multimodal Document Parser:**
  - Ingests raw Excel field logs (`.xlsx`), scanned ultrasonic inspection reports, and P&ID metadata (`.json`).
- **100% On-Premise Sovereign RAG:**
  - BM25 hybrid ranking over MRPL Standard Operating Procedures (`SOP Manual Section 14`) with zero cloud dependencies.

---

## 📄 Slide 7: Real Industrial Deliverables (Not Chat Messages)
- **Direct Output Generation:**
  1. **Microsoft Word (`.docx`) Approval Note:** Structured with official PSU headers (Subject, Background, Inspection Findings, ASME Calculation, Financial Implication, Delegation of Power, Recommendation).
  2. **Excel (`.xlsx`) Calculation Workbook:** Formatted parameter tables with color-coded safety compliance flags.

---

## 🔒 Slide 8: Live Air-Gap Verification (Verifiable Egress Proof)
- **The Sovereign Guarantee:** Proving that zero network packets escape the machine.
- **Live Socket Sniffer:**
  - Real-time monitor scanning active TCP/UDP sockets via `psutil`.
  - Logs $0$ external WAN connections outside `127.0.0.1` / `192.168.1.X`.
  - Outputs a digitally generated **On-Premise Air-Gap Audit Certificate**.

---

## 🌐 Slide 9: Distributed Edge-to-Server Industrial Topology
- **Realistic Plant Architecture:**
  - **Master Edge Station (Bhanu's Laptop):** UI + State Graph DAG + Sandboxed Runner.
  - **Server Compute Pod (Friend's Laptop):** Ollama / llama.cpp running over isolated private LAN.
- **The Pitch:** Demonstrates how control room workstations communicate with on-premise refinery server racks over air-gapped subnets.

---

## 🚀 Slide 10: Business Impact, Scalability & Roadmap
- **Immediate Value for MRPL:**
  - Reduces turnaround approval note preparation time from **6 hours to under 30 seconds**.
  - 100% compliant with Indian Public Sector Undertaking cybersecurity policies.
- **Horizontal Scalability:** Readily deployable across IOCL, ONGC, HPCL, BPCL, GAIL, and defense-linked ordnance manufacturing units.
- **Team Execution:** Lead by Bhanu Teja with fully tested deterministic code and 100% pass rate.

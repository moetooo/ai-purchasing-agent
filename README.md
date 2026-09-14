# AI Purchasing Agent

**Live Demo:** [https://demo-ai-purchasing-agent.streamlit.app/](https://demo-ai-purchasing-agent.streamlit.app/)

This repository contains a full-stack AI Purchasing Agent built to assist buyers with procurement decisions. The agent analyzes context, respects hard operational constraints, makes autonomous (or HITL) decisions, and automatically validates its own actions.

## Architecture & Design Principles

* **Untrusted Proposal Pattern**: A recommendation comes into the system (e.g., Buy 800 units of SKU-001). The agent treats this strictly as a proposal and gathers contextual data before acting.
* **Hard Constraint Enforcement**: The system relies on a purely Python-based deterministic constraint engine that evaluates budget limits, storage capacities, MOQ, and supplier availability. The LLM cannot override math. If the constraint engine outputs a `max_feasible_qty` of 500, the LLM will modify the order down from 800 to 500.
* **Closed-Loop Feedback & Validation**: Creating the purchase order isn't the final step. A post-action validator inspects the actual database state and compares it against expected execution, classifying the outcome as `VALID`, `PARTIALLY_VALID`, or `INVALID`. 

![Architecture Diagram](architecture.png)

## Scenarios Handled

The system handles the 5 core scenarios natively:
1. **Fully Feasible**: Ideal conditions. Result: `ACCEPT`
2. **Storage Limit Breach**: Recommendation exceeds warehouse capacity. Result: `MODIFY`
3. **Budget Breach**: Total cost exceeds allocated purchasing budget. Result: `REJECT` or `MODIFY`
4. **Supplier Capacity Bottleneck**: Supplier does not have enough stock to fulfill the order. Result: `INVESTIGATE` or `MODIFY`
5. **Partial Execution Validation Demo (The "Demo Story")**: The agent intends to buy 500 units, but a supplier bottleneck (simulated in the API) results in a PO of 300 units being created. The validator flags it as `PARTIALLY_VALID`.

## Setup & Run Instructions

### Prerequisites
1. Python 3.11+
2. A Google Gemini API Key

### Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Environment Setup

Rename `.env.example` to `.env` and insert your API key:
```
GOOGLE_API_KEY=your_gemini_api_key_here
```

### Running Locally

You can run the Streamlit frontend locally. The database will automatically seed with mock data.

```bash
streamlit run frontend/dashboard.py
```

To start the FastAPI Mock backend separately:
```bash
python main.py
```

### Running Evaluation Tests
We have built an automated evaluation suite to run the system through the core scenarios and grade decision accuracy, constraint compliance, and post-validation tracking.

```bash
python tests/run_eval.py
```

## Docker

You can also run everything using the provided Dockerfile.
```bash
docker build -t ai-purchasing-agent .
docker run -p 8000:8000 -p 8501:8501 --env-file .env ai-purchasing-agent
```

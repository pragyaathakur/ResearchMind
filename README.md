# ResearchMind — Agentic AI System

ResearchMind is a sequential multi-agent orchestrator designed to automate deep web research, structured data extraction, and comprehensive synthesis. Built to solve the core challenges of autonomous AI hallucination and uncontrolled tool execution, the platform introduces a human-guided approach to agentic workflows.

## 🚀 Features & Architecture

* **Sequential Multi-Agent Workflow:** Utilizes specialized, stateful nodes built with **LangGraph** to break down research objectives, coordinate dynamic web searches, and execute granular content scraping.
* **Human-in-the-Loop (HITL) Middleware:** Features custom execution middleware that allows users to intercept, review, and modify external tool calls in real time before final compilation, ensuring total control over data gathering.
* **Context-Rich Extraction:** Integrates robust web scraping APIs to pull deep, high-fidelity data from external sources while filtering out noise.
* **Intuitive Interface:** Wrapped in a responsive **Streamlit** frontend combined with custom HTML/CSS for a seamless user experience.

## 🛠️ Tech Stack

| Component | Technologies Used |
| :--- | :--- |
| **Core Frameworks** | Python, LangChain, LangGraph |
| **Frontend UI** | Streamlit, HTML, CSS |
| **Data & Extraction** | Web Scraping APIs, External Search Tools |


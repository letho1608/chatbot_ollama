# Individual Report

## Personal Information
- **Name:** Lê Quang Thọ
- **Student ID:** 2A202600597
- **Team:** Team 9
- **Date:** 1/6/2026

## I. Technical Contribution (15 pts)
- **Project Initialization & Core Architecture:** Initiated the "Tysor Cyber Security AI Chatbot" project. Built the foundational backend architecture using FastAPI (`main.py`) and set up the modular `core/` directory structure (`agent.py`, `config.py`, `memory.py`, `rag.py`, `safety.py`, `tunnel.py`, `validator.py`).
- **Agent Loop & RAG:** Implemented the core ReAct agent loop (`core/agent.py`) integrating tool execution. Developed the Retrieval-Augmented Generation (RAG) capabilities (`core/rag.py`) for document processing and vector search.
- **System Monitoring & Telemetry:** Built `core/monitor.py` for local Ollama prompt logging, performance telemetry, and system tracking. Added auto-scaling worker queues (`core/queue.py`).
- **Testing & Code Quality:** Refactored project structure to be more maintainable (moving root scripts to `core/`). Developed comprehensive unit tests across all modules (`tests/test_agent.py`, `tests/test_api.py`, `tests/test_rag.py`, etc.) ensuring high test coverage. Added `.gitignore` and `.mailmap` for clean version control.
- **Deployment & Networking:** Integrated Cloudflare Tunnels for exposing the local AI server safely (`core/tunnel.py`, `cloudflared.exe` auto-install, `start.bat`, `wait_for_tunnel.py`).

## II. Debugging Case Study (10 pts)
- **Failure Case:** During deployment on Windows, the startup script (`start.bat`) failed to properly run the Python code responsible for starting and monitoring the Cloudflare Tunnel. The batch file threw errors like `'import' is not recognized as an internal or external command`.
- **Identification:** I identified the failure by analyzing the console output during server startup. The Windows Command Prompt (`cmd.exe`) was misinterpreting the inline multi-line Python command (`python -c "..."`) as native batch commands, causing a syntax crash.
- **Resolution via Logs/Trace:** Tracing the execution flow showed that while the Uvicorn server started correctly in the background, the tunnel monitoring loop failed to execute, leaving the server without a public URL.
- **Final Fix:** I resolved the issue by extracting the inline Python code from `start.bat` into a dedicated standalone script named `wait_for_tunnel.py`. The `start.bat` was then updated to simply call `python wait_for_tunnel.py`, ensuring cross-platform compatibility and clean execution without batch parser conflicts.

## III. Personal Insights (10 pts)
- **LLM Chatbots vs ReAct Agents:** A standard LLM chatbot relies purely on its internal parametric memory, which often leads to outdated information or hallucinations, especially in the rapidly changing cybersecurity domain. In contrast, a ReAct (Reasoning and Acting) Agent can autonomously decide to use external tools (like RAG to search documents or Web Fetch to search the internet) to ground its responses in verified data.
- **Differences in Reasoning & Reliability:** ReAct agents require much more complex system prompts and careful parsing of the model's output (Thought/Action/Observation loop). While they are significantly more reliable for factual answering, they are also slower because they require multiple inference steps. Standard chatbots are faster but less trustworthy for technical security queries.
- **Experimental Findings:** While building `core/agent.py`, I realized that providing clear tool descriptions and examples in the system prompt is critical. Without strict guidelines, the agent sometimes falls into infinite loops of calling the same tool or formatting the tool inputs incorrectly.

## IV. Future Improvements (5 pts)
- **Production RAG & Multi-Agent System:** The current RAG system can be scaled by migrating from a local vector store to a production-grade database like Milvus or Pinecone. Additionally, transitioning the architecture to a multi-agent system (e.g., separating a 'Security Analyst Agent' from a 'Code Review Agent') would improve response quality and task delegation.
- **Enhancements for Safety & Monitoring:** Implement more robust guardrails in `core/safety.py` using LLM-based output evaluation (Self-Reflection) to catch harmful or unsafe security advice before it reaches the user.
- **Next-step Improvements:** Integrate GraphRAG to capture complex relationships between cybersecurity entities (e.g., linking specific APT groups to their typical CVEs and attack vectors) to provide deeper, more contextual answers.

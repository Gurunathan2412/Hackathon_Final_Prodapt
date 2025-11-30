# Telecom Assistant

Modular AI-driven telecom customer assistant integrating:
- LangGraph (orchestration)
- CrewAI (billing & account)
- AutoGen (network troubleshooting)
- LangChain (service recommendations)
- LlamaIndex (knowledge retrieval)

## Setup
1. Create .env and set OPENAI_API_KEY.
2. pip install -r telecom_assistant/requirements.txt
3. (Optional) Run vector store build: from utils.document_loader import ensure_vector_store; ensure_vector_store()
4. streamlit run telecom_assistant/app.py

## Features
Submit queries via UI. System classifies and routes to appropriate agent framework.

## Enhancements
- Caching for agents (CrewAI, LangChain, AutoGen, LlamaIndex) to reduce init latency.
- Structured error responses with detail and fallback suggestions.
- UI expanders for intermediate JSON and full state.

## Notes
Some advanced multi-agent behaviors depend on external service availability and API keys.

### Logging
Loguru integrated for classification and agent error events (optional install).

### Troubleshooting
If an agent returns 'not initialized', verify package installed in active venv and API key loaded.

### Caching
Agents and query engines are cached after first creation to improve performance; restart app to rebuild if underlying data changes.

### Sample Queries
- Why is my bill higher this month?
- Recommend a plan for a family of four streaming daily.
- I can't make calls, signal drops frequently.
- How do I enable VoLTE?

### Security Note
Do not commit .env containing API keys. Rotate keys periodically.

### Future Work
- Add authentication & user management
- Enhanced analytics dashboard
- Automatic agent performance evaluation
- Prompt optimization and cost tracking

### License
Internal project; add license if distributing.

Status field indicates pipeline progression (classified -> ok/error -> completed). Example status values: classified, ok, error, completed.

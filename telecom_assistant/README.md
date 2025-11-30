# Telecom Assistant - Multi-Agent Customer Support System

A sophisticated customer support system using multiple AI agent frameworks (CrewAI, AutoGen, LangChain, LlamaIndex) orchestrated with LangGraph.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Add your OPENAI_API_KEY to .env

# Run the application
streamlit run ui/streamlit_app.py
```

## 📋 Features

- **Multi-Framework Architecture**: CrewAI, AutoGen, LangChain, LlamaIndex
- **Intelligent Query Routing**: Automatic classification and routing
- **Admin Dashboard**: Document upload and knowledge base management
- **Customer Dashboard**: Interactive query interface
- **Database Integration**: 13 tables with comprehensive customer data

## 🏗️ Architecture

### Query Types & Frameworks:
1. **Billing Queries** → CrewAI agents
2. **Network Issues** → AutoGen multi-agent conversation
3. **Service Plans** → LangChain ReAct agent
4. **Technical Support** → LlamaIndex query engine

### Orchestration:
- **LangGraph** StateGraph with conditional routing
- Context enrichment and response formatting

## 📁 Project Structure

```
telecom_assistant/
├── agents/          # Agent implementations (CrewAI, AutoGen, LangChain, LlamaIndex)
├── config/          # Configuration files
├── data/            # Database and vector store
├── orchestration/   # LangGraph orchestration
├── ui/              # Streamlit interface
├── utils/           # Utility functions
├── docs/            # Documentation and archives
├── tests/           # Test files
└── app.py           # Main application entry
```

## 📚 Documentation

Full documentation is available in `docs/documentation/`:
- [Quick Start Guide](docs/documentation/QUICK_START.md)
- [Implementation Verification](docs/documentation/IMPLEMENTATION_VERIFICATION.md)
- [Sample Queries Test Guide](docs/documentation/SAMPLE_QUERIES_TEST_GUIDE.md)
- [Validation Summary](docs/documentation/VALIDATION_SUMMARY.md)

## 🧪 Testing

Run tests from the `tests/` directory:
```bash
# Quick validation (< 5 seconds)
python tests/test_quick_validation.py

# Classification accuracy test
python tests/test_sample_queries_classification.py

# Integration tests
python tests/test_integration.py
```

## 🛠️ Utilities

- `check_data.py` - Database data verification utility

## 🔧 Technologies

- **Python 3.13+**
- **CrewAI 1.6.1** - Multi-agent collaboration
- **AutoGen** - Conversational agents with function calling
- **LangChain** - ReAct agents and tools
- **LlamaIndex** - Vector-based retrieval
- **LangGraph** - Workflow orchestration
- **Streamlit** - Web interface
- **SQLite** - Data storage
- **OpenAI GPT-4o-mini** - LLM backend

## 📝 License

Copyright © 2025 Telecom Assistant Project

## 🤝 Support

For issues or questions, refer to the documentation in `docs/documentation/`.

---

**Status**: ✅ Production Ready | **Version**: 1.0 | **Last Updated**: November 30, 2025

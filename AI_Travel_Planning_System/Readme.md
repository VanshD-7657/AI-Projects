
# 🌍 AI Travel Planning System

[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-Streamlit-red?style=for-the-badge)](https://vd-ai-travel-planning-system.streamlit.app/)

### An intelligent multi-agent AI travel assistant that helps users create personalized travel itineraries, search flights, gather real-time travel information, and generate downloadable travel plans.

## 🚀 Features

- 🤖 Multi-Agent AI Workflow using LangGraph
- ✈️ Real-Time Flight Search
- 🌐 Live Travel Information via Tavily Search
- 🧠 Context-Aware Conversations with Persistent Memory
- 💾 PostgreSQL (Neon Cloud) Integration
- 📄 Automated Travel Itinerary PDF Generation
- ⚡ Fast Inference with Groq LLM
- 🎯 Personalized Travel Recommendations

---

## 🛠️ Tech Stack

### Languages
- Python

### Frameworks & Libraries
- LangChain
- LangGraph
- Streamlit

### LLM
- Groq LLM

### Database
- PostgreSQL (Neon Cloud)

### Tools & APIs
- Tavily Search API
- Flight Search Tool
- PDF Generation Tool

---

## 📂 Project Structure

```bash
AI_Travel_Planning_System/
│
├── app.py
├── main.py
├── agents/
├── tools/
├── prompts/
├── requirements.txt
├── .env
└── README.md
````

## 🏗️ System Workflow

```text
User Query
    │
    ▼
Travel Planner Agent
    │
    ▼
LangGraph Workflow
    │
    ├── Flight Search Tool
    ├── Tavily Search Tool
    └── PDF Generator Tool
    │
    ▼
Groq LLM
    │
    ▼
PostgreSQL Memory (Neon)
    │
    ▼
Final Travel Plan
```

## ⚙️ Installation

### Clone Repository

```bash
git clone https://github.com/VanshD-7657/AI-Projects.git
cd AI_Travel_Planning_System
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Environment

#### Windows

```bash
venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
DATABASE_URL=your_neon_postgresql_connection_string
```

### Run Application

```bash
streamlit run app.py
```

---

## 🌐 Deployment

* Streamlit Cloud
* Neon PostgreSQL

---

## 🚧 Challenges Solved

* Migrated from Local PostgreSQL to Neon Cloud PostgreSQL
* Resolved Streamlit Cloud deployment issues
* Implemented secure secrets management
* Integrated multiple tools within LangGraph workflows
* Fixed dependency and environment configuration issues
* Debugged production-level database connectivity problems

---

## 📚 Learning Outcomes

* Multi-Agent AI Systems
* LangGraph Workflow Design
* LLM Application Development
* Cloud Database Integration
* Tool Calling & Agent Orchestration
* Production Deployment
* Streamlit Cloud Deployment
* Generative AI Application Development

---

## 🔮 Future Enhancements

* Hotel Search Integration
* Weather Forecast Integration
* Maps & Route Optimization
* User Authentication
* Budget Planning Module
* Voice-Based Travel Assistant
* Multi-Language Support

---

## 👨‍💻 Author

**Vansh Dhall**

Aspiring Data Scientist | AI & Machine Learning Enthusiast

GitHub: https://github.com/VanshD-7657

```
```

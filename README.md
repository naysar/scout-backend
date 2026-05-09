# Scout - AI Research Agent

Scout is an autonomous AI research agent that takes a goal, breaks it into tasks, searches the web, critiques its own results, and generates a structured report in real time.

Live demo: https://scout-frontend-mauve.vercel.app

---

## What it does

Type any research goal. Scout will:
- Break it into 4-6 sub-tasks using an LLM
- Search the web for each task using Tavily
- Score each result 1-5 and retry if quality is too low
- Store findings in vector memory for future sessions
- Synthesize everything into a structured markdown report

---

## Architecture

Goal -> Planner -> Executor -> Critic -> Memory -> Reporter
             ^_______________|
             (retry if score < 3)

- Planner - Llama 3.3 70B breaks the goal into concrete sub-tasks
- Executor - Tavily searches the web for each task
- Critic - LLM scores results 1-5, retries poor results (score < 3)
- Memory - ChromaDB stores findings, recalls related past research
- Reporter - Synthesizes all findings into a markdown report

---

## Tech stack

Backend
- Python 3.11
- LangGraph - agent state machine
- LangChain + Groq (Llama 3.3 70B) - LLM inference
- Tavily - web search
- ChromaDB Cloud - vector memory
- FastAPI - REST API + SSE streaming
- PostgreSQL - user auth persistence
- JWT - authentication

Frontend
- Next.js 14
- React
- Server-Sent Events for real-time streaming

Infrastructure
- Railway - backend deployment
- Vercel - frontend deployment

---

## Running locally

1. Clone the repo
2. Create a virtual environment and install dependencies with pip install -r requirements.txt
3. Copy .env.example to .env and fill in your keys
4. Run with uvicorn src.api.main:app --reload --port 8000

---

## Key features

- Self-correcting - critic node scores each result and retries if quality is insufficient
- Persistent memory - ChromaDB stores past research, related queries recall previous findings
- Real-time streaming - SSE streams agent progress live to the frontend
- Auth system - JWT + bcrypt + rate limiting + PostgreSQL
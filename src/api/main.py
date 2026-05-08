import asyncio
import uuid
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from src.agent.graph import graph
from src.agent.state import AgentState

app = FastAPI()

from src.auth.routes import router as auth_router
app.include_router(auth_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

tasks = {}

class ResearchRequest(BaseModel):
    goal: str

@app.post("/run")
async def run_agent(request: ResearchRequest):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "running", "report": None, "logs": []}
    asyncio.create_task(run_in_background(task_id, request.goal))
    return {"task_id": task_id}

async def run_in_background(task_id: str, goal: str):
    initial_state: AgentState = {
        "goal": goal,
        "tasks": [],
        "current_task_index": 0,
        "scratchpad": [],
        "final_report": None
    }
    def log(msg):
        tasks[task_id]["logs"].append(msg)
        print(msg)
    log(f"Starting research: {goal}")
    try:
        final_state = await asyncio.to_thread(graph.invoke, initial_state)
        tasks[task_id]["report"] = final_state["final_report"]
        tasks[task_id]["status"] = "done"
        log("Research complete!")
    except Exception as e:
        tasks[task_id]["status"] = "failed"
        log(f"Error: {str(e)}")

@app.get("/stream/{task_id}")
async def stream(task_id: str):
    async def event_generator():
        last_index = 0
        while True:
            task = tasks.get(task_id)
            if not task:
                yield {"data": "Task not found"}
                break
            logs = task["logs"]
            while last_index < len(logs):
                yield {"data": logs[last_index]}
                last_index += 1
            if task["status"] == "done":
                yield {"data": "REPORT:" + task["report"]}
                yield {"data": "[DONE]"}
                break
            elif task["status"] == "failed":
                yield {"data": "[FAILED]"}
                break
            await asyncio.sleep(0.5)
    return EventSourceResponse(event_generator())

@app.get("/status/{task_id}")
async def status(task_id: str):
    task = tasks.get(task_id)
    if not task:
        return {"error": "Task not found"}
    return task
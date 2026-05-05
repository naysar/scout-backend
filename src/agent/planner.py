import json
import os
from langchain_groq import ChatGroq
from src.agent.state import AgentState

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)

def planner_node(state: AgentState) -> AgentState:
    print("\n🧠 PLANNER: Breaking down goal into tasks...")

    prompt = f"""You are a research planning assistant.

Break down this research goal into 4-6 concrete sub-tasks:
Goal: {state["goal"]}

Respond ONLY with a JSON array like this, nothing else:
[
  {{"id": 1, "description": "search for X", "status": "pending", "result": null}},
  {{"id": 2, "description": "search for Y", "status": "pending", "result": null}}
]"""

    response = llm.invoke(prompt)
    content = response.content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]

    tasks = json.loads(content.strip())

    print(f"✅ PLANNER: Created {len(tasks)} tasks")
    for t in tasks:
        print(f"   {t['id']}. {t['description']}")

    return {
        **state,
        "tasks": tasks,
        "current_task_index": 0
    }

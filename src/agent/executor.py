import os
from tavily import TavilyClient
from src.agent.state import AgentState

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

def executor_node(state: AgentState) -> AgentState:
    tasks = state["tasks"]
    index = state["current_task_index"]
    task = tasks[index]

    print(f"\n🔍 EXECUTOR: Working on task {task['id']}: {task['description']}")

    # search the web
    search_result = tavily.search(query=task["description"], max_results=3)
    
    # extract useful content
    findings = []
    for r in search_result["results"]:
        findings.append(f"- {r['title']}: {r['content'][:300]}")
    
    result_text = "\n".join(findings)
    print(f"✅ EXECUTOR: Found {len(findings)} results")

    # update the task
    tasks[index] = {
        **task,
        "status": "done",
        "result": result_text
    }

    return {
        **state,
        "tasks": tasks,
        "scratchpad": state["scratchpad"] + [f"Task {task['id']}: {result_text}"],
        "current_task_index": index + 1
    }

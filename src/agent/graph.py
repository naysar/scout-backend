from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, END
from src.agent.state import AgentState
from src.agent.planner import planner_node
from src.agent.executor import executor_node
from src.agent.critic import critic_node
from src.agent.reporter import reporter_node
from src.agent.memory import memory_node

def should_continue(state: AgentState) -> str:
    index = state["current_task_index"]
    total = len(state["tasks"])
    if index >= total:
        return "memory"
    else:
        return "executor"

builder = StateGraph(AgentState)
builder.add_node("planner", planner_node)
builder.add_node("executor", executor_node)
builder.add_node("critic", critic_node)
builder.add_node("memory", memory_node)
builder.add_node("reporter", reporter_node)

builder.set_entry_point("planner")
builder.add_edge("planner", "executor")
builder.add_edge("executor", "critic")
builder.add_conditional_edges("critic", should_continue, {
    "executor": "executor",
    "memory": "memory"
})
builder.add_edge("memory", "reporter")
builder.add_edge("reporter", END)

graph = builder.compile()
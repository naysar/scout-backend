from dotenv import load_dotenv
load_dotenv()

from src.agent.graph import graph
from src.agent.state import AgentState

goal = input("Enter your research goal: ")

initial_state: AgentState = {
    "goal": goal,
    "tasks": [],
    "current_task_index": 0,
    "scratchpad": [],
    "final_report": None
}

print("\n🚀 Starting agent...\n")
final_state = graph.invoke(initial_state)

print("\n\n📄 FINAL REPORT:")
print("="*50)
print(final_state["final_report"])
print("="*50)

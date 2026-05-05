from dotenv import load_dotenv
load_dotenv()

from src.agent.state import AgentState
from src.agent.planner import planner_node
from src.agent.executor import executor_node
from src.agent.critic import critic_node
from src.agent.reporter import reporter_node

initial_state: AgentState = {
    "goal": "Research the current state of electric vehicles in 2025",
    "tasks": [],
    "current_task_index": 0,
    "scratchpad": [],
    "final_report": None
}

state = planner_node(initial_state)

# run all tasks through executor + critic
for i in range(len(state["tasks"])):
    state = executor_node(state)
    state = critic_node(state)

state = reporter_node(state)

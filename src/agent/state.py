from typing import TypedDict, List, Optional

class Task(TypedDict):
    id: int
    description: str
    status: str
    result: Optional[str]

class AgentState(TypedDict):
    goal: str
    tasks: List[Task]
    current_task_index: int
    scratchpad: List[str]
    final_report: Optional[str]

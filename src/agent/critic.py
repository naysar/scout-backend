import os
import json
from langchain_groq import ChatGroq
from src.agent.state import AgentState

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)

MAX_RETRIES = 2

def critic_node(state: AgentState) -> AgentState:
    tasks = state["tasks"]
    index = state["current_task_index"] - 1
    task = tasks[index]
    
    attempt = task.get("attempts", 1)
    print(f"\n🔎 CRITIC: Evaluating task {task['id']} (attempt {attempt})...")

    prompt = f"""You are a strict research quality critic.

Original task: {task['description']}
Result obtained: {task['result']}

Score the result from 1-5:
- 5: Excellent, specific data, directly answers the task
- 4: Good, relevant info but missing some details
- 3: Acceptable, somewhat relevant
- 2: Poor, vague or barely relevant
- 1: Useless, completely off-topic

Respond ONLY with a JSON object:
{{"score": <1-5>, "reason": "<one sentence>", "verdict": "accept" or "retry"}}

If score >= 3, verdict must be "accept". If score < 3, verdict must be "retry"."""

    response = llm.invoke(prompt)
    content = response.content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]

    evaluation = json.loads(content.strip())
    score = evaluation["score"]
    verdict = evaluation["verdict"]
    reason = evaluation["reason"]

    print(f"   Score: {score}/5 | Verdict: {verdict}")
    print(f"   Reason: {reason}")

    if verdict == "retry" and attempt < MAX_RETRIES:
        print(f"⚠️  CRITIC: Retrying task {task['id']} (attempt {attempt + 1})...")
        tasks[index] = {
            **task,
            "status": "pending",
            "result": None,
            "attempts": attempt + 1
        }
        return {
            **state,
            "tasks": tasks,
            "current_task_index": index
        }

    tasks[index] = {**task, "status": "done"}
    return {**state, "tasks": tasks}
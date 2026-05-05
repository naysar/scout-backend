import os
import json
from langchain_groq import ChatGroq
from src.agent.state import AgentState

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)

def critic_node(state: AgentState) -> AgentState:
    tasks = state["tasks"]
    index = state["current_task_index"] - 1  # just executed task
    task = tasks[index]

    print(f"\n🔎 CRITIC: Evaluating task {task['id']}...")

    prompt = f"""You are a research quality critic.

Original task: {task['description']}
Result obtained: {task['result']}

Score the result from 1-5 based on:
- Relevance to the task
- Information quality
- Completeness

Respond ONLY with a JSON object, nothing else:
{{"score": <1-5>, "reason": "<one sentence>", "verdict": "accept" or "retry"}}

If score >= 3, verdict must be "accept". If score < 3, verdict must be "retry".
"""

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

    # if retry, mark task as pending again and go back
    if verdict == "retry":
        print(f"⚠️  CRITIC: Retrying task {task['id']}...")
        tasks[index] = {**task, "status": "pending", "result": None}
        return {
            **state,
            "tasks": tasks,
            "current_task_index": index  # go back to this task
        }

    tasks[index] = {**task, "status": "done"}
    return {**state, "tasks": tasks}

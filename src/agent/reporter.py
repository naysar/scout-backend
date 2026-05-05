import os
from langchain_groq import ChatGroq
from src.agent.state import AgentState

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)

def reporter_node(state: AgentState) -> AgentState:
    print("\n📝 REPORTER: Synthesizing final report...")

    completed_tasks = [t for t in state["tasks"] if t["status"] == "done"]
    
    findings = ""
    for task in completed_tasks:
        findings += f"\n### {task['description']}\n{task['result']}\n"

    prompt = f"""You are a research report writer.

Original goal: {state["goal"]}

Here are the research findings:
{findings}

Write a clean, structured markdown research report with:
- An executive summary (2-3 sentences)
- A section for each major finding
- A conclusion

Be concise and factual. Use only the information provided."""

    response = llm.invoke(prompt)
    report = response.content.strip()

    print("✅ REPORTER: Report complete!")
    print("\n" + "="*50)
    print(report)
    print("="*50)

    return {**state, "final_report": report}

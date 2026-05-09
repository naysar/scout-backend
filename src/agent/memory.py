import chromadb
import os
from src.agent.state import AgentState

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("research_memory")

def memory_node(state: AgentState) -> AgentState:
    print("\n🧠 MEMORY: Storing findings...")
    
    for task in state["tasks"]:
        if task["status"] == "done" and task["result"]:
            collection.add(
                documents=[task["result"]],
                metadatas=[{"goal": state["goal"], "task": task["description"]}],
                ids=[f"{state['goal'][:30]}_{task['id']}".replace(" ", "_")]
            )
    
    print(f"✅ MEMORY: Stored {len(state['tasks'])} findings")
    return state

def recall_memory(goal: str) -> str:
    try:
        results = collection.query(query_texts=[goal], n_results=3)
        if results["documents"][0]:
            print(f"\n📚 MEMORY: Found {len(results['documents'][0])} related past findings")
            return "\n".join(results["documents"][0])
    except:
        pass
    return ""

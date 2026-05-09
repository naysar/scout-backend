import chromadb
import os
from src.agent.state import AgentState

def get_collection():
    api_key = os.getenv("CHROMA_API_KEY")
    tenant = os.getenv("CHROMA_TENANT")
    database = os.getenv("CHROMA_DATABASE")
    
    if api_key and tenant and database:
        client = chromadb.HttpClient(
            host="api.trychroma.com",
            ssl=True,
            headers={"x-chroma-token": api_key},
            tenant=tenant,
            database=database,
        )
    else:
        client = chromadb.PersistentClient(path="./chroma_db")
    
    return client.get_or_create_collection("research_memory")

def memory_node(state: AgentState) -> AgentState:
    print("\n🧠 MEMORY: Storing findings...")
    try:
        collection = get_collection()
        for task in state["tasks"]:
            if task["status"] == "done" and task["result"]:
                collection.add(
                    documents=[task["result"]],
                    metadatas=[{"goal": state["goal"], "task": task["description"]}],
                    ids=[f"{state['goal'][:30]}_{task['id']}".replace(" ", "_")]
                )
        print(f"✅ MEMORY: Stored {len(state['tasks'])} findings")
    except Exception as e:
        print(f"⚠️ MEMORY: Could not store findings: {e}")
    return state

def recall_memory(goal: str) -> str:
    try:
        collection = get_collection()
        results = collection.query(query_texts=[goal], n_results=3)
        if results["documents"][0]:
            print(f"\n📚 MEMORY: Found {len(results['documents'][0])} related past findings")
            return "\n".join(results["documents"][0])
    except Exception as e:
        print(f"⚠️ MEMORY: Could not recall findings: {e}")
    return ""

from dotenv import load_dotenv
load_dotenv()

import pytest
from unittest.mock import patch, MagicMock
from src.agent.state import AgentState

def make_state(goal="test goal", tasks=[], index=0):
    return AgentState(
        goal=goal,
        tasks=tasks,
        current_task_index=index,
        scratchpad=[],
        final_report=None
    )

def test_state_structure():
    state = make_state(goal="test", tasks=[], index=0)
    assert state["goal"] == "test"
    assert state["tasks"] == []
    assert state["current_task_index"] == 0
    assert state["scratchpad"] == []
    assert state["final_report"] is None

def test_planner_creates_tasks():
    mock_response = MagicMock()
    mock_response.content = '[{"id": 1, "description": "search X", "status": "pending", "result": null}]'
    with patch("langchain_groq.ChatGroq.invoke", return_value=mock_response):
        with patch("src.agent.memory.recall_memory", return_value=""):
            from src.agent.planner import planner_node
            state = make_state(goal="research AI")
            result = planner_node(state)
            assert len(result["tasks"]) == 1
            assert result["tasks"][0]["status"] == "pending"

def test_critic_accepts_high_score():
    mock_response = MagicMock()
    mock_response.content = '{"score": 4, "reason": "good result", "verdict": "accept"}'
    with patch("langchain_groq.ChatGroq.invoke", return_value=mock_response):
        from src.agent.critic import critic_node
        tasks = [{"id": 1, "description": "search X", "status": "done", "result": "some result", "attempts": 1}]
        state = make_state(tasks=tasks, index=1)
        result = critic_node(state)
        assert result["tasks"][0]["status"] == "done"

def test_critic_retries_low_score():
    mock_response = MagicMock()
    mock_response.content = '{"score": 2, "reason": "bad result", "verdict": "retry"}'
    with patch("langchain_groq.ChatGroq.invoke", return_value=mock_response):
        from src.agent.critic import critic_node
        tasks = [{"id": 1, "description": "search X", "status": "done", "result": "bad result", "attempts": 1}]
        state = make_state(tasks=tasks, index=1)
        result = critic_node(state)
        assert result["tasks"][0]["status"] == "pending"
        assert result["current_task_index"] == 0

def test_reporter_generates_report():
    mock_response = MagicMock()
    mock_response.content = "## Report\nThis is the report."
    with patch("langchain_groq.ChatGroq.invoke", return_value=mock_response):
        from src.agent.reporter import reporter_node
        tasks = [{"id": 1, "description": "search X", "status": "done", "result": "some result"}]
        state = make_state(goal="research AI", tasks=tasks)
        result = reporter_node(state)
        assert result["final_report"] is not None
        assert "Report" in result["final_report"]
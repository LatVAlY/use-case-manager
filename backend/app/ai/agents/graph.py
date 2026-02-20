from typing import AsyncGenerator
from langgraph.graph import StateGraph, END
from langgraph.graph.message import MessagesState
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage

from app.clients import get_chat_llm
from app.ai.agents.prompts import AGENT_SYSTEM
from app.ai.agents.tools import create_agent_tools


def get_llm():
    return get_chat_llm(temperature=0.3)


def create_chat_agent(context: dict):

    llm = get_llm()
    tools = create_agent_tools(context)
    llm_with_tools = llm.bind_tools(tools)
    tool_node = ToolNode(tools)

    def agent_node(state: MessagesState) -> dict:
        messages = state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: MessagesState) -> str:
        messages = state["messages"]
        if not messages:
            return "end"
        last = messages[-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return "end"

    graph = StateGraph(MessagesState)

    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
    graph.add_edge("tools", "agent")

    return graph.compile()


def _to_messages(history: list) -> list[BaseMessage]:

    out = []
    for h in history:
        role, content = h.get("role", ""), h.get("content", "")
        if role == "user":
            out.append(HumanMessage(content=content))
        elif role == "assistant":
            out.append(AIMessage(content=content))
    return out


async def stream_agent_response(
    graph,
    user_message: str,
    history: list,
    on_event=None,
) -> AsyncGenerator[str, None]:

    messages = _to_messages(history) + [HumanMessage(content=user_message)]
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=AGENT_SYSTEM)] + messages

    full_content = ""
    async for event in graph.astream(
        {"messages": messages},
        stream_mode=["messages", "updates"],
    ):
        # Mixed mode yields (stream_id, payload)
        if isinstance(event, tuple) and len(event) == 2:
            stream_id, payload = event
            if stream_id == "messages":
                # payload is (chunk, metadata)
                if isinstance(payload, tuple) and len(payload) == 2:
                    chunk, metadata = payload
                    node_name = metadata.get("langgraph_node", "")
                    if node_name == "agent" and hasattr(chunk, "content") and chunk.content:
                        full_content += chunk.content
                        yield chunk.content
            elif stream_id == "updates" and isinstance(payload, dict):
                for msg in payload.get("agent", {}).get("messages", []):
                    if hasattr(msg, "tool_calls") and msg.tool_calls and on_event:
                        for tc in msg.tool_calls:
                            name = getattr(tc, "name", "") if hasattr(tc, "name") else (tc.get("name", "") if isinstance(tc, dict) else "")
                            args = getattr(tc, "args", {}) if hasattr(tc, "args") else (tc.get("args", {}) if isinstance(tc, dict) else {})
                            evt = {"type": "tool_start", "name": str(name), "args": args if isinstance(args, dict) else {}}
                            if hasattr(on_event, "__call__"):
                                try:
                                    r = on_event(evt)
                                    if hasattr(r, "__await__"):
                                        await r
                                except Exception:
                                    pass
                for msg in payload.get("tools", {}).get("messages", []):
                    if on_event and hasattr(msg, "content"):
                        evt = {"type": "tool_end", "content": str(msg.content)[:500]}
                        try:
                            r = on_event(evt)
                            if hasattr(r, "__await__"):
                                await r
                        except Exception:
                            pass

    if full_content and on_event:
        try:
            r = on_event({"type": "agent_done", "content": full_content})
            if hasattr(r, "__await__"):
                await r
        except Exception:
            pass

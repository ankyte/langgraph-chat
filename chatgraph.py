from langchain_core.messages import SystemMessage, ToolMessage
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import add_messages, StateGraph, END # add_message: to update graph state
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Annotated # to define state of graph
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv
load_dotenv()

model = ChatOpenAI(model="gpt-4.1-nano")
search_tool = TavilySearchResults(max_results=1)
tools = [search_tool]
memory = MemorySaver()
llm_with_tools = model.bind_tools(tools=tools)

# Graph State

class State(TypedDict):
    messages: Annotated[list, add_messages]

# Defining Nodes

async def model(state: State):
    messages = state["messages"]
    if isinstance(messages[-1], SystemMessage):
        return state
    result = await llm_with_tools.ainvoke(state["messages"])
    return {
        "messages": [result], 
    }

async def tool_node(state):
    """Custom tool node that handles tool calls from the LLM."""
    
    tool_calls = state["messages"][-1].tool_calls # Get the tool calls from the last message
    tool_messages = [] # Initialize list to store tool messages
    
    for tool_call in tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_id = tool_call["id"]
        
        # Handle the search tool
        if tool_name == "tavily_search_results_json":
            search_results = await search_tool.ainvoke(tool_args)
            
            tool_message = ToolMessage(
                content=str(search_results),
                tool_call_id=tool_id,
                name=tool_name
            )
            
            tool_messages.append(tool_message)
    
    return {"messages": tool_messages}

# Router

async def tools_router(state: State):
    last_message = state["messages"][-1]

    if(hasattr(last_message, "tool_calls") and len(last_message.tool_calls) > 0):
        return "tool_node"
    return END

# Building graph
class Graph:
    def __init__(self):
        graph_builder = StateGraph(State)

        # adding nodes
        graph_builder.add_node("model", model)
        graph_builder.add_node("tool_node", tool_node)

        graph_builder.set_entry_point("model")

        # adding edges
        graph_builder.add_conditional_edges("model", tools_router)
        graph_builder.add_edge("tool_node", "model")

        self.graph = graph_builder.compile(checkpointer=memory)

    
    def get_graph(self):
        return self.graph
    
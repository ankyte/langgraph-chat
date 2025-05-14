import streamlit as st
import uuid
import asyncio
from typing import Iterator, Dict, Any
from chatgraph import Graph
from langchain_core.messages import HumanMessage, AIMessageChunk, ToolMessage
from util import state_manager

graph = Graph().get()

APP_NAME = "FolioPilot"

# Set page configuration
st.set_page_config(
    page_title=APP_NAME,
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = {}  # Store all chat sessions

if "current_chat_id" not in st.session_state:
    new_chat_id = str(uuid.uuid4())
    st.session_state.current_chat_id = new_chat_id
    st.session_state.chat_sessions[new_chat_id] = {
        "messages": [],
        "checkpoint_id": uuid.uuid4(),
        "title": "New Chat"
    }

# Function to create a new chat
def create_new_chat():
    new_chat_id = str(uuid.uuid4())
    st.session_state.current_chat_id = new_chat_id
    st.session_state.chat_sessions[new_chat_id] = {
        "messages": [],
        "checkpoint_id": None,
        "title": "New Chat"
    }
    st.rerun()

# Function to switch to existing chat
def switch_to_chat(chat_id):
    st.session_state.current_chat_id = chat_id
    st.rerun()

# Function to get chat title from the first user message
def generate_chat_title(message):
    if len(message) > 30:
        return message[:30] + "..."
    return message

# Modified function to handle async streaming
async def get_streaming_response(prompt, checkpoint_id):
    config = {
        "configurable": {
            "thread_id": checkpoint_id
        }
    }
    
    async_generator = graph.astream_events({
        "messages": [HumanMessage(content=prompt)],
    }, config=config, version="v2")
    
    events = []
    async for event in async_generator:
        events.append(event)

    return events

def serialise_ai_message_chunk(chunk):
    if(isinstance(chunk, AIMessageChunk)):
        return chunk.content
    else:
        raise TypeError(
            f"Object of type {type(chunk).__name__} is not correctly formatted for serialisation"
        )

# This function runs the async function and returns the results
def stream_response(prompt, checkpoint_id):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(get_streaming_response(prompt, checkpoint_id))
    finally:
        loop.close()

# Sidebar
with st.sidebar:
    st.title(APP_NAME)
    
    # New chat button
    if st.button("➕", use_container_width=True):
        create_new_chat()
    
    st.divider()
    st.subheader("Previous chats")
    
    # Display chat history
    for chat_id, chat_data in reversed(list(st.session_state.chat_sessions.items())):
        if chat_id == st.session_state.current_chat_id:
            button_type = "primary"
        else:
            button_type = "secondary"
        
        # Create a button for each chat session
        if st.button(chat_data["title"], key=f"chat_{chat_id}", 
                    use_container_width=True, type=button_type):
            switch_to_chat(chat_id)

# Main chat area
current_chat = st.session_state.chat_sessions[st.session_state.current_chat_id]

# Display chat title
st.header(current_chat["title"])

# Convert stored messages to Streamlit chat message format
for message in current_chat["messages"]:
    role = message["role"]
    content = message["content"]
    
    with st.chat_message(role):
        st.write(content)

# Process user input
if prompt := st.chat_input("Type your message here..."):
    # Add user message to chat
    current_chat["messages"].append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
    
    # If this is the first message, update the chat title
    if len(current_chat["messages"]) == 1:
        current_chat["title"] = generate_chat_title(prompt)
    
    # Get the checkpoint_id
    checkpoint_id = current_chat["checkpoint_id"]
    
    try:
        # Create assistant message container for streaming
        with st.chat_message("assistant"):
            # Initialize variables for response tracking
            full_response = ""
            search_status = None
            
            # Process the streaming response
            response_container = st.empty()
            
            # Get and process all events
            events = stream_response(prompt, checkpoint_id)
            
            for event in events:
                event_type = event["event"]
                if event_type == "on_chat_model_stream":
                    # Update the full response
                    chunk_content = serialise_ai_message_chunk(event["data"]["chunk"])
                    full_response += chunk_content
                    # Update the displayed response
                    response_container.write(full_response)
                    
                elif event_type == "on_chat_model_end":
                    # Check if there are tool calls for search
                    tool_calls = event["data"]["output"].tool_calls if hasattr(event["data"]["output"], "tool_calls") else []
                    tavily_search_calls = [call for call in tool_calls if call["name"] == "tavily_search_results_json"]
                    data_tool_calls = [call for call in tool_calls if call["name"] == "data_fetch_tool"]

                    if tavily_search_calls:
                        search_query = tavily_search_calls[0]["args"].get("query", "")
                        search_status = st.status(f"Searching for: {search_query}", expanded=True)
                        search_status.update(label=f"Searching for: {search_query}", state="running")
                    if data_tool_calls:
                        data_id = str(repr(data_tool_calls[0]["args"]))
                        st.data_editor(state_manager.get(data_id), use_container_width=True)
                        
                        # Signal that a search is starting
                        # data_tool_query = data_tool_calls[0]["args"].get("query", "")
                        # Create a status indicator for search
                        # search_status = st.status(f"Searching for: {data_tool_query}", expanded=True)
                        # search_status.update(label=f"Searching for: {search_query}", state="running")
                    
                elif event_type == "on_tool_end" and search_status:
                    output = event["data"]["output"]
                    if isinstance(output, list):
                        # Extract URLs from list of search results
                        urls = []
                        for item in output:
                            if isinstance(item, dict) and "url" in item:
                                urls.append(item["url"])
                        
                        search_status.update(label="Search completed", state="complete")
                        search_status.write(f"Search results:")
                        search_status(urls)
                                
            # Add assistant's complete response to chat history
            current_chat["messages"].append({"role": "assistant", "content": full_response})
            
    except Exception as e:
        st.error(f"Error: {str(e)}")
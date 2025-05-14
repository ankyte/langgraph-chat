import streamlit as st
import uuid
from chatgraph import Graph
from typing import Iterator, Dict, List, Tuple, Any
import uuid
from langchain_core.messages import HumanMessage

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
        "checkpoint_id": None,
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

def stream_response(response) -> Iterator[Dict[str, Any]]:
    full_response = ""
    checkpoint_id = None
        
    for line in response.iter_lines():
        if line:
            line_text = line.decode('utf-8')
            if line_text.startswith("data: "):
                data_str = line_text[6:]  # Remove "data: " prefix
                event_type = data.get("type", "")
                
                # Handle different event types
                if event_type == "checkpoint" and "checkpoint_id" in data:
                    checkpoint_id = data["checkpoint_id"]
                    
                elif event_type == "content" and "content" in data:
                    content = data["content"]
                    full_response += content
                    yield {"type": "content", "content": content}
                    
                elif event_type == "search_start" and "query" in data:
                    yield {"type": "search_start", "query": data["query"]}
                    
                elif event_type == "search_results" and "urls" in data:
                    yield {"type": "search_results", "urls": data["urls"]}
                    
                elif event_type == "end":
                    yield {"type": "end"}
                    break
    
    # Update the checkpoint_id in session state
    current_chat = st.session_state.chat_sessions[st.session_state.current_chat_id]
    if checkpoint_id:
        current_chat["checkpoint_id"] = checkpoint_id
    
    # Return the complete response as the final yield
    yield {"type": "complete", "content": full_response}

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

async def generate_chat_responses(prompt:str, checkpoint_id: str):
    is_new_conversation = checkpoint_id is None
    if is_new_conversation:
        # Generate new checkpoint ID for first message in conversation
        new_checkpoint_id = str(uuid.uuid4())

        config = {
            "configurable": {
                "thread_id": new_checkpoint_id
            }
        }
        
        # Initialize with first message
        events = graph.astream_events(
            {"messages": [HumanMessage(content=prompt)]},
            version="v2",
            config=config
        )
        
        async for event in events:
            event_type = event["event"]
            if event_type == "on_chat_model_stream":
                yield event["data"]["chunk"]
                
            elif event_type == "on_chat_model_end":
                # Check if there are tool calls for search
                tool_calls = event["data"]["output"].tool_calls if hasattr(event["data"]["output"], "tool_calls") else []
                search_calls = [call for call in tool_calls if call["name"] == "tavily_search_results_json"]
                
                if search_calls:
                    search_query = search_calls[0]["args"].get("query", "")
                    yield search_query
                    
            elif event_type == "on_tool_end" and event["name"] == "tavily_search_results_json":
                output = event["data"]["output"] # Search completed - send results or error
                
                if isinstance(output, list):
                    urls = []
                    for item in output:
                        if isinstance(item, dict) and "url" in item:
                            urls.append(item["url"])
                    
                    yield urls
    

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
    
    # Prepare the message and checkpoint_id
    checkpoint_id = current_chat["checkpoint_id"]
    
    try:
        # Use async for to iterate over the async generator
        response = generate_chat_responses(prompt, checkpoint_id)

        # Create assistant message container for streaming
        with st.chat_message("assistant"):
            # Initialize variables for response tracking
            full_response = ""
            search_status = None
            
            # Process the streaming response
            response_container = st.empty()
            
            # Stream generator that yields text for writing
            def content_generator():
                for event in stream_api_response(url):
                    if event["type"] == "content":
                        yield event["content"]
            
            # Stream full response processing with search handling
            for event in stream_api_response(url):
                if event["type"] == "content":
                    # Update the full response
                    full_response += event["content"]
                    # Update the displayed response
                    response_container.write(full_response)
                    
                elif event["type"] == "search_start":
                    # Create a status indicator for search
                    search_status = st.status(f"Searching for: {event['query']}", expanded=True)
                    search_status.update(label=f"Searching for: {event['query']}", state="running")
                    
                elif event["type"] == "search_results" and search_status:
                    # Display search results in the status
                    urls_html = "<ul>"
                    for url in event["urls"]:
                        urls_html += f"<li><a href='{url}' target='_blank'>{url}</a></li>"
                    urls_html += "</ul>"
                    
                    search_status.update(label="Search completed", state="complete")
                    search_status.markdown(f"Search results:\n{urls_html}", unsafe_allow_html=True)
                    
                elif event["type"] == "complete":
                    # This event contains the full response
                    full_response = event["content"]
            
            # Add assistant's complete response to chat history
            current_chat["messages"].append({"role": "assistant", "content": full_response})
            
    except Exception as e:
        st.error(f"Error: {str(e)}")
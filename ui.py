import streamlit as st
import requests
import uuid
import json
import time
from typing import Iterator, Dict, List, Tuple, Any

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

# API endpoint
BASE_URL = "http://127.0.0.1:8000"

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

# Function to stream API response
def stream_api_response(url) -> Iterator[Dict[str, Any]]:
    """
    Stream API response and handle different event types.
    Returns a generator that yields content chunks and event metadata.
    """
    full_response = ""
    checkpoint_id = None
    
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                if line_text.startswith("data: "):
                    data_str = line_text[6:]  # Remove "data: " prefix
                    try:
                        data = json.loads(data_str)
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
                            
                    except json.JSONDecodeError:
                        pass
    
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
    encoded_message = prompt.replace(" ", "%20")
    
    try:
        # Construct the API URL with parameters
        if checkpoint_id:
            url = f"{BASE_URL}/chat_stream/{encoded_message}?checkpoint_id={checkpoint_id}"
        else:
            url = f"{BASE_URL}/chat_stream/{encoded_message}"
        
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
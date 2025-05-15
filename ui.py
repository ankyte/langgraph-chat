import streamlit as st
import datetime
import uuid
import asyncio
from chatgraph import Graph
from langchain_core.messages import HumanMessage, AIMessageChunk, SystemMessage
from util import state_manager
from tools.chart import generate_chart
from st_ui.dashboard import dashboard_ui
from tools.suggestions import suggest_followups

graph = Graph().get()
APP_NAME = "FolioPilot"

st.set_page_config(
    page_title=APP_NAME,
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = {}

if "current_chat_id" not in st.session_state:
    new_chat_id = str(uuid.uuid4())
    st.session_state.current_chat_id = new_chat_id
    st.session_state.chat_sessions[new_chat_id] = {
        "messages": [],
        "checkpoint_id": uuid.uuid4(),
        "title": "New Chat"
    }

def create_new_chat():
    new_chat_id = str(uuid.uuid4())
    st.session_state.current_chat_id = new_chat_id
    st.session_state.chat_sessions[new_chat_id] = {
        "messages": [],
        "checkpoint_id": None,
        "title": "New Chat"
    }
    st.session_state.input_mode = "initial"
    st.rerun()

def switch_to_chat(chat_id):
    st.session_state.current_chat_id = chat_id
    st.rerun()

def generate_chat_title(message):
    return message[:30] + "..." if len(message) > 30 else message

async def get_streaming_response(prompt, checkpoint_id):
    if len(current_chat["messages"]) <= 1:
        initial_state = {
            "messages": [SystemMessage(content=f"You are a finance bot. Today is {str(datetime.datetime.now())}")]
        }
        config = {"configurable": {"thread_id": checkpoint_id}}
        response = await graph.ainvoke(initial_state, config=config)

    config = {"configurable": {"thread_id": checkpoint_id}}
    async_generator = graph.astream_events({
        "messages": [HumanMessage(content=prompt)],
    }, config=config, version="v2")

    events = []
    async for event in async_generator:
        events.append(event)
    return events

def serialise_ai_message_chunk(chunk):
    if isinstance(chunk, AIMessageChunk):
        return chunk.content
    else:
        raise TypeError(f"Object of type {type(chunk).__name__} is not AIMessageChunk")

def stream_response(prompt, checkpoint_id):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(get_streaming_response(prompt, checkpoint_id))
    finally:
        loop.close()

def run_llm(prompt):
    current_chat = st.session_state.chat_sessions[st.session_state.current_chat_id]
    current_chat["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    if len(current_chat["messages"]) == 1:
        current_chat["title"] = generate_chat_title(prompt)

    checkpoint_id = current_chat["checkpoint_id"]
    try:
        with st.chat_message("assistant"):
            full_response = ""
            search_status = None
            response_container = st.empty()
            events = stream_response(prompt, checkpoint_id)
            dfs = []

            for event in events:
                event_type = event["event"]

                if event_type == "on_chat_model_stream":
                    chunk_content = serialise_ai_message_chunk(event["data"]["chunk"])
                    full_response += chunk_content
                    response_container.write(full_response)

                elif event_type == "on_chat_model_end":
                    tool_calls = event["data"]["output"].tool_calls if hasattr(event["data"]["output"], "tool_calls") else []
                    for call in tool_calls:
                        name = call["name"]
                        args = call["args"]
                        if name == "data_fetch_tool":
                            df = state_manager.get(str(repr(args)))
                            dfs.append(df)
                            st.data_editor(df, use_container_width=True, key=uuid.uuid4())
                        elif name == "chart_tool":
                            df = state_manager.get(str(repr({
                                "port": args["port"],
                                "report_date": args["report_date"]
                            })))
                            generate_chart(df, args['chart_type'])
                        elif name == "dashboard_tool":
                            st.session_state["dashboard_portfolio"] = args["port"]
                            st.session_state["view_dashboard"] = st.button(f"Dashboard {args['port']}")
                        elif name == "report_tool":
                            with open("report.pdf", "rb") as pdf_file:
                                PDFbyte = pdf_file.read()

                            st.download_button(label=f"Download Report for {args['port']}",
                                data=PDFbyte,
                                file_name=f"{args['port']}_report.pdf",
                                mime='application/octet-stream'
                            )

                        elif name == "tavily_search_results_json":
                            search_query = args.get("query", "")
                            search_status = st.status(f"Searching for: {search_query}", expanded=True)
                            search_status.update(label=f"Searching for: {search_query}", state="running")

                elif event_type == "on_tool_end" and search_status:
                    output = event["data"]["output"]
                    if isinstance(output, list):
                        search_status.update(label="Search completed", state="complete")

            current_chat["messages"].append({
                "role": "assistant", "content": full_response, "dataframes": dfs
            })

    except Exception as e:
        st.error("Something went wrong: " + str(e))

# Sidebar
with st.sidebar:
    st.title(APP_NAME)
    if st.button("➕", use_container_width=True):
        create_new_chat()
    st.divider()
    st.subheader("Previous chats")
    for chat_id, chat_data in reversed(list(st.session_state.chat_sessions.items())):
        if st.button(chat_data["title"], key=f"chat_{chat_id}", use_container_width=True):
            switch_to_chat(chat_id)

# Chat UI
current_chat = st.session_state.chat_sessions[st.session_state.current_chat_id]
st.header(current_chat["title"])

if "suggestions" not in st.session_state:
    st.session_state.suggestions = []
if "input_mode" not in st.session_state:
    st.session_state.input_mode = "initial"

if len(current_chat["messages"]) <= 1:
    st.write("Ask anything about your portfolio")

    def fetch_dynamic_starter_prompts():
        return [
            "Show me the performance data of SEL-AGG.",
            "What are the risk metrics of this fund?",
            "Can you explain the fund attribution?",
            "Compare returns of two funds over 5 years.",
            "How has this fund performed vs the benchmark?"
        ]

    if st.session_state.input_mode == "initial":
        st.write("💡 Try one of these to get started:")
        prompts = fetch_dynamic_starter_prompts()
        for i, prompt in enumerate(prompts):
            if st.button(prompt, key=f"starter_prompt_{i}"):
                run_llm(prompt)
                st.session_state.suggestions = suggest_followups(prompt)
                st.session_state.input_mode = "chat"
                st.rerun()

for message in current_chat["messages"]:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        for df in message.get("dataframes", []):
            st.data_editor(df, key=uuid.uuid4())

# Manual chat input
if prompt := st.chat_input("Type your message here..."):
    run_llm(prompt)
    st.session_state.suggestions = suggest_followups(prompt)

# Show follow-up suggestions
if st.session_state.get("suggestions"):
    st.write("💬 Suggested follow-ups:")
    for i, q in enumerate(st.session_state.suggestions):
        if st.button(q, key=f"followup_{i}"):
            run_llm(q)
            st.session_state.suggestions = suggest_followups(q)
            st.rerun()

# Optional dashboard UI
if "view_dashboard" in st.session_state and st.session_state["view_dashboard"]:
    dashboard_ui()

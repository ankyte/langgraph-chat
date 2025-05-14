import streamlit as st
from predictive_chat import suggest_followups

# Session state initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "suggestions" not in st.session_state:
    st.session_state.suggestions = []
if "input_mode" not in st.session_state:
    st.session_state.input_mode = "initial"
if "followup_click_count" not in st.session_state:
    st.session_state.followup_click_count = 0

st.title("🧠 Smart Financial Chat Assistant")
st.write("Ask a financial question and get intelligent follow-up suggestions.")

# Function to fetch dynamic starter prompts
def fetch_dynamic_starter_prompts():
    return [
        "Show me the performance data of SEL-AGG.",
        "What are the risk metrics of this fund?",
        "Can you explain the fund attribution?",
        "Compare returns of two funds over 5 years.",
        "How has this fund performed vs the benchmark?"
    ]

# Initial mode — show starter prompts and custom question input
if st.session_state.input_mode == "initial":
    st.write("💡 Try one of these to get started:")
    starter_prompts = fetch_dynamic_starter_prompts()
    cols = st.columns(2)
    for i, prompt in enumerate(starter_prompts):
        if cols[i % 2].button(prompt):
            st.session_state.messages.append(("user", prompt))
            st.session_state.suggestions = suggest_followups(prompt)
            st.session_state.input_mode = "chat"
            st.rerun()

    user_input = st.text_input("Or ask your own question:", key="initial_input")
    if user_input:
        st.session_state.messages.append(("user", user_input))
        st.session_state.suggestions = suggest_followups(user_input)
        st.session_state.input_mode = "chat"
        st.rerun()

# Show the conversation
for role, msg in st.session_state.messages:
    st.chat_message(role).markdown(msg)

# Show follow-up suggestions (limit to 2 clicks)
if st.session_state.suggestions and st.session_state.followup_click_count < 2:
    st.write("### Suggested follow-up questions:")
    cols = st.columns(len(st.session_state.suggestions))
    for i, suggestion in enumerate(st.session_state.suggestions):
        if cols[i].button(suggestion):
            st.session_state.messages.append(("user", suggestion))
            st.session_state.followup_click_count += 1
            if st.session_state.followup_click_count < 2:
                st.session_state.suggestions = suggest_followups(suggestion)
            else:
                st.session_state.suggestions = []
            st.rerun()

# Chat input is always shown in chat mode
if st.session_state.input_mode == "chat":
    user_free_input = st.chat_input("Enter your message:")
    if user_free_input:
        st.session_state.messages.append(("user", user_free_input))
        if st.session_state.followup_click_count < 2:
            st.session_state.suggestions = suggest_followups(user_free_input)
        else:
            st.session_state.suggestions = []
        st.rerun()
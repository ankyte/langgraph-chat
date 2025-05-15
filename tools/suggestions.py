import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

def suggest_followups(user_query):
    """
    Use Together API-compatible GPT model to suggest follow-up questions for a financial chatbot.
    """
    prompt = f"""
    The user asked: "{user_query}"

    Based on this, suggest 3 intelligent follow-up questions related to finance data or user query,
    fund performance, attribution, or risk.

    Only return the questions in a bullet list.
    """
    llm = ChatOpenAI(
        model="gpt-4.1-nano",
        temperature=0.7,
        max_tokens=100
    )
    response = llm.invoke(prompt)
    # Process the response and filter out unwanted lines like "Here are three intelligent follow-up questions"
    raw_lines = response.content.strip().split("\n")

    # Only return lines that appear to be actual questions, removing introductory text
    follow_up_questions = [
        line.lstrip("•-1234567890. ").strip()  # Removes bullet points, numbers, etc.
        for line in raw_lines
        if "?" in line and len(line.strip()) > 5
    ]
    
    return follow_up_questions


def suggestion_ui_element(prompts, col_length=2, run_llm=None):
    cols = st.columns(col_length)
    for i, prompt in enumerate(prompts):
        if cols[i % col_length].button(prompt):
            if run_llm:
                run_llm(prompt)
            else:
                st.session_state['suggested_prompt'] = prompt
                st.session_state.input_mode = "chat"
                st.rerun()
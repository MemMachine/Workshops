#!/usr/bin/env python3
"""
MemMachine Workshop Chatbot - WITHOUT Memory
A simple stateless chatbot using AWS Bedrock — demonstrates limitations without memory.
"""

import logging

import streamlit as st

from utils import (
    AWS_REGION,
    MODEL_ID,
    call_bedrock,
    clean_response,
    load_css,
    test_bedrock_connection,
    typewriter_effect,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config MUST be the first Streamlit command
st.set_page_config(
    page_title="Chatbot WITHOUT Memory",
    page_icon="⚠️",
    layout="wide",
)


# ------------------------------------------------------------------
# Session state
# ------------------------------------------------------------------

def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "model_id" not in st.session_state:
        st.session_state.model_id = MODEL_ID


# ------------------------------------------------------------------
# Chat logic
# ------------------------------------------------------------------

def chat_without_memory(user_message: str) -> str:
    """Simple stateless chat — no memory context."""
    prompt = f"""You are a helpful AI assistant.

USER MESSAGE: {user_message}

Instructions:
- Respond helpfully and conversationally
- Do NOT include any reasoning tags, thinking blocks, or meta-commentary
- Provide your response directly without any <reasoning> or </reasoning> tags
- Just give a natural, conversational response"""

    response = call_bedrock(prompt)
    return clean_response(response)


# ------------------------------------------------------------------
# UI
# ------------------------------------------------------------------

def render_header():
    st.markdown(
        """
        <div class="header-wrapper">
            <h1>⚠️ Chatbot WITHOUT Memory</h1>
            <p class="header-subtitle">This chatbot has NO memory — it forgets everything between messages!</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_memory_status():
    st.markdown(
        """
        <div class="memory-status-indicator">
            <span class="memory-status-text">
                ⚪ <strong>No Memory Mode</strong> — This chatbot forgets everything!
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():
    load_css()
    initialize_session_state()
    render_header()

    # Sidebar
    with st.sidebar:
        st.markdown("### Configuration")
        st.info(f"**Model:** {st.session_state.model_id}")
        st.info(f"**Region:** {AWS_REGION}")

        st.divider()

        st.markdown("### Connection Status")
        if st.button("Test Connection"):
            success, message = test_bedrock_connection()
            (st.success if success else st.error)(f"{'✅' if success else '❌'} {message}")

        st.divider()

        st.markdown("### Try This")
        st.markdown("""
        1. Say: **"My name is Alice"**
        2. Then ask: **"What's my name?"**
        3. Notice: It won't remember!
        """)

        st.divider()

        if st.button("Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    # Memory status
    render_memory_status()

    # Chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Type your message…"):
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Generating response..."):
                response = chat_without_memory(prompt)

            st.session_state.messages.append({"role": "assistant", "content": response})
            st.write_stream(typewriter_effect(response))


if __name__ == "__main__":
    main()

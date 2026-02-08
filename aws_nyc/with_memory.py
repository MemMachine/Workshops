#!/usr/bin/env python3
"""
MemMachine Workshop Chatbot - WITH Memory
A chatbot with MemMachine memory integration — demonstrates persistent memory capabilities.
"""

import logging
import os
import time
from datetime import datetime, timezone

import requests
import streamlit as st
from dotenv import load_dotenv

from utils import (
    AVAILABLE_MODELS,
    AWS_REGION,
    MODEL_ID,
    call_bedrock,
    clean_response,
    load_css,
    test_bedrock_connection,
    typewriter_effect,
)

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config MUST be the first Streamlit command
st.set_page_config(
    page_title="Chatbot WITH Memory",
    page_icon="✨",
    layout="wide",
)

# ------------------------------------------------------------------
# MemMachine configuration
# ------------------------------------------------------------------

MEMORY_SERVER_URL = os.getenv("MEMORY_SERVER_URL", "")
ORG_ID = os.getenv("ORG_ID", "")
PROJECT_ID = os.getenv("PROJECT_ID", "")
USER_ID = os.getenv("USER_ID", "")

_MISSING = [
    name for name, val in [
        ("MEMORY_SERVER_URL", MEMORY_SERVER_URL),
        ("ORG_ID", ORG_ID),
        ("PROJECT_ID", PROJECT_ID),
        ("USER_ID", USER_ID),
    ]
    if not val
]
if _MISSING:
    st.error(
        f"Missing required environment variables: {', '.join(_MISSING)}. "
        "Please set them in your .env file (see .env.example)."
    )
    st.stop()

MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


# ------------------------------------------------------------------
# Memory helpers
# ------------------------------------------------------------------

def _retry_request(request_fn, description: str):
    """Execute *request_fn* with retry + exponential back-off.

    Returns the Response on success, or None on failure.
    """
    for attempt in range(MAX_RETRIES):
        try:
            resp = request_fn()
            resp.raise_for_status()
            return resp
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 503 and attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
            logger.warning("%s failed (HTTP %s): %s", description, e.response.status_code, e)
            st.warning(f"⚠ {description} failed: {e}")
            return None
        except requests.exceptions.Timeout:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
            logger.warning("%s timed out after %d retries", description, MAX_RETRIES)
            st.warning(f"⚠ {description} timed out. The server may be slow.")
            return None
        except Exception as e:
            logger.exception("%s failed", description)
            st.error(f"⚠ {description} failed: {e}")
            return None
    return None


def add_memory(message: str, role: str = "user") -> bool:
    """Add a message to MemMachine memory."""
    resp = _retry_request(
        lambda: requests.post(
            f"{MEMORY_SERVER_URL}/api/v2/memories",
            json={
                "org_id": ORG_ID,
                "project_id": PROJECT_ID,
                "messages": [
                    {
                        "content": message,
                        "producer": USER_ID,
                        "produced_for": "agent",
                        "role": role,
                        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                        "metadata": {"user_id": USER_ID},
                    }
                ],
            },
            timeout=60,
        ),
        "Memory storage",
    )
    return resp is not None


def search_memories(query: str) -> str:
    """Search for relevant memories and return combined context text."""
    resp = _retry_request(
        lambda: requests.post(
            f"{MEMORY_SERVER_URL}/api/v2/memories/search",
            json={
                "org_id": ORG_ID,
                "project_id": PROJECT_ID,
                "query": query,
                "top_k": 5,
                "types": ["episodic", "semantic"],
                "filter": f"metadata.user_id='{USER_ID}'",
            },
            timeout=60,
        ),
        "Memory search",
    )
    if resp is None:
        return ""

    data = resp.json()
    context_parts = []
    content = data.get("content", {})

    # Episodic memory
    episodic = content.get("episodic_memory", {})
    if isinstance(episodic, dict):
        long_term = episodic.get("long_term_memory", {}).get("episodes", [])
        short_term = episodic.get("short_term_memory", {}).get("episodes", [])
        for episode in long_term + short_term:
            if isinstance(episode, dict):
                ctx = episode.get("content") or episode.get("episode_content", "")
                if ctx:
                    context_parts.append(ctx)

    # Semantic memory
    for memory in content.get("semantic_memory", []):
        if isinstance(memory, dict):
            ctx = memory.get("content") or memory.get("memory_content", "")
            if ctx:
                context_parts.append(ctx)

    return "\n\n".join(context_parts)


def delete_all_memories() -> bool:
    """Delete all memories for the current user."""
    filter_str = f"metadata.user_id='{USER_ID}'"

    def _list_ids(memory_type: str, id_keys: list[str]) -> list[str]:
        ids = []
        page_num = 0
        while True:
            resp = _retry_request(
                lambda: requests.post(
                    f"{MEMORY_SERVER_URL}/api/v2/memories/list",
                    json={
                        "org_id": ORG_ID,
                        "project_id": PROJECT_ID,
                        "filter": filter_str,
                        "type": memory_type,
                        "page_size": 100,
                        "page_num": page_num,
                    },
                    timeout=60,
                ),
                f"List {memory_type} memories",
            )
            if resp is None:
                break
            memories = resp.json().get("content", {}).get(f"{memory_type}_memory", [])
            if not memories:
                break
            for mem in memories:
                if isinstance(mem, dict):
                    for key in id_keys:
                        mid = mem.get(key)
                        if mid:
                            ids.append(mid)
                            break
            if len(memories) < 100:
                break
            page_num += 1
        return ids

    try:
        episodic_ids = _list_ids("episodic", ["id", "uid", "episode_id"])
        if episodic_ids:
            requests.post(
                f"{MEMORY_SERVER_URL}/api/v2/memories/episodic/delete",
                json={"org_id": ORG_ID, "project_id": PROJECT_ID, "episodic_ids": episodic_ids},
                timeout=60,
            )

        semantic_ids = _list_ids("semantic", ["id", "feature_id", "semantic_id"])
        if semantic_ids:
            requests.post(
                f"{MEMORY_SERVER_URL}/api/v2/memories/semantic/delete",
                json={"org_id": ORG_ID, "project_id": PROJECT_ID, "semantic_ids": semantic_ids},
                timeout=60,
            )

        return True
    except Exception as e:
        logger.exception("Failed to delete memories")
        st.error(f"Error deleting memories: {e}")
        return False


# ------------------------------------------------------------------
# Chat logic
# ------------------------------------------------------------------

def chat_with_memory(user_message: str) -> tuple[str, str]:
    """Chat with memory: store -> search -> enhance prompt -> respond -> store."""
    # 1. Store the user message
    add_memory(user_message, role="user")

    # 2. Search for relevant memories
    context = search_memories(user_message)

    # 3. Build prompt
    if context:
        prompt = f"""You are a helpful AI assistant with access to the user's memory.

RELEVANT MEMORY CONTEXT:
{context}

USER MESSAGE: {user_message}

Instructions:
- Use the memory context to provide personalized responses
- Reference past conversations naturally when relevant
- Be conversational and helpful
- If no relevant context exists, respond normally
- Do NOT include any reasoning tags, thinking blocks, or meta-commentary
- Provide your response directly without any <reasoning> or </reasoning> tags
- Just give a natural, conversational response"""
    else:
        prompt = f"""You are a helpful AI assistant.

USER MESSAGE: {user_message}

Instructions:
- Respond helpfully and conversationally
- Do NOT include any reasoning tags, thinking blocks, or meta-commentary
- Provide your response directly without any <reasoning> or </reasoning> tags
- Just give a natural, conversational response"""

    # 4. Call Bedrock
    response = call_bedrock(prompt, model_id=st.session_state.model_id)
    response = clean_response(response)

    # 5. Store the assistant response
    add_memory(f"Assistant: {response}", role="assistant")

    return response, context


# ------------------------------------------------------------------
# Connection testing
# ------------------------------------------------------------------

def test_connections() -> dict[str, tuple[bool, str]]:
    """Test connections to MemMachine and Bedrock."""
    results = {}

    try:
        resp = requests.get(f"{MEMORY_SERVER_URL}/api/v2/health", timeout=5)
        if resp.status_code == 200:
            results["memmachine"] = (True, "MemMachine connection: OK")
        else:
            results["memmachine"] = (False, f"MemMachine connection: Status {resp.status_code}")
    except Exception as e:
        results["memmachine"] = (False, f"MemMachine connection failed: {e}")

    success, msg = test_bedrock_connection()
    results["bedrock"] = (success, msg)

    return results


# ------------------------------------------------------------------
# UI
# ------------------------------------------------------------------

def render_header():
    st.markdown(
        """
        <div class="header-wrapper">
            <h1>✨ Chatbot WITH Memory</h1>
            <p class="header-subtitle">This chatbot has persistent memory — it remembers everything!</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_memory_status():
    st.markdown(
        """
        <div class="memory-status-indicator active">
            <span class="memory-status-text">
                🧠 <strong>MemMachine Active</strong> — Persistent memory enabled!
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------
# Session state
# ------------------------------------------------------------------

def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "model_id" not in st.session_state:
        st.session_state.model_id = MODEL_ID
    if "user_id" not in st.session_state:
        st.session_state.user_id = USER_ID
    if "show_memory_context" not in st.session_state:
        st.session_state.show_memory_context = False


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

        # Model selection
        st.markdown("#### Select Model")
        model_options = list(AVAILABLE_MODELS.keys())
        model_display_names = [AVAILABLE_MODELS[m] for m in model_options]

        current_model = st.session_state.model_id
        if current_model in model_options:
            default_index = model_options.index(current_model)
        else:
            default_index = 0
            st.session_state.model_id = model_options[0]

        selected_display = st.selectbox(
            "Choose Model",
            model_display_names,
            index=default_index,
            help="Select a Bedrock model. Memory context is retained across model switches!",
            key="model_select_display",
        )

        selected_model_id = model_options[model_display_names.index(selected_display)]
        if st.session_state.model_id != selected_model_id:
            st.session_state.model_id = selected_model_id
            st.success(f"Switched to: {selected_display}")
            st.caption("Memory context is retained across model switches!")

        st.info(f"**Current Model:** {AVAILABLE_MODELS.get(st.session_state.model_id, st.session_state.model_id)}")
        st.info(f"**Region:** {AWS_REGION}")
        st.info(f"**Memory Server:** {MEMORY_SERVER_URL}")
        st.info(f"**User ID:** {st.session_state.user_id}")

        st.divider()

        st.markdown("### Connection Status")
        if st.button("Test Connections"):
            results = test_connections()
            for _service, (success, message) in results.items():
                (st.success if success else st.error)(f"{'✅' if success else '❌'} {message}")

        st.divider()

        st.markdown("### Try This")
        st.markdown("""
        1. Say: **"My name is Alice"**
        2. Then ask: **"What's my name?"**
        3. Notice: It remembers!
        4. **Switch models** using the dropdown above
        5. Ask again — memory persists across models!
        6. Restart and ask again — memory persists!
        """)

        st.divider()

        st.session_state.show_memory_context = st.checkbox(
            "Show Memory Context",
            value=st.session_state.show_memory_context,
            help="Show the memory context used for each response",
        )

        st.divider()

        if st.button("Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        if st.button("Delete All Memories", use_container_width=True, type="secondary"):
            if delete_all_memories():
                st.success("All memories deleted!")
                st.session_state.messages = []
                st.rerun()
            else:
                st.error("Failed to delete memories")

    # Memory status
    render_memory_status()

    # Chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if st.session_state.show_memory_context and message.get("memory_context"):
                with st.expander("Memory Context Used"):
                    st.text(message["memory_context"])

    # Chat input
    if prompt := st.chat_input("Type your message…"):
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Storing in memory... Searching memories... Generating response..."):
                response, memory_context = chat_with_memory(prompt)

            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "memory_context": memory_context,
            })

            st.write_stream(typewriter_effect(response))

            if st.session_state.show_memory_context and memory_context:
                with st.expander("Memory Context Used"):
                    st.text(memory_context if memory_context else "No relevant context found.")


if __name__ == "__main__":
    main()

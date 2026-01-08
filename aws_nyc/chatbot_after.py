#!/usr/bin/env python3
"""
MemMachine Workshop Chatbot - AFTER (With Memory)
A chatbot with MemMachine memory integration - demonstrates persistent memory capabilities
Streamlit-based interactive chat interface
"""

import os
import json
import re
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

import boto3
import requests
import streamlit as st
from dotenv import load_dotenv

# Set page config MUST be first Streamlit command
st.set_page_config(
    page_title="Chatbot WITH Memory",
    page_icon="✨",
    layout="wide"
)

# Load environment variables
load_dotenv()

# Configuration
MEMORY_SERVER_URL = os.getenv("MEMORY_SERVER_URL", "http://localhost:8080")
ORG_ID = os.getenv("ORG_ID", "workshop-org")
PROJECT_ID = os.getenv("PROJECT_ID", "workshop-project")
USER_ID = os.getenv("USER_ID", "workshop-user")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "openai.gpt-oss-20b-1:0")

# Available Bedrock models for selection (on-demand models only)
# Note: Models requiring inference profiles (provisioned throughput) are excluded
# Claude Opus, 3.5, and 4.5 models require inference profiles, so only smaller Claude models are included
# End-of-life models (Amazon Titan) have been removed
# Meta Llama 3.1 models require inference profiles
AVAILABLE_MODELS = {
    "openai.gpt-oss-20b-1:0": "OpenAI GPT-OSS 20B",
    "anthropic.claude-3-sonnet-20240229-v1:0": "Anthropic Claude 3 Sonnet",
    "anthropic.claude-3-haiku-20240307-v1:0": "Anthropic Claude 3 Haiku",
    "us.deepseek.r1-v1:0": "DeepSeek R1",
    "qwen.qwen3-32b-v1:0": "Qwen 3 32B",
    "mistral.mixtral-8x7b-instruct-v0:1": "Mistral Mixtral 8x7B Instruct",
    "mistral.mistral-7b-instruct-v0:2": "Mistral 7B Instruct",
}

# Initialize Bedrock client
@st.cache_resource
def get_bedrock_client():
    """Get or create Bedrock runtime client."""
    return boto3.client(
        'bedrock-runtime',
        region_name=AWS_REGION
    )

# Typing effect speed
TYPING_SPEED = 0.02


def add_memory(message: str, role: str = "user") -> bool:
    """Add a message to MemMachine memory with retry logic."""
    import time
    
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
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
                            "metadata": {"user_id": USER_ID}
                        }
                    ]
                },
                timeout=60
            )
            response.raise_for_status()
            return True
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 503:
                # Service Unavailable - retry
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    st.warning(f"⚠ Memory server is temporarily unavailable (503). Please try again in a moment.")
                    return False
            else:
                st.error(f"⚠ Memory storage failed: {e}")
                return False
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
                continue
            else:
                st.warning(f"⚠ Memory storage timed out. The server may be slow. Please try again.")
                return False
        except Exception as e:
            st.error(f"⚠ Memory storage failed: {e}")
            return False
    
    return False


def search_memories(query: str) -> str:
    """Search for relevant memories with retry logic."""
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            filter_str = f"metadata.user_id='{USER_ID}'"
            response = requests.post(
                f"{MEMORY_SERVER_URL}/api/v2/memories/search",
                json={
                    "org_id": ORG_ID,
                    "project_id": PROJECT_ID,
                    "query": query,
                    "top_k": 5,
                    "types": ["episodic", "semantic"],
                    "filter": filter_str
                },
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract context from response
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
            semantic = content.get("semantic_memory", [])
            for memory in semantic:
                if isinstance(memory, dict):
                    ctx = memory.get("content") or memory.get("memory_content", "")
                    if ctx:
                        context_parts.append(ctx)
            
            return "\n\n".join(context_parts) if context_parts else ""
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 503:
                # Service Unavailable - retry
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    st.warning(f"⚠ Memory server is temporarily unavailable (503). Returning empty context.")
                    return ""
            else:
                st.error(f"⚠ Memory search failed: {e}")
                return ""
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
                continue
            else:
                st.warning(f"⚠ Memory search timed out. The server may be slow. Returning empty context.")
                return ""
        except Exception as e:
            st.error(f"⚠ Memory search failed: {e}")
            return ""
    
    return ""


def call_bedrock(prompt: str, model_id: Optional[str] = None) -> str:
    """Call AWS Bedrock model.
    
    Args:
        prompt: The prompt to send to the model.
        model_id: The model ID to use. If None, uses the model from session state.
    """
    if model_id is None:
        model_id = st.session_state.get("model_id", MODEL_ID)
    
    bedrock_runtime = get_bedrock_client()
    try:
        # Determine model provider and format request accordingly
        if model_id.startswith("anthropic."):
            # Anthropic models require anthropic_version field
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000,
                "temperature": 0.7
            })
        elif model_id.startswith("us.deepseek.") or model_id.startswith("qwen."):
            # DeepSeek and Qwen models use messages format (similar to OpenAI)
            body = json.dumps({
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000,
                "temperature": 0.7,
                "top_p": 0.9
            })
        elif model_id.startswith("meta.") or model_id.startswith("mistral."):
            # Meta and Mistral models use similar format to Anthropic
            body = json.dumps({
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000,
                "temperature": 0.7
            })
        elif model_id.startswith("amazon.titan"):
            # Amazon Titan models use prompt field instead of messages
            body = json.dumps({
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": 1000,
                    "temperature": 0.7
                }
            })
        else:
            # Default format for OpenAI and other models
            body = json.dumps({
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000,
                "temperature": 0.7
            })
        
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=body,
            contentType="application/json",
            accept="application/json"
        )
        
        response_body = json.loads(response['body'].read())
        
        # Extract response based on model format
        if "choices" in response_body:
            # OpenAI, DeepSeek, Qwen format
            if isinstance(response_body["choices"], list) and len(response_body["choices"]) > 0:
                choice = response_body["choices"][0]
                # Check if it's message format (OpenAI) or text format (DeepSeek/Qwen)
                if "message" in choice:
                    return choice["message"]["content"]
                elif "text" in choice:
                    return choice["text"].strip()
        elif "content" in response_body:
            # Anthropic format
            if isinstance(response_body["content"], list):
                return "".join(
                    part["text"] for part in response_body["content"] 
                    if part.get("type") == "text"
                ).strip()
            return response_body["content"][0]["text"]
        elif "results" in response_body:
            # Amazon Titan format
            return response_body["results"][0]["outputText"]
        elif "generation" in response_body:
            # Alternative Titan format
            return response_body["generation"]
        else:
            # Fallback: return string representation
            return str(response_body)
    except Exception as e:
        return f"Error calling Bedrock: {e}"


def typewriter_effect(text: str, speed: float = TYPING_SPEED):
    """Generator that yields text word by word to create a typing effect."""
    words = text.split(" ")
    for i, word in enumerate(words):
        if i == 0:
            yield word
        else:
            yield " " + word
        time.sleep(speed)


def load_css():
    """Load CSS from styles.css file."""
    css_path = Path(__file__).parent / "styles.css"
    try:
        with css_path.open(encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass


def render_header():
    """Render the header with title and info."""
    st.markdown(
        """
        <div class="header-wrapper">
            <h1>✨ Chatbot WITH Memory (AFTER)</h1>
            <p class="header-subtitle">This chatbot has persistent memory - it remembers everything!</p>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_memory_status():
    """Render the memory status indicator."""
    st.markdown(
        """
        <div class="memory-status-indicator active">
            <span class="memory-status-text">
                🧠 <strong>MemMachine Active</strong> - Persistent memory enabled!
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )


def initialize_session_state():
    """Initialize session state with default values."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "model_id" not in st.session_state:
        st.session_state.model_id = MODEL_ID
    if "user_id" not in st.session_state:
        st.session_state.user_id = USER_ID
    if "show_memory_context" not in st.session_state:
        st.session_state.show_memory_context = False


def clean_response(response: str) -> str:
    """Remove reasoning tags and clean up response."""
    # Remove <reasoning>...</reasoning> blocks
    response = re.sub(r'<reasoning>.*?</reasoning>', '', response, flags=re.DOTALL | re.IGNORECASE)
    # Remove any remaining reasoning tags
    response = re.sub(r'</?reasoning>', '', response, flags=re.IGNORECASE)
    # Clean up extra whitespace
    response = re.sub(r'\n\s*\n\s*\n', '\n\n', response)
    return response.strip()


def chat_with_memory(user_message: str) -> tuple[str, str]:
    """Main chat function WITH memory integration.
    
    Returns:
        tuple: (response, memory_context) - The assistant response and the memory context used
    """
    # Step 1: Store the user message in memory
    add_memory(user_message, role="user")
    
    # Step 2: Search for relevant memories
    context = search_memories(user_message)
    
    # Step 3: Build prompt with context
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
    
    # Step 4: Call Bedrock with selected model
    response = call_bedrock(prompt, model_id=st.session_state.model_id)
    
    # Step 5: Clean response to remove any reasoning sections
    response = clean_response(response)
    
    # Step 6: Store the cleaned response in memory
    add_memory(f"Assistant: {response}", role="assistant")
    
    return response, context


def test_connections():
    """Test connections to MemMachine and Bedrock."""
    results = {}
    
    # Test MemMachine
    try:
        response = requests.get(f"{MEMORY_SERVER_URL}/api/v2/health", timeout=5)
        if response.status_code == 200:
            results["memmachine"] = (True, "✅ MemMachine connection: OK")
        else:
            results["memmachine"] = (False, f"⚠ MemMachine connection: Status {response.status_code}")
    except Exception as e:
        results["memmachine"] = (False, f"❌ MemMachine connection failed: {e}")
    
    # Test Bedrock
    try:
        bedrock = boto3.client('bedrock', region_name=AWS_REGION)
        bedrock.list_foundation_models()
        results["bedrock"] = (True, "✅ AWS Bedrock connection: OK")
    except Exception as e:
        results["bedrock"] = (False, f"❌ AWS Bedrock connection failed: {e}")
    
    return results


def delete_all_memories():
    """Delete all memories for the current user."""
    try:
        filter_str = f"metadata.user_id='{USER_ID}'"
        
        # List episodic memories
        episodic_ids = []
        page_num = 0
        while True:
            resp = requests.post(
                f"{MEMORY_SERVER_URL}/api/v2/memories/list",
                json={
                    "org_id": ORG_ID,
                    "project_id": PROJECT_ID,
                    "filter": filter_str,
                    "type": "episodic",
                    "page_size": 100,
                    "page_num": page_num,
                },
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            episodic_memories = data.get("content", {}).get("episodic_memory", [])
            
            if not episodic_memories:
                break
            
            for memory in episodic_memories:
                if isinstance(memory, dict):
                    memory_id = memory.get("id") or memory.get("uid") or memory.get("episode_id")
                    if memory_id:
                        episodic_ids.append(memory_id)
            
            if len(episodic_memories) < 100:
                break
            page_num += 1
        
        # Delete episodic memories
        if episodic_ids:
            requests.post(
                f"{MEMORY_SERVER_URL}/api/v2/memories/episodic/delete",
                json={
                    "org_id": ORG_ID,
                    "project_id": PROJECT_ID,
                    "episodic_ids": episodic_ids,
                },
                timeout=60,
            )
        
        # List semantic memories
        semantic_ids = []
        page_num = 0
        while True:
            resp = requests.post(
                f"{MEMORY_SERVER_URL}/api/v2/memories/list",
                json={
                    "org_id": ORG_ID,
                    "project_id": PROJECT_ID,
                    "filter": filter_str,
                    "type": "semantic",
                    "page_size": 100,
                    "page_num": page_num,
                },
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            semantic_memories = data.get("content", {}).get("semantic_memory", [])
            
            if not semantic_memories:
                break
            
            for memory in semantic_memories:
                if isinstance(memory, dict):
                    memory_id = memory.get("id") or memory.get("feature_id") or memory.get("semantic_id")
                    if memory_id:
                        semantic_ids.append(memory_id)
            
            if len(semantic_memories) < 100:
                break
            page_num += 1
        
        # Delete semantic memories
        if semantic_ids:
            requests.post(
                f"{MEMORY_SERVER_URL}/api/v2/memories/semantic/delete",
                json={
                    "org_id": ORG_ID,
                    "project_id": PROJECT_ID,
                    "semantic_ids": semantic_ids,
                },
                timeout=60,
            )
        
        return True
    except Exception as e:
        st.error(f"Error deleting memories: {e}")
        return False


def main():
    """Main Streamlit application."""
    load_css()
    initialize_session_state()
    render_header()
    
    # Sidebar with configuration and info
    with st.sidebar:
        st.markdown("### Configuration")
        
        # Model selection dropdown
        st.markdown("#### Select Model")
        model_options = list(AVAILABLE_MODELS.keys())
        model_display_names = [AVAILABLE_MODELS[model] for model in model_options]
        
        # Find current model index
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
            key="model_select_display"
        )
        
        # Update session state with selected model ID
        selected_model_id = model_options[model_display_names.index(selected_display)]
        if st.session_state.model_id != selected_model_id:
            st.session_state.model_id = selected_model_id
            st.success(f"🔄 Switched to: {selected_display}")
            st.caption("💡 Memory context is retained across model switches!")
        
        st.info(f"**Current Model:** {AVAILABLE_MODELS.get(st.session_state.model_id, st.session_state.model_id)}")
        st.info(f"**Region:** {AWS_REGION}")
        st.info(f"**Memory Server:** {MEMORY_SERVER_URL}")
        st.info(f"**User ID:** {st.session_state.user_id}")
        
        st.divider()
        
        st.markdown("### Connection Status")
        if st.button("Test Connections"):
            results = test_connections()
            for service, (success, message) in results.items():
                if success:
                    st.success(message)
                else:
                    st.error(message)
        
        st.divider()
        
        st.markdown("### Try This")
        st.markdown("""
        1. Say: **"My name is Alice"**
        2. Then ask: **"What's my name?"**
        3. Notice: It remembers!
        4. **Switch models** using the dropdown above
        5. Ask again - memory persists across models! 🧠
        6. Restart and ask again - memory persists!
        """)
        
        st.divider()
        
        # Memory context toggle
        st.session_state.show_memory_context = st.checkbox(
            "Show Memory Context",
            value=st.session_state.show_memory_context,
            help="Show the memory context used for each response"
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
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show memory context if enabled
            if st.session_state.show_memory_context and message.get("memory_context"):
                with st.expander("🔍 Memory Context Used"):
                    st.text(message["memory_context"])
    
    # Chat input
    if prompt := st.chat_input("Type your message…"):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("💾 Storing in memory... 🔍 Searching memories... 🤖 Generating response..."):
                response, memory_context = chat_with_memory(prompt)
            
            # Add assistant response to history
            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "memory_context": memory_context
            })
            
            # Show response with typing effect
            st.write_stream(typewriter_effect(response))
            
            # Show memory context if enabled
            if st.session_state.show_memory_context and memory_context:
                with st.expander("🔍 Memory Context Used"):
                    st.text(memory_context if memory_context else "No relevant context found.")


if __name__ == "__main__":
    main()

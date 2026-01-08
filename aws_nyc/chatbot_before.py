#!/usr/bin/env python3
"""
MemMachine Workshop Chatbot - BEFORE (Without Memory)
A simple stateless chatbot using AWS Bedrock - demonstrates limitations without memory
Streamlit-based interactive chat interface
"""

import os
import json
import re
import time
from pathlib import Path

import boto3
import streamlit as st
from dotenv import load_dotenv

# Set page config MUST be first Streamlit command
st.set_page_config(
    page_title="Chatbot WITHOUT Memory",
    page_icon="⚠️",
    layout="wide"
)

# Load environment variables
load_dotenv()

# Configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "openai.gpt-oss-20b-1:0")

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


def call_bedrock(prompt: str) -> str:
    """Call AWS Bedrock model."""
    bedrock_runtime = get_bedrock_client()
    try:
        # Determine model provider and format request accordingly
        if MODEL_ID.startswith("anthropic."):
            # Anthropic models require anthropic_version field
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000,
                "temperature": 0.7
            })
        elif MODEL_ID.startswith("meta.") or MODEL_ID.startswith("mistral."):
            # Meta and Mistral models use similar format to Anthropic
            body = json.dumps({
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000,
                "temperature": 0.7
            })
        elif MODEL_ID.startswith("amazon.titan"):
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
            modelId=MODEL_ID,
            body=body,
            contentType="application/json",
            accept="application/json"
        )
        
        response_body = json.loads(response['body'].read())
        
        # Extract response based on model format
        if "choices" in response_body:
            # OpenAI format
            return response_body["choices"][0]["message"]["content"]
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
            <h1>⚠️ Chatbot WITHOUT Memory (BEFORE)</h1>
            <p class="header-subtitle">This chatbot has NO memory - it forgets everything between messages!</p>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_memory_status():
    """Render the memory status indicator."""
    st.markdown(
        """
        <div class="memory-status-indicator">
            <span class="memory-status-text">
                ⚪ <strong>No Memory Mode</strong> - This chatbot forgets everything!
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


def clean_response(response: str) -> str:
    """Remove reasoning tags and clean up response."""
    # Remove <reasoning>...</reasoning> blocks
    response = re.sub(r'<reasoning>.*?</reasoning>', '', response, flags=re.DOTALL | re.IGNORECASE)
    # Remove any remaining reasoning tags
    response = re.sub(r'</?reasoning>', '', response, flags=re.IGNORECASE)
    # Clean up extra whitespace
    response = re.sub(r'\n\s*\n\s*\n', '\n\n', response)
    return response.strip()


def chat_without_memory(user_message: str) -> str:
    """Simple chat function WITHOUT memory - stateless."""
    # Build simple prompt - no memory context
    prompt = f"""You are a helpful AI assistant.

USER MESSAGE: {user_message}

Instructions:
- Respond helpfully and conversationally
- Do NOT include any reasoning tags, thinking blocks, or meta-commentary
- Provide your response directly without any <reasoning> or </reasoning> tags
- Just give a natural, conversational response"""
    
    # Call Bedrock
    response = call_bedrock(prompt)
    # Clean response to remove any reasoning sections
    return clean_response(response)


def test_connection():
    """Test connection to Bedrock."""
    try:
        bedrock = boto3.client('bedrock', region_name=AWS_REGION)
        bedrock.list_foundation_models()
        return True, "✅ AWS Bedrock connection: OK"
    except Exception as e:
        return False, f"❌ AWS Bedrock connection failed: {e}"


def main():
    """Main Streamlit application."""
    load_css()
    initialize_session_state()
    render_header()
    
    # Sidebar with configuration and info
    with st.sidebar:
        st.markdown("### Configuration")
        st.info(f"**Model:** {st.session_state.model_id}")
        st.info(f"**Region:** {AWS_REGION}")
        
        st.divider()
        
        st.markdown("### Connection Status")
        if st.button("Test Connection"):
            success, message = test_connection()
            if success:
                st.success(message)
            else:
                st.error(message)
        
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
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message…"):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Generating response..."):
                response = chat_without_memory(prompt)
            
            # Add assistant response to history
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Show response with typing effect
            st.write_stream(typewriter_effect(response))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Shared utilities for the MemMachine Workshop chatbots.

Contains Bedrock client management, model formatting, response cleaning,
CSS loading, and common UI components used by both chatbot variants.
"""

import json
import logging
import os
import re
import time
from pathlib import Path

import boto3
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "openai.gpt-oss-20b-1:0")

AVAILABLE_MODELS = {
    "openai.gpt-oss-20b-1:0": "OpenAI GPT-OSS 20B",
    "anthropic.claude-3-sonnet-20240229-v1:0": "Anthropic Claude 3 Sonnet",
    "anthropic.claude-3-haiku-20240307-v1:0": "Anthropic Claude 3 Haiku",
    "us.deepseek.r1-v1:0": "DeepSeek R1",
    "qwen.qwen3-32b-v1:0": "Qwen 3 32B",
    "mistral.mixtral-8x7b-instruct-v0:1": "Mistral Mixtral 8x7B Instruct",
    "mistral.mistral-7b-instruct-v0:2": "Mistral 7B Instruct",
}

TYPING_SPEED = 0.02

# ---------------------------------------------------------------------------
# Bedrock client
# ---------------------------------------------------------------------------

@st.cache_resource
def get_bedrock_client():
    """Get or create Bedrock runtime client."""
    return boto3.client("bedrock-runtime", region_name=AWS_REGION)


# ---------------------------------------------------------------------------
# Bedrock model invocation
# ---------------------------------------------------------------------------

def _build_request_body(model_id: str, prompt: str) -> str:
    """Build the JSON request body for a given Bedrock model."""
    if model_id.startswith("anthropic."):
        return json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000,
            "temperature": 0.7,
        })
    if model_id.startswith("us.deepseek.") or model_id.startswith("qwen."):
        return json.dumps({
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000,
            "temperature": 0.7,
            "top_p": 0.9,
        })
    if model_id.startswith("meta.") or model_id.startswith("mistral."):
        return json.dumps({
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000,
            "temperature": 0.7,
        })
    if model_id.startswith("amazon.titan"):
        return json.dumps({
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": 1000,
                "temperature": 0.7,
            },
        })
    # Default (OpenAI and others)
    return json.dumps({
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1000,
        "temperature": 0.7,
    })


def _extract_response_text(response_body: dict) -> str:
    """Extract the generated text from a Bedrock response."""
    if "choices" in response_body:
        choices = response_body["choices"]
        if isinstance(choices, list) and choices:
            choice = choices[0]
            if "message" in choice:
                return choice["message"]["content"]
            if "text" in choice:
                return choice["text"].strip()
    if "content" in response_body:
        content = response_body["content"]
        if isinstance(content, list):
            return "".join(
                part["text"] for part in content if part.get("type") == "text"
            ).strip()
        return content[0]["text"]
    if "results" in response_body:
        return response_body["results"][0]["outputText"]
    if "generation" in response_body:
        return response_body["generation"]
    return str(response_body)


def call_bedrock(prompt: str, model_id: str | None = None) -> str:
    """Call an AWS Bedrock model and return the response text."""
    if model_id is None:
        model_id = st.session_state.get("model_id", MODEL_ID)

    bedrock_runtime = get_bedrock_client()
    try:
        body = _build_request_body(model_id, prompt)
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=body,
            contentType="application/json",
            accept="application/json",
        )
        response_body = json.loads(response["body"].read())
        return _extract_response_text(response_body)
    except Exception as e:
        logger.exception("Bedrock invocation failed")
        return f"Error calling Bedrock: {e}"


# ---------------------------------------------------------------------------
# Response cleaning
# ---------------------------------------------------------------------------

def clean_response(response: str) -> str:
    """Remove reasoning tags and clean up response text."""
    response = re.sub(r"<reasoning>.*?</reasoning>", "", response, flags=re.DOTALL | re.IGNORECASE)
    response = re.sub(r"</?reasoning>", "", response, flags=re.IGNORECASE)
    response = re.sub(r"\n\s*\n\s*\n", "\n\n", response)
    return response.strip()


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------

def typewriter_effect(text: str, speed: float = TYPING_SPEED):
    """Generator that yields text word-by-word to create a typing effect."""
    words = text.split(" ")
    for i, word in enumerate(words):
        yield word if i == 0 else " " + word
        time.sleep(speed)


def load_css():
    """Load CSS from styles.css file."""
    css_path = Path(__file__).parent / "styles.css"
    try:
        with css_path.open(encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass


def test_bedrock_connection() -> tuple[bool, str]:
    """Test connectivity to AWS Bedrock."""
    try:
        bedrock = boto3.client("bedrock", region_name=AWS_REGION)
        bedrock.list_foundation_models()
        return True, "AWS Bedrock connection: OK"
    except Exception as e:
        logger.warning("Bedrock connection test failed: %s", e)
        return False, f"AWS Bedrock connection failed: {e}"

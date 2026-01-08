# AWS NYC Workshop - Quick Start

This directory contains all materials for the **MemMachine Workshop @ AWS NYC**.

## Files

- `workshop_guide.mdx` - Complete step-by-step workshop guide
- `checklist.md` - Quick reference checklist
- `chatbot_before.py` - **BEFORE**: Stateless chatbot without memory (Streamlit web UI)
- `chatbot_after.py` - **AFTER**: Memory-aware chatbot with MemMachine (Streamlit web UI)
- `styles.css` - CSS styling for the web interface
- `requirements.txt` - Python dependencies
- `README.md` - This file

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment

Create a `.env` file:

```bash
# MemMachine Configuration
MEMORY_SERVER_URL=your-server-url
ORG_ID=workshop-org
PROJECT_ID=workshop-project
USER_ID=workshop-user

# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key

# Bedrock Model
BEDROCK_MODEL_ID=openai.gpt-oss-20b-1:0
```

**Replace:**
- `your-server-url` with your MemMachine server URL (from CloudFormation outputs)
- AWS credentials with your own

### 3. Compare Both Chatbots

**Run the "BEFORE" chatbot (no memory):**
```bash
streamlit run chatbot_before.py
```

This will open a web interface in your browser. Try:
- Say: "My name is Alice"
- Then ask: "What's my name?"
- Notice: It doesn't remember!

**Run the "AFTER" chatbot (with memory):**
```bash
streamlit run chatbot_after.py
```

This will open a web interface in your browser. Try:
- Say: "My name is Alice"
- Then ask: "What's my name?"
- Notice: It remembers! ✨
- **Bonus**: Switch models using the dropdown - memory persists across models!

## Full Workshop Guide

For complete step-by-step instructions, see:
- **Workshop Guide**: `workshop_guide.mdx`
- **Quick Checklist**: `checklist.md`

## What This Demonstrates

### Before vs After Comparison

**BEFORE (No Memory):**
- Stateless chatbot
- Each message is independent
- Cannot remember previous conversations
- No personalization

**AFTER (With Memory):**
- Stateful chatbot with persistent memory
- Remembers past conversations
- Personalized responses
- Context-aware across sessions

### Key Features Demonstrated

1. **Memory Storage**: User messages are stored in MemMachine
2. **Memory Search**: Relevant past conversations are retrieved
3. **Context Enhancement**: Retrieved memories are used to enhance prompts
4. **Bedrock Integration**: AWS Bedrock provides the LLM inference
5. **Persistent Memory**: Memories persist across sessions
6. **Model Switching**: In the "AFTER" chatbot, you can switch between different Bedrock models while retaining memory context
7. **Interactive Web UI**: Both chatbots feature a modern Streamlit web interface for easy interaction

## Architecture

```
User Input
    ↓
Store in MemMachine
    ↓
Search Relevant Memories
    ↓
Build Context-Enhanced Prompt
    ↓
Call AWS Bedrock
    ↓
Store Response in Memory
    ↓
Return Response
```

## Testing Memory

1. **First Session:**
   ```
   You: My name is Alice
   You: I love Python programming
   ```

2. **Restart Chatbot** (exit and run again)

3. **Second Session:**
   ```
   You: What's my name?
   Assistant: [Should remember "Alice"]
   
   You: What do I love?
   Assistant: [Should remember "Python programming"]
   ```

## Troubleshooting

### Connection Issues
- Verify `MEMORY_SERVER_URL` is correct
- Check MemMachine is running: `curl http://YOUR_IP:8080/api/v2/health`
- Verify security group allows port 8080

### Bedrock Issues
- Verify Bedrock model access in AWS Console
- Check AWS credentials are correct
- Verify region matches your Bedrock models

### Memory Not Working
- Check API responses for errors
- Verify `ORG_ID` and `PROJECT_ID` match
- Test memory search manually via API

## Next Steps

- Explore the interactive web interface features
- Try switching models in the "AFTER" chatbot to see memory persist across models
- Integrate with your own applications
- Explore advanced features (ProfileMemory, custom prompts)
- Review production considerations

## Resources

- [Workshop Guide](workshop_guide.mdx)
- [MemMachine Documentation](https://memmachine.ai/docs)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [GitHub Repository](https://github.com/MemMachine/MemMachine)


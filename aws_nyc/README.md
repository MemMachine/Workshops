# AWS NYC Workshop - Quick Start

This directory contains all materials for the **MemMachine Workshop @ AWS NYC**.

## Files

- `bedrock-cft.yml` - CloudFormation template for deploying MemMachine on AWS EC2
- `workshop_guide.mdx` - Complete step-by-step workshop guide
- `checklist.md` - Quick reference checklist
- `without_memory.py` - Stateless chatbot without memory (Streamlit web UI)
- `with_memory.py` - Memory-aware chatbot with MemMachine (Streamlit web UI)
- `utils.py` - Shared utilities (Bedrock client, model formatting, UI helpers)
- `styles.css` - CSS styling for the web interface
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variable template
- `README.md` - This file

## Quick Start

### 1. Deploy MemMachine

Deploy the included CloudFormation template to provision an EC2 instance running MemMachine with an API Gateway for public access:

```bash
aws cloudformation create-stack \
    --stack-name memmachine-workshop \
    --template-body file://bedrock-cft.yml \
    --parameters ParameterKey=KeyPairName,ParameterValue=YOUR_KEY_PAIR \
                 ParameterKey=PostgresPassword,ParameterValue=YOUR_PASSWORD \
                 ParameterKey=Neo4jPassword,ParameterValue=YOUR_PASSWORD \
                 ParameterKey=AwsAccessKeyId,ParameterValue=YOUR_ACCESS_KEY \
                 ParameterKey=AwsSecretAccessKey,ParameterValue=YOUR_SECRET_KEY \
                 ParameterKey=AwsRegion,ParameterValue=us-west-2 \
    --capabilities CAPABILITY_NAMED_IAM \
    --region us-west-2
```

Once the stack is created, retrieve the **ApplicationURL** from the stack outputs — this is your public MemMachine API endpoint (via API Gateway).

> **Note:** Port 8080 on the EC2 instance is only accessible within the VPC. All external API access goes through the API Gateway URL.

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Environment

Copy the example environment file and fill in your values:

```bash
cp .env.example .env
```

Then edit `.env` — set `MEMORY_SERVER_URL` to the **ApplicationURL** from your CloudFormation stack outputs (the API Gateway URL, e.g. `https://abc123.execute-api.us-west-2.amazonaws.com`).

### 4. Compare Both Chatbots

**Run the chatbot without memory:**
```bash
streamlit run without_memory.py
```

This will open a web interface in your browser. Try:
- Say: "My name is Alice"
- Then ask: "What's my name?"
- Notice: It doesn't remember!

**Run the chatbot with memory:**
```bash
streamlit run with_memory.py
```

This will open a web interface in your browser. Try:
- Say: "My name is Alice"
- Then ask: "What's my name?"
- Notice: It remembers!
- **Bonus**: Switch models using the dropdown — memory persists across models!

### Docker (Optional)

```bash
# From the repository root
docker build -t memmachine-workshop .
docker run --env-file aws_nyc/.env -p 8501:8501 memmachine-workshop
```

## Full Workshop Guide

For complete step-by-step instructions, see:
- **Workshop Guide**: `workshop_guide.mdx`
- **Quick Checklist**: `checklist.md`

## What This Demonstrates

### Without Memory vs With Memory

**Without Memory:**
- Stateless chatbot
- Each message is independent
- Cannot remember previous conversations
- No personalization

**With Memory:**
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
6. **Model Switching**: In the memory-enabled chatbot, you can switch between different Bedrock models while retaining memory context
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

### Infrastructure

```
Client (Chatbot)
    ↓ HTTPS
API Gateway (public)
    ↓ VPC Link
Network Load Balancer (internal)
    ↓
EC2 Instance (MemMachine + PostgreSQL + Neo4j)
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
- Verify `MEMORY_SERVER_URL` is set to the API Gateway URL (not the EC2 IP)
- Check MemMachine is running via the API Gateway health endpoint
- Verify the CloudFormation stack completed successfully

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
- Try switching models in the memory-enabled chatbot to see memory persist across models
- Integrate with your own applications
- Explore advanced features (ProfileMemory, custom prompts)
- Review production considerations

## Resources

- [Workshop Guide](workshop_guide.mdx)
- [MemMachine Documentation](https://memmachine.ai/docs)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [GitHub Repository](https://github.com/MemMachine/MemMachine)

# AWS NYC Workshop - Quick Checklist

## Pre-Workshop Setup

### Prerequisites Check
- [ ] AWS Account with the following permissions:
  - **EC2**: `ec2:*` (Create/Describe VPCs, Subnets, Security Groups, Instances, Key Pairs, Internet Gateways, Route Tables)
  - **IAM**: `iam:CreateRole`, `iam:CreateInstanceProfile`, `iam:AttachRolePolicy`, `iam:PutRolePolicy`, `iam:PassRole`
  - **CloudFormation**: `cloudformation:*` (Create/Update/Delete stacks, Describe stacks/events)
  - **CloudWatch Logs**: `logs:CreateLogGroup`, `logs:PutRetentionPolicy`
  - **Elastic Load Balancing**: `elasticloadbalancing:*` (Create/Describe Load Balancers, Target Groups, Listeners)
  - **API Gateway**: `apigateway:*` (Create/Manage HTTP APIs, VPC Links, Integrations, Routes, Stages)
  - **Bedrock**: `bedrock:InvokeModel`, `bedrock:ListFoundationModels`, `bedrock:GetFoundationModel`
- [ ] AWS CLI installed (`aws --version`)
- [ ] AWS credentials configured (`aws sts get-caller-identity`)
- [ ] EC2 Key Pair created in your region
- [ ] Bedrock model access enabled
- [ ] Python 3.9+ installed (Python 3.9 or higher)

### Required Information
- [ ] AWS Access Key ID
- [ ] AWS Secret Access Key
- [ ] EC2 Key Pair name
- [ ] AWS Region (e.g., us-east-1)
- [ ] Bedrock model IDs (embedding & language)

---

## Part 1: Deploy MemMachine

### Step 1: CloudFormation Deployment
- [ ] Download `bedrock-cft.yml` template
- [ ] Set environment variables or prepare parameters
- [ ] Deploy stack via AWS CLI or Console
- [ ] Wait for stack creation (5-10 minutes)
- [ ] Retrieve stack outputs (PublicIP, URLs)

### Step 2: Verification
- [ ] Test health endpoint: `curl http://IP:8080/api/v2/health`
- [ ] Verify API docs accessible: `http://IP:8080/docs`
- [ ] Check Neo4j browser: `http://IP:7474`

**Key Outputs to Save:**
- PublicIP: `_____________`
- MemMachine URL: `http://_____________:8080`
- Neo4j URL: `http://_____________:7474`

---

## Part 2: Build Chatbot

### Step 1: Environment Setup
- [ ] Navigate to workshop directory: `cd workshop/aws_nyc`
- [ ] Create virtual environment (optional)
- [ ] Install dependencies: `pip install -r requirements.txt`
  - Includes: `boto3`, `requests`, `python-dotenv`, `streamlit`

### Step 2: Configuration
- [ ] Create `.env` file
- [ ] Set `MEMORY_SERVER_URL` (from Part 1)
- [ ] Set AWS credentials
- [ ] Set Bedrock model ID
- [ ] Set ORG_ID and PROJECT_ID

### Step 3: Chatbot Code
- [ ] Use `chatbot_before.py` (stateless, no memory - Streamlit web UI)
- [ ] Use `chatbot_after.py` (with MemMachine memory - Streamlit web UI)
- [ ] Test "BEFORE" chatbot: `streamlit run chatbot_before.py`
- [ ] Test "AFTER" chatbot: `streamlit run chatbot_after.py`
- [ ] Compare the difference in the web interface!
- [ ] Try switching models in "AFTER" chatbot dropdown

---

## Part 3: Compare Before & After

### Test "BEFORE" Chatbot (No Memory)
- [ ] Run: `streamlit run chatbot_before.py`
- [ ] Web interface opens in browser
- [ ] Send: "My name is [YourName]"
- [ ] Ask: "What's my name?"
- [ ] Notice: It doesn't remember! (This is expected)

### Test "AFTER" Chatbot (With Memory)
- [ ] Run: `streamlit run chatbot_after.py`
- [ ] Web interface opens in browser
- [ ] Send: "My name is [YourName]"
- [ ] Send: "I love [something]"
- [ ] Ask: "What's my name?"
- [ ] Verify chatbot remembers! ✨
- [ ] Try switching models using the dropdown
- [ ] Verify memory persists across model switches!

### Memory Persistence Test
- [ ] Restart chatbot
- [ ] Ask: "What did we talk about earlier?"
- [ ] Verify memory persists across sessions

### Advanced Test
- [ ] Have a multi-turn conversation
- [ ] Ask follow-up questions
- [ ] Verify context is maintained
- [ ] Switch models mid-conversation using dropdown
- [ ] Verify memory context is retained across different models
- [ ] Toggle "Show Memory Context" to see retrieved memories

---

## Part 4: Troubleshooting

### Common Issues
- [ ] **Connection refused**: Check security group, verify MemMachine running
- [ ] **Bedrock access denied**: Verify model access in AWS Console
- [ ] **Memory not working**: Check API responses, verify URLs
- [ ] **Stack creation failed**: Check CloudFormation events

### Verification Commands
```bash
# Test MemMachine
curl http://YOUR_IP:8080/api/v2/health

# Test Bedrock
aws bedrock list-foundation-models --region us-east-1

# Check stack status
aws cloudformation describe-stacks --stack-name YOUR_STACK_NAME
```

---

## Workshop Goals Checklist

By the end of the workshop, you should have:
- [ ] MemMachine deployed on AWS EC2
- [ ] Working chatbot using Bedrock
- [ ] Memory integration functional
- [ ] Understanding of memory flow
- [ ] Production-ready architecture pattern

---

## Quick Reference

### MemMachine API Endpoints
- Health: `GET /api/v2/health`
- Add Memory: `POST /api/v2/memories`
- Search Memories: `POST /api/v2/memories/search`
- List Memories: `POST /api/v2/memories/list`

### Key Environment Variables
```bash
MEMORY_SERVER_URL=http://IP:8080
ORG_ID=workshop-org
PROJECT_ID=workshop-project
USER_ID=workshop-user
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=openai.gpt-oss-20b-1:0
```

### Useful Commands
```bash
# Deploy stack
aws cloudformation create-stack ...

# Check status
aws cloudformation describe-stacks --stack-name YOUR_STACK

# Get outputs
aws cloudformation describe-stacks --stack-name YOUR_STACK --query 'Stacks[0].Outputs'

# Test API
curl http://IP:8080/api/v2/health
```

---

## Next Steps After Workshop

- [ ] Review production considerations (security, scaling)
- [ ] Explore advanced features (ProfileMemory, custom prompts)
- [ ] Customize the Streamlit web interface
- [ ] Integrate with your own applications
- [ ] Join MemMachine community (Discord, GitHub)

---

## Resources

- **Workshop Guide**: `workshop_guide.mdx` (in this directory)
- **MemMachine Docs**: https://memmachine.ai/docs
- **GitHub**: https://github.com/MemMachine/MemMachine
- **Discord**: https://discord.gg/usydANvKqD

---

**Workshop Date**: _____________  
**Your Name**: _____________  
**Stack Name**: _____________  
**Notes**: _____________


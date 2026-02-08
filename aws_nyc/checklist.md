# AWS NYC Workshop - Quick Checklist

## Pre-Workshop Setup

### Prerequisites Check
- [ ] AWS Account with the following IAM managed policies attached (or equivalent permissions):
  - `AmazonEC2FullAccess` — VPC, subnets, security groups, EC2 instances
  - `IAMFullAccess` — IAM roles and instance profiles for EC2
  - `AWSCloudFormationFullAccess` — stack create/update/delete
  - `CloudWatchLogsFullAccess` — log groups for MemMachine
  - `ElasticLoadBalancingFullAccess` — Network Load Balancer
  - `AmazonAPIGatewayAdministrator` — HTTP API, VPC Link, routes
  - `AmazonS3ReadOnlyAccess` — access CFT template from S3 (if hosted in a bucket)
  - `AmazonBedrockFullAccess` — model invocation and listing
- [ ] AWS CLI installed (`aws --version`)
- [ ] AWS credentials configured (`aws sts get-caller-identity`)
- [ ] EC2 Key Pair created in your region
- [ ] Bedrock model access enabled
- [ ] Python 3.9+ installed (Python 3.9 or higher)

### Required Information
- [ ] AWS Access Key ID
- [ ] AWS Secret Access Key
- [ ] EC2 Key Pair name
- [ ] AWS Region (e.g., us-west-2)
- [ ] Bedrock model IDs (embedding & language)

---

## Part 1: Deploy MemMachine

### Step 1: CloudFormation Deployment
- [ ] Locate `bedrock-cft.yml` template (included in this directory)
- [ ] Set environment variables or prepare parameters
- [ ] Deploy stack via AWS CLI or Console
- [ ] Wait for stack creation (5-10 minutes)
- [ ] Retrieve stack outputs (ApplicationURL, PublicIP, Neo4j URL)

### Step 2: Verification
- [ ] Test health endpoint via API Gateway: `curl https://YOUR_API_GATEWAY_URL/api/v2/health`
- [ ] Verify API docs accessible: `https://YOUR_API_GATEWAY_URL/docs`
- [ ] Check Neo4j browser: `http://PUBLIC_IP:7474`

> **Note:** Port 8080 on the EC2 instance is only accessible within the VPC. Use the API Gateway URL for all MemMachine API access.

**Key Outputs to Save:**
- ApplicationURL (API Gateway): `_____________`
- PublicIP: `_____________`
- Neo4j URL: `http://_____________:7474`

---

## Part 2: Build Chatbot

### Step 1: Environment Setup
- [ ] Navigate to workshop directory: `cd aws_nyc`
- [ ] Create virtual environment (optional)
- [ ] Install dependencies: `pip install -r requirements.txt`
  - Includes: `boto3`, `requests`, `python-dotenv`, `streamlit`

### Step 2: Configuration
- [ ] Copy `.env.example` to `.env`
- [ ] Set `MEMORY_SERVER_URL` to the **ApplicationURL** (API Gateway URL) from Part 1
- [ ] Set AWS credentials
- [ ] Set Bedrock model ID
- [ ] Set ORG_ID and PROJECT_ID

### Step 3: Chatbot Code
- [ ] Use `without_memory.py` (stateless, no memory - Streamlit web UI)
- [ ] Use `with_memory.py` (with MemMachine memory - Streamlit web UI)
- [ ] Test chatbot without memory: `streamlit run without_memory.py`
- [ ] Test chatbot with memory: `streamlit run with_memory.py`
- [ ] Compare the difference in the web interface!
- [ ] Try switching models in the memory-enabled chatbot dropdown

---

## Part 3: Compare Without vs With Memory

### Test Chatbot Without Memory
- [ ] Run: `streamlit run without_memory.py`
- [ ] Web interface opens in browser
- [ ] Send: "My name is [YourName]"
- [ ] Ask: "What's my name?"
- [ ] Notice: It doesn't remember! (This is expected)

### Test Chatbot With Memory
- [ ] Run: `streamlit run with_memory.py`
- [ ] Web interface opens in browser
- [ ] Send: "My name is [YourName]"
- [ ] Send: "I love [something]"
- [ ] Ask: "What's my name?"
- [ ] Verify chatbot remembers!
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
- [ ] **Connection refused**: Verify `MEMORY_SERVER_URL` is the API Gateway URL (not the EC2 IP directly)
- [ ] **Bedrock access denied**: Verify model access in AWS Console
- [ ] **Memory not working**: Check API responses, verify URLs
- [ ] **Stack creation failed**: Check CloudFormation events

### Verification Commands
```bash
# Test MemMachine via API Gateway
curl https://YOUR_API_GATEWAY_URL/api/v2/health

# Test MemMachine directly (only works from within the VPC / SSH into EC2)
# curl http://localhost:8080/api/v2/health

# Test Bedrock
aws bedrock list-foundation-models --region us-west-2

# Check stack status
aws cloudformation describe-stacks --stack-name YOUR_STACK_NAME

# Get stack outputs (including ApplicationURL)
aws cloudformation describe-stacks --stack-name YOUR_STACK_NAME --query 'Stacks[0].Outputs'
```

---

## Workshop Goals Checklist

By the end of the workshop, you should have:
- [ ] MemMachine deployed on AWS EC2 (with API Gateway)
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
MEMORY_SERVER_URL=https://YOUR_API_GATEWAY_URL
ORG_ID=workshop-org
PROJECT_ID=workshop-project
USER_ID=workshop-user
AWS_REGION=us-west-2
BEDROCK_MODEL_ID=openai.gpt-oss-20b-1:0
```

### CloudFormation Template Parameters
```
StackName              - Name for the stack (default: memmachine-bedrock-ec2-stack)
InstanceType           - EC2 instance type (default: t3.xlarge)
KeyPairName            - EC2 key pair for SSH access
PostgresPassword       - PostgreSQL password (min 8 chars)
Neo4jPassword          - Neo4j password (min 8 chars)
AwsAccessKeyId         - AWS Access Key ID for Bedrock
AwsSecretAccessKey     - AWS Secret Access Key for Bedrock
AwsRegion              - AWS region for Bedrock (default: us-west-2)
BedrockEmbeddingModel  - Embedding model ID (default: amazon.titan-embed-text-v2:0)
BedrockLanguageModel   - Language model ID (default: openai.gpt-oss-20b-1:0)
AllowedCIDR            - CIDR for SSH/Neo4j access (default: 0.0.0.0/0)
```

### Useful Commands
```bash
# Deploy stack
aws cloudformation create-stack \
    --stack-name memmachine-workshop \
    --template-body file://bedrock-cft.yml \
    --parameters ParameterKey=KeyPairName,ParameterValue=YOUR_KEY \
                 ParameterKey=PostgresPassword,ParameterValue=YOUR_PW \
                 ParameterKey=Neo4jPassword,ParameterValue=YOUR_PW \
                 ParameterKey=AwsAccessKeyId,ParameterValue=YOUR_KEY_ID \
                 ParameterKey=AwsSecretAccessKey,ParameterValue=YOUR_SECRET \
                 ParameterKey=AwsRegion,ParameterValue=us-west-2 \
    --capabilities CAPABILITY_NAMED_IAM \
    --region us-west-2

# Check status
aws cloudformation describe-stacks --stack-name YOUR_STACK

# Get outputs
aws cloudformation describe-stacks --stack-name YOUR_STACK --query 'Stacks[0].Outputs'

# Test API via API Gateway
curl https://YOUR_API_GATEWAY_URL/api/v2/health
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
- **CloudFormation Template**: `bedrock-cft.yml` (in this directory)
- **MemMachine Docs**: https://memmachine.ai/docs
- **GitHub**: https://github.com/MemMachine/MemMachine
- **Discord**: https://discord.gg/usydANvKqD

---

**Workshop Date**: _____________
**Your Name**: _____________
**Stack Name**: _____________
**API Gateway URL**: _____________
**Notes**: _____________

# AI Travel Companion - Capstone Project

## Overview
Build a production-ready AI Travel Companion using Amazon Bedrock AgentCore that helps users plan complete travel itineraries with intelligent budget allocation, preference memory, and comprehensive research capabilities.

## Quick Start
1. **Prerequisites**: AWS Account, Python 3.9+, Node.js 18+
2. **Setup**: Follow notebooks in order (01-foundation → 09-optimization)
3. **Deploy**: Use provided CDK templates for AWS deployment
4. **Monitor**: Access CloudWatch dashboards for observability

## Project Structure
```
capstone-project/
├── notebooks/              # Step-by-step implementation
│   ├── 01-foundation.ipynb
│   ├── 02-runtime-setup.ipynb
│   ├── 03-gateway-integration.ipynb
│   ├── 04-memory-implementation.ipynb
│   ├── 05-identity-oauth.ipynb
│   ├── 06-code-interpreter.ipynb
│   ├── 07-browser-tools.ipynb
│   ├── 08-observability.ipynb
│   └── 09-optimization.ipynb
├── backend/                # Python AgentCore implementation
├── frontend/               # TypeScript + React UI
├── infrastructure/         # AWS CDK deployment
├── docs/                  # Additional documentation
└── monitoring/            # CloudWatch configurations
```

## Learning Path
Each notebook builds upon the previous, teaching AgentCore components progressively:

**Phase 1**: Foundation & Runtime  
**Phase 2**: Gateway & Memory  
**Phase 3**: Identity & Code Interpreter  
**Phase 4**: Browser Tools & Observability  
**Phase 5**: Production Deployment & Optimization  

## Key Features Implemented
- ✅ Conversational travel planning with clarifying questions
- ✅ User preference memory (hotel types, food preferences)
- ✅ Flight and hotel search integration
- ✅ Budget optimization calculations
- ✅ Attraction research and review analysis
- ✅ Google Drive itinerary storage
- ✅ Real-time monitoring and observability

## Expected Outcomes
Upon completion, you'll have:
1. A fully deployed AI Travel Companion on AWS
2. Mastery of all 7 AgentCore components
3. Production-ready code with monitoring
4. A portfolio-worthy project demonstrating AI agent capabilities

## Support
- 📚 Comprehensive documentation in each notebook
- 🔧 Starter code and templates provided
- 📊 CloudWatch dashboards for debugging
- 💬 Discussion forums for questions

Start with `notebooks/01-foundation.ipynb` to begin your journey!
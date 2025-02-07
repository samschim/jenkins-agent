# Jenkins LangChain Agent System

Welcome to the Jenkins LangChain Agent System documentation. This system provides an intelligent, AI-powered management interface for Jenkins CI/CD servers.

## Overview

The Jenkins LangChain Agent System is a multi-agent architecture that uses Large Language Models (LLMs) to automate and enhance Jenkins management tasks. The system consists of specialized agents that work together to handle different aspects of Jenkins administration.

## Key Features

- 🤖 **Intelligent Task Routing**: Uses embeddings to route tasks to specialized agents
- 📊 **Comprehensive Metrics**: Collects and analyzes build and pipeline metrics
- 🔍 **Log Analysis**: AI-powered analysis of build logs and error patterns
- 🔄 **Pipeline Management**: Automated pipeline creation and optimization
- 🔌 **Plugin Management**: Smart plugin installation and configuration
- 👥 **User Management**: Handles user permissions and access control

## Quick Links

- [Architecture Overview](Architecture)
- [Getting Started](Getting-Started)
- [Configuration Guide](Configuration)
- [Agent Documentation](Agents)
- [API Reference](API-Reference)
- [Deployment Guide](Deployment)
- [Contributing Guide](Contributing)

## System Requirements

- Python 3.8+
- Jenkins server with API access
- OpenAI API key (for LLM functionality)
- Redis (for caching and rate limiting)
- MongoDB (for data persistence)

## Installation

```bash
# Clone the repository
git clone https://github.com/samschim/jenkins-agent.git

# Install dependencies
cd jenkins-agent
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run the system
python -m langchain_jenkins.main
```

## Basic Usage

```python
from langchain_jenkins.agents.supervisor import SupervisorAgent

# Initialize the supervisor agent
supervisor = SupervisorAgent()

# Handle a task
result = await supervisor.handle_task("Create a new pipeline for Python project")

# Get system insights
insights = await supervisor.collect_metrics_and_insights()
```

## Support

For issues and feature requests, please use our [GitHub Issues](https://github.com/samschim/jenkins-agent/issues) page.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
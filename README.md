# Jenkins LangChain Agent System

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests](https://github.com/samschim/jenkins-agent/actions/workflows/tests.yml/badge.svg)](https://github.com/samschim/jenkins-agent/actions/workflows/tests.yml)
[![Docker](https://github.com/samschim/jenkins-agent/actions/workflows/docker.yml/badge.svg)](https://github.com/samschim/jenkins-agent/actions/workflows/docker.yml)

<img src="docs/images/logo.png" alt="Jenkins LangChain Agent" width="200"/>

*An intelligent, AI-powered management system for Jenkins CI/CD servers using LangChain and Large Language Models.*

[Getting Started](#getting-started) •
[Documentation](#documentation) •
[Features](#features) •
[Contributing](#contributing) •
[Support](#support)

</div>

---

## 🌟 Highlights

- 🤖 **Natural Language Interface**: Control Jenkins using plain English
- 🔄 **Intelligent Automation**: AI-powered pipeline and build management
- 🔍 **Smart Analysis**: Automated log analysis and error detection
- 📊 **Comprehensive Metrics**: Real-time insights and recommendations
- 🛡️ **Security First**: Built-in security scanning and best practices

## 🚀 Features

### 🤖 Intelligent Task Routing
- Embedding-based task assignment
- Multi-agent coordination
- Natural language processing
- Context-aware responses

### 📊 Pipeline Management
- Automated pipeline generation
- Security scanning and hardening
- Performance optimization
- Template-based customization

### 🔍 Build Management
- Build optimization
- Resource utilization analysis
- Dependency management
- Build prediction

### 📈 System Insights
- Comprehensive metrics collection
- Performance analysis
- Automated recommendations
- Trend analysis

### 🎯 User Interfaces
- Interactive chat mode
- Rich CLI interface
- Modern web dashboard
- Real-time updates

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- Jenkins server with API access
- OpenAI API key
- Redis server (optional, for caching)
- MongoDB (optional, for persistence)

### Quick Start

1. Install using pip:
```bash
pip install jenkins-langchain-agent
```

2. Or clone and install:
```bash
# Clone repository
git clone https://github.com/samschim/jenkins-agent.git
cd jenkins-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

3. Configure environment:
```bash
# Copy example configuration
cp .env.example .env

# Edit configuration
vim .env
```

4. Start the system:
```bash
# Start with basic configuration
python -m langchain_jenkins.main

# Or use Docker
docker-compose up -d
```

## 💻 Usage

### Interactive Chat Mode
```bash
# Start chat mode
jenkins-agent chat

> Create a new pipeline for Python project
Creating pipeline...
Pipeline created successfully!

> Analyze build logs for my-project
Analyzing logs...
Found 3 potential issues...
```

### Command Line Interface
```bash
# Create a job
jenkins-agent create-job my-project --type python --with-tests

# Trigger a build
jenkins-agent build my-project

# Analyze logs
jenkins-agent analyze my-project

# Show metrics
jenkins-agent metrics
```

### Python API
```python
from langchain_jenkins.agents.supervisor import SupervisorAgent

# Initialize supervisor
supervisor = SupervisorAgent()

# Handle tasks
async def main():
    # Create a pipeline
    result = await supervisor.handle_task(
        "Create a new pipeline for Java project with testing"
    )
    print(result)
    
    # Analyze build logs
    result = await supervisor.handle_task(
        "Analyze build logs for my-project"
    )
    print(result)
    
    # Get system insights
    insights = await supervisor.collect_metrics_and_insights()
    print(insights)

# Run tasks
import asyncio
asyncio.run(main())
```

### Web API
```bash
# Start the web server
python -m langchain_jenkins.web.app

# Use the API
curl -X POST http://localhost:8000/api/v1/tasks \
    -H "Content-Type: application/json" \
    -d '{"task": "Create a new build job named my-project"}'
```

## 📚 Documentation

- [Getting Started Guide](docs/wiki/Getting-Started.md)
- [Architecture Overview](docs/wiki/Architecture.md)
- [Configuration Guide](docs/wiki/Configuration.md)
- [API Reference](docs/wiki/API-Reference.md)
- [Development Guide](docs/wiki/Development-Guide.md)

## 🧪 Testing

Run the test suite:
```bash
# Run all tests
pytest

# Run specific test files
pytest tests/unit/
pytest tests/integration/

# Run with coverage
pytest --cov=langchain_jenkins
```

## 🔧 Configuration

The system can be configured using environment variables or a `.env` file:

```bash
# Jenkins Configuration
JENKINS_URL=http://your-jenkins-server:8080
JENKINS_USER=your-username
JENKINS_API_TOKEN=your-api-token

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key

# Optional: Redis Configuration
REDIS_URL=redis://localhost:6379

# Optional: MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=jenkins_agent
```

## 🐳 Docker Support

Run with Docker:
```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Or use the provided Kubernetes manifests:
```bash
# Deploy to Kubernetes
kubectl apply -f k8s/
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. Make your changes
4. Run tests
   ```bash
   pytest
   ```
5. Submit a pull request

## 📝 Code Style

We use [Black](https://github.com/psf/black) for code formatting:
```bash
# Install Black
pip install black

# Format code
black .
```

## 🔒 Security

- Never commit sensitive credentials
- Use environment variables for secrets
- Keep dependencies updated
- Follow security best practices

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [LangChain](https://github.com/hwchase17/langchain)
- [OpenAI](https://openai.com/)
- [Jenkins](https://www.jenkins.io/)

## 📧 Support

For support and questions:
- Create an [Issue](https://github.com/samschim/jenkins-agent/issues)
- Join our [Discord Community](https://discord.gg/jenkins-agent)
- Contact [support@jenkins-agent.com](mailto:support@jenkins-agent.com)

## 🗺️ Roadmap

See our [Roadmap](ROADMAP.md) for planned features and improvements.

## 📊 Project Status

- [x] Core Agent System
- [x] Pipeline Management
- [x] Build Management
- [x] User Interfaces
- [x] Documentation
- [ ] Advanced Analytics
- [ ] Machine Learning Integration
- [ ] Cloud Provider Integration

## 📈 Metrics

![Build Status](https://img.shields.io/jenkins/build?jobUrl=https%3A%2F%2Fjenkins.example.com%2Fjob%2Fjenkins-agent)
![Coverage](https://img.shields.io/codecov/c/github/samschim/jenkins-agent)
![Dependencies](https://img.shields.io/librariesio/github/samschim/jenkins-agent)

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=samschim/jenkins-agent&type=Date)](https://star-history.com/#samschim/jenkins-agent&Date)

---

<div align="center">
Made with ❤️ by the Jenkins LangChain Agent Team
</div>
#!/bin/bash

####################################################
# Enhanced Jenkins Setup Script                     #
# Features:                                         #
# - Local LLM support with LM Studio               #
# - Advanced CI/CD pipelines                       #
# - GitHub Actions integration                      #
# - Multi-agent configuration                      #
# - Security hardening                             #
####################################################

# Strict error handling
set -euo pipefail

# Default values
JENKINS_PORT=8080
JENKINS_AGENT_PORT=50000
LM_STUDIO_PORT=1234
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000

# Load environment variables
if [ -f .env ]; then
    source .env
fi

# Required environment variables
: "${GITHUB_USERNAME:?Environment variable GITHUB_USERNAME is required}"
: "${GITHUB_TOKEN:?Environment variable GITHUB_TOKEN is required}"
: "${LOCAL_REPO_PATH:?Environment variable LOCAL_REPO_PATH is required}"
: "${LM_STUDIO_MODEL:=mistral-7b-instruct-v0.2.Q4_K_M.gguf}"

# Function to log messages with timestamps
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to install Docker
install_docker() {
    log_message "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    sudo systemctl enable docker
    sudo systemctl start docker
    rm get-docker.sh
}

# Function to install monitoring stack
install_monitoring() {
    log_message "Setting up monitoring stack..."
    
    # Create monitoring network
    docker network create monitoring || true
    
    # Start Prometheus
    docker run -d \
        --name prometheus \
        --network monitoring \
        --restart unless-stopped \
        -p $PROMETHEUS_PORT:9090 \
        -v $PWD/prometheus.yml:/etc/prometheus/prometheus.yml \
        prom/prometheus
    
    # Start Grafana
    docker run -d \
        --name grafana \
        --network monitoring \
        --restart unless-stopped \
        -p $GRAFANA_PORT:3000 \
        -v grafana-storage:/var/lib/grafana \
        grafana/grafana
}

# Function to create Jenkins configuration
create_jenkins_config() {
    log_message "Creating Jenkins configuration..."
    
    # Create Jenkins configuration directory
    sudo mkdir -p /var/lib/jenkins/init.groovy.d
    
    # Create security configuration
    cat << 'EOF' | sudo tee /var/lib/jenkins/init.groovy.d/security.groovy
import jenkins.model.*
import hudson.security.*
import jenkins.security.s2m.AdminWhitelistRule

def instance = Jenkins.getInstance()

// Enable CSRF protection
instance.setCrumbIssuer(new DefaultCrumbIssuer(true))

// Enable agent to master security
instance.getInjector().getInstance(AdminWhitelistRule.class).setMasterKillSwitch(false)

// Configure security realm
def realm = new HudsonPrivateSecurityRealm(false)
instance.setSecurityRealm(realm)

// Configure authorization
def strategy = new GlobalMatrixAuthorizationStrategy()
strategy.add(Jenkins.ADMINISTER, "admin")
instance.setAuthorizationStrategy(strategy)

instance.save()
EOF

    # Create agent configuration
    cat << 'EOF' | sudo tee /var/lib/jenkins/init.groovy.d/agents.groovy
import jenkins.model.*
import hudson.model.*
import hudson.slaves.*
import hudson.plugins.sshslaves.*

// Create agent configurations
def createAgent(String name, String description, int executors, String remotePath) {
    def launcher = new SSHLauncher(
        "localhost",           // Host
        22,                    // Port
        "jenkins-agent",       // Credentials ID
        "",                   // JVM Options
        null,                 // JavaPath
        "",                   // Prefix Start Agent Command
        "",                   // Suffix Start Agent Command
        60,                   // Launch Timeout
        3,                    // Maximum Number of Retries
        15,                   // Retry Wait Time
        new NonVerifyingKeyVerificationStrategy()
    )
    
    def agent = new DumbSlave(
        name,
        description,
        remotePath,
        String.valueOf(executors),
        Node.Mode.NORMAL,
        "",                   // Labels
        launcher,
        RetentionStrategy.INSTANCE
    )
    
    Jenkins.instance.addNode(agent)
}

// Create agents
createAgent("agent1", "Build Agent 1", 2, "/home/jenkins/agent1")
createAgent("agent2", "Build Agent 2", 2, "/home/jenkins/agent2")
createAgent("llm-agent", "LLM Processing Agent", 1, "/home/jenkins/llm-agent")
EOF
}

# Function to create pipeline templates
create_pipeline_templates() {
    log_message "Creating pipeline templates..."
    
    # Create pipeline library
    mkdir -p "$LOCAL_REPO_PATH/jenkins-pipeline-library/vars"
    
    # Create shared library for LLM integration
    cat << 'EOF' > "$LOCAL_REPO_PATH/jenkins-pipeline-library/vars/llmAnalyze.groovy"
def call(Map config = [:]) {
    def text = config.text ?: ''
    def endpoint = config.endpoint ?: 'http://localhost:1234/v1/completions'
    
    def response = sh(script: """
        curl -X POST ${endpoint} \
            -H 'Content-Type: application/json' \
            -d '{
                "prompt": "${text}",
                "max_tokens": 500,
                "temperature": 0.7
            }'
    """, returnStdout: true)
    
    return readJSON(text: response).choices[0].text
}
EOF

    # Create standard pipeline template
    cat << 'EOF' > "$LOCAL_REPO_PATH/jenkins-pipeline-library/vars/standardPipeline.groovy"
def call(Map config = [:]) {
    pipeline {
        agent {
            label config.agent ?: 'any'
        }
        
        options {
            timestamps()
            ansiColor('xterm')
            buildDiscarder(logRotator(numToKeepStr: '10'))
            timeout(time: 1, unit: 'HOURS')
        }
        
        environment {
            GITHUB_TOKEN = credentials('github-token')
        }
        
        stages {
            stage('Checkout') {
                steps {
                    checkout scm
                }
            }
            
            stage('Code Analysis') {
                parallel {
                    stage('Static Analysis') {
                        steps {
                            sh 'sonar-scanner'
                        }
                    }
                    stage('LLM Analysis') {
                        agent {
                            label 'llm-agent'
                        }
                        steps {
                            script {
                                def code = readFile('.')
                                def analysis = llmAnalyze(
                                    text: "Analyze this code for potential issues:\n${code}",
                                    endpoint: 'http://localhost:1234/v1/completions'
                                )
                                writeFile file: 'llm-analysis.txt', text: analysis
                            }
                        }
                    }
                }
            }
            
            stage('Build') {
                steps {
                    script {
                        if (fileExists('package.json')) {
                            sh 'npm install && npm run build'
                        } else if (fileExists('requirements.txt')) {
                            sh 'pip install -r requirements.txt'
                            sh 'python setup.py build'
                        }
                    }
                }
            }
            
            stage('Test') {
                steps {
                    script {
                        if (fileExists('package.json')) {
                            sh 'npm test'
                        } else if (fileExists('requirements.txt')) {
                            sh 'python -m pytest'
                        }
                    }
                }
            }
            
            stage('Security Scan') {
                steps {
                    sh 'trivy fs .'
                }
            }
            
            stage('Deploy') {
                when {
                    branch 'main'
                }
                steps {
                    script {
                        if (fileExists('docker-compose.yml')) {
                            sh 'docker-compose up -d'
                        } else if (fileExists('Dockerfile')) {
                            sh 'docker build -t ${JOB_NAME}:${BUILD_NUMBER} .'
                            sh 'docker push ${JOB_NAME}:${BUILD_NUMBER}'
                        }
                    }
                }
            }
        }
        
        post {
            always {
                archiveArtifacts artifacts: 'llm-analysis.txt', allowEmptyArchive: true
                junit '**/test-results/*.xml'
            }
            success {
                script {
                    if (env.BRANCH_NAME == 'main') {
                        def message = "Build #${BUILD_NUMBER} successful!\n"
                        message += "Job: ${JOB_NAME}\n"
                        message += "See: ${BUILD_URL}"
                        
                        sh """
                            curl -X POST ${DISCORD_WEBHOOK_URL} \
                                -H 'Content-Type: application/json' \
                                -d '{"content": "${message}"}'
                        """
                    }
                }
            }
            failure {
                script {
                    def analysis = llmAnalyze(
                        text: "Analyze this build failure:\n${currentBuild.rawBuild.getLog(100).join('\n')}",
                        endpoint: 'http://localhost:1234/v1/completions'
                    )
                    
                    emailext(
                        subject: "Build Failed: ${JOB_NAME} #${BUILD_NUMBER}",
                        body: "Build failed. AI Analysis:\n\n${analysis}\n\nSee: ${BUILD_URL}",
                        recipientProviders: [developers(), requestor()]
                    )
                }
            }
        }
    }
}
EOF
}

# Function to create GitHub Actions workflow templates
create_github_workflows() {
    log_message "Creating GitHub Actions workflow templates..."
    
    # Create .github/workflows directory
    mkdir -p "$LOCAL_REPO_PATH/.github/workflows"
    
    # Create CI workflow
    cat << 'EOF' > "$LOCAL_REPO_PATH/.github/workflows/ci.yml"
name: CI Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Code Analysis
        uses: github/codeql-action/analyze@v2
        with:
          languages: python, javascript
      
      - name: LLM Analysis
        env:
          LM_STUDIO_URL: http://localhost:1234
        run: |
          curl -X POST ${LM_STUDIO_URL}/v1/completions \
            -H "Content-Type: application/json" \
            -d '{
              "prompt": "Analyze this code for potential issues:\n$(cat $(find . -type f -name "*.py" -o -name "*.js"))",
              "max_tokens": 500
            }' > llm-analysis.txt
      
      - name: Upload Analysis
        uses: actions/upload-artifact@v3
        with:
          name: code-analysis
          path: llm-analysis.txt

  test:
    needs: analyze
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Run tests
        run: |
          python -m pytest --junitxml=test-results.xml
      
      - name: Upload test results
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: test-results.xml

  security:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          format: 'sarif'
          output: 'trivy-results.sarif'
      
      - name: Upload security results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'

  deploy:
    if: github.ref == 'refs/heads/main'
    needs: [test, security]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build and push Docker image
        uses: docker/build-push-action@v4
        with:
          push: true
          tags: ${{ github.repository }}:${{ github.sha }}
      
      - name: Deploy to staging
        run: |
          echo "Deploying to staging environment..."
          # Add deployment steps here
EOF
}

# Main installation process
main() {
    log_message "Starting enhanced Jenkins setup..."
    
    # System updates
    sudo apt update && sudo apt upgrade -y
    
    # Install basic requirements
    sudo apt install -y \
        openjdk-17-jdk \
        git \
        curl \
        wget \
        jq \
        docker.io \
        docker-compose
    
    # Install Docker if not present
    if ! command -v docker &> /dev/null; then
        install_docker
    fi
    
    # Install monitoring stack
    install_monitoring
    
    # Install Jenkins
    log_message "Installing Jenkins..."
    curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | sudo tee /usr/share/keyrings/jenkins-keyring.asc > /dev/null
    echo deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/ | sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null
    sudo apt update
    sudo apt install -y jenkins
    
    # Configure Jenkins
    create_jenkins_config
    
    # Start Jenkins
    sudo systemctl enable jenkins
    sudo systemctl start jenkins
    
    # Wait for Jenkins to start
    log_message "Waiting for Jenkins to start..."
    until curl -s http://localhost:$JENKINS_PORT > /dev/null; do
        sleep 5
    done
    
    # Get initial admin password
    JENKINS_PASSWORD=$(sudo cat /var/lib/jenkins/secrets/initialAdminPassword)
    
    # Install Jenkins plugins
    log_message "Installing Jenkins plugins..."
    JENKINS_URL="http://localhost:$JENKINS_PORT"
    JENKINS_USER="admin"
    
    wget $JENKINS_URL/jnlpJars/jenkins-cli.jar
    
    java -jar jenkins-cli.jar -s $JENKINS_URL -auth admin:$JENKINS_PASSWORD install-plugin \
        workflow-aggregator \
        git \
        github \
        github-branch-source \
        pipeline-github-lib \
        docker-workflow \
        kubernetes \
        job-dsl \
        configuration-as-code \
        prometheus \
        discord-notifier \
        email-ext \
        ansicolor \
        timestamper \
        ws-cleanup \
        -deploy
    
    # Create pipeline templates
    create_pipeline_templates
    
    # Create GitHub workflows
    create_github_workflows
    
    # Final configuration
    log_message "Performing final configuration..."
    
    # Create Jenkins jobs
    java -jar jenkins-cli.jar -s $JENKINS_URL -auth admin:$JENKINS_PASSWORD \
        create-job global-pipeline-library << 'EOF'
<?xml version='1.1' encoding='UTF-8'?>
<org.jenkinsci.plugins.workflow.libs.GlobalLibraries plugin="workflow-cps-global-lib@2.19">
  <libraries>
    <org.jenkinsci.plugins.workflow.libs.LibraryConfiguration>
      <name>pipeline-library</name>
      <retriever class="org.jenkinsci.plugins.workflow.libs.SCMSourceRetriever">
        <scm class="jenkins.plugins.git.GitSCMSource">
          <remote>${LOCAL_REPO_PATH}/jenkins-pipeline-library</remote>
        </scm>
      </retriever>
      <defaultVersion>main</defaultVersion>
      <implicit>true</implicit>
      <allowVersionOverride>true</allowVersionOverride>
    </org.jenkinsci.plugins.workflow.libs.LibraryConfiguration>
  </libraries>
</org.jenkinsci.plugins.workflow.libs.GlobalLibraries>
EOF
    
    # Final message
    log_message "Setup complete!"
    log_message "Jenkins URL: http://localhost:$JENKINS_PORT"
    log_message "Initial admin password: $JENKINS_PASSWORD"
    log_message "LM Studio URL: http://localhost:$LM_STUDIO_PORT"
    log_message "Prometheus URL: http://localhost:$PROMETHEUS_PORT"
    log_message "Grafana URL: http://localhost:$GRAFANA_PORT"
}

# Run main installation
main
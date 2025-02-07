#!/bin/bash

####################################################
# To use this script:                              #
# 1. Create a .env file with your credentials:     #
# GITHUB_USERNAME="your-username"                  #
# GITHUB_TOKEN="your-token"                        #
# LOCAL_REPO_PATH="/path/to/repos"                 #
# 2. Make the script executable:                   #
# chmod +x setup-jenkins.sh                        #
# 3. Run the script:                              #
# sudo bash -c 'source .env && ./setup-jenkins.sh' #
####################################################

# Strict error handling
set -euo pipefail

# Function to log messages with timestamps
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check and install UFW
check_install_ufw() {
    if ! command -v ufw >/dev/null 2>&1; then
        log_message "UFW not found. Installing UFW..."
        sudo apt update
        sudo apt install -y ufw
        log_message "UFW installation completed."
    else
        log_message "UFW is already installed."
    fi
}

# Function to wait for Jenkins and handle initial setup
wait_for_jenkins() {
    local max_attempts=120  # Increased to 120 (40 minutes total)
    local attempt=1
    local jenkins_url="http://localhost:8080"
    
    log_message "Waiting for Jenkins to initialize..."
    
    # Wait for Jenkins to create admin password file
    while [ ! -f /var/lib/jenkins/secrets/initialAdminPassword ] && [ $attempt -le $max_attempts ]; do
        log_message "Waiting for Jenkins to create admin password (attempt $attempt/$max_attempts)..."
        sleep 20
        attempt=$((attempt + 1))
    done
    
    if [ ! -f /var/lib/jenkins/secrets/initialAdminPassword ]; then
        log_message "Error: Jenkins failed to create admin password file"
        exit 1
    fi
    
    # Get the initial admin password
    JENKINS_PASSWORD=$(sudo cat /var/lib/jenkins/secrets/initialAdminPassword)
    log_message "Initial Admin Password: $JENKINS_PASSWORD"
    
    # Reset attempt counter for URL check
    attempt=1
    
    # Wait for Jenkins to be available
    log_message "Waiting for Jenkins to become available..."
    while [ $attempt -le $max_attempts ]; do
        if curl -s -o /dev/null -w "%{http_code}" "$jenkins_url" | grep -q "403\|200"; then
            log_message "Jenkins is now available!"
            # Add additional wait time for Jenkins to fully initialize
            sleep 60
            return 0
        fi
        log_message "Attempt $attempt/$max_attempts - Jenkins is not ready yet..."
        sleep 20
        attempt=$((attempt + 1))
    done
    
    log_message "Error: Jenkins failed to become available after $(($max_attempts * 20)) seconds"
    exit 1
}

# Function to install plugins with retry mechanism
install_jenkins_plugins() {
    local max_retries=5  # Increased retries
    local retry=0
    local plugins=("$@")
    
    while [ $retry -lt $max_retries ]; do
        if java -jar jenkins-cli.jar -s $JENKINS_URL -auth $JENKINS_USER:$JENKINS_PASSWORD install-plugin "${plugins[@]}" -deploy; then
            log_message "Plugins installed successfully"
            return 0
        else
            retry=$((retry + 1))
            log_message "Plugin installation failed. Attempt $retry of $max_retries"
            sleep 60  # Increased wait time between retries
        fi
    done
    
    log_message "Failed to install plugins after $max_retries attempts"
    exit 1
}

# Function to process repositories in batches
process_repositories() {
    local repos="$1"
    local batch_size=10
    local total_repos=$(echo "$repos" | wc -l)
    local current=0
    
    log_message "Processing $total_repos repositories in batches of $batch_size..."
    
    while IFS= read -r repo; do
        [ -z "$repo" ] && continue
        
        current=$((current + 1))
        repo_name=$(basename "$repo" .git)
        
        # Clone repository if it doesn't exist
        if [ ! -d "$LOCAL_REPO_PATH/$repo_name" ]; then
            log_message "[$current/$total_repos] Cloning $repo_name..."
            git clone "$repo" "$LOCAL_REPO_PATH/$repo_name" || {
                log_message "Warning: Failed to clone $repo_name, continuing..."
                continue
            }
        fi
        
        # Set up webhook
        log_message "[$current/$total_repos] Setting up webhook for $repo_name..."
        curl -X POST -H "Authorization: token $GITHUB_TOKEN" \
            -H "Accept: application/vnd.github.v3+json" \
            "https://api.github.com/repos/$GITHUB_USERNAME/$repo_name/hooks" \
            -d '{
                "name": "web",
                "active": true,
                "events": ["push", "pull_request"],
                "config": {
                    "url": "'"$JENKINS_URL"'/github-webhook/",
                    "content_type": "json"
                }
            }' || log_message "Warning: Failed to create webhook for $repo_name"
        
        # Sleep after each batch
        if [ $((current % batch_size)) -eq 0 ]; then
            log_message "Processed $current/$total_repos repositories. Waiting..."
            sleep 30
        fi
    done <<< "$repos"
}

## Function to add GitHub credentials with retry mechanism
add_github_credentials() {
    local max_retries=5
    local retry=0
    local wait_time=30
    
    log_message "Adding GitHub credentials to Jenkins..."
    
    while [ $retry -lt $max_retries ]; do
        # Test Jenkins CLI connectivity first
        if ! java -jar jenkins-cli.jar -s $JENKINS_URL -auth $JENKINS_USER:$JENKINS_PASSWORD who-am-i; then
            log_message "Jenkins CLI connection test failed. Retrying in $wait_time seconds... (Attempt $((retry + 1))/$max_retries)"
            sleep $wait_time
            retry=$((retry + 1))
            continue
        fi
        
        # Create temporary credentials file
        local temp_cred_file=$(mktemp)
        echo '<com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl>
  <scope>GLOBAL</scope>
  <id>github-credentials</id>
  <description>GitHub Credentials</description>
  <username>'"$GITHUB_USERNAME"'</username>
  <password>'"$GITHUB_TOKEN"'</password>
</com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl>' > "$temp_cred_file"

        # Try to add credentials with timeout
        if timeout 30s java -jar jenkins-cli.jar -s $JENKINS_URL -auth $JENKINS_USER:$JENKINS_PASSWORD \
            create-credentials-by-xml system::system::jenkins _ < "$temp_cred_file"; then
            rm -f "$temp_cred_file"
            log_message "GitHub credentials added successfully!"
            return 0
        fi
        
        rm -f "$temp_cred_file"
        log_message "Failed to add GitHub credentials. Retrying in $wait_time seconds... (Attempt $((retry + 1))/$max_retries)"
        sleep $wait_time
        retry=$((retry + 1))
    done
    
    log_message "Failed to add GitHub credentials after $max_retries attempts"
    return 1
}

# Function to verify Jenkins is fully operational
verify_jenkins_ready() {
    local max_attempts=30
    local attempt=1
    local wait_time=20
    
    log_message "Verifying Jenkins is fully operational..."
    
    while [ $attempt -le $max_attempts ]; do
        # Try a simple Jenkins CLI command
        if java -jar jenkins-cli.jar -s $JENKINS_URL -auth $JENKINS_USER:$JENKINS_PASSWORD who-am-i >/dev/null 2>&1; then
            log_message "Jenkins is fully operational!"
            return 0
        fi
        
        log_message "Waiting for Jenkins to be fully operational (Attempt $attempt/$max_attempts)..."
        sleep $wait_time
        attempt=$((attempt + 1))
    done
    
    log_message "Jenkins failed to become fully operational"
    return 1
}

# Load environment variables
if [ -f .env ]; then
    source .env
fi

# Check for required environment variables
: "${GITHUB_USERNAME:?Environment variable GITHUB_USERNAME is required}"
: "${GITHUB_TOKEN:?Environment variable GITHUB_TOKEN is required}"
: "${LOCAL_REPO_PATH:?Environment variable LOCAL_REPO_PATH is required}"
log_message "Required environment variables checked"

# Create directory for local repositories
mkdir -p "$LOCAL_REPO_PATH"
log_message "Created directory for local repositories"

# System update and Java installation
log_message "Updating system and installing Java..."
sudo apt update && sudo apt upgrade -y
sudo apt install openjdk-17-jdk -y

# Install UFW
check_install_ufw

# Jenkins repository setup
log_message "Setting up Jenkins repository..."
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | sudo tee /usr/share/keyrings/jenkins-keyring.asc > /dev/null
echo deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/ | sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null

# Jenkins installation
log_message "Installing Jenkins..."
sudo apt update
sudo apt install jenkins -y

# Start and enable Jenkins
log_message "Starting Jenkins service..."
sudo systemctl start jenkins
sudo systemctl enable jenkins

# Configure firewall
log_message "Configuring firewall..."
sudo ufw allow 8080
sudo ufw --force enable

# Jenkins configuration
JENKINS_URL="http://localhost:8080"
JENKINS_USER="admin"

# Wait for Jenkins to be ready
wait_for_jenkins

# Download Jenkins CLI
if [ ! -f jenkins-cli.jar ]; then
    log_message "Downloading Jenkins CLI..."
    wget -O jenkins-cli.jar $JENKINS_URL/jnlpJars/jenkins-cli.jar
fi

# Install required plugins
log_message "Installing Jenkins plugins..."
required_plugins=(
    "credentials"
    "credentials-binding"
    "plain-credentials"
    "ssh-credentials"
    "job-dsl"
    "workflow-aggregator"
    "git"
    "github"
)

install_jenkins_plugins "${required_plugins[@]}"

# Wait for plugins to be installed
log_message "Waiting for plugins to be installed..."
sleep 120  # Increased to 2 minutes

# Verify Jenkins is ready before proceeding
if ! verify_jenkins_ready; then
    log_message "ERROR: Jenkins is not fully operational after plugin installation"
    exit 1
fi

# Add GitHub credentials with retry mechanism
if ! add_github_credentials; then
    log_message "ERROR: Failed to add GitHub credentials"
    exit 1
fi

# Fetch GitHub repositories
log_message "Fetching GitHub repositories..."
repos=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
    "https://api.github.com/user/repos?per_page=100" | jq -r '.[].ssh_url')

# Process repositories
process_repositories "$repos"

# Create Groovy scripts for job creation
echo "Creating job configuration scripts..."
cat << 'EOF' > create_jobs.groovy
def repositories = new File("repositories.txt").readLines()

repositories.each { repoUrl ->
    def repoName = repoUrl.tokenize('/')[-1].split('\\.')[0]
    
    pipelineJob("${repoName}-build") {
        description("Build pipeline for ${repoName}")
        
        definition {
            cpsScm {
                scm {
                    git {
                        remote {
                            url(repoUrl)
                            credentials('github-credentials')
                        }
                        branches('*/main', '*/master')
                    }
                }
                scriptPath('Jenkinsfile')
            }
        }
        
        triggers {
            githubPush()
        }
    }
}
EOF

# Create update repos script
cat << 'EOF' > update_repos.groovy
def repositories = new File("repositories.txt").readLines()
def localRepoPath = System.getenv("LOCAL_REPO_PATH")

if (!localRepoPath) {
    throw new Exception("LOCAL_REPO_PATH environment variable not set")
}

repositories.each { repoUrl ->
    def repoName = repoUrl.tokenize('/')[-1].split('\\.')[0]
    
    job("${repoName}-update") {
        description("Automatic update for ${repoName}")
        
        triggers {
            scm('H/5 * * * *')
        }
        
        steps {
            shell("""
                set -e
                cd "${localRepoPath}/${repoName}" || exit 1
                
                if [ ! -d .git ]; then
                    echo "Error: ${repoName} is not a git repository!"
                    exit 1
                fi
                
                BRANCH=\$(git remote show origin | awk '/HEAD branch/ {print \$NF}')
                git pull origin \$BRANCH
            """)
        }
    }
}
EOF

echo "$repos" > repositories.txt

# Create and configure seed job
echo "Creating seed job..."
cat << EOF > seed-job-config.xml
<?xml version='1.1' encoding='UTF-8'?>
<project>
  <actions/>
  <description>Job to create all repository-specific jobs</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <scm class="hudson.scm.NullSCM"/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers/>
  <concurrentBuild>false</concurrentBuild>
  <builders>
    <javaposse.jobdsl.plugin.ExecuteDslScripts plugin="job-dsl@1.81">
      <scriptText>
$(cat create_jobs.groovy)
$(cat update_repos.groovy)
      </scriptText>
      <ignoreMissingFiles>false</ignoreMissingFiles>
      <failOnMissingPlugin>false</failOnMissingPlugin>
      <failOnSeedCollision>false</failOnSeedCollision>
      <unstableOnDeprecation>false</unstableOnDeprecation>
      <removedJobAction>IGNORE</removedJobAction>
      <removedViewAction>IGNORE</removedViewAction>
      <removedConfigFilesAction>IGNORE</removedConfigFilesAction>
      <lookupStrategy>JENKINS_ROOT</lookupStrategy>
    </javaposse.jobdsl.plugin.ExecuteDslScripts>
  </builders>
  <publishers/>
  <buildWrappers/>
</project>
EOF

# Create and run seed job
curl -X POST "$JENKINS_URL/createItem?name=seed-job" \
    --user "$JENKINS_USER:$JENKINS_PASSWORD" \
    --header "Content-Type: application/xml" \
    --data-binary @seed-job-config.xml

java -jar jenkins-cli.jar -s $JENKINS_URL -auth $JENKINS_USER:$JENKINS_PASSWORD build seed-job -s

# Clone repositories (single pass)
echo "Cloning repositories..."
echo "$repos" | while IFS= read -r repo; do
    repo_name=$(basename "$repo" .git)
    if [ ! -d "$LOCAL_REPO_PATH/$repo_name" ]; then
        git clone "$repo" "$LOCAL_REPO_PATH/$repo_name"
    fi
done

# Configure GitHub webhooks
echo "Setting up GitHub webhooks..."
echo "$repos" | while IFS= read -r repo; do
    repo_name=$(basename "$repo" .git)
    
    curl -X POST -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        "https://api.github.com/repos/$GITHUB_USERNAME/$repo_name/hooks" \
        -d '{
            "name": "web",
            "active": true,
            "events": ["push", "pull_request", "issues", "create", "delete", "fork"],
            "config": {
                "url": "'"$JENKINS_URL"'/github-webhook/",
                "content_type": "json"
            }
        }'
done

# Set up cron job for repository updates
CRON_JOB="*/5 * * * * for repo in \$(find $LOCAL_REPO_PATH -mindepth 1 -maxdepth 1 -type d); do [ -d \"\$repo/.git\" ] && (cd \"\$repo\" && BRANCH=\$(git remote show origin | awk '/HEAD branch/ {print \$NF}') && git pull origin \$BRANCH); done"

(crontab -l 2>/dev/null | grep -Fv "$CRON_JOB"; echo "$CRON_JOB") | crontab -

log_message "Setup complete! Please change the admin password after first login."
log_message "Jenkins URL: $JENKINS_URL"
log_message "Initial admin password: $JENKINS_PASSWORD"



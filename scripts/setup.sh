#!/usr/bin/env bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Default values
GITHUB_USERNAME=""
JENKINS_HOME="/var/jenkins_home"
WORKSPACE_DIR="${JENKINS_HOME}/workspace"
BACKUP_DIR="${JENKINS_HOME}/backups"
LOG_DIR="${JENKINS_HOME}/logs"
SYNC_INTERVAL=300  # 5 minutes

# Function to log messages
log() {
    local level=$1
    local message=$2
    local color=$NC
    
    case $level in
        "INFO") color=$GREEN ;;
        "WARN") color=$YELLOW ;;
        "ERROR") color=$RED ;;
    esac
    
    echo -e "${color}[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $message${NC}"
}

# Function to check required tools
check_requirements() {
    log "INFO" "Checking requirements..."
    
    local required_tools=("git" "curl" "jq")
    local missing_tools=()
    
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log "ERROR" "Missing required tools: ${missing_tools[*]}"
        log "INFO" "Installing missing tools..."
        apt-get update && apt-get install -y "${missing_tools[@]}"
    fi
}

# Function to setup directories
setup_directories() {
    log "INFO" "Setting up directories..."
    
    mkdir -p "$WORKSPACE_DIR" "$BACKUP_DIR" "$LOG_DIR"
    chmod -R 755 "$WORKSPACE_DIR" "$BACKUP_DIR" "$LOG_DIR"
}

# Function to configure Git
setup_git() {
    log "INFO" "Configuring Git..."
    
    git config --global user.name "Jenkins Agent"
    git config --global user.email "jenkins@agent.local"
    git config --global core.autocrlf input
    git config --global core.fileMode false
    git config --global pull.rebase false
}

# Function to get all repositories for a user
get_repositories() {
    local username=$1
    local page=1
    local repos=()
    
    log "INFO" "Fetching repositories for user ${username}..."
    
    while true; do
        local response
        response=$(curl -s -H "Authorization: Bearer $GITHUB_TOKEN" \
            "https://api.github.com/users/${username}/repos?page=${page}&per_page=100")
        
        local page_repos
        page_repos=$(echo "$response" | jq -r '.[].clone_url')
        
        if [ -z "$page_repos" ]; then
            break
        fi
        
        repos+=("$page_repos")
        ((page++))
    done
    
    echo "${repos[@]}"
}

# Function to clone or update a repository
sync_repository() {
    local repo_url=$1
    local repo_name
    repo_name=$(basename "$repo_url" .git)
    local repo_path="${WORKSPACE_DIR}/${repo_name}"
    
    if [ -d "$repo_path" ]; then
        log "INFO" "Updating repository: ${repo_name}"
        (cd "$repo_path" && git pull)
    else
        log "INFO" "Cloning repository: ${repo_name}"
        git clone "$repo_url" "$repo_path"
    fi
}

# Function to backup workspace
backup_workspace() {
    local timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${BACKUP_DIR}/workspace_${timestamp}.tar.gz"
    
    log "INFO" "Creating backup: ${backup_file}"
    tar -czf "$backup_file" -C "$JENKINS_HOME" workspace
    
    # Keep only last 5 backups
    (cd "$BACKUP_DIR" && ls -t | tail -n +6 | xargs -r rm --)
}

# Function to setup cron jobs
setup_cron() {
    log "INFO" "Setting up cron jobs..."
    
    # Add cron job for repository sync
    echo "*/${SYNC_INTERVAL} * * * * $0 sync >> ${LOG_DIR}/sync.log 2>&1" | crontab -
    
    # Add cron job for daily backup at 2 AM
    echo "0 2 * * * $0 backup >> ${LOG_DIR}/backup.log 2>&1" | crontab -
}

# Function to monitor system resources
monitor_resources() {
    log "INFO" "Monitoring system resources..."
    
    local cpu_usage
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}')
    local mem_usage
    mem_usage=$(free | grep Mem | awk '{print $3/$2 * 100.0}')
    local disk_usage
    disk_usage=$(df -h "$WORKSPACE_DIR" | tail -1 | awk '{print $5}')
    
    log "INFO" "CPU Usage: ${cpu_usage}%"
    log "INFO" "Memory Usage: ${mem_usage}%"
    log "INFO" "Disk Usage: ${disk_usage}"
}

# Main function
main() {
    local command=${1:-"setup"}
    
    case $command in
        "setup")
            if [ -z "$GITHUB_TOKEN" ]; then
                log "ERROR" "GITHUB_TOKEN environment variable is required"
                exit 1
            fi
            
            if [ -z "$GITHUB_USERNAME" ]; then
                log "ERROR" "GITHUB_USERNAME environment variable is required"
                exit 1
            fi
            
            check_requirements
            setup_directories
            setup_git
            
            local repos
            mapfile -t repos < <(get_repositories "$GITHUB_USERNAME")
            
            for repo in "${repos[@]}"; do
                sync_repository "$repo"
            done
            
            setup_cron
            backup_workspace
            monitor_resources
            ;;
            
        "sync")
            local repos
            mapfile -t repos < <(get_repositories "$GITHUB_USERNAME")
            
            for repo in "${repos[@]}"; do
                sync_repository "$repo"
            done
            ;;
            
        "backup")
            backup_workspace
            ;;
            
        "monitor")
            monitor_resources
            ;;
            
        *)
            log "ERROR" "Unknown command: ${command}"
            echo "Usage: $0 [setup|sync|backup|monitor]"
            exit 1
            ;;
    esac
}

main "$@"
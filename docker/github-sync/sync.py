#!/usr/bin/env python3

import os
import sys
import time
import logging
import asyncio
import aiohttp
from github import Github
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.getenv('LOG_DIR', '/var/jenkins_home/logs'), 'sync.log'))
    ]
)
logger = logging.getLogger('github-sync')

class GitHubSync:
    def __init__(self):
        self.github = Github(os.getenv('GITHUB_TOKEN'))
        self.workspace_dir = Path(os.getenv('WORKSPACE_DIR', '/var/jenkins_home/workspace'))
        self.backup_dir = Path(os.getenv('BACKUP_DIR', '/var/jenkins_home/backups'))
        self.username = os.getenv('GITHUB_USERNAME')
        self.sync_interval = int(os.getenv('SYNC_INTERVAL', 300))

    async def get_repositories(self) -> List[Dict[str, Any]]:
        """Get all repositories for the user."""
        try:
            user = self.github.get_user(self.username)
            repos = []
            for repo in user.get_repos():
                repos.append({
                    'name': repo.name,
                    'clone_url': repo.clone_url,
                    'default_branch': repo.default_branch,
                    'updated_at': repo.updated_at
                })
            return repos
        except Exception as e:
            logger.error(f"Error getting repositories: {e}")
            return []

    async def sync_repository(self, repo: Dict[str, Any]) -> bool:
        """Sync a single repository."""
        repo_path = self.workspace_dir / repo['name']
        try:
            if not repo_path.exists():
                logger.info(f"Cloning repository: {repo['name']}")
                os.system(f"git clone {repo['clone_url']} {repo_path}")
            else:
                logger.info(f"Updating repository: {repo['name']}")
                os.system(f"cd {repo_path} && git fetch && git pull")
            return True
        except Exception as e:
            logger.error(f"Error syncing repository {repo['name']}: {e}")
            return False

    async def backup_workspace(self):
        """Create a backup of the workspace."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_dir / f"workspace_{timestamp}.tar.gz"
            
            logger.info(f"Creating backup: {backup_file}")
            os.system(f"tar -czf {backup_file} -C {self.workspace_dir.parent} workspace")
            
            # Keep only last 5 backups
            backups = sorted(self.backup_dir.glob('workspace_*.tar.gz'))
            for old_backup in backups[:-5]:
                old_backup.unlink()
        except Exception as e:
            logger.error(f"Error creating backup: {e}")

    async def monitor_resources(self):
        """Monitor system resources."""
        try:
            # Get CPU usage
            with open('/proc/loadavg') as f:
                cpu = float(f.read().split()[0])
            
            # Get memory usage
            with open('/proc/meminfo') as f:
                mem = {}
                for line in f:
                    if ':' in line:
                        key, val = line.split(':')
                        mem[key] = int(val.split()[0])
                mem_used = (mem['MemTotal'] - mem['MemFree']) / mem['MemTotal'] * 100
            
            # Get disk usage
            disk = os.statvfs(self.workspace_dir)
            disk_used = (disk.f_blocks - disk.f_bfree) / disk.f_blocks * 100
            
            logger.info(f"System Resources - CPU Load: {cpu:.1f}, Memory: {mem_used:.1f}%, Disk: {disk_used:.1f}%")
        except Exception as e:
            logger.error(f"Error monitoring resources: {e}")

    async def run_forever(self):
        """Run the sync process continuously."""
        while True:
            try:
                logger.info("Starting sync cycle")
                
                # Get repositories
                repos = await self.get_repositories()
                
                # Sync repositories
                tasks = [self.sync_repository(repo) for repo in repos]
                results = await asyncio.gather(*tasks)
                
                # Create backup
                await self.backup_workspace()
                
                # Monitor resources
                await self.monitor_resources()
                
                logger.info(f"Sync cycle completed. Success: {sum(results)}, Failed: {len(results) - sum(results)}")
                
                # Wait for next cycle
                await asyncio.sleep(self.sync_interval)
            except Exception as e:
                logger.error(f"Error in sync cycle: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying

async def main():
    if not os.getenv('GITHUB_TOKEN'):
        logger.error("GITHUB_TOKEN environment variable is required")
        sys.exit(1)
    
    if not os.getenv('GITHUB_USERNAME'):
        logger.error("GITHUB_USERNAME environment variable is required")
        sys.exit(1)
    
    syncer = GitHubSync()
    await syncer.run_forever()

if __name__ == '__main__':
    asyncio.run(main())
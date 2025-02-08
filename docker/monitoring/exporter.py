#!/usr/bin/env python3

import os
import time
import psutil
import logging
import aiohttp
import asyncio
from prometheus_client import start_http_server, Gauge, Counter, Histogram
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('monitoring')

class JenkinsExporter:
    """Export Jenkins metrics to Prometheus."""
    
    def __init__(self):
        # Jenkins metrics
        self.build_duration = Histogram(
            'jenkins_build_duration_seconds',
            'Build duration in seconds',
            ['job_name']
        )
        self.build_success = Counter(
            'jenkins_build_success_total',
            'Total successful builds',
            ['job_name']
        )
        self.build_failure = Counter(
            'jenkins_build_failure_total',
            'Total failed builds',
            ['job_name']
        )
        self.queue_size = Gauge(
            'jenkins_queue_size',
            'Number of jobs in queue'
        )
        self.executor_count = Gauge(
            'jenkins_executor_count',
            'Number of executors'
        )
        
        # System metrics
        self.cpu_usage = Gauge(
            'system_cpu_usage_percent',
            'CPU usage percentage'
        )
        self.memory_usage = Gauge(
            'system_memory_usage_percent',
            'Memory usage percentage'
        )
        self.disk_usage = Gauge(
            'system_disk_usage_percent',
            'Disk usage percentage',
            ['mount_point']
        )
        
        # GitHub metrics
        self.repo_sync_status = Gauge(
            'github_repo_sync_status',
            'Repository sync status (1=success, 0=failure)',
            ['repo_name']
        )
        self.repo_sync_time = Gauge(
            'github_repo_sync_time_seconds',
            'Time taken to sync repository',
            ['repo_name']
        )
        
        # Jenkins API configuration
        self.jenkins_url = os.getenv('JENKINS_URL', 'http://jenkins:8080')
        self.jenkins_user = os.getenv('JENKINS_USER', 'admin')
        self.jenkins_token = os.getenv('JENKINS_API_TOKEN')
        
        # Initialize session
        self.session = None
    
    async def setup(self):
        """Setup aiohttp session."""
        self.session = aiohttp.ClientSession(
            auth=aiohttp.BasicAuth(self.jenkins_user, self.jenkins_token)
        )
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.session:
            await self.session.close()
    
    async def collect_jenkins_metrics(self):
        """Collect metrics from Jenkins."""
        try:
            # Get queue information
            async with self.session.get(f"{self.jenkins_url}/queue/api/json") as response:
                queue = await response.json()
                self.queue_size.set(len(queue['items']))
            
            # Get executor information
            async with self.session.get(f"{self.jenkins_url}/computer/api/json") as response:
                computers = await response.json()
                total_executors = sum(c['numExecutors'] for c in computers['computer'])
                self.executor_count.set(total_executors)
            
            # Get job information
            async with self.session.get(f"{self.jenkins_url}/api/json") as response:
                jobs = await response.json()
                for job in jobs['jobs']:
                    async with self.session.get(f"{job['url']}api/json") as job_response:
                        job_info = await job_response.json()
                        if 'lastBuild' in job_info:
                            build_url = f"{job_info['lastBuild']['url']}api/json"
                            async with self.session.get(build_url) as build_response:
                                build = await build_response.json()
                                duration = build['duration'] / 1000  # Convert to seconds
                                self.build_duration.observe(duration, labels={'job_name': job['name']})
                                if build['result'] == 'SUCCESS':
                                    self.build_success.inc({'job_name': job['name']})
                                elif build['result'] == 'FAILURE':
                                    self.build_failure.inc({'job_name': job['name']})
        except Exception as e:
            logger.error(f"Error collecting Jenkins metrics: {e}")
    
    def collect_system_metrics(self):
        """Collect system metrics."""
        try:
            # CPU usage
            self.cpu_usage.set(psutil.cpu_percent())
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.memory_usage.set(memory.percent)
            
            # Disk usage
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    self.disk_usage.labels(partition.mountpoint).set(usage.percent)
                except Exception:
                    continue
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    async def collect_github_metrics(self):
        """Collect GitHub sync metrics."""
        try:
            workspace_dir = os.getenv('WORKSPACE_DIR', '/var/jenkins_home/workspace')
            for repo in os.listdir(workspace_dir):
                repo_path = os.path.join(workspace_dir, repo)
                if os.path.isdir(repo_path):
                    start_time = time.time()
                    result = os.system(f"cd {repo_path} && git pull --dry-run > /dev/null 2>&1")
                    sync_time = time.time() - start_time
                    
                    self.repo_sync_status.labels(repo).set(1 if result == 0 else 0)
                    self.repo_sync_time.labels(repo).set(sync_time)
        except Exception as e:
            logger.error(f"Error collecting GitHub metrics: {e}")
    
    async def run_forever(self):
        """Run the exporter forever."""
        await self.setup()
        
        try:
            while True:
                await self.collect_jenkins_metrics()
                self.collect_system_metrics()
                await self.collect_github_metrics()
                await asyncio.sleep(15)  # Collect every 15 seconds
        finally:
            await self.cleanup()

async def main():
    """Main entry point."""
    # Start Prometheus HTTP server
    start_http_server(9100)
    logger.info("Started Prometheus metrics server on port 9100")
    
    # Start metrics collection
    exporter = JenkinsExporter()
    await exporter.run_forever()

if __name__ == '__main__':
    asyncio.run(main())
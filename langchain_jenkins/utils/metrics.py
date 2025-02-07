"""Metrics collection and analysis for Jenkins."""
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from ..tools.jenkins_api import JenkinsAPI
from ..utils.monitoring import monitor
from ..utils.cache import Cache

class MetricsCollector:
    """Collects and analyzes Jenkins metrics."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.jenkins = JenkinsAPI()
        self.cache = Cache()
        
    @monitor.monitor_performance()
    async def collect_build_metrics(
        self,
        job_name: Optional[str] = None,
        time_window: timedelta = timedelta(days=7)
    ) -> Dict[str, Any]:
        """Collect build-related metrics.
        
        Args:
            job_name: Optional job name to filter metrics
            time_window: Time window to collect metrics for
            
        Returns:
            Build metrics
        """
        # Try to get from cache first
        cache_key = f"build_metrics:{job_name}:{time_window}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        
        try:
            # Get all jobs or specific job
            if job_name:
                jobs = [await self.jenkins.get_job_info(job_name)]
            else:
                system_info = await self.jenkins.get_system_info()
                jobs = system_info.get("jobs", [])
            
            metrics = {
                "total_builds": 0,
                "successful_builds": 0,
                "failed_builds": 0,
                "average_duration": 0,
                "build_frequency": 0,
                "job_metrics": {}
            }
            
            # Calculate metrics for each job
            for job in jobs:
                job_name = job["name"]
                job_info = await self.jenkins.get_job_info(job_name)
                
                if "lastBuild" not in job_info:
                    continue
                
                # Get recent builds
                builds = [b for b in job_info.get("builds", [])]
                recent_builds = [
                    b for b in builds
                    if (datetime.now() - datetime.fromtimestamp(b["timestamp"] / 1000)) <= time_window
                ]
                
                if not recent_builds:
                    continue
                
                # Calculate job-specific metrics
                successful = sum(1 for b in recent_builds if b["result"] == "SUCCESS")
                failed = sum(1 for b in recent_builds if b["result"] == "FAILURE")
                durations = [b["duration"] for b in recent_builds]
                avg_duration = sum(durations) / len(durations) if durations else 0
                
                job_metrics = {
                    "total_builds": len(recent_builds),
                    "successful_builds": successful,
                    "failed_builds": failed,
                    "success_rate": successful / len(recent_builds) if recent_builds else 0,
                    "average_duration": avg_duration,
                    "build_frequency": len(recent_builds) / time_window.days
                }
                
                metrics["job_metrics"][job_name] = job_metrics
                metrics["total_builds"] += len(recent_builds)
                metrics["successful_builds"] += successful
                metrics["failed_builds"] += failed
                metrics["average_duration"] += avg_duration
            
            # Calculate overall averages
            num_jobs = len(metrics["job_metrics"])
            if num_jobs > 0:
                metrics["average_duration"] /= num_jobs
                metrics["build_frequency"] = metrics["total_builds"] / time_window.days
            
            # Cache the results
            await self.cache.set(cache_key, metrics, expire=300)  # Cache for 5 minutes
            
            return metrics
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }
    
    @monitor.monitor_performance()
    async def collect_pipeline_metrics(
        self,
        pipeline_name: Optional[str] = None,
        time_window: timedelta = timedelta(days=7)
    ) -> Dict[str, Any]:
        """Collect pipeline-related metrics.
        
        Args:
            pipeline_name: Optional pipeline name to filter metrics
            time_window: Time window to collect metrics for
            
        Returns:
            Pipeline metrics
        """
        # Try to get from cache first
        cache_key = f"pipeline_metrics:{pipeline_name}:{time_window}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        
        try:
            # Get all pipelines or specific pipeline
            if pipeline_name:
                pipelines = [await self.jenkins.get_job_info(pipeline_name)]
            else:
                system_info = await self.jenkins.get_system_info()
                pipelines = [
                    job for job in system_info.get("jobs", [])
                    if "workflow" in job.get("_class", "").lower()
                ]
            
            metrics = {
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "average_duration": 0,
                "pipeline_metrics": {}
            }
            
            # Calculate metrics for each pipeline
            for pipeline in pipelines:
                pipeline_name = pipeline["name"]
                pipeline_info = await self.jenkins.get_job_info(pipeline_name)
                
                if "lastBuild" not in pipeline_info:
                    continue
                
                # Get recent runs
                runs = [r for r in pipeline_info.get("builds", [])]
                recent_runs = [
                    r for r in runs
                    if (datetime.now() - datetime.fromtimestamp(r["timestamp"] / 1000)) <= time_window
                ]
                
                if not recent_runs:
                    continue
                
                # Calculate pipeline-specific metrics
                successful = sum(1 for r in recent_runs if r["result"] == "SUCCESS")
                failed = sum(1 for r in recent_runs if r["result"] == "FAILURE")
                durations = [r["duration"] for r in recent_runs]
                avg_duration = sum(durations) / len(durations) if durations else 0
                
                pipeline_metrics = {
                    "total_runs": len(recent_runs),
                    "successful_runs": successful,
                    "failed_runs": failed,
                    "success_rate": successful / len(recent_runs) if recent_runs else 0,
                    "average_duration": avg_duration,
                    "run_frequency": len(recent_runs) / time_window.days
                }
                
                metrics["pipeline_metrics"][pipeline_name] = pipeline_metrics
                metrics["total_runs"] += len(recent_runs)
                metrics["successful_runs"] += successful
                metrics["failed_runs"] += failed
                metrics["average_duration"] += avg_duration
            
            # Calculate overall averages
            num_pipelines = len(metrics["pipeline_metrics"])
            if num_pipelines > 0:
                metrics["average_duration"] /= num_pipelines
            
            # Cache the results
            await self.cache.set(cache_key, metrics, expire=300)  # Cache for 5 minutes
            
            return metrics
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }
    
    @monitor.monitor_performance()
    async def generate_recommendations(
        self,
        build_metrics: Dict[str, Any],
        pipeline_metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations based on metrics.
        
        Args:
            build_metrics: Build metrics data
            pipeline_metrics: Pipeline metrics data
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Analyze build metrics
        if build_metrics["status"] != "error":
            # Check success rate
            for job_name, job_metrics in build_metrics["job_metrics"].items():
                if job_metrics["success_rate"] < 0.8:  # Less than 80% success
                    recommendations.append({
                        "type": "build",
                        "severity": "high",
                        "job": job_name,
                        "message": f"Job {job_name} has a low success rate ({job_metrics['success_rate']*100:.1f}%). Consider reviewing build configuration and tests."
                    })
                
                # Check build frequency
                if job_metrics["build_frequency"] < 0.1:  # Less than 1 build per 10 days
                    recommendations.append({
                        "type": "build",
                        "severity": "medium",
                        "job": job_name,
                        "message": f"Job {job_name} is built infrequently. Consider automating builds or removing if unused."
                    })
                
                # Check build duration
                if job_metrics["average_duration"] > 3600:  # More than 1 hour
                    recommendations.append({
                        "type": "build",
                        "severity": "medium",
                        "job": job_name,
                        "message": f"Job {job_name} has long average build time ({job_metrics['average_duration']/60:.1f} minutes). Consider optimizing build steps."
                    })
        
        # Analyze pipeline metrics
        if pipeline_metrics["status"] != "error":
            for pipeline_name, pipeline_metrics in pipeline_metrics["pipeline_metrics"].items():
                if pipeline_metrics["success_rate"] < 0.8:  # Less than 80% success
                    recommendations.append({
                        "type": "pipeline",
                        "severity": "high",
                        "pipeline": pipeline_name,
                        "message": f"Pipeline {pipeline_name} has a low success rate ({pipeline_metrics['success_rate']*100:.1f}%). Review pipeline stages and error patterns."
                    })
                
                # Check pipeline duration
                if pipeline_metrics["average_duration"] > 7200:  # More than 2 hours
                    recommendations.append({
                        "type": "pipeline",
                        "severity": "medium",
                        "pipeline": pipeline_name,
                        "message": f"Pipeline {pipeline_name} takes long to complete ({pipeline_metrics['average_duration']/60:.1f} minutes). Consider parallelizing stages or optimizing steps."
                    })
        
        return recommendations
    
    @monitor.monitor_performance()
    async def collect_metrics(self) -> Dict[str, Any]:
        """Collect all metrics and generate recommendations.
        
        Returns:
            Complete metrics and recommendations
        """
        # Collect all metrics
        build_metrics = await self.collect_build_metrics()
        pipeline_metrics = await self.collect_pipeline_metrics()
        
        # Generate recommendations
        recommendations = await self.generate_recommendations(
            build_metrics,
            pipeline_metrics
        )
        
        return {
            "timestamp": time.time(),
            "builds": build_metrics,
            "pipelines": pipeline_metrics,
            "recommendations": recommendations
        }
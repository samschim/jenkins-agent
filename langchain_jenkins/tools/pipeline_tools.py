"""Pipeline management tools for LangChain agents."""
from typing import Dict, Any, List, Optional
from .jenkins_api import JenkinsAPI

class PipelineTools:
    """Tools for managing Jenkins pipelines."""
    
    def __init__(self):
        """Initialize pipeline tools with Jenkins API client."""
        self.jenkins = JenkinsAPI()
    
    async def get_pipeline_status(self, pipeline_name: str) -> Dict[str, Any]:
        """Get the status of a pipeline.
        
        Args:
            pipeline_name: Name of the pipeline
            
        Returns:
            Pipeline status information
        """
        return await self.jenkins.get_job_info(pipeline_name)
    
    async def get_pipeline_stages(
        self,
        pipeline_name: str,
        build_number: str = "lastBuild"
    ) -> List[Dict[str, Any]]:
        """Get information about pipeline stages.
        
        Args:
            pipeline_name: Name of the pipeline
            build_number: Build number or "lastBuild"
            
        Returns:
            List of stage information
        """
        endpoint = f"/job/{pipeline_name}/{build_number}/wfapi/describe"
        response = await self.jenkins._request("GET", endpoint)
        return response.get("stages", [])
    
    async def get_pipeline_definition(self, pipeline_name: str) -> str:
        """Get the Jenkinsfile content for a pipeline.
        
        Args:
            pipeline_name: Name of the pipeline
            
        Returns:
            Jenkinsfile content
        """
        endpoint = f"/job/{pipeline_name}/config.xml"
        async with self.jenkins._request("GET", endpoint) as response:
            return response.text
    
    async def update_pipeline_definition(
        self,
        pipeline_name: str,
        jenkinsfile: str
    ) -> bool:
        """Update the Jenkinsfile content for a pipeline.
        
        Args:
            pipeline_name: Name of the pipeline
            jenkinsfile: New Jenkinsfile content
            
        Returns:
            True if update was successful
        """
        endpoint = f"/job/{pipeline_name}/config.xml"
        try:
            await self.jenkins._request("POST", endpoint, data=jenkinsfile)
            return True
        except Exception:
            return False
    
    async def analyze_pipeline_performance(
        self,
        pipeline_name: str,
        builds: Optional[int] = 10
    ) -> Dict[str, Any]:
        """Analyze pipeline performance across multiple builds.
        
        Args:
            pipeline_name: Name of the pipeline
            builds: Number of recent builds to analyze
            
        Returns:
            Performance analysis results
        """
        # Get recent builds
        job_info = await self.jenkins.get_job_info(pipeline_name)
        recent_builds = job_info.get("builds", [])[:builds]
        
        # Collect stage timing data
        performance_data = []
        for build in recent_builds:
            build_number = build["number"]
            stages = await self.get_pipeline_stages(pipeline_name, str(build_number))
            performance_data.append({
                "build_number": build_number,
                "stages": [
                    {
                        "name": stage["name"],
                        "duration": stage.get("durationMillis", 0)
                    }
                    for stage in stages
                ]
            })
        
        # Calculate statistics
        stage_stats = {}
        for build in performance_data:
            for stage in build["stages"]:
                if stage["name"] not in stage_stats:
                    stage_stats[stage["name"]] = []
                stage_stats[stage["name"]].append(stage["duration"])
        
        # Calculate averages and identify bottlenecks
        analysis = {
            "average_durations": {
                name: sum(durations) / len(durations)
                for name, durations in stage_stats.items()
            },
            "bottlenecks": sorted(
                stage_stats.keys(),
                key=lambda x: sum(stage_stats[x]) / len(stage_stats[x]),
                reverse=True
            )[:3]
        }
        
        return analysis
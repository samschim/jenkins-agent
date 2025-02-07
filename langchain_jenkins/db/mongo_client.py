"""MongoDB client for log storage and analysis."""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import motor.motor_asyncio
from ..config.config import config

class MongoClient:
    """MongoDB client for log storage and analysis."""
    
    def __init__(self):
        """Initialize MongoDB client."""
        self.client = motor.motor_asyncio.AsyncIOMotorClient(
            config.mongodb.url
        )
        self.db = self.client[config.mongodb.database]
        
        # Collections
        self.logs = self.db.build_logs
        self.errors = self.db.build_errors
        self.trends = self.db.error_trends
    
    async def store_build_log(
        self,
        build_id: str,
        job_name: str,
        log_text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store a build log.
        
        Args:
            build_id: Build identifier
            job_name: Name of the job
            log_text: Build log content
            metadata: Optional build metadata
            
        Returns:
            Storage result
        """
        document = {
            "build_id": build_id,
            "job_name": job_name,
            "log_text": log_text,
            "timestamp": datetime.utcnow(),
            "metadata": metadata or {}
        }
        
        result = await self.logs.insert_one(document)
        return {
            "status": "stored",
            "id": str(result.inserted_id),
            "build_id": build_id
        }
    
    async def store_build_error(
        self,
        build_id: str,
        job_name: str,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store a build error.
        
        Args:
            build_id: Build identifier
            job_name: Name of the job
            error_type: Type of error
            error_message: Error message
            stack_trace: Optional stack trace
            metadata: Optional error metadata
            
        Returns:
            Storage result
        """
        document = {
            "build_id": build_id,
            "job_name": job_name,
            "error_type": error_type,
            "error_message": error_message,
            "stack_trace": stack_trace,
            "timestamp": datetime.utcnow(),
            "metadata": metadata or {}
        }
        
        result = await self.errors.insert_one(document)
        
        # Update error trends
        await self._update_error_trends(
            job_name,
            error_type,
            error_message
        )
        
        return {
            "status": "stored",
            "id": str(result.inserted_id),
            "build_id": build_id
        }
    
    async def _update_error_trends(
        self,
        job_name: str,
        error_type: str,
        error_message: str
    ) -> None:
        """Update error trend statistics.
        
        Args:
            job_name: Name of the job
            error_type: Type of error
            error_message: Error message
        """
        # Get current date (truncated to day)
        today = datetime.utcnow().replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )
        
        # Update daily trends
        await self.trends.update_one(
            {
                "job_name": job_name,
                "error_type": error_type,
                "date": today
            },
            {
                "$inc": {"count": 1},
                "$push": {
                    "messages": {
                        "$each": [error_message],
                        "$slice": -10  # Keep last 10 messages
                    }
                }
            },
            upsert=True
        )
    
    async def get_build_log(
        self,
        build_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a build log.
        
        Args:
            build_id: Build identifier
            
        Returns:
            Build log document
        """
        return await self.logs.find_one({"build_id": build_id})
    
    async def get_build_errors(
        self,
        build_id: str
    ) -> List[Dict[str, Any]]:
        """Get build errors.
        
        Args:
            build_id: Build identifier
            
        Returns:
            List of error documents
        """
        cursor = self.errors.find({"build_id": build_id})
        return await cursor.to_list(length=None)
    
    async def get_job_logs(
        self,
        job_name: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get logs for a job.
        
        Args:
            job_name: Name of the job
            limit: Maximum number of logs to return
            
        Returns:
            List of log documents
        """
        cursor = self.logs.find(
            {"job_name": job_name}
        ).sort(
            "timestamp", -1
        ).limit(limit)
        
        return await cursor.to_list(length=None)
    
    async def get_job_errors(
        self,
        job_name: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get errors for a job.
        
        Args:
            job_name: Name of the job
            limit: Maximum number of errors to return
            
        Returns:
            List of error documents
        """
        cursor = self.errors.find(
            {"job_name": job_name}
        ).sort(
            "timestamp", -1
        ).limit(limit)
        
        return await cursor.to_list(length=None)
    
    async def get_error_trends(
        self,
        job_name: Optional[str] = None,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get error trends.
        
        Args:
            job_name: Optional job name filter
            days: Number of days to analyze
            
        Returns:
            List of trend documents
        """
        # Calculate date range
        end_date = datetime.utcnow().replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )
        start_date = end_date - timedelta(days=days)
        
        # Build query
        query = {"date": {"$gte": start_date, "$lte": end_date}}
        if job_name:
            query["job_name"] = job_name
        
        cursor = self.trends.find(query).sort("date", 1)
        return await cursor.to_list(length=None)
    
    async def get_common_errors(
        self,
        job_name: Optional[str] = None,
        days: int = 7,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get most common errors.
        
        Args:
            job_name: Optional job name filter
            days: Number of days to analyze
            limit: Maximum number of errors to return
            
        Returns:
            List of common errors
        """
        # Calculate date range
        end_date = datetime.utcnow().replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )
        start_date = end_date - timedelta(days=days)
        
        # Build pipeline
        pipeline = [
            {
                "$match": {
                    "date": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": {
                        "job_name": "$job_name",
                        "error_type": "$error_type"
                    },
                    "total_count": {"$sum": "$count"},
                    "messages": {"$push": "$messages"}
                }
            },
            {
                "$sort": {"total_count": -1}
            },
            {
                "$limit": limit
            }
        ]
        
        if job_name:
            pipeline[0]["$match"]["job_name"] = job_name
        
        cursor = self.trends.aggregate(pipeline)
        return await cursor.to_list(length=None)
    
    async def get_error_patterns(
        self,
        job_name: Optional[str] = None,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get error patterns.
        
        Args:
            job_name: Optional job name filter
            days: Number of days to analyze
            
        Returns:
            List of error patterns
        """
        # Get error trends
        trends = await self.get_error_trends(job_name, days)
        
        # Analyze patterns
        patterns = []
        for trend in trends:
            # Check for recurring errors
            if trend["count"] > 1:
                patterns.append({
                    "job_name": trend["job_name"],
                    "error_type": trend["error_type"],
                    "frequency": trend["count"],
                    "first_seen": trend["date"],
                    "messages": trend["messages"][:3]  # Sample messages
                })
        
        return sorted(
            patterns,
            key=lambda x: x["frequency"],
            reverse=True
        )
    
    async def get_error_correlations(
        self,
        job_name: Optional[str] = None,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get error correlations.
        
        Args:
            job_name: Optional job name filter
            days: Number of days to analyze
            
        Returns:
            List of correlated errors
        """
        # Get errors in time range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        query = {"timestamp": {"$gte": start_date, "$lte": end_date}}
        if job_name:
            query["job_name"] = job_name
        
        cursor = self.errors.find(query)
        errors = await cursor.to_list(length=None)
        
        # Analyze correlations
        correlations = []
        error_types = {}
        
        for error in errors:
            job = error["job_name"]
            error_type = error["error_type"]
            timestamp = error["timestamp"]
            
            # Check for related errors within 5 minutes
            window_start = timestamp - timedelta(minutes=5)
            window_end = timestamp + timedelta(minutes=5)
            
            related = [
                e for e in errors
                if e["job_name"] == job
                and e["error_type"] != error_type
                and window_start <= e["timestamp"] <= window_end
            ]
            
            if related:
                key = f"{job}:{error_type}"
                if key not in error_types:
                    error_types[key] = {
                        "job_name": job,
                        "error_type": error_type,
                        "related_errors": set(),
                        "count": 0
                    }
                
                error_types[key]["count"] += 1
                error_types[key]["related_errors"].update(
                    e["error_type"] for e in related
                )
        
        # Format correlations
        for key, data in error_types.items():
            if data["count"] > 1:
                correlations.append({
                    "job_name": data["job_name"],
                    "error_type": data["error_type"],
                    "frequency": data["count"],
                    "related_errors": list(data["related_errors"])
                })
        
        return sorted(
            correlations,
            key=lambda x: x["frequency"],
            reverse=True
        )

# Global instance
mongo_client = MongoClient()
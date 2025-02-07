"""Test metrics collection and analysis."""
import pytest
from datetime import timedelta
from langchain_jenkins.utils.metrics import MetricsCollector

pytestmark = pytest.mark.asyncio

async def test_collect_build_metrics(mock_jenkins_api):
    """Test collecting build metrics."""
    collector = MetricsCollector()
    metrics = await collector.collect_build_metrics(time_window=timedelta(days=1))
    
    assert metrics["status"] != "error"
    assert "total_builds" in metrics
    assert "successful_builds" in metrics
    assert "failed_builds" in metrics
    assert "average_duration" in metrics
    assert "build_frequency" in metrics
    assert "job_metrics" in metrics

async def test_collect_pipeline_metrics(mock_jenkins_api):
    """Test collecting pipeline metrics."""
    collector = MetricsCollector()
    metrics = await collector.collect_pipeline_metrics(time_window=timedelta(days=1))
    
    assert metrics["status"] != "error"
    assert "total_runs" in metrics
    assert "successful_runs" in metrics
    assert "failed_runs" in metrics
    assert "average_duration" in metrics
    assert "pipeline_metrics" in metrics

async def test_generate_recommendations(mock_jenkins_api):
    """Test generating recommendations from metrics."""
    collector = MetricsCollector()
    
    # Get metrics
    build_metrics = await collector.collect_build_metrics()
    pipeline_metrics = await collector.collect_pipeline_metrics()
    
    # Generate recommendations
    recommendations = await collector.generate_recommendations(
        build_metrics,
        pipeline_metrics
    )
    
    assert isinstance(recommendations, list)
    if recommendations:
        recommendation = recommendations[0]
        assert "type" in recommendation
        assert "severity" in recommendation
        assert "message" in recommendation

async def test_collect_metrics(mock_jenkins_api):
    """Test collecting all metrics."""
    collector = MetricsCollector()
    metrics = await collector.collect_metrics()
    
    assert metrics["status"] != "error"
    assert "timestamp" in metrics
    assert "builds" in metrics
    assert "pipelines" in metrics
    assert "recommendations" in metrics

async def test_metrics_caching(mock_jenkins_api):
    """Test that metrics are properly cached."""
    collector = MetricsCollector()
    
    # First call should hit the API
    metrics1 = await collector.collect_metrics()
    
    # Second call should use cache
    metrics2 = await collector.collect_metrics()
    
    assert metrics1 == metrics2

async def test_error_handling(mock_jenkins_api):
    """Test error handling in metrics collection."""
    collector = MetricsCollector()
    
    # Test with invalid job name
    metrics = await collector.collect_build_metrics(job_name="nonexistent-job")
    assert metrics["status"] == "error"
    assert "error" in metrics
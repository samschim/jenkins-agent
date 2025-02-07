# Enhanced Supervisor Agent with Embedding-Based Task Routing and Metrics Collection

This PR enhances the supervisor agent with more intelligent task routing using embeddings and adds comprehensive metrics collection capabilities.

## Changes

### 1. Embedding-Based Task Routing
- Added `EmbeddingManager` class for managing task and capability embeddings
- Replaced simple keyword-based routing with semantic similarity matching
- Improved accuracy of task routing to specialized agents

### 2. Metrics Collection
- Added `MetricsCollector` class for comprehensive metrics gathering
- Collects build and pipeline metrics with caching
- Generates automated recommendations based on metrics
- Provides insights about system health and performance

### 3. Enhanced Supervisor Agent
- Integrated embedding-based routing
- Added metrics collection and insights generation
- Improved error handling and logging
- Better handling of complex tasks

### 4. Testing
- Added unit tests for metrics collection
- Added unit tests for enhanced supervisor functionality
- Improved test coverage and error handling tests

## Technical Details

### Embedding-Based Routing
The new routing system uses OpenAI embeddings to calculate semantic similarity between tasks and agent capabilities. This provides more accurate and flexible task routing compared to the previous keyword-based approach.

```python
async def _determine_agent(self, task: str) -> str:
    return await self.embedding_manager.find_best_agent(task)
```

### Metrics Collection
The metrics collector gathers comprehensive data about builds and pipelines:
- Build success rates and durations
- Pipeline performance metrics
- Resource utilization
- Automated recommendations

```python
async def collect_metrics(self) -> Dict[str, Any]:
    build_metrics = await self.collect_build_metrics()
    pipeline_metrics = await self.collect_pipeline_metrics()
    recommendations = await self.generate_recommendations(
        build_metrics,
        pipeline_metrics
    )
    return {
        "builds": build_metrics,
        "pipelines": pipeline_metrics,
        "recommendations": recommendations
    }
```

## Testing

All new functionality is covered by unit tests:

```bash
pytest tests/unit/test_metrics.py -v
pytest tests/unit/test_enhanced_supervisor.py -v
```

## Future Improvements

1. Add more sophisticated metrics analysis
2. Implement trend analysis over time
3. Add machine learning for predictive analytics
4. Enhance recommendation system with more context

## Deployment Notes

This change requires:
- OpenAI API access for embeddings
- Redis for metrics caching
- Additional environment variables for API configuration
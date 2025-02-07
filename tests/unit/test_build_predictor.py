"""Unit tests for build predictor."""
import pytest
import numpy as np
from unittest.mock import AsyncMock, patch
from langchain_jenkins.ai.build_predictor import (
    BuildPredictor,
    BuildPrediction
)

@pytest.fixture
def predictor():
    """Create a build predictor for testing."""
    predictor = BuildPredictor()
    predictor.analysis_chain = AsyncMock()
    return predictor

def test_extract_features(predictor):
    """Test feature extraction."""
    build_history = [
        {
            "duration": 100,
            "changes": ["change1", "change2"],
            "culprits": ["user1"],
            "resourceUsage": {
                "memory": 80,
                "cpu": 60
            },
            "artifacts": ["artifact1"],
            "actions": ["action1", "action2"],
            "result": "SUCCESS"
        }
    ]
    
    features = predictor._extract_features(build_history)
    
    assert isinstance(features, np.ndarray)
    assert features.shape == (1, 8)  # 8 features including result
    assert features[0][0] == 100  # duration
    assert features[0][1] == 2    # num changes
    assert features[0][7] == 1    # success

@pytest.mark.asyncio
async def test_predict_build(predictor):
    """Test build prediction."""
    # Mock AI response
    predictor.analysis_chain.arun.return_value = """{
        "risk_factors": ["High complexity"],
        "warning_signs": ["Many changes"],
        "recommendations": ["Code review"]
    }"""
    
    current_build = {
        "duration": 100,
        "changes": ["change1"],
        "culprits": [],
        "resourceUsage": {
            "memory": 50,
            "cpu": 40
        },
        "artifacts": [],
        "actions": ["action1"],
        "result": "UNKNOWN"
    }
    
    build_history = [
        {
            "duration": 90,
            "changes": [],
            "culprits": [],
            "resourceUsage": {
                "memory": 40,
                "cpu": 30
            },
            "artifacts": [],
            "actions": ["action1"],
            "result": "SUCCESS"
        }
    ]
    
    result = await predictor.predict_build(current_build, build_history)
    
    assert isinstance(result, BuildPrediction)
    assert isinstance(result.probability, float)
    assert 0 <= result.probability <= 1
    assert len(result.risk_factors) > 0
    assert len(result.warning_signs) > 0
    assert len(result.recommendations) > 0

def test_calculate_risk_score(predictor):
    """Test risk score calculation."""
    build = {
        "changes": ["change1", "change2"],
        "culprits": ["user1"],
        "resourceUsage": {
            "memory": 80,
            "cpu": 60
        }
    }
    
    history = [
        {"result": "SUCCESS"},
        {"result": "FAILURE"},
        {"result": "SUCCESS"}
    ]
    
    risk_score = predictor._calculate_risk_score(build, history)
    
    assert isinstance(risk_score, float)
    assert 0 <= risk_score <= 1

def test_train_model(predictor):
    """Test model training."""
    build_history = [
        {
            "duration": 100,
            "changes": ["change1"],
            "culprits": [],
            "resourceUsage": {
                "memory": 50,
                "cpu": 40
            },
            "artifacts": [],
            "actions": ["action1"],
            "result": "SUCCESS"
        },
        {
            "duration": 150,
            "changes": ["change1", "change2"],
            "culprits": ["user1"],
            "resourceUsage": {
                "memory": 80,
                "cpu": 70
            },
            "artifacts": [],
            "actions": ["action1", "action2"],
            "result": "FAILURE"
        }
    ]
    
    predictor._train_model(build_history)
    
    assert hasattr(predictor.classifier, "classes_")
    assert predictor.classifier.n_features_in_ == 7  # Number of features
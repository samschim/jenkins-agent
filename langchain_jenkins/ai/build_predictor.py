"""AI-powered build prediction module."""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from ..config.config import config
from ..utils.cache import cache

@dataclass
class BuildPrediction:
    """Build prediction results."""
    probability: float
    risk_factors: List[str]
    warning_signs: List[str]
    recommendations: List[str]

class BuildPredictor:
    """Predicts build outcomes using ML and AI."""
    
    def __init__(self):
        """Initialize build predictor."""
        self.llm = ChatOpenAI(
            model=config.llm.model,
            temperature=0.1
        )
        
        # Initialize ML models
        self.classifier = RandomForestClassifier(n_estimators=100)
        self.scaler = StandardScaler()
        
        # Create analysis chain
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at analyzing Jenkins build patterns.
Analyze the build history and metrics to identify risk factors.

Format your response as JSON with these keys:
- risk_factors: list of identified risk factors
- warning_signs: list of early warning signs
- recommendations: list of preventive actions"""),
            ("human", "{build_metrics}")
        ])
        
        self.analysis_chain = LLMChain(
            llm=self.llm,
            prompt=self.analysis_prompt
        )
    
    def _extract_features(
        self,
        build_history: List[Dict[str, Any]]
    ) -> np.ndarray:
        """Extract features from build history.
        
        Args:
            build_history: List of build information
            
        Returns:
            Feature matrix
        """
        features = []
        for build in build_history:
            build_features = [
                build.get("duration", 0),
                len(build.get("changes", [])),
                len(build.get("culprits", [])),
                build.get("resourceUsage", {}).get("memory", 0),
                build.get("resourceUsage", {}).get("cpu", 0),
                len(build.get("artifacts", [])),
                len(build.get("actions", [])),
                1 if build.get("result") == "SUCCESS" else 0
            ]
            features.append(build_features)
        
        return np.array(features)
    
    def _train_model(
        self,
        build_history: List[Dict[str, Any]]
    ) -> None:
        """Train the ML model on build history.
        
        Args:
            build_history: List of build information
        """
        # Extract features and labels
        features = self._extract_features(build_history)
        X = features[:, :-1]  # All columns except last
        y = features[:, -1]   # Last column (success/failure)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.classifier.fit(X_scaled, y)
    
    @cache.cached("build_prediction")
    async def predict_build(
        self,
        current_build: Dict[str, Any],
        build_history: List[Dict[str, Any]]
    ) -> BuildPrediction:
        """Predict build outcome using ML and AI.
        
        Args:
            current_build: Current build information
            build_history: Previous build history
            
        Returns:
            Build prediction results
        """
        # Train model if needed
        if not hasattr(self.classifier, "classes_"):
            self._train_model(build_history)
        
        # Extract and scale features
        features = self._extract_features([current_build])
        X = features[:, :-1]
        X_scaled = self.scaler.transform(X)
        
        # Get ML prediction
        probability = self.classifier.predict_proba(X_scaled)[0][1]
        
        # Get feature importance
        importances = self.classifier.feature_importances_
        feature_names = [
            "duration", "changes", "culprits", "memory",
            "cpu", "artifacts", "actions"
        ]
        important_features = [
            (name, importance)
            for name, importance in zip(feature_names, importances)
            if importance > 0.1
        ]
        
        # Prepare metrics for AI analysis
        metrics = {
            "probability": probability,
            "important_features": important_features,
            "current_build": current_build,
            "recent_history": build_history[-5:]  # Last 5 builds
        }
        
        # Get AI analysis
        result = await self.analysis_chain.arun(
            build_metrics=str(metrics)
        )
        analysis = eval(result)
        
        return BuildPrediction(
            probability=probability,
            risk_factors=analysis["risk_factors"],
            warning_signs=analysis["warning_signs"],
            recommendations=analysis["recommendations"]
        )
    
    def _calculate_risk_score(
        self,
        build: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> float:
        """Calculate risk score for a build.
        
        Args:
            build: Build information
            history: Build history
            
        Returns:
            Risk score between 0 and 1
        """
        risk_score = 0.0
        weights = {
            "changes": 0.3,
            "culprits": 0.2,
            "resources": 0.2,
            "history": 0.3
        }
        
        # Risk from changes
        num_changes = len(build.get("changes", []))
        risk_score += weights["changes"] * min(num_changes / 10, 1.0)
        
        # Risk from culprits
        num_culprits = len(build.get("culprits", []))
        risk_score += weights["culprits"] * min(num_culprits / 5, 1.0)
        
        # Risk from resource usage
        if "resourceUsage" in build:
            memory_usage = build["resourceUsage"].get("memory", 0)
            cpu_usage = build["resourceUsage"].get("cpu", 0)
            resource_risk = (
                (memory_usage / 100 + cpu_usage / 100) / 2
            )
            risk_score += weights["resources"] * resource_risk
        
        # Risk from history
        if history:
            recent_failures = sum(
                1 for b in history[-5:]
                if b.get("result") != "SUCCESS"
            )
            risk_score += weights["history"] * (recent_failures / 5)
        
        return min(risk_score, 1.0)

# Global instance
predictor = BuildPredictor()
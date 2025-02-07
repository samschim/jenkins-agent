"""AI-enhanced log analysis module."""
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.schema import HumanMessage, AIMessage
from ..config.config import config
from ..utils.cache import cache

@dataclass
class LogPattern:
    """Pattern found in log entries."""
    pattern: str
    frequency: int
    severity: str
    context: str

@dataclass
class LogAnalysis:
    """Analysis results for log entries."""
    patterns: List[LogPattern]
    error_types: List[str]
    root_causes: List[str]
    recommendations: List[str]
    severity: str

class AILogAnalyzer:
    """AI-powered log analysis."""
    
    def __init__(self):
        """Initialize AI log analyzer."""
        self.llm = ChatOpenAI(
            model=config.llm.model,
            temperature=0.1
        )
        
        # Create analysis chain
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert Jenkins log analyzer. Analyze the build log and provide:
1. Common patterns and their frequency
2. Error types and their severity
3. Root causes of failures
4. Recommendations for fixes

Format your response as JSON with these keys:
- patterns: list of {pattern, frequency, severity, context}
- error_types: list of error types found
- root_causes: list of identified root causes
- recommendations: list of suggested fixes
- severity: overall severity (low/medium/high/critical)"""),
            ("human", "{log_text}")
        ])
        
        self.analysis_chain = LLMChain(
            llm=self.llm,
            prompt=self.analysis_prompt
        )
        
        # Create prediction chain
        self.prediction_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at predicting Jenkins build failures.
Analyze the build patterns and predict potential failures.

Format your response as JSON with these keys:
- failure_probability: float between 0 and 1
- risk_factors: list of identified risk factors
- warning_signs: list of early warning signs
- preventive_actions: list of recommended actions"""),
            ("human", "{build_patterns}")
        ])
        
        self.prediction_chain = LLMChain(
            llm=self.llm,
            prompt=self.prediction_prompt
        )
    
    @cache.cached("log_analysis")
    async def analyze_log(self, log_text: str) -> LogAnalysis:
        """Analyze a build log using AI.
        
        Args:
            log_text: Build log text to analyze
            
        Returns:
            Log analysis results
        """
        # Extract key sections (limit size for token constraints)
        sections = self._extract_log_sections(log_text)
        summary = "\n".join(sections[:3])  # Most relevant sections
        
        # Get AI analysis
        result = await self.analysis_chain.arun(log_text=summary)
        analysis = eval(result)  # Convert string to dict
        
        # Convert to LogAnalysis object
        return LogAnalysis(
            patterns=[
                LogPattern(**pattern)
                for pattern in analysis["patterns"]
            ],
            error_types=analysis["error_types"],
            root_causes=analysis["root_causes"],
            recommendations=analysis["recommendations"],
            severity=analysis["severity"]
        )
    
    def _extract_log_sections(self, log_text: str) -> List[str]:
        """Extract relevant sections from log text.
        
        Args:
            log_text: Full log text
            
        Returns:
            List of relevant log sections
        """
        sections = []
        
        # Extract error sections
        error_pattern = r"ERROR:.*?(?=\n\n|\Z)"
        error_sections = re.findall(error_pattern, log_text, re.DOTALL)
        sections.extend(error_sections)
        
        # Extract build step sections
        step_pattern = r"\[.*?\] Running step:.*?(?=\n\n|\Z)"
        step_sections = re.findall(step_pattern, log_text, re.DOTALL)
        sections.extend(step_sections)
        
        # Extract test failure sections
        test_pattern = r"Test.*?FAILED.*?(?=\n\n|\Z)"
        test_sections = re.findall(test_pattern, log_text, re.DOTALL)
        sections.extend(test_sections)
        
        return sections
    
    @cache.cached("failure_prediction")
    async def predict_failures(
        self,
        build_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Predict potential build failures using AI.
        
        Args:
            build_history: List of previous build results
            
        Returns:
            Failure prediction results
        """
        # Extract build patterns
        patterns = self._extract_build_patterns(build_history)
        
        # Get AI prediction
        result = await self.prediction_chain.arun(
            build_patterns=str(patterns)
        )
        
        return eval(result)  # Convert string to dict
    
    def _extract_build_patterns(
        self,
        build_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extract patterns from build history.
        
        Args:
            build_history: List of previous build results
            
        Returns:
            Build patterns and statistics
        """
        patterns = {
            "success_rate": 0,
            "failure_patterns": [],
            "timing_patterns": [],
            "resource_patterns": []
        }
        
        # Calculate success rate
        successes = sum(
            1 for build in build_history
            if build.get("result") == "SUCCESS"
        )
        patterns["success_rate"] = successes / len(build_history)
        
        # Analyze failure patterns
        failures = [
            build for build in build_history
            if build.get("result") != "SUCCESS"
        ]
        if failures:
            failure_causes = [
                build.get("failureCause", "unknown")
                for build in failures
            ]
            patterns["failure_patterns"] = self._find_common_patterns(
                failure_causes
            )
        
        # Analyze timing patterns
        durations = [
            build.get("duration", 0)
            for build in build_history
        ]
        patterns["timing_patterns"] = {
            "mean": np.mean(durations),
            "std": np.std(durations),
            "anomalies": self._find_timing_anomalies(durations)
        }
        
        # Analyze resource patterns
        if "resourceUsage" in build_history[0]:
            memory_usage = [
                build["resourceUsage"].get("memory", 0)
                for build in build_history
            ]
            cpu_usage = [
                build["resourceUsage"].get("cpu", 0)
                for build in build_history
            ]
            patterns["resource_patterns"] = {
                "memory": {
                    "mean": np.mean(memory_usage),
                    "max": max(memory_usage)
                },
                "cpu": {
                    "mean": np.mean(cpu_usage),
                    "max": max(cpu_usage)
                }
            }
        
        return patterns
    
    def _find_common_patterns(self, items: List[str]) -> List[Dict[str, Any]]:
        """Find common patterns in a list of strings.
        
        Args:
            items: List of strings to analyze
            
        Returns:
            List of pattern dictionaries
        """
        patterns = {}
        for item in items:
            if item in patterns:
                patterns[item]["count"] += 1
            else:
                patterns[item] = {
                    "pattern": item,
                    "count": 1
                }
        
        # Sort by frequency
        return sorted(
            patterns.values(),
            key=lambda x: x["count"],
            reverse=True
        )
    
    def _find_timing_anomalies(
        self,
        durations: List[float]
    ) -> List[Dict[str, Any]]:
        """Find timing anomalies in build durations.
        
        Args:
            durations: List of build durations
            
        Returns:
            List of anomalies
        """
        mean = np.mean(durations)
        std = np.std(durations)
        threshold = 2  # Standard deviations
        
        anomalies = []
        for duration in durations:
            z_score = abs(duration - mean) / std
            if z_score > threshold:
                anomalies.append({
                    "duration": duration,
                    "z_score": z_score,
                    "type": "slow" if duration > mean else "fast"
                })
        
        return sorted(
            anomalies,
            key=lambda x: abs(x["z_score"]),
            reverse=True
        )

class BuildTroubleshooter:
    """AI-powered build troubleshooter."""
    
    def __init__(self):
        """Initialize build troubleshooter."""
        self.llm = ChatOpenAI(
            model=config.llm.model,
            temperature=0.1
        )
        
        # Create troubleshooting chain
        self.troubleshoot_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert Jenkins build troubleshooter.
Analyze the build failure and provide step-by-step troubleshooting steps.

Format your response as JSON with these keys:
- diagnosis: detailed diagnosis of the problem
- steps: list of troubleshooting steps
- verification: list of verification steps
- prevention: list of preventive measures"""),
            ("human", "Build failure details:\n{failure_details}")
        ])
        
        self.troubleshoot_chain = LLMChain(
            llm=self.llm,
            prompt=self.troubleshoot_prompt
        )
    
    @cache.cached("troubleshooting")
    async def troubleshoot_failure(
        self,
        build_info: Dict[str, Any],
        log_analysis: LogAnalysis
    ) -> Dict[str, Any]:
        """Generate troubleshooting steps for a build failure.
        
        Args:
            build_info: Build information
            log_analysis: Log analysis results
            
        Returns:
            Troubleshooting steps and recommendations
        """
        # Combine build info and log analysis
        failure_details = {
            "build_info": build_info,
            "error_types": log_analysis.error_types,
            "root_causes": log_analysis.root_causes,
            "patterns": [
                {
                    "pattern": p.pattern,
                    "severity": p.severity,
                    "context": p.context
                }
                for p in log_analysis.patterns
            ]
        }
        
        # Get AI troubleshooting steps
        result = await self.troubleshoot_chain.arun(
            failure_details=str(failure_details)
        )
        
        return eval(result)  # Convert string to dict

# Global instances
log_analyzer = AILogAnalyzer()
troubleshooter = BuildTroubleshooter()
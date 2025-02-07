"""Security scanning tools for Jenkins pipelines."""
import json
import re
from typing import Dict, Any, List, Optional
from langchain_community.chat_models import ChatOpenAI
from ..config.config import config

class SecurityScanner:
    """Security scanner for Jenkins pipelines."""
    
    def __init__(self):
        """Initialize security scanner."""
        self.llm = ChatOpenAI(
            model=config.llm.model,
            temperature=config.llm.temperature,
            openai_api_base=config.llm.api_base,
            openai_api_key=config.llm.api_key
        )
        
        # Common security rules
        self.rules = {
            "credentials": {
                "patterns": [
                    r"password\s*=",
                    r"secret\s*=",
                    r"token\s*=",
                    r"key\s*="
                ],
                "severity": "high",
                "description": "Hardcoded credentials"
            },
            "shell_injection": {
                "patterns": [
                    r"sh\s+['\"]\${.*}",
                    r"bat\s+['\"]\${.*}"
                ],
                "severity": "high",
                "description": "Potential shell injection"
            },
            "unsafe_git": {
                "patterns": [
                    r"git\s+clone\s+http://",
                    r"git\s+clone\s+git://"
                ],
                "severity": "medium",
                "description": "Insecure Git protocol"
            }
        }
    
    async def scan_pipeline(self, pipeline: str) -> Dict[str, Any]:
        """Scan a pipeline for security issues.
        
        Args:
            pipeline: Pipeline configuration
            
        Returns:
            Scan results and recommendations
        """
        findings = []
        
        # Check each rule
        for rule_name, rule in self.rules.items():
            for pattern in rule["patterns"]:
                matches = re.finditer(pattern, pipeline, re.IGNORECASE)
                for match in matches:
                    findings.append({
                        "rule": rule_name,
                        "severity": rule["severity"],
                        "description": rule["description"],
                        "line": pipeline.count("\n", 0, match.start()) + 1,
                        "match": match.group(0)
                    })
        
        # Get security analysis from LLM
        if findings:
            prompt = f"""
            Analyze these security findings in a Jenkins pipeline:
            Pipeline: {pipeline}
            Findings: {json.dumps(findings)}
            
            Provide a JSON response with:
            1. Risk assessment for each finding
            2. Recommended fixes
            3. Overall security score (0-100)
            4. Priority of fixes (high/medium/low)
            """
            
            response = await self.llm.agenerate([prompt])
            analysis = json.loads(response.generations[0][0].text)
        else:
            analysis = {
                "risk_assessment": [],
                "recommended_fixes": [],
                "security_score": 100,
                "priority": "low"
            }
        
        return {
            "status": "success",
            "findings": findings,
            "analysis": analysis
        }
    
    async def secure_pipeline(self, pipeline: str) -> Dict[str, Any]:
        """Enhance pipeline security.
        
        Args:
            pipeline: Pipeline configuration
            
        Returns:
            Secured pipeline and improvements
        """
        # First scan the pipeline
        scan_results = await self.scan_pipeline(pipeline)
        
        if scan_results["findings"]:
            prompt = f"""
            Enhance the security of this Jenkins pipeline:
            {pipeline}
            
            Fix these security issues:
            {json.dumps(scan_results["findings"])}
            
            Return a JSON response with:
            1. Secured pipeline code
            2. List of improvements made
            3. Additional security recommendations
            """
            
            response = await self.llm.agenerate([prompt])
            improvements = json.loads(response.generations[0][0].text)
            
            # Verify the secured pipeline
            verify_results = await self.scan_pipeline(improvements["pipeline"])
            
            return {
                "status": "success",
                "original_pipeline": pipeline,
                "secured_pipeline": improvements["pipeline"],
                "improvements": improvements["improvements"],
                "recommendations": improvements["recommendations"],
                "verification": verify_results
            }
        else:
            return {
                "status": "success",
                "message": "Pipeline already follows security best practices",
                "pipeline": pipeline,
                "security_score": 100
            }
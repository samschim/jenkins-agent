"""Pipeline generation tools for Jenkins."""
import json
from typing import Dict, Any, List, Optional
from langchain_community.chat_models import ChatOpenAI
from ..config.config import config

class PipelineGenerator:
    """Generates Jenkins pipelines based on project requirements."""
    
    def __init__(self):
        """Initialize pipeline generator."""
        self.llm = ChatOpenAI(
            model=config.llm.model,
            temperature=config.llm.temperature,
            openai_api_base=config.llm.api_base,
            openai_api_key=config.llm.api_key
        )
        
        # Common pipeline templates
        self.templates = {
            "java": self._get_java_template(),
            "python": self._get_python_template(),
            "node": self._get_node_template(),
            "docker": self._get_docker_template()
        }
    
    def _get_java_template(self) -> str:
        """Get Java project pipeline template."""
        return """pipeline {
    agent any
    
    tools {
        maven 'Maven 3'
        jdk 'JDK 11'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Build') {
            steps {
                sh 'mvn clean package'
            }
        }
        
        stage('Test') {
            steps {
                sh 'mvn test'
            }
            post {
                always {
                    junit '**/target/surefire-reports/*.xml'
                }
            }
        }
        
        {additional_stages}
    }
    
    post {
        always {
            cleanWs()
        }
    }
}"""
    
    def _get_python_template(self) -> str:
        """Get Python project pipeline template."""
        return """pipeline {
    agent any
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Setup') {
            steps {
                sh '''
                    python -m venv venv
                    . venv/bin/activate
                    pip install -r requirements.txt
                '''
            }
        }
        
        stage('Test') {
            steps {
                sh '''
                    . venv/bin/activate
                    pytest tests/
                '''
            }
            post {
                always {
                    junit '**/test-results/*.xml'
                }
            }
        }
        
        {additional_stages}
    }
    
    post {
        always {
            cleanWs()
        }
    }
}"""
    
    def _get_node_template(self) -> str:
        """Get Node.js project pipeline template."""
        return """pipeline {
    agent any
    
    tools {
        nodejs 'Node 16'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Install') {
            steps {
                sh 'npm install'
            }
        }
        
        stage('Test') {
            steps {
                sh 'npm test'
            }
        }
        
        {additional_stages}
    }
    
    post {
        always {
            cleanWs()
        }
    }
}"""
    
    def _get_docker_template(self) -> str:
        """Get Docker project pipeline template."""
        return """pipeline {
    agent any
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Build') {
            steps {
                sh 'docker build -t ${IMAGE_NAME}:${BUILD_NUMBER} .'
            }
        }
        
        stage('Test') {
            steps {
                sh '''
                    docker run --rm ${IMAGE_NAME}:${BUILD_NUMBER} test
                '''
            }
        }
        
        {additional_stages}
    }
    
    post {
        always {
            cleanWs()
            sh 'docker rmi ${IMAGE_NAME}:${BUILD_NUMBER} || true'
        }
    }
}"""
    
    async def _generate_stages(
        self,
        requirements: List[str],
        project_type: str
    ) -> str:
        """Generate additional pipeline stages based on requirements.
        
        Args:
            requirements: List of project requirements
            project_type: Type of project (java, python, node, docker)
            
        Returns:
            Pipeline stages as string
        """
        prompt = f"""
        Generate Jenkins pipeline stages for a {project_type} project with these requirements:
        {json.dumps(requirements)}
        
        The stages should:
        1. Follow best practices for {project_type} projects
        2. Include necessary environment setup
        3. Handle dependencies correctly
        4. Include proper error handling
        5. Use appropriate tools and commands
        
        Return ONLY the stage definitions in Jenkinsfile format.
        """
        
        response = await self.llm.agenerate([prompt])
        return response.generations[0][0].text.strip()
    
    async def _analyze_requirements(
        self,
        requirements: List[str]
    ) -> Dict[str, Any]:
        """Analyze project requirements for pipeline generation.
        
        Args:
            requirements: List of project requirements
            
        Returns:
            Analysis results
        """
        prompt = f"""
        Analyze these project requirements for Jenkins pipeline generation:
        {json.dumps(requirements)}
        
        Provide a JSON response with:
        1. Required tools and versions
        2. Build steps needed
        3. Test requirements
        4. Deployment needs
        5. Security considerations
        6. Performance optimizations
        """
        
        response = await self.llm.agenerate([prompt])
        return json.loads(response.generations[0][0].text)
    
    async def _validate_pipeline(self, pipeline: str) -> Dict[str, Any]:
        """Validate a pipeline configuration.
        
        Args:
            pipeline: Pipeline configuration
            
        Returns:
            Validation results
        """
        prompt = f"""
        Validate this Jenkins pipeline configuration:
        {pipeline}
        
        Check for:
        1. Syntax correctness
        2. Security issues
        3. Best practices
        4. Performance concerns
        5. Error handling
        
        Return a JSON response with validation results.
        """
        
        response = await self.llm.agenerate([prompt])
        return json.loads(response.generations[0][0].text)
    
    async def generate_pipeline(
        self,
        project_type: str,
        requirements: List[str],
        validate: bool = True
    ) -> Dict[str, Any]:
        """Generate a Jenkins pipeline based on requirements.
        
        Args:
            project_type: Type of project (java, python, node, docker)
            requirements: List of project requirements
            validate: Whether to validate the generated pipeline
            
        Returns:
            Generated pipeline and metadata
        """
        try:
            # Get base template
            if project_type not in self.templates:
                return {
                    "status": "error",
                    "error": f"Unsupported project type: {project_type}"
                }
            
            template = self.templates[project_type]
            
            # Analyze requirements
            analysis = await self._analyze_requirements(requirements)
            
            # Generate additional stages
            stages = await self._generate_stages(requirements, project_type)
            
            # Combine template and stages
            pipeline = template.format(additional_stages=stages)
            
            # Validate if requested
            validation = None
            if validate:
                validation = await self._validate_pipeline(pipeline)
                if not validation.get("valid", False):
                    return {
                        "status": "error",
                        "error": "Pipeline validation failed",
                        "validation": validation
                    }
            
            return {
                "status": "success",
                "pipeline": pipeline,
                "analysis": analysis,
                "validation": validation,
                "project_type": project_type
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def optimize_pipeline(
        self,
        pipeline: str,
        project_type: str
    ) -> Dict[str, Any]:
        """Optimize a pipeline configuration.
        
        Args:
            pipeline: Pipeline configuration
            project_type: Type of project
            
        Returns:
            Optimized pipeline and improvements
        """
        prompt = f"""
        Optimize this {project_type} Jenkins pipeline:
        {pipeline}
        
        Consider:
        1. Build performance
        2. Resource usage
        3. Parallel execution
        4. Caching
        5. Best practices
        
        Return a JSON response with:
        1. Optimized pipeline
        2. List of improvements
        3. Expected benefits
        """
        
        try:
            response = await self.llm.agenerate([prompt])
            result = json.loads(response.generations[0][0].text)
            
            # Validate optimized pipeline
            validation = await self._validate_pipeline(result["pipeline"])
            if not validation.get("valid", False):
                return {
                    "status": "error",
                    "error": "Optimized pipeline validation failed",
                    "validation": validation
                }
            
            return {
                "status": "success",
                "original_pipeline": pipeline,
                "optimized_pipeline": result["pipeline"],
                "improvements": result["improvements"],
                "benefits": result["benefits"],
                "validation": validation
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
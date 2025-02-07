"""FastAPI web interface for Jenkins Agent."""
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, WebSocket, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta
import asyncio
from ..agents.supervisor import SupervisorAgent
from ..config.config import config

# Initialize FastAPI app
app = FastAPI(
    title="Jenkins Agent API",
    description="API for interacting with Jenkins through LangChain agents",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# JWT settings
JWT_SECRET = "your-secret-key"  # In production, use environment variable
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Initialize supervisor agent
supervisor = SupervisorAgent()

# Models
class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str

class TaskRequest(BaseModel):
    """Task request model."""
    task: str
    agent_type: Optional[str] = None

class TaskResponse(BaseModel):
    """Task response model."""
    status: str
    result: Dict[str, Any]
    task: str
    agent_type: str

# Authentication
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user from token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return username
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

# Routes
@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login to get access token."""
    # In production, validate against your user database
    if form_data.username != config.jenkins.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(
        data={"sub": form_data.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/task", response_model=TaskResponse)
async def execute_task(
    task_request: TaskRequest,
    current_user: str = Depends(get_current_user)
):
    """Execute a task using the supervisor agent."""
    try:
        if task_request.agent_type:
            result = await supervisor.handle_task(
                task_request.task,
                agent_type=task_request.agent_type
            )
        else:
            result = await supervisor.handle_task(task_request.task)
        
        return {
            "status": "success",
            "result": result,
            "task": task_request.task,
            "agent_type": result.get("agent_type", "unknown")
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    try:
        while True:
            # Receive task from client
            data = await websocket.receive_json()
            task = data.get("task")
            if not task:
                await websocket.send_json({
                    "status": "error",
                    "message": "No task provided"
                })
                continue
            
            # Execute task
            try:
                result = await supervisor.handle_task(task)
                await websocket.send_json({
                    "status": "success",
                    "result": result,
                    "task": task
                })
            except Exception as e:
                await websocket.send_json({
                    "status": "error",
                    "message": str(e),
                    "task": task
                })
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

@app.get("/agents")
async def list_agents(current_user: str = Depends(get_current_user)):
    """List available agent types."""
    return {
        "agents": [
            {
                "type": "build",
                "description": "Manages Jenkins builds"
            },
            {
                "type": "log",
                "description": "Analyzes build logs"
            },
            {
                "type": "pipeline",
                "description": "Manages Jenkins pipelines"
            },
            {
                "type": "plugin",
                "description": "Manages Jenkins plugins"
            },
            {
                "type": "user",
                "description": "Manages Jenkins users"
            }
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
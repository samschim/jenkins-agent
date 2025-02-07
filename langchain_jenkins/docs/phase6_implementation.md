# Phase 6: User Interface Implementation

## Overview
Phase 6 adds user interfaces to the LangChain Jenkins Agent system, including a FastAPI web interface, CLI tool, and Discord bot integration.

## New Components

### 1. Web Interface
#### FastAPI Server (`web/app.py`)
- RESTful API endpoints
- WebSocket support
- JWT authentication
- CORS support

#### Features
- Task execution
- Agent management
- Real-time updates
- Authentication

### 2. CLI Tool
#### Command-Line Interface (`cli/jenkins_cli.py`)
- Interactive mode
- Rich text formatting
- Progress indicators
- JSON output

#### Features
- Task execution
- Agent listing
- Interactive shell
- Authentication

### 3. Discord Integration
#### Discord Bot (`discord/bot.py`)
- Slash commands
- Rich embeds
- Error handling
- Authentication

#### Features
- Task execution
- Agent listing
- Help system
- Status updates

## Implementation Details

### Web Interface
```python
# Initialize FastAPI app
app = FastAPI(
    title="Jenkins Agent API",
    description="API for interacting with Jenkins through LangChain agents",
    version="1.0.0"
)

# Execute task endpoint
@app.post("/task", response_model=TaskResponse)
async def execute_task(
    task_request: TaskRequest,
    current_user: str = Depends(get_current_user)
):
    result = await supervisor.handle_task(task_request.task)
    return {
        "status": "success",
        "result": result,
        "task": task_request.task,
        "agent_type": result.get("agent_type", "unknown")
    }
```

### CLI Tool
```python
# Task execution command
@cli.command()
@click.argument("task")
@click.option("--agent", help="Specific agent type to use")
def task(task: str, agent: Optional[str] = None):
    with Progress() as progress:
        task_id = progress.add_task("[cyan]Executing task...", total=None)
        result = asyncio.run(client.execute_task(task, agent))
        progress.remove_task(task_id)
```

### Discord Bot
```python
@bot.tree.command(name="task", description="Execute a Jenkins task")
async def task_command(
    interaction: discord.Interaction,
    task: str,
    agent: Optional[str] = None
):
    result = await bot.execute_task(task, agent)
    embed = discord.Embed(
        title="Task Completed",
        description=task,
        color=discord.Color.green()
    )
    await interaction.followup.send(embed=embed)
```

## Usage Examples

### Web Interface
```bash
# Start the server
uvicorn langchain_jenkins.web.app:app --host 0.0.0.0 --port 8000

# Execute task (using curl)
curl -X POST "http://localhost:8000/task" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"task": "Start build for project-x"}'
```

### CLI Tool
```bash
# Login
jenkins-cli login

# Execute task
jenkins-cli task "Start build for project-x"

# Interactive mode
jenkins-cli interactive
```

### Discord Bot
```bash
# Set token
export DISCORD_TOKEN=your-token

# Start bot
python -m langchain_jenkins.discord.bot

# Use commands in Discord
/task Start build for project-x
/agents
/help
```

## Configuration

### Web Interface
```python
# JWT settings
JWT_SECRET = "your-secret-key"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### CLI Tool
```python
# API settings
BASE_URL = "http://localhost:8000"
TOKEN_FILE = "~/.jenkins-cli/token"

# Output settings
THEME = "monokai"
PROGRESS_STYLE = "cyan"
```

### Discord Bot
```python
# Bot settings
COMMAND_PREFIX = "/"
EMBED_COLOR = discord.Color.blue()
MAX_RESULT_LENGTH = 1000
```

## Testing
```python
# Test web interface
@pytest.mark.asyncio
async def test_execute_task():
    response = await client.post(
        "/task",
        json={"task": "test task"}
    )
    assert response.status_code == 200

# Test CLI
def test_cli_task():
    result = runner.invoke(cli, ["task", "test task"])
    assert result.exit_code == 0

# Test Discord bot
@pytest.mark.asyncio
async def test_task_command():
    interaction = MockInteraction()
    await task_command(interaction, "test task")
    assert interaction.response.sent
```

## Next Steps
1. Add web frontend (React/Vue)
2. Enhance CLI features
3. Add more Discord commands
4. Improve error handling
5. Add monitoring
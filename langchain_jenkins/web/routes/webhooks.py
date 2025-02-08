from fastapi import APIRouter, Request, HTTPException
from langchain_jenkins.webhooks.github_handler import GitHubWebhookHandler

router = APIRouter()
github_handler = GitHubWebhookHandler()

@router.post("/github")
async def github_webhook(request: Request):
    """Handle GitHub webhook events."""
    try:
        result = await github_handler.handle_webhook(request)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
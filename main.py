"""
GitHub Claude Webhook Service

A FastAPI-based webhook service that automatically responds to GitHub issues using Claude AI.
This service listens for GitHub webhook events and provides AI-powered responses to issues
marked with the 'claude-discuss' label.

Reference: https://docs.github.com/en/webhooks/webhook-events-and-payloads
"""

import subprocess
import json
import hmac
import hashlib
import os
import logging
from typing import Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import uvicorn
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="GitHub Claude Webhook")

claude_reply_signature = "\n\n---\n*🔧 此回覆由 [Claude Code](https://claude.ai/code) 自動分析生成*"

def analyze_issue_with_claude(issue_data: str) -> str:
    prompt = f"""作為一個專業的軟體開發助手，請分析以下 GitHub issue 並提供建設性的回應。
以下是 issue 的詳細資訊，以 JSON 格式呈現：

{issue_data}

請根據以上對話歷史，提供適當的回應或繼續討論，可參考以下建議：
1. 對這個 issue 的分析（如果是首次回應）或對最新留言的回應
2. 建議的後續步驟或解決方向
3. 如果需要更多資訊，請具體說明需要什麼
4. 適當的表情符號讓回應更友善

請用繁體中文回應，保持專業但友善的語調。
"""

    try:
        timeout = int(os.getenv("CLAUDE_TIMEOUT"))
        result = subprocess.run(
            ["claude", prompt],
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
        )
        return f"{result.stdout.strip()}{claude_reply_signature}"
    except subprocess.CalledProcessError as e:
        logger.error(f"Claude API error: {e.stderr}")
        return f"🤖 分析系統暫時無法使用。我會稍後查看這個 issue。{claude_reply_signature}"
    except subprocess.TimeoutExpired:
        logger.error("Claude API timeout")
        return f"🤖 分析處理時間過長，我會稍後查看這個 issue。{claude_reply_signature}"
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return f"🤖 系統發生未預期的錯誤，我會稍後查看這個 issue。{claude_reply_signature}"


def post_comment(repo: str, issue_number: int, comment: str) -> bool:
    try:
        cmd = ["gh", "issue", "comment", str(issue_number), "--repo", repo, "--body", comment]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error posting comment: {e.stderr}")
        return False


async def handle_issues_labeled(repo_path: Path, payload: dict[str, Any]) -> JSONResponse:
    label = payload.get("label", {}).get("name")
    if label != "claude-discuss":
        logger.info(f"Label ignored: {label}")
        return JSONResponse({"message": f"Label ignored: {label}"}, status_code=200)

    repo_full_name = payload.get("repository", {}).get("full_name")
    issue_number = payload.get("issue", {}).get("number")

    try:
        gh_cmd = [
            "gh",
            "issue",
            "view",
            str(issue_number),
            "--json",
            "title,body,author,labels,state,comments",
        ]
        gh_result = subprocess.run(
            gh_cmd, cwd=repo_path, capture_output=True, text=True, check=True
        )
        issue_info = json.loads(gh_result.stdout)
        logger.info(f"Viewing issue #{issue_number}: {issue_info.get('title')}...")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error viewing issue with gh: {e.stderr}")
        raise HTTPException(status_code=500, detail="Failed to fetch issue details")
    except Exception as e:
        logger.error(f"Unexpected error viewing issue: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch issue details")

    claude_thoughts = analyze_issue_with_claude(json.dumps(issue_info, ensure_ascii=False))
    success = post_comment(repo_full_name, issue_number, claude_thoughts)

    if success:
        logger.info(f"Comment posted successfully for issue #{issue_number} in {repo_full_name}")
        return JSONResponse({"message": "Comment posted successfully"}, status_code=200)
    else:
        raise HTTPException(status_code=500, detail="Failed to post comment")


async def handle_issue_comment_created(repo_path: Path, payload: dict[str, Any]) -> JSONResponse:
    issue = payload.get("issue", {})
    issue_labels = issue.get("labels", [])
    if not any(label.get("name") == "claude-discuss" for label in issue_labels):
        logger.info(f"Issue #{issue.get('number')} not marked for claude-discuss")
        return JSONResponse({"message": "Issue not marked for claude-discuss"}, status_code=200)

    repo_full_name = payload.get("repository", {}).get("full_name")
    issue_number = issue.get("number")

    try:
        gh_cmd = [
            "gh",
            "issue",
            "view",
            str(issue_number),
            "--json",
            "title,body,author,labels,state,comments",
        ]
        gh_result = subprocess.run(
            gh_cmd, cwd=repo_path, capture_output=True, text=True, check=True
        )
        issue_info = json.loads(gh_result.stdout)
        logger.info(f"Viewing issue #{issue_number}: {issue_info.get('title')}...")
        comments = issue_info.get("comments", [])
        if comments and comments[-1].get("body", "").endswith(claude_reply_signature):
            logger.info(f"Issue #{issue_number} already has a Claude reply, skipping...")
            return JSONResponse({"message": "Claude reply already exists"}, status_code=200)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error viewing issue with gh: {e.stderr}")
        raise HTTPException(status_code=500, detail="Failed to fetch issue details")
    except Exception as e:
        logger.error(f"Unexpected error viewing issue: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch issue details")

    claude_thoughts = analyze_issue_with_claude(json.dumps(issue_info, ensure_ascii=False))
    success = post_comment(repo_full_name, issue_number, claude_thoughts)

    if success:
        logger.info(f"Reply posted successfully for issue #{issue_number} in {repo_full_name}")
        return JSONResponse({"message": "Reply posted successfully"}, status_code=200)
    else:
        raise HTTPException(status_code=500, detail="Failed to post reply")


@app.post("/webhook")
async def github_webhook(request: Request):
    try:
        secret = os.getenv("GITHUB_WEBHOOK_SECRET")
        if not secret:
            raise HTTPException(status_code=500, detail="Webhook secret not configured")

        signature = request.headers.get("X-Hub-Signature-256")
        if not signature:
            raise HTTPException(status_code=400, detail="Missing signature header")

        payload_body = await request.body()
        expected_signature = hmac.new(
            secret.encode("utf-8"), payload_body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(f"sha256={expected_signature}", signature):
            raise HTTPException(status_code=401, detail="Invalid signature")

        payload = json.loads(payload_body)
        event_type = request.headers.get("X-GitHub-Event") + "." + payload.get("action")

        repository = payload.get("repository", {})
        repo_full_name = repository.get("full_name")
        ssh_url = repository.get("ssh_url")

        workdir = Path.home() / "workdir"
        workdir.mkdir(exist_ok=True)
        repo_path = workdir / repo_full_name.split("/")[-1]

        if not repo_path.exists():
            try:
                subprocess.run(
                    ["git", "clone", ssh_url, "--depth", "1"],
                    cwd=workdir,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                logger.info(f"Cloned repository: {repo_full_name}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to clone repository {repo_full_name}: {e.stderr}")
                raise HTTPException(status_code=500, detail="Failed to clone repository")
        else:
            logger.info(f"Repository already exists: {repo_path}")

        if event_type == "issues.labeled":
            return await handle_issues_labeled(repo_path, payload)
        elif event_type == "issue_comment.created":
            return await handle_issue_comment_created(repo_path, payload)
        else:
            logger.info(f"Event ignored: {event_type}")
            return JSONResponse({"message": "Event ignored"}, status_code=200)

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail=e)


@app.get("/")
async def health_check():
    return {"status": "GitHub Issue Webhook is running"}


if __name__ == "__main__":
    port = int(os.getenv("PORT"))
    uvicorn.run(app, host="0.0.0.0", port=port)

import subprocess
import json
import hmac
import hashlib
import os
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="GitHub Issue Webhook")

def verify_signature(payload_body: bytes, signature: str, secret: str) -> bool:
    """驗證 GitHub webhook 簽名"""
    if not signature.startswith('sha256='):
        return False
    
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload_body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected_signature}", signature)

def analyze_issue_with_claude(issue_data: Dict[str, Any]) -> str:
    """使用 Claude API 分析 GitHub issue"""
    title = issue_data.get('title', '')
    body = issue_data.get('body', '')
    labels = [label['name'] for label in issue_data.get('labels', [])]
    author = issue_data.get('user', {}).get('login', 'Unknown')
    
    # 構建給 Claude 的 prompt
    prompt = f"""作為一個專業的軟體開發助手，請分析以下 GitHub issue 並提供建設性的回應。

Issue 標題: {title}
作者: {author}
標籤: {', '.join(labels) if labels else '無'}

Issue 內容:
{body}

請提供：
1. 對這個 issue 的初步分析
2. 建議的後續步驟或解決方向
3. 如果需要更多資訊，請具體說明需要什麼
4. 適當的表情符號讓回應更友善

請用繁體中文回應，保持專業但友善的語調。"""

    try:
        # 使用 subprocess 呼叫 claude 命令
        timeout = int(os.getenv('CLAUDE_TIMEOUT', 120))
        result = subprocess.run(
            ['claude', prompt],
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout
        )
        
        claude_response = result.stdout.strip()
        
        # 加上 Claude Code 標識
        response_with_signature = f"{claude_response}\n\n---\n*🔧 此回覆由 [Claude Code](https://claude.ai/code) 自動分析生成*"
        
        return response_with_signature
        
    except subprocess.CalledProcessError as e:
        print(f"Claude API error: {e.stderr}")
        return "🤖 抱歉，分析系統暫時無法使用。我會稍後回來查看這個 issue。\n\n---\n*🔧 此回覆由 [Claude Code](https://claude.ai/code) 自動分析生成*"
    except subprocess.TimeoutExpired:
        print("Claude API timeout")
        return "🤖 分析處理時間過長，請稍後我會再次查看這個 issue。\n\n---\n*🔧 此回覆由 [Claude Code](https://claude.ai/code) 自動分析生成*"
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return "🤖 系統發生未預期的錯誤，我會稍後回來查看這個 issue。\n\n---\n*🔧 此回覆由 [Claude Code](https://claude.ai/code) 自動分析生成*"

def post_comment_via_gh(repo: str, issue_number: int, comment: str) -> bool:
    """使用 gh CLI 發表留言"""
    try:
        cmd = [
            'gh', 'issue', 'comment', str(issue_number),
            '--repo', repo,
            '--body', comment
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error posting comment: {e.stderr}")
        return False

@app.post("/webhook")
async def github_webhook(request: Request):
    """處理 GitHub webhook"""
    try:
        # 讀取原始 payload 用於簽名驗證
        payload_body = await request.body()
        
        # 驗證簽名（如果設定了 secret）
        webhook_secret = os.getenv('GITHUB_WEBHOOK_SECRET')
        if webhook_secret:
            signature = request.headers.get('X-Hub-Signature-256')
            if not signature or not verify_signature(payload_body, signature, webhook_secret):
                raise HTTPException(status_code=401, detail="Invalid signature")
        
        payload = json.loads(payload_body)
        event_type = request.headers.get('X-GitHub-Event')
        
        if event_type != 'issues':
            return JSONResponse({"message": "Event ignored"}, status_code=200)
        
        action = payload.get('action')
        if action not in ['opened', 'reopened']:
            return JSONResponse({"message": "Action ignored"}, status_code=200)
        
        issue = payload.get('issue', {})
        repository = payload.get('repository', {})
        
        repo_full_name = repository.get('full_name')
        issue_number = issue.get('number')
        
        if not repo_full_name or not issue_number:
            raise HTTPException(status_code=400, detail="Missing required data")
        
        # 使用 Claude API 分析 issue 並產生想法
        claude_thoughts = analyze_issue_with_claude(issue)
        
        # 使用 gh CLI 發表留言
        success = post_comment_via_gh(repo_full_name, issue_number, claude_thoughts)
        
        if success:
            return JSONResponse({"message": "Comment posted successfully"}, status_code=200)
        else:
            raise HTTPException(status_code=500, detail="Failed to post comment")
            
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def health_check():
    return {"status": "GitHub Issue Webhook is running"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('PORT', 50454))
    uvicorn.run(app, host="0.0.0.0", port=port)

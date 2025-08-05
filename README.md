# GitHub Claude Webhook Service

A FastAPI-based webhook service that automatically responds to GitHub issues using Claude AI. This service listens for GitHub webhook events and provides AI-powered responses to issues marked with specific labels.

## Features

- **Automatic Issue Analysis**: Responds to issues labeled with `claude-discuss` with AI-powered analysis and suggestions
- **Automated Implementation**: Automatically implements solutions for issues labeled with `claude-implement` and creates pull requests
- **Secure Webhook Handling**: Validates GitHub webhook signatures for security
- **Branch Management**: Automatically creates feature branches for implementations
- **Pull Request Creation**: Automatically creates PRs with detailed descriptions

## Supported Labels

- `claude-discuss`: Provides AI-powered discussion and analysis for issues
- `claude-implement`: Automatically implements solutions and creates pull requests

## Prerequisites

Before running this service, ensure you have the following installed:

- [uv](https://docs.astral.sh/uv/) - Fast Python package installer and resolver
- [Claude CLI](https://claude.ai/code) - For AI-powered responses
- [GitHub CLI (gh)](https://cli.github.com/) - For GitHub API interactions

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd claude-assistant
```

### 2. Environment Configuration

Copy the sample environment file and configure it:

```bash
cp sample.env .env
```

Edit `.env` file with your configuration:

```env
# GitHub webhook secret (set this in your GitHub repository webhook settings)
GITHUB_WEBHOOK_SECRET=your_webhook_secret_here

# Port for the FastAPI server (default: 8000)
PORT=8000

# Timeout for Claude API calls in seconds (default: 300)
CLAUDE_TIMEOUT=300
```

## Configuration

### GitHub Webhook Setup

1. Go to your GitHub repository settings
2. Navigate to "Webhooks" and click "Add webhook"
3. Set the payload URL to your service endpoint: `https://your-domain:port/webhook`
4. Set content type to `application/json`
5. Set the secret to match your `GITHUB_WEBHOOK_SECRET`
6. Select individual events: `Issues` and `Issue comments`
7. Ensure the webhook is active

### Repository Access

Ensure the service has access to your repositories:

1. The GitHub CLI must be authenticated with appropriate permissions
2. The service needs read/write access to create branches and pull requests
3. SSH keys should be properly configured for git operations

## Usage

### Running the Service

```bash
uv run python main.py
```

### Using the Service

- Discussion Mode: Add the `claude-discuss` label to any issue to get AI-powered analysis and suggestions
- Implementation Mode: Add the `claude-implement` label to any issue to automatically implement the solution

The service will:
- Monitor webhook events from your GitHub repository
- Analyze issues with the specified labels
- Post comments with AI-generated responses
- For implementation issues, create feature branches and pull requests automatically

## API Endpoints

- `GET /` - Health check endpoint
- `POST /webhook` - GitHub webhook receiver endpoint

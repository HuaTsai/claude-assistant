# GitHub Claude Webhook Service

A FastAPI-based webhook service that automatically responds to GitHub issues using Claude AI. This service listens for GitHub webhook events and provides AI-powered responses to issues marked with specific labels.

## Features

- **Automatic Issue Analysis**: Responds to issues labeled with `claude-discuss` with AI-powered analysis and suggestions
- **Automated Implementation**: Automatically implements solutions for issues labeled with `claude-implement` and creates pull requests
- **Secure Webhook Handling**: Validates GitHub webhook signatures for security
- **Bilingual Support**: Supports both Traditional Chinese and English responses
- **Branch Management**: Automatically creates feature branches for implementations
- **Pull Request Creation**: Automatically creates PRs with detailed descriptions

## Supported Labels

- `claude-discuss`: Provides AI-powered discussion and analysis for issues
- `claude-implement`: Automatically implements solutions and creates pull requests

## Prerequisites

Before running this service, ensure you have the following installed:

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) - Fast Python package installer and resolver
- [Claude CLI](https://claude.ai/code) - For AI-powered responses
- [GitHub CLI (gh)](https://cli.github.com/) - For GitHub API interactions
- Git - For repository operations

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd claude-assistant
```

### 2. Install Python dependencies

This project uses [uv](https://docs.astral.sh/uv/) for dependency management:

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync
```

Alternatively, you can use pip:

```bash
pip install -r requirements.txt
```

### 3. Install system dependencies

**Claude CLI:**
```bash
# Follow the installation guide at https://claude.ai/code
```

**GitHub CLI:**
```bash
# macOS
brew install gh

# Ubuntu/Debian
sudo apt install gh

# Windows
winget install GitHub.cli
```

**Authenticate with GitHub:**
```bash
gh auth login
```

### 4. Environment Configuration

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
3. Set the payload URL to your service endpoint: `https://your-domain.com/webhook`
4. Set content type to `application/json`
5. Set the secret to match your `GITHUB_WEBHOOK_SECRET`
6. Select individual events: `Issues` and `Issue comments`
7. Ensure the webhook is active

### Repository Access

Ensure the service has access to your repositories:

1. The GitHub CLI must be authenticated with appropriate permissions
2. The service needs read/write access to create branches and pull requests
3 SSH keys should be properly configured for git operations

## Usage

### Running the Service

**Development mode:**
```bash
uv run python main.py
```

**Production mode with Uvicorn:**
```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

### Using the Service

1. **Discussion Mode**: Add the `claude-discuss` label to any issue to get AI-powered analysis and suggestions
2. **Implementation Mode**: Add the `claude-implement` label to any issue to automatically implement the solution

The service will:
- Monitor webhook events from your GitHub repository
- Analyze issues with the specified labels
- Post comments with AI-generated responses
- For implementation issues, create feature branches and pull requests automatically

## API Endpoints

- `GET /` - Health check endpoint
- `POST /webhook` - GitHub webhook receiver endpoint

## Project Structure

```
claude-assistant/
├── main.py              # Main FastAPI application
├── pyproject.toml       # Project configuration and dependencies
├── uv.lock             # Dependency lock file
├── sample.env          # Environment variables template
├── LICENSE             # MIT License
└── README.md           # This file
```

## Dependencies

### Runtime Dependencies
- **FastAPI[standard]** (>=0.116.1) - Web framework for building the webhook API
- **python-dotenv** - Environment variable management (included with FastAPI[standard])
- **uvicorn** - ASGI server (included with FastAPI[standard])

### Development Dependencies
- **ruff** (>=0.12.7) - Python linter and formatter

### External Dependencies
- **Claude CLI** - AI-powered code analysis and implementation
- **GitHub CLI (gh)** - GitHub API interactions
- **Git** - Version control operations

## Development

### Code Style

This project uses Ruff for code formatting and linting:

```bash
# Format code
uv run ruff format

# Check for linting issues
uv run ruff check

# Fix auto-fixable linting issues
uv run ruff check --fix
```

### Development Setup

```bash
# Install development dependencies
uv sync --group dev

# Run the application in development mode
uv run python main.py
```

## Security

- Webhook signatures are validated using HMAC-SHA256
- Environment variables are used for sensitive configuration
- The service validates GitHub webhook authenticity before processing

## Troubleshooting

### Common Issues

1. **Authentication Issues**: Ensure GitHub CLI is properly authenticated with `gh auth status`
2. **Webhook Signature Validation Failed**: Check that `GITHUB_WEBHOOK_SECRET` matches your GitHub webhook configuration
3. **Claude CLI Not Found**: Ensure Claude CLI is installed and available in your PATH
4. **Repository Clone Issues**: Verify SSH keys are properly configured for GitHub

### Logs

The service provides detailed logging for debugging. Check the console output for error messages and debugging information.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## Support

For issues and questions, please create an issue in the GitHub repository.
# Sentinel.AI Risk Gatekeeper Action

A GitHub Action that queries the **Sentinel.AI** agent for a pre-deployment risk assessment. If the risk score exceeds your configured threshold, the pipeline is automatically blocked — preventing risky deployments before they happen.

## Quick Start

```yaml
# .github/workflows/deploy.yml
name: Deploy with Sentinel.AI Risk Gate

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Sentinel.AI Risk Check
        id: sentinel
        uses: SentinelAI/risk-gatekeeper-action@v1
        with:
          api-key: ${{ secrets.SENTINEL_API_KEY }}
          service: 'user-auth-service'
          environment: 'production'
          change-type: 'code-deploy'

      # If the risk check passes, continue deploying
      - name: Deploy
        run: echo "Deploying! Risk score was ${{ steps.sentinel.outputs.risk-score }}"
```

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `api-key` | ✅ | — | Your Sentinel.AI API key (store as a GitHub secret) |
| `service` | ✅ | — | Name of the service being deployed |
| `environment` | ❌ | `production` | Target environment (`production`, `staging`, `development`) |
| `change-type` | ❌ | `code-deploy` | Type of change (`code-deploy`, `db-migration`, `config-change`, `rollback`) |
| `sentinel-url` | ❌ | `http://localhost:8000` | Base URL of your Sentinel.AI backend |
| `risk-threshold` | ❌ | `70` | Maximum acceptable risk score (0–100) |

## Outputs

| Output | Description |
|--------|-------------|
| `risk-score` | Numeric risk score (0–100) |
| `risk-level` | Human-readable level (`low`, `medium`, `high`) |
| `recommendation` | Short recommendation from the AI agent |

## How it Works

1. Your CI/CD pipeline triggers the action before deployment
2. The action sends deployment context to your Sentinel.AI backend
3. The AI agent analyzes the risk based on past incidents and deployment history
4. If the risk score exceeds the threshold → **pipeline is blocked** ❌
5. If the risk score is acceptable → **deployment proceeds** ✅

## Getting Your API Key

1. Open the Sentinel.AI dashboard
2. Navigate to **Projects & Keys**
3. Create a new project for your service
4. Copy the generated `sentinel_...` API key
5. Add it as a GitHub secret named `SENTINEL_API_KEY`

## License

MIT

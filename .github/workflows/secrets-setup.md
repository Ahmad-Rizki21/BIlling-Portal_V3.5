# GitHub Secrets Configuration Guide

This guide explains how to set up the required secrets for the CI/CD pipeline.

## Required Secrets for GitHub Repository

### Core Application Secrets
```
STAGING_DB_PASSWORD           # Staging database password
STAGING_SECRET_KEY           # Staging application secret key (32+ chars)
STAGING_ENCRYPTION_KEY       # Staging encryption key (32 chars)
STAGING_REDIS_PASSWORD       # Staging Redis password
STAGING_XENDIT_CALLBACK_TOKEN_ARTACOMINDO  # Xendit callback token for Artacom
STAGING_XENDIT_CALLBACK_TOKEN_JELANTIK     # Xendit callback token for Jelantik
STAGING_XENDIT_API_KEY_JAKINET              # Xendit API key for Jakinet
STAGING_XENDIT_API_KEY_JELANTIK             # Xendit API key for Jelantik

PROD_DB_PASSWORD            # Production database password
PROD_SECRET_KEY            # Production application secret key (32+ chars)
PROD_ENCRYPTION_KEY        # Production encryption key (32 chars)
PROD_REDIS_PASSWORD        # Production Redis password
PROD_REPLICATION_PASSWORD  # Database replication password
PROD_XENDIT_CALLBACK_TOKEN_ARTACOMINDO     # Production Xendit callback Artacom
PROD_XENDIT_CALLBACK_TOKEN_JELANTIK        # Production Xendit callback Jelantik
PROD_XENDIT_API_KEY_JAKINET                 # Production Xendit API Jakinet
PROD_XENDIT_API_KEY_JELANTIK                # Production Xendit API Jelantik
```

### Monitoring and Security
```
PROD_GRAFANA_PASSWORD      # Grafana admin password
PROD_SENTRY_DSN           # Sentry error tracking DSN
STAGING_GRAFANA_PASSWORD  # Staging Grafana password
```

### External Services
```
SLACK_WEBHOOK             # Slack webhook for notifications
DOCKERHUB_USERNAME        # Docker Hub username (if using Docker Hub)
DOCKERHUB_TOKEN          # Docker Hub access token
AWS_ACCESS_KEY_ID        # AWS access key (for backups)
AWS_SECRET_ACCESS_KEY    # AWS secret key (for backups)
```

## How to Set Up Secrets

### Method 1: Using GitHub CLI
```bash
# Set staging secrets
gh secret set STAGING_DB_PASSWORD --body "your_staging_db_password"
gh secret set STAGING_SECRET_KEY --body "your_staging_secret_key"
gh secret set STAGING_ENCRYPTION_KEY --body "your_staging_encryption_key"
gh secret set STAGING_REDIS_PASSWORD --body "your_staging_redis_password"
gh secret set STAGING_XENDIT_CALLBACK_TOKEN_ARTACOMINDO --body "your_xendit_callback_token"
gh secret set STAGING_XENDIT_CALLBACK_TOKEN_JELANTIK --body "your_xendit_callback_token"
gh secret set STAGING_XENDIT_API_KEY_JAKINET --body "your_xendit_api_key"
gh secret set STAGING_XENDIT_API_KEY_JELANTIK --body "your_xendit_api_key"
gh secret set STAGING_GRAFANA_PASSWORD --body "your_staging_grafana_password"

# Set production secrets
gh secret set PROD_DB_PASSWORD --body "your_prod_db_password"
gh secret set PROD_SECRET_KEY --body "your_prod_secret_key"
gh secret set PROD_ENCRYPTION_KEY --body "your_prod_encryption_key"
gh secret set PROD_REDIS_PASSWORD --body "your_prod_redis_password"
gh secret set PROD_REPLICATION_PASSWORD --body "your_replication_password"
gh secret set PROD_XENDIT_CALLBACK_TOKEN_ARTACOMINDO --body "your_prod_xendit_callback_token"
gh secret set PROD_XENDIT_CALLBACK_TOKEN_JELANTIK --body "your_prod_xendit_callback_token"
gh secret set PROD_XENDIT_API_KEY_JAKINET --body "your_prod_xendit_api_key"
gh secret set PROD_XENDIT_API_KEY_JELANTIK --body "your_prod_xendit_api_key"
gh secret set PROD_GRAFANA_PASSWORD --body "your_prod_grafana_password"
gh secret set PROD_SENTRY_DSN --body "your_sentry_dsn"

# Set external services
gh secret set SLACK_WEBHOOK --body "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
gh secret set DOCKERHUB_USERNAME --body "your_dockerhub_username"
gh secret set DOCKERHUB_TOKEN --body "your_dockerhub_token"
gh secret set AWS_ACCESS_KEY_ID --body "your_aws_access_key"
gh secret set AWS_SECRET_ACCESS_KEY --body "your_aws_secret_key"
```

### Method 2: Using GitHub Web Interface
1. Go to your repository on GitHub
2. Click on **Settings** tab
3. Click on **Secrets and variables** in the left sidebar
4. Click on **Actions**
5. Click **New repository secret**
6. Add each secret with its name and value

## Security Best Practices

### Secret Generation
Use cryptographically secure random strings for sensitive values:

```bash
# Generate strong secret keys (32+ characters)
openssl rand -base64 32

# Generate encryption keys (32 characters exactly)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Generate database passwords
openssl rand -base64 24
```

### Environment Separation
- **Never** use the same secrets across staging and production
- **Never** commit secrets to version control
- **Always** use different Xendit API keys for each environment
- **Always** rotate secrets regularly

### Secret Rotation
Plan to rotate secrets every 90 days:
1. Database passwords
2. Application secret keys
3. Encryption keys
4. API keys
5. Service credentials

### Access Control
- Limit who has access to repository secrets
- Use GitHub teams for appropriate access control
- Enable audit logs for secret access
- Review secret access regularly

## Environment-Specific Configuration

### Development Environment
Use `.env` file for local development (not committed to git):
```bash
cp .env.example .env
# Edit .env with local development values
```

### Staging Environment
- Use staging-specific API keys and credentials
- Connect to staging databases and services
- Enable debug logging for troubleshooting

### Production Environment
- Use production-specific API keys and credentials
- Connect to production databases and services
- Disable debug logging
- Enable all security features

## Troubleshooting

### Common Issues
1. **Secret not found**: Ensure the secret name matches exactly
2. **Invalid secret value**: Check for trailing spaces or special characters
3. **Permission denied**: Verify you have admin access to the repository
4. **Workflow failure**: Check that all required secrets are properly configured

### Debugging Secrets
To verify secrets are correctly configured:
```bash
# List all secrets
gh secret list

# Check specific secret (shows only metadata, not value)
gh secret view SECRET_NAME
```

## Monitoring and Alerts

Set up notifications for:
- Secret creation/modification
- Failed workflow runs due to missing secrets
- Unusual access patterns to secrets

Use GitHub's audit log and security alerts to monitor secret usage.
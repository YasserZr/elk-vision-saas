# GitHub Actions Workflows

This directory contains CI/CD workflows for the ELK Vision SaaS application.

## Workflows Overview

### 1. Backend CI (`backend-ci.yml`)

Runs on every pull request and push to main/develop branches affecting backend code.

**Jobs:**
- **Lint**: Code quality checks (Black, isort, Flake8, Pylint, MyPy)
- **Test**: Unit and integration tests with coverage
- **Security**: Dependency vulnerabilities (Safety) and security issues (Bandit)
- **Build**: Docker image build validation

**Caching:**
- pip dependencies (`~/.cache/pip`)
- Docker layers (`/tmp/.buildx-cache`)

**Services:**
- PostgreSQL 15
- MongoDB 7
- Redis 7

### 2. Frontend CI (`frontend-ci.yml`)

Runs on every pull request and push to main/develop branches affecting frontend code.

**Jobs:**
- **Lint**: ESLint, Prettier, TypeScript type checking
- **Test**: Jest tests with coverage
- **Security**: npm audit for vulnerabilities
- **Build**: Next.js production build
- **Docker Build**: Frontend Docker image
- **Lighthouse**: Performance audit (optional)

**Caching:**
- node_modules (`~/.npm`)
- Next.js build cache (`.next/cache`)
- Docker layers (`/tmp/.buildx-cache`)

### 3. Full Stack CI (`full-stack-ci.yml`)

Comprehensive workflow that orchestrates backend and frontend CI with additional integration tests.

**Jobs:**
- **Changes Detection**: Identifies which parts of the codebase changed
- **Backend CI**: Runs backend-ci.yml workflow
- **Frontend CI**: Runs frontend-ci.yml workflow
- **Integration Tests**: Tests backend/frontend interaction with docker-compose
- **E2E Tests**: Playwright end-to-end tests
- **Docker Compose Validation**: Validates docker-compose.yml syntax
- **Deployment Preview**: Creates PR comment with deployment info

**Features:**
- Smart change detection (only runs affected jobs)
- Full stack integration testing
- E2E testing with Playwright
- Deployment preview comments on PRs

### 4. Deploy to Production (`deploy-production.yml`)

Automated production deployment workflow.

**Triggers:**
- Push to main branch
- Git tags matching `v*.*.*`
- Manual workflow dispatch

**Jobs:**
- **Build and Push**: Builds Docker images and pushes to GitHub Container Registry
- **Deploy**: Deploys to production server via SSH
- **Rollback**: Automatic rollback on deployment failure

**Features:**
- Zero-downtime deployment
- Automatic database backup before deployment
- Health checks after deployment
- Automatic rollback on failure
- Deployment notifications

### 5. Dependabot (`dependabot.yml`)

Automated dependency updates configuration.

**Update Schedules:**
- Backend (pip): Weekly on Monday
- Frontend (npm): Weekly on Monday
- Docker images: Weekly on Tuesday
- GitHub Actions: Weekly on Wednesday

**Features:**
- Automated PR creation for dependency updates
- Security updates prioritized
- Configurable review assignments
- Smart grouping of related updates

## Setup Instructions

### 1. Repository Secrets

Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions):

```
# Production Server
PRODUCTION_SERVER=your-server-ip
PRODUCTION_USER=deploy-user
PRODUCTION_DOMAIN=yourdomain.com
SSH_PRIVATE_KEY=<your-ssh-private-key>

# Production Environment Variables
PRODUCTION_API_URL=https://yourdomain.com/api
PRODUCTION_WS_URL=wss://yourdomain.com/ws

# Optional: Codecov
CODECOV_TOKEN=<your-codecov-token>
```

### 2. GitHub Container Registry Setup

Enable GitHub Container Registry:
1. Go to Settings → Packages
2. Enable "Improved Container Support"
3. Update package visibility settings

### 3. Enable GitHub Actions

1. Go to Settings → Actions → General
2. Enable "Allow all actions and reusable workflows"
3. Set workflow permissions to "Read and write permissions"

### 4. Branch Protection Rules

Configure branch protection for `main`:
- Require pull request reviews (1-2 reviewers)
- Require status checks to pass:
  - Backend CI / Lint
  - Backend CI / Test
  - Backend CI / Build
  - Frontend CI / Lint
  - Frontend CI / Test
  - Frontend CI / Build
- Require branches to be up to date
- Include administrators (optional)

## Usage Examples

### Running Workflows Locally

Use [act](https://github.com/nektos/act) to test workflows locally:

```bash
# Install act
choco install act-cli  # Windows
brew install act       # macOS

# Run backend CI
act pull_request -W .github/workflows/backend-ci.yml

# Run frontend CI
act pull_request -W .github/workflows/frontend-ci.yml

# Run full stack CI
act pull_request -W .github/workflows/full-stack-ci.yml
```

### Manual Deployment

Trigger manual deployment:
1. Go to Actions tab
2. Select "Deploy to Production" workflow
3. Click "Run workflow"
4. Choose environment (production/staging)
5. Click "Run workflow"

### Viewing Test Results

Test results and coverage reports are automatically uploaded as artifacts:
- Backend coverage: `backend-coverage-report`
- Frontend coverage: `frontend-coverage-report`
- E2E reports: `playwright-report`
- Security reports: `bandit-security-report`

Download artifacts from the workflow run page.

## Cache Management

### Cache Keys

Workflows use semantic cache keys for efficient caching:

**Backend:**
```
${{ runner.os }}-pip-${{ hashFiles('backend/requirements.txt') }}
${{ runner.os }}-buildx-backend-${{ github.sha }}
```

**Frontend:**
```
${{ runner.os }}-node-${{ hashFiles('frontend/package-lock.json') }}
${{ runner.os }}-nextjs-${{ hashFiles('frontend/**/*.ts') }}
${{ runner.os }}-buildx-frontend-${{ github.sha }}
```

### Clearing Caches

GitHub Actions automatically removes caches not accessed in 7 days. To manually clear:
1. Go to Actions → Caches
2. Delete specific caches

## Optimization Tips

### 1. Speed Up Builds

- Use `actions/cache` for dependencies
- Enable Docker BuildKit with layer caching
- Run independent jobs in parallel
- Use matrix builds for multiple versions

### 2. Reduce Action Minutes

- Use path filters to skip unchanged code
- Cache Docker layers between runs
- Use larger runners for faster builds (paid)
- Optimize test execution time

### 3. Better Test Reports

- Use [actions/upload-artifact](https://github.com/actions/upload-artifact) for reports
- Integrate with [Codecov](https://codecov.io) for coverage tracking
- Add test summary to PR comments

## Troubleshooting

### Common Issues

**1. Cache Not Working**
- Verify cache key matches
- Check if cache size exceeds 5GB limit
- Ensure restore-keys are correct

**2. Docker Build Fails**
- Check Dockerfile syntax
- Verify base image availability
- Review Docker build logs

**3. Tests Failing in CI but Pass Locally**
- Check environment variables
- Verify service versions match
- Review timing-dependent tests

**4. Deployment Fails**
- Verify SSH key is correct
- Check server accessibility
- Review deployment logs

### Debug Mode

Enable debug logging:
1. Repository Settings → Secrets
2. Add secret: `ACTIONS_STEP_DEBUG = true`
3. Add secret: `ACTIONS_RUNNER_DEBUG = true`

## Best Practices

1. **Keep workflows DRY**: Use reusable workflows
2. **Fast feedback**: Run fastest tests first
3. **Secure secrets**: Never log sensitive data
4. **Version pinning**: Pin action versions with SHA
5. **Caching strategy**: Cache dependencies aggressively
6. **Status badges**: Add workflow badges to README
7. **Matrix builds**: Test multiple versions
8. **Notifications**: Set up Slack/email notifications

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [Encrypted Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Caching Dependencies](https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [Playwright GitHub Actions](https://playwright.dev/docs/ci-intro)

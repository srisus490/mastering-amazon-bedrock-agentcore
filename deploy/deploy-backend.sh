#!/usr/bin/env bash
# deploy/deploy-backend.sh
#
# Builds the FastAPI backend container, pushes it to ECR, and deploys
# it to ECS Fargate via CloudFormation.
#
# Required env vars:
#   JWT_SECRET_KEY  – secret for signing JWTs  (run: openssl rand -hex 32)
#
# Optional env vars (have sensible defaults):
#   AWS_REGION        – AWS region          (default: us-east-1)
#   STACK_NAME        – CF stack name       (default: file-monitoring-backend)
#   IMAGE_TAG         – Docker image tag    (default: latest)
#   BEDROCK_REGION    – Bedrock region      (default: us-east-1)
#   BEDROCK_MODEL_ID  – Bedrock model ID

set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
STACK_NAME="${STACK_NAME:-file-monitoring-backend}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
BEDROCK_REGION="${BEDROCK_REGION:-us-east-1}"
BEDROCK_MODEL_ID="${BEDROCK_MODEL_ID:-anthropic.claude-3-sonnet-20240229-v1:0}"

# Repo root = one directory above deploy/
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# ── Validate prerequisites ────────────────────────────────────────────────────
if [[ -z "${JWT_SECRET_KEY:-}" ]]; then
  echo "ERROR: JWT_SECRET_KEY is required."
  echo "  Generate one with: openssl rand -hex 32"
  exit 1
fi

for cmd in aws docker; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "ERROR: '${cmd}' not found"; exit 1; }
done

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REGISTRY="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

echo "==> Stack      : ${STACK_NAME}"
echo "==> Region     : ${REGION}"
echo "==> Account    : ${ACCOUNT_ID}"
echo "==> Image tag  : ${IMAGE_TAG}"
echo ""

# ── 1. Deploy / update CloudFormation stack ───────────────────────────────────
echo "==> Deploying CloudFormation stack (ECR + ECS + ALB + EFS)..."
aws cloudformation deploy \
  --template-file "$(dirname "$0")/backend-stack.yaml" \
  --stack-name   "${STACK_NAME}" \
  --parameter-overrides \
      BedrockRegion="${BEDROCK_REGION}" \
      BedrockModelId="${BEDROCK_MODEL_ID}" \
      JwtSecretKey="${JWT_SECRET_KEY}" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region       "${REGION}" \
  --no-fail-on-empty-changeset

# ── 2. Fetch stack outputs ────────────────────────────────────────────────────
get_output() {
  aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --region     "${REGION}" \
    --query      "Stacks[0].Outputs[?OutputKey=='${1}'].OutputValue" \
    --output     text
}

ECR_REPO_URI=$(get_output EcrRepositoryUri)
CLUSTER=$(get_output EcsClusterName)
SERVICE=$(get_output EcsServiceName)
BACKEND_URL=$(get_output BackendApiUrl)

IMAGE_URI="${ECR_REPO_URI}:${IMAGE_TAG}"

echo ""
echo "==> ECR URI    : ${ECR_REPO_URI}"
echo "==> ECS Cluster: ${CLUSTER}"
echo "==> ECS Service: ${SERVICE}"
echo ""

# ── 3. Build Docker image ─────────────────────────────────────────────────────
echo "==> Building Docker image..."
docker build \
  --platform linux/amd64 \
  -t "${IMAGE_URI}" \
  "${REPO_ROOT}"

# ── 4. Push to ECR ────────────────────────────────────────────────────────────
echo "==> Authenticating with ECR..."
aws ecr get-login-password --region "${REGION}" \
  | docker login --username AWS --password-stdin "${ECR_REGISTRY}"

echo "==> Pushing image to ECR..."
docker push "${IMAGE_URI}"

# ── 5. Force ECS service to pick up the new image ────────────────────────────
echo "==> Triggering ECS rolling deploy..."
aws ecs update-service \
  --cluster "${CLUSTER}" \
  --service "${SERVICE}" \
  --force-new-deployment \
  --region  "${REGION}" \
  --no-cli-pager >/dev/null

echo ""
echo "==> Waiting for service to become stable (this may take ~3 min)..."
aws ecs wait services-stable \
  --cluster "${CLUSTER}" \
  --services "${SERVICE}" \
  --region  "${REGION}"

echo ""
echo "======================================================"
echo "  Backend deployed successfully!"
echo "  API URL: ${BACKEND_URL}"
echo ""
echo "  Next step – deploy the web dashboard:"
echo "    BACKEND_URL=${BACKEND_URL} ./deploy/deploy-web-dashboard.sh"
echo "======================================================"

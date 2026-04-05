#!/usr/bin/env bash
# deploy/deploy-web-dashboard.sh
#
# Deploys the static web dashboard to S3 + CloudFront.
#
# Required env vars:
#   BACKEND_URL   – URL of the running backend API
#                   e.g. http://file-monitoring-backend-alb-xxxx.us-east-1.elb.amazonaws.com
#
# Optional env vars (have sensible defaults):
#   AWS_REGION    – AWS region (default: us-east-1)
#   STACK_NAME    – CloudFormation stack name (default: file-monitoring-web)

set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
STACK_NAME="${STACK_NAME:-file-monitoring-web}"
WEB_DIR="$(cd "$(dirname "$0")/../web-dashboard" && pwd)"

# ── Validate prerequisites ────────────────────────────────────────────────────
if [[ -z "${BACKEND_URL:-}" ]]; then
  echo "ERROR: BACKEND_URL is required."
  echo "  Example: BACKEND_URL=http://my-alb.us-east-1.elb.amazonaws.com $0"
  exit 1
fi

command -v aws  >/dev/null 2>&1 || { echo "ERROR: aws CLI not found"; exit 1; }
aws sts get-caller-identity --query Account --output text >/dev/null \
  || { echo "ERROR: AWS credentials not configured"; exit 1; }

echo "==> Stack    : ${STACK_NAME}"
echo "==> Region   : ${REGION}"
echo "==> Backend  : ${BACKEND_URL}"
echo ""

# ── 1. Deploy / update CloudFormation stack ───────────────────────────────────
echo "==> Deploying CloudFormation stack (S3 + CloudFront)..."
aws cloudformation deploy \
  --template-file "$(dirname "$0")/web-dashboard-stack.yaml" \
  --stack-name   "${STACK_NAME}" \
  --parameter-overrides BackendApiUrl="${BACKEND_URL}" \
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

BUCKET=$(get_output BucketName)
CF_ID=$(get_output CloudFrontDistributionId)
DASHBOARD_URL=$(get_output DashboardURL)

echo ""
echo "==> Bucket             : ${BUCKET}"
echo "==> CloudFront ID      : ${CF_ID}"
echo "==> Dashboard URL      : ${DASHBOARD_URL}"
echo ""

# ── 3. Build runtime config pointing at the backend ──────────────────────────
echo "==> Writing config/config.json with backend URL..."
CONFIG_JSON=$(cat <<EOF
{
  "apiBaseURL": "${BACKEND_URL}",
  "refreshInterval": 30000,
  "cacheTimeout": 30000,
  "retryAttempts": 3,
  "retryBackoff": 100,
  "chartMaxDataPoints": 100,
  "paginationPageSize": 50
}
EOF
)

# ── 4. Upload static assets (long-lived cache) ────────────────────────────────
echo "==> Syncing static assets to s3://${BUCKET}/ ..."
aws s3 sync "${WEB_DIR}/" "s3://${BUCKET}/" \
  --region       "${REGION}" \
  --delete \
  --exclude      "config/config.json" \
  --cache-control "public, max-age=86400, stale-while-revalidate=3600"

# Re-upload HTML files without cache so users always get the latest shell
for html in "${WEB_DIR}"/*.html; do
  [[ -f "$html" ]] || continue
  filename=$(basename "$html")
  aws s3 cp "$html" "s3://${BUCKET}/${filename}" \
    --region         "${REGION}" \
    --content-type   "text/html; charset=utf-8" \
    --cache-control  "no-cache, no-store, must-revalidate"
done

# Upload config (always no-cache)
echo "${CONFIG_JSON}" | aws s3 cp - "s3://${BUCKET}/config/config.json" \
  --region       "${REGION}" \
  --content-type "application/json" \
  --cache-control "no-cache, no-store, must-revalidate"

# ── 5. Invalidate CloudFront cache ────────────────────────────────────────────
echo "==> Invalidating CloudFront cache..."
aws cloudfront create-invalidation \
  --distribution-id "${CF_ID}" \
  --paths "/*" \
  --no-cli-pager

echo ""
echo "======================================================"
echo "  Web dashboard deployed successfully!"
echo "  URL: ${DASHBOARD_URL}"
echo "======================================================"

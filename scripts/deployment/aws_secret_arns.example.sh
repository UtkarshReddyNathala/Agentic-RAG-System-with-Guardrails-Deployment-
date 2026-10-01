#!/usr/bin/env bash
# IDs (ARNs) of the secrets in AWS Secrets Manager, used to fill in the ECS task definitions.
#
# Do not commit real values. Either:
#   - run `python scripts/deployment/create_aws_secrets.py`, which creates the
#     secrets and saves their ARNs to aws_secret_arns.sh (ignored by git), or
#   - copy this file to aws_secret_arns.sh and fill in the ARNs yourself.
export NEON_DB_URL_ARN="<NEON_DB_URL_ARN>"
export UPSTASH_REDIS_REST_URL_ARN="<UPSTASH_REDIS_REST_URL_ARN>"
export UPSTASH_REDIS_REST_TOKEN_ARN="<UPSTASH_REDIS_REST_TOKEN_ARN>"
export QDRANT_URL_ARN="<QDRANT_URL_ARN>"
export QDRANT_API_KEY_ARN="<QDRANT_API_KEY_ARN>"
export OPENAI_API_KEY_ARN="<OPENAI_API_KEY_ARN>"
export JINA_API_KEY_ARN="<JINA_API_KEY_ARN>"
export PORTKEY_API_KEY_ARN="<PORTKEY_API_KEY_ARN>"
export RAG_API_KEY_ARN="<RAG_API_KEY_ARN>"
export LOGFIRE_TOKEN_ARN="<LOGFIRE_TOKEN_ARN>"
export LANGSMITH_API_KEY_ARN="<LANGSMITH_API_KEY_ARN>"

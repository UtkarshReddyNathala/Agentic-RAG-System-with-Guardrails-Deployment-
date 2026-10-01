#!/usr/bin/env bash
# IDs of the AWS resources you create during setup (see docs/deployment.md).
#
# Copy this file to aws_deploy_state.sh (ignored by git) and fill in the IDs as
# you create each resource. render_task_defs.py and destroy_aws_deployment.sh
# read from that file. Never commit real account or resource IDs.
VPC_ID="<VPC_ID>"
IGW_ID="<IGW_ID>"
AZ1="<AZ1>"
AZ2="<AZ2>"
PUBLIC_SUBNET_1="<PUBLIC_SUBNET_1>"
PUBLIC_SUBNET_2="<PUBLIC_SUBNET_2>"
PRIVATE_SUBNET_1="<PRIVATE_SUBNET_1>"
PRIVATE_SUBNET_2="<PRIVATE_SUBNET_2>"
EIP_1="<EIP_ALLOCATION_ID>"
NAT_GW_1="<NAT_GATEWAY_ID>"
PUBLIC_RT="<PUBLIC_ROUTE_TABLE_ID>"
PRIVATE_RT="<PRIVATE_ROUTE_TABLE_ID>"
ALB_SG="<ALB_SECURITY_GROUP_ID>"
API_SG="<API_SECURITY_GROUP_ID>"
UI_SG="<UI_SECURITY_GROUP_ID>"
ECR_URI="<ACCOUNT_ID>.dkr.ecr.<AWS_REGION>.amazonaws.com/enterprise-rag"
SECRETS_POLICY_ARN="<SECRETS_POLICY_ARN>"
IMAGE_TAG=latest
ALB_ARN="<ALB_ARN>"
ALB_DNS="<ALB_DNS_NAME>"
API_TG_ARN="<API_TARGET_GROUP_ARN>"
UI_TG_ARN="<UI_TARGET_GROUP_ARN>"
LISTENER_ARN="<LISTENER_ARN>"
RAG_API_TASK_DEF_ARN="<RAG_API_TASK_DEF_ARN>"
RAG_UI_TASK_DEF_ARN="<RAG_UI_TASK_DEF_ARN>"

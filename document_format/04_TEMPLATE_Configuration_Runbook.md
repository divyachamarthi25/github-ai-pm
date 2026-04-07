---
doc_type: runbook
doc_id: RBK-YYYY-###
title: "[Runbook: Action — Service — Context]"
cloud_providers: [aws, azure, gcp, multi-cloud]
services: [service-1, service-2]
tags: [tag1, tag2, tag3]
runbook_type: deployment | configuration | troubleshooting | disaster-recovery | maintenance | onboarding
trigger: "[When should this runbook be executed? e.g., During initial cluster setup, When P1 incident X occurs]"
estimated_duration: "[e.g., 45 minutes]"
skill_level: beginner | intermediate | advanced
status: draft | active | deprecated
author: "Name / Team"
reviewed_by: "Name / Team"
created_date: YYYY-MM-DD
last_validated_date: YYYY-MM-DD
last_updated: YYYY-MM-DD
related_docs: []
---

# [RBK-YYYY-###] — [Runbook Title]

> **Type:** `[deployment|configuration|troubleshooting]` | **Duration:** `~[X] minutes` | **Skill Level:** `[beginner|intermediate|advanced]`

---

## 1. Runbook Overview

### 1.1 Purpose
<!--
  1–2 sentences describing what this runbook does and when to use it.
  Example: "This runbook walks through configuring AWS EKS IRSA (IAM Roles for Service Accounts) 
  to allow pods to access AWS S3 and DynamoDB without static credentials. Execute during new 
  cluster setup or when adding IAM permissions for a new microservice."
-->

[Purpose statement here]

### 1.2 Trigger Conditions
<!-- When exactly should someone execute this runbook? Be specific. -->

Use this runbook when:
- [Trigger condition 1 — e.g., "Setting up a new EKS cluster for the first time"]
- [Trigger condition 2 — e.g., "A new microservice requires AWS service permissions"]
- [Trigger condition 3]

Do NOT use this runbook when:
- [Anti-condition 1 — e.g., "Modifying existing IRSA roles — see RBK-2025-005 instead"]

### 1.3 Outcome
<!-- What state will the system be in after successful completion? -->

After completing this runbook:
- [Expected outcome 1]
- [Expected outcome 2]
- [Expected outcome 3]

---

## 2. Prerequisites

### 2.1 Access & Permissions Required

| Requirement | Details | How to Obtain |
|-------------|---------|---------------|
| [e.g., AWS IAM permission: `iam:CreateRole`] | [Why needed] | [e.g., Request via ServiceNow ticket to cloud-ops team] |
| [e.g., kubectl cluster-admin role] | [Why needed] | [e.g., Run `kubectl auth can-i create pods --all-namespaces`] |
| [e.g., Terraform state bucket access] | [Why needed] | [e.g., Included in `team-devops` IAM group] |

### 2.2 Tools & Versions Required

| Tool | Required Version | Installation / Verification |
|------|-----------------|----------------------------|
| [e.g., AWS CLI] | [e.g., >= 2.15.0] | `aws --version` |
| [e.g., kubectl] | [e.g., >= 1.29] | `kubectl version --client` |
| [e.g., Terraform] | [e.g., >= 1.7.0] | `terraform version` |
| [e.g., Helm] | [e.g., >= 3.14] | `helm version` |

### 2.3 Environment Variables to Set

```bash
export AWS_ACCOUNT_ID="123456789012"       # Replace with target account
export AWS_REGION="us-east-1"              # Replace with target region
export CLUSTER_NAME="my-eks-cluster"       # Replace with cluster name
export NAMESPACE="my-namespace"            # Kubernetes namespace
export SERVICE_ACCOUNT_NAME="my-sa"       # Service account name
```

### 2.4 Pre-Execution Checklist

- [ ] [Prerequisite check 1 — e.g., Confirm cluster is in `ACTIVE` state: `aws eks describe-cluster --name $CLUSTER_NAME`]
- [ ] [Prerequisite check 2]
- [ ] [Prerequisite check 3]
- [ ] Notify team in `#cloud-ops` Slack channel before executing in production

---

## 3. Step-by-Step Instructions

> ⚠️ **IMPORTANT:** Execute steps in order. Do not skip steps. If any step fails, stop and refer to Section 6 (Troubleshooting) before proceeding.

---

### Step 1: [Step Title]

**Purpose of this step:** [One sentence explaining why this step is needed]

```bash
# Command(s) to execute
# Replace placeholders in <angle brackets>

aws eks [command] \
  --cluster-name $CLUSTER_NAME \
  --region $AWS_REGION
```

**Expected Output:**
```
[Paste expected output or describe what success looks like]
```

**Verification:**
```bash
# Command to verify this step succeeded
```

✅ **Success condition:** [What you should see if this step worked]
❌ **If this fails:** [Quick guidance or pointer to troubleshooting section]

---

### Step 2: [Step Title]

**Purpose of this step:** [One sentence]

```bash
# Command(s)
```

**Expected Output:**
```
[Expected output]
```

**Verification:**
```bash
# Verification command
```

✅ **Success condition:** [...]
❌ **If this fails:** [...]

---

### Step 3: [Step Title]

*(Repeat the step pattern above for all steps)*

---

### Step N: Final Validation

**Purpose:** Confirm the entire configuration is working end-to-end.

```bash
# End-to-end validation command(s)
```

**Expected Output:**
```
[Expected output for successful end-to-end validation]
```

---

## 4. Configuration Reference

### 4.1 Key Configuration Files

| File | Location | Purpose |
|------|----------|---------|
| [e.g., values.yaml] | [e.g., `./helm/my-service/values.yaml`] | [Purpose] |
| [e.g., iam-policy.json] | [e.g., `./iac/iam/iam-policy.json`] | [Purpose] |

### 4.2 Full Configuration Template

```yaml
# Full working configuration template for this runbook
# Replace all <PLACEHOLDER> values before use
```

---

## 5. Rollback Procedure

> Execute this section if the runbook steps caused an issue and you need to revert.

### 5.1 Rollback Trigger Conditions
- [e.g., Service is failing health checks after Step 4 completion]
- [e.g., Permissions are incorrect and cannot be corrected forward]

### 5.2 Rollback Steps

1. **[Rollback Step 1]**
   ```bash
   # Rollback command
   ```

2. **[Rollback Step 2]**
   ```bash
   # Rollback command
   ```

### 5.3 Rollback Verification

```bash
# Verify rollback succeeded
```

---

## 6. Troubleshooting

### Issue: [Common Error Title]
- **Symptom:** [What the operator sees]
- **Cause:** [Why this happens]
- **Fix:**
  ```bash
  # Fix command
  ```

### Issue: [Common Error Title]
- **Symptom:** [...]
- **Cause:** [...]
- **Fix:**
  ```bash
  # Fix command
  ```

---

## 7. Post-Execution Checklist

- [ ] [Post-step 1 — e.g., Update CMDB / config registry with new resource ARNs]
- [ ] [Post-step 2 — e.g., Add monitoring alert for new IAM role usage]
- [ ] [Post-step 3 — e.g., Update team wiki with new service account mapping]
- [ ] Notify team in `#cloud-ops` that execution is complete

---

## TL;DR / Summary

<!--
  REQUIRED. 3–5 sentences summarizing what this runbook does, when to use it, and what it produces.
  This section will be retrieved as a standalone chunk by the AI. Make it complete.
-->

[Full standalone summary of the runbook's purpose and outcome.]

---

*Document ID: RBK-YYYY-### | Template Version: 1.0 | Multi-Cloud Solutions Team*

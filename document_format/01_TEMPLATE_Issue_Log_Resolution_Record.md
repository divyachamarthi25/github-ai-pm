---
doc_type: issue-log
doc_id: ISS-YYYY-###
title: "[One-line description of the issue]"
cloud_providers: [aws, azure, gcp, multi-cloud]   # delete inapplicable
services: [service-1, service-2]                   # e.g., [eks, iam, vpc]
tags: [tag1, tag2, tag3]                           # e.g., [networking, permissions, terraform]
severity: critical | high | medium | low
status: open | in-progress | resolved | wont-fix
environment: dev | staging | prod | poc
author: "Name / Team"
created_date: YYYY-MM-DD
resolved_date: YYYY-MM-DD                          # leave blank if unresolved
last_updated: YYYY-MM-DD
related_docs: []                                   # e.g., [ISS-2025-002, RBK-2025-001]
---

# [ISS-YYYY-###] — Issue Title

> **Severity:** `[critical|high|medium|low]` | **Status:** `[open|resolved]` | **Environment:** `[dev|staging|prod]`

---

## 1. Issue Summary

<!-- 
  2–3 sentences. Write as if this is all someone will read.
  Name the cloud provider, service, and symptom explicitly.
  Example: "AWS EKS cluster in us-east-1 failed to pull container images from ECR due to an expired IAM role 
  trust policy. The issue caused a full deployment outage for the payments service for 47 minutes on 2025-03-12."
-->

[Write a concise, standalone summary here.]

---

## 2. Problem Statement

### 2.1 What Happened
<!-- Describe the observable symptoms. What did users/systems experience? -->

- **Symptom:** [Describe the visible failure]
- **First Observed:** YYYY-MM-DD HH:MM UTC
- **Impact Duration:** [e.g., 47 minutes]
- **Services Affected:** [List specific services / endpoints]
- **Users / Systems Affected:** [Scope of impact]

### 2.2 Error Messages / Logs
<!-- Paste exact error messages verbatim. These are critical for AI keyword matching. -->

```
[Paste exact error message, stack trace, or log snippet here]
```

**Log Source:** [e.g., AWS CloudWatch Logs, Azure Monitor, GKE Stackdriver]
**Log Path / Query Used:**
```
[e.g., CloudWatch Insights query or kubectl command used to retrieve logs]
```

---

## 3. Environment Context

| Parameter | Value |
|-----------|-------|
| Cloud Provider | [AWS / Azure / GCP / Multi-Cloud] |
| Region / Zone | [e.g., us-east-1, eastus, us-central1] |
| Service(s) | [e.g., AWS EKS v1.29, Azure AKS, GCP GKE] |
| IaC Tool | [e.g., Terraform v1.7.2, Pulumi, ARM Templates] |
| Environment | [dev / staging / prod / poc] |
| Account / Project ID | [Masked if sensitive, e.g., acct-****1234] |
| Relevant Configuration | [e.g., VPC CIDR, node pool size, IAM role ARN] |

---

## 4. Root Cause Analysis

### 4.1 Root Cause
<!-- 
  Be explicit. Name the exact configuration, API behavior, or service interaction that caused the issue.
  Bad: "Permissions were wrong."
  Good: "The IAM Role `eks-node-role` was missing the `ecr:GetAuthorizationToken` permission in its 
  attached policy `AmazonEC2ContainerRegistryReadOnly`, which was inadvertently removed during a 
  Terraform plan on 2025-03-11."
-->

[Root cause explanation here]

### 4.2 Contributing Factors
<!-- List secondary causes, process gaps, or conditions that allowed this to happen -->

- [Factor 1]
- [Factor 2]

### 4.3 Why It Was Not Caught Earlier
<!-- What monitoring, review, or process gap allowed this to reach the current environment? -->

[Explanation]

---

## 5. Investigation Timeline

| Time (UTC) | Action Taken | Finding |
|------------|-------------|---------|
| YYYY-MM-DD HH:MM | [First alert / discovery] | [What was found] |
| YYYY-MM-DD HH:MM | [Investigation step] | [What was found] |
| YYYY-MM-DD HH:MM | [Fix applied] | [Outcome] |
| YYYY-MM-DD HH:MM | [Validation] | [Confirmed resolved / not resolved] |

---

## 6. Resolution

### 6.1 Fix Applied
<!-- 
  Describe the exact fix. Include commands, config changes, or code snippets.
  Write as a self-contained procedure — assume the reader has no prior context.
-->

**Resolution Type:** `[Config Change | Code Fix | Infra Change | Policy Update | Workaround]`

**Steps Taken:**

1. [Step 1 — include exact command or config if applicable]
   ```bash
   # Example command
   aws iam attach-role-policy --role-name eks-node-role --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly
   ```

2. [Step 2]

3. [Step 3]

### 6.2 Configuration Change (Before / After)

**Before:**
```hcl
# or yaml/json/bash — paste original config
```

**After:**
```hcl
# paste corrected config
```

### 6.3 Validation
<!-- How was the fix confirmed to work? -->

- [ ] [Validation step 1 — e.g., redeployed affected service]
- [ ] [Validation step 2 — e.g., confirmed no errors in CloudWatch for 30 minutes]
- [ ] [Validation step 3 — e.g., smoke test passed]

---

## 7. Prevention & Follow-Up Actions

| Action Item | Owner | Due Date | Status |
|-------------|-------|----------|--------|
| [e.g., Add IAM drift detection to CI/CD pipeline] | [Name/Team] | YYYY-MM-DD | Open |
| [e.g., Add CloudWatch alarm for ECR pull failures] | [Name/Team] | YYYY-MM-DD | Open |
| [e.g., Update runbook RBK-2025-001 with new IAM checklist] | [Name/Team] | YYYY-MM-DD | Open |

---

## 8. Lessons Learned

<!-- 
  Write in plain language. These will be directly retrieved by the GPT when similar issues arise.
  Focus on transferable insights, not just what happened here.
-->

1. [Lesson 1 — e.g., "Always validate IAM role policies after Terraform applies in staging before promoting to prod."]
2. [Lesson 2]
3. [Lesson 3]

---

## TL;DR / Summary

<!--
  REQUIRED. Write 3–5 sentences that fully summarize the issue, root cause, and resolution.
  This section will be retrieved as a standalone chunk by the AI. Make it complete.
-->

[The issue, in plain English. What happened, why, and how it was fixed.]

---

*Document ID: ISS-YYYY-### | Template Version: 1.0 | Multi-Cloud Solutions Team*

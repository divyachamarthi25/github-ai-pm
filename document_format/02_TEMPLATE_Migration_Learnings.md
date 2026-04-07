---
doc_type: migration-learning
doc_id: MLR-YYYY-###
title: "[Migration: Source → Target — Topic]"
cloud_providers: [aws, azure, gcp, multi-cloud]
source_platform: "[e.g., On-Prem VMware / AWS EC2 / Azure AKS]"
target_platform: "[e.g., GCP GKE / AWS EKS / Azure Container Apps]"
services: [service-1, service-2, service-3]
migration_phase: discovery | planning | execution | validation | cutover | post-migration
tags: [tag1, tag2, tag3]
workload_type: containers | databases | networking | storage | iam | serverless | data-pipelines | other
migration_pattern: lift-and-shift | re-platform | re-architect | retire | retain
status: in-progress | completed | abandoned
author: "Name / Team"
created_date: YYYY-MM-DD
migration_start_date: YYYY-MM-DD
migration_end_date: YYYY-MM-DD
last_updated: YYYY-MM-DD
related_docs: []
---

# [MLR-YYYY-###] — Migration Learnings: [Source] → [Target]

> **Migration Pattern:** `[lift-and-shift|re-platform|re-architect]` | **Phase:** `[execution|completed]` | **Workload:** `[containers|databases|etc.]`

---

## 1. Migration Overview

### 1.1 Context and Objective
<!--
  Describe what was migrated, from where to where, and why.
  Be explicit about cloud providers, services, and business drivers.
  Example: "This document captures learnings from migrating the Order Management microservice 
  cluster (12 services) from AWS EKS 1.24 on us-east-1 to GCP GKE Autopilot on us-central1, 
  driven by a cost optimization initiative in Q1 2025."
-->

[Migration context here]

### 1.2 Scope

| Attribute | Detail |
|-----------|--------|
| Workload Name | [e.g., Order Management Service] |
| Source Cloud / Platform | [e.g., AWS EKS v1.24, us-east-1] |
| Target Cloud / Platform | [e.g., GCP GKE Autopilot, us-central1] |
| Number of Services / Components | [e.g., 12 microservices] |
| Data Volume (if applicable) | [e.g., 2.3 TB PostgreSQL database] |
| Migration Pattern | [Lift-and-Shift / Re-platform / Re-architect] |
| Target Go-Live Date | YYYY-MM-DD |
| Actual Go-Live Date | YYYY-MM-DD |
| Team Size | [e.g., 4 engineers] |

### 1.3 Migration Phases Covered in This Document

- [ ] Discovery
- [ ] Planning & Design
- [ ] Execution
- [ ] Validation & Testing
- [ ] Cutover
- [ ] Post-Migration Stabilization

---

## 2. Pre-Migration Assessment Learnings

### 2.1 Discovery Gaps Found
<!--
  What did you find during discovery that was not in the original plan?
  These are high-value learnings for future migrations.
-->

| Gap Found | Impact | How Identified |
|-----------|--------|----------------|
| [e.g., Undocumented dependency on AWS SQS FIFO queue] | [Blocked container migration until SQS equivalent was configured in GCP Pub/Sub] | [Discovered during traffic analysis] |
| | | |

### 2.2 Assumptions That Were Wrong
<!--
  List assumptions made during planning that turned out to be incorrect.
  These are the most valuable learnings for the AI knowledge base.
-->

1. **Assumption:** [State the assumption as it was written in the plan]
   **Reality:** [What was actually true]
   **Impact:** [How it affected the migration timeline or design]

2. **Assumption:** [...]
   **Reality:** [...]
   **Impact:** [...]

---

## 3. Technical Learnings by Phase

### 3.1 Infrastructure & Networking

#### Learning: [Short title of learning]
- **Cloud Provider / Service:** [e.g., GCP VPC, AWS Transit Gateway]
- **Situation:** [What you tried or assumed]
- **What Happened:** [The actual outcome]
- **Resolution / Adaptation:** [How you addressed it]
- **Reusable Guidance:** [Transferable rule or pattern for future migrations]

```yaml
# Include relevant config snippet if applicable
```

#### Learning: [Short title]
[Repeat pattern above]

---

### 3.2 IAM & Security

#### Learning: [Short title]
- **Cloud Provider / Service:** [e.g., AWS IAM → GCP IAM]
- **Situation:** [...]
- **What Happened:** [...]
- **Resolution / Adaptation:** [...]
- **Reusable Guidance:** [...]

---

### 3.3 Data Migration

#### Learning: [Short title]
- **Service:** [e.g., AWS RDS PostgreSQL → GCP Cloud SQL]
- **Data Volume:** [e.g., 800 GB]
- **Tool Used:** [e.g., AWS DMS, pgdump, Datastream]
- **Situation:** [...]
- **What Happened:** [...]
- **Resolution / Adaptation:** [...]
- **Reusable Guidance:** [...]

---

### 3.4 Application / Container Migration

#### Learning: [Short title]
- **Service:** [e.g., AWS EKS → GCP GKE Autopilot]
- **Situation:** [...]
- **What Happened:** [...]
- **Resolution / Adaptation:** [...]
- **Reusable Guidance:** [...]

---

### 3.5 CI/CD & Toolchain

#### Learning: [Short title]
- **Tools Involved:** [e.g., Jenkins → Cloud Build, Terraform, ArgoCD]
- **Situation:** [...]
- **What Happened:** [...]
- **Resolution / Adaptation:** [...]
- **Reusable Guidance:** [...]

---

## 4. Issues Encountered During Migration

| Issue ID | Description | Severity | Status | Resolution Summary |
|----------|-------------|----------|--------|--------------------|
| [ISS-YYYY-###] | [One-line description] | High | Resolved | [One-line fix] |
| | | | | |

> For full issue details, see linked Issue Log documents in `related_docs`.

---

## 5. Performance & Cost Observations

### 5.1 Performance Comparison

| Metric | Source (Pre-Migration) | Target (Post-Migration) | Delta |
|--------|----------------------|------------------------|-------|
| [e.g., P99 API Latency] | [e.g., 120ms] | [e.g., 98ms] | [-18%] |
| [e.g., Throughput (RPS)] | | | |
| [e.g., Cold Start Time] | | | |

### 5.2 Cost Observations

| Cost Category | Source Monthly Estimate | Target Monthly Estimate | Notes |
|---------------|------------------------|------------------------|-------|
| Compute | $[X] | $[X] | |
| Networking | $[X] | $[X] | |
| Storage | $[X] | $[X] | |
| **Total** | **$[X]** | **$[X]** | |

---

## 6. What Worked Well

<!-- 
  List tools, patterns, and decisions that accelerated the migration or reduced risk.
  Be specific — name the tool, version, and why it worked.
-->

1. [e.g., "Using Terraform workspaces for environment separation reduced config drift during parallel execution."]
2. [...]
3. [...]

---

## 7. What to Do Differently Next Time

<!--
  Concrete, actionable recommendations for the next migration of this type.
  These are prime retrieval targets for the GPT.
-->

1. [e.g., "Run AWS Service Control Policy audit before planning GCP IAM equivalence mapping — undetected SCPs caused 3 days of delay."]
2. [...]
3. [...]

---

## 8. Reusable Patterns and Templates

<!-- Link or describe any reusable artifacts produced during this migration -->

| Artifact | Description | Location |
|----------|-------------|----------|
| [e.g., Terraform module: cross-cloud VPC peering] | [Description] | [Repo path / link] |
| [e.g., Network policy migration checklist] | [Description] | [Link] |

---

## TL;DR / Summary

<!--
  REQUIRED. 3–5 sentences capturing the migration, key learnings, and top recommendations.
  This section will be retrieved as a standalone chunk by the AI. Make it complete.
-->

[Full standalone summary of the migration and its most important learnings.]

---

*Document ID: MLR-YYYY-### | Template Version: 1.0 | Multi-Cloud Solutions Team*

# AI-Retrieval Friendly Documentation Guidelines
## Multi-Cloud Solutions Team — Custom GPT Knowledge Base

---

## Why AI-Retrieval Friendly Documentation Matters

When documents are ingested into a RAG (Retrieval-Augmented Generation) pipeline, the AI does not read linearly — it retrieves semantically relevant **chunks**. Poor structure leads to lost context, hallucinated answers, and incomplete retrievals. These guidelines ensure every document in our knowledge base is optimized for both human readers and AI retrieval systems.

---

## Core Principles

### 1. Metadata First
Every document **must** start with a YAML frontmatter block. This is the primary filter layer used by the retrieval system to scope queries before semantic search even begins.

```yaml
---
doc_type: issue-log | migration-learning | poc-finding | runbook | comparison-note
doc_id: UNIQUE-ID (e.g., ISS-2025-001)
title: Human-readable title
cloud_providers: [aws, azure, gcp, multi-cloud]
services: [list of specific services involved]
tags: [keyword1, keyword2, keyword3]
severity: critical | high | medium | low   # for issues
status: open | resolved | in-progress | archived
author: Name / Team
created_date: YYYY-MM-DD
last_updated: YYYY-MM-DD
related_docs: [DOC-ID-1, DOC-ID-2]
---
```

> **Rule:** Never skip or partially fill metadata. Incomplete metadata = invisible document to the retrieval system.

---

### 2. Chunk-Aware Section Design

RAG systems split documents into chunks (typically 512–1024 tokens). Write sections so that **each section is self-contained and meaningful in isolation**.

| Do | Don't |
|----|-------|
| Repeat the subject noun in each section | Use pronouns like "it", "this", "the above" across sections |
| Start every section with a 1-line context sentence | Jump straight into technical detail without context |
| Use explicit headings like `## Problem Statement` | Use vague headings like `## Details` or `## More Info` |
| Summarize at the end of long sections | Let sections trail off without closure |

---

### 3. Keyword Density and Specificity

AI embeddings rely on lexical and semantic signals. Use:
- **Full product names**: `AWS S3`, not just `S3` or "the bucket service"
- **Error codes verbatim**: `Error: AccessDeniedException`, not "the permission error"
- **Version numbers**: `Terraform v1.7.2`, `Python 3.11`, `Kubernetes 1.29`
- **Action verbs**: `resolved`, `mitigated`, `configured`, `deprecated`, `migrated`

Avoid jargon without expansion on first use. Write: `IAM (Identity and Access Management)` before shortening to `IAM`.

---

### 4. Structured Answer Patterns

Where possible, write in **Q→A or Problem→Solution patterns**. These map directly to how a GPT answers user questions.

```markdown
## Problem
Describe what broke or what was unknown.

## Root Cause
Explain why it happened. Be specific. Include service names and conditions.

## Resolution / Finding
State the fix or finding clearly and completely. Assume this section will be read in isolation.

## Validation
How was the resolution confirmed?
```

---

### 5. Avoid These Anti-Patterns

| Anti-Pattern | Why It Hurts Retrieval |
|---|---|
| Wall of text with no headings | Chunker splits mid-thought; context is lost |
| Tables without row/column labels | AI cannot interpret unlabeled table cells |
| Screenshots as primary documentation | AI cannot read images; always add text descriptions |
| Numbered steps with no step titles | If step 3 is retrieved, context of the overall task is lost |
| Abbreviations not defined | Embedding model may not resolve `CW` to `CloudWatch` correctly |
| Links as the only reference | External links may break; always summarize linked content inline |

---

### 6. Linking and Cross-References

Use `related_docs` in metadata AND inline references:

```markdown
> See also: [ISS-2025-003 — IAM Role Trust Policy Misconfiguration](../issues/ISS-2025-003.md)
```

Cross-references allow the retrieval system to surface related documents and enable the GPT to suggest follow-up reading.

---

### 7. Summary Block (Required)

Every document must end with a `## TL;DR / Summary` section — a 3–5 sentence paragraph that can stand alone as a complete answer. This is the fallback chunk when the retrieval system has low confidence on specific sections.

---

### 8. Document Naming Convention

```
{DOC_TYPE_CODE}-{YEAR}-{SEQ_NUMBER}_{slug}.md

Examples:
ISS-2025-001_s3-cross-account-replication-failure.md
MLR-2025-004_eks-to-gke-network-policy-learnings.md
POC-2025-002_azure-openai-vs-bedrock-latency.md
RBK-2025-007_terraform-multi-region-deploy-runbook.md
CMP-2025-001_aws-vs-azure-blob-storage-comparison.md
```

---

### 9. Document Type Quick Reference

| Code | Document Type | Primary Use |
|------|--------------|-------------|
| `ISS` | Issue Log & Resolution Record | Incident post-mortems, bug tracking |
| `MLR` | Migration Learnings | Lessons from cloud migrations |
| `POC` | POC Findings | Proof-of-concept evaluation results |
| `RBK` | Configuration Runbook | Step-by-step operational guides |
| `CMP` | Comparison Note | Side-by-side service/tool evaluations |

---

### 10. Review Checklist Before Publishing

- [ ] YAML frontmatter is complete with all required fields
- [ ] `doc_id` is unique and follows naming convention
- [ ] All abbreviations are expanded on first use
- [ ] Each section is self-contained (readable without surrounding context)
- [ ] Problem/Resolution sections use specific service names and error codes
- [ ] `TL;DR / Summary` section is present at the end
- [ ] `related_docs` references are populated
- [ ] Document saved with correct filename convention

---

*Guidelines Version: 1.0 | Owner: Multi-Cloud Solutions Team | Last Updated: 2025*

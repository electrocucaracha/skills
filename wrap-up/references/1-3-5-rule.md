# Task Prioritization: The 1-3-5 Rule

## Overview

The 1-3-5 rule is a simple, effective framework for organizing daily tasks by priority:

- **1 high-priority task**: The single most critical item that must be completed
- **3 medium-priority tasks**: Important but less urgent items that contribute to weekly/monthly goals
- **5 low-priority tasks**: Smaller, routine tasks that add value but are flexible

This creates a realistic daily workload while maintaining focus on what matters most.

## How to Apply the Rule

### 1. High-Priority Task (1 item)

**Characteristics:**
- Directly impacts project success, release, or blocking dependencies
- Often has external stakeholders or deadline pressure
- If nothing else gets done, this is what should be completed

**Examples:**
- Merge critical security fix to production
- Unblock team by resolving deployment blocker
- Complete time-sensitive PR review for release candidate

### 2. Medium-Priority Tasks (3 items)

**Characteristics:**
- Advance team goals or project roadmap
- Have moderate urgency or impact
- Typically 1-3 hours each

**Examples:**
- Implement feature branch for upcoming sprint
- Respond to architectural review feedback
- Update documentation for new module

### 3. Low-Priority Tasks (5 items)

**Characteristics:**
- Routine work that supports ongoing operations
- Nice-to-have improvements
- Can be deferred if time runs short
- Typically <1 hour each

**Examples:**
- Reply to Slack questions in #help channel
- Update README with new examples
- Fix formatting in config files
- Clean up abandoned feature branches
- Add unit test for utility function

## Task Wording

### Action-Oriented Language

❌ **Avoid:**
- "Report" → ✓ "Draft Q3 sales report and share with leadership"
- "Code review" → ✓ "Review and approve PR #543 for database optimization"
- "Documentation" → ✓ "Update API reference with new endpoint parameters"

### Include Context/Value

Each task should briefly explain **why** it was done:

```markdown
1. **[HIGH]** Merge Auth Security Patch
   - *Why*: CVE-2026-XXXX threatens production; blocking customer deployments

2. **[MEDIUM]** 
   - Implement User Analytics Dashboard
     - *Why*: Required for Sprint 24 roadmap commitment
   - Review PR #445 - Kafka Consumer Refactor
     - *Why*: Unblocks data pipeline team
   - Add Test Coverage for Payment Module
     - *Why*: Reduces tech debt, improves CI reliability

3. **[LOW]**
   - Respond to 3 pending questions in #ask-devs
   - Update CONTRIBUTING.md with new CI patterns
   - Fix typo in service health dashboard
   - Clean up local Docker volumes
   - Add comments to batch-processor utility
```

## Evaluation Framework

When categorizing tasks, ask:

- **High**: Is this blocking someone, a deadline, or production issue?
- **Medium**: Does this advance a key initiative or prevent future problems?
- **Low**: Is this routine, nice-to-have, or <1 hour of work?

## Integration with Meeting Minutes

When synthesizing wrapup from both GitHub activity and meetings:

1. **GitHub activity** typically maps to:
   - PRs, code reviews, commits → medium/low priority completed work
   - CI/CD fixes → high/medium priority if blocking

2. **Meeting context** adds:
   - Stakeholder priorities
   - Deadline/urgency signals
   - Team commitments and blockers

3. **Synthesis strategy**:
   - Start with meeting action items (highest priority)
   - Layer in GitHub completions that align with those items
   - Identify unplanned work (PRs, reviews) and categorize appropriately
   - Ensure high-priority reflects meeting decisions + blocking issues


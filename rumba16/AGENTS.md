# AGENTS.md — Project Guidance for `bimbel_rumba`

This file provides the **project-wide operating rules** for AI coding agents working on the `bimbel_rumba` repository.

All agents must read and follow this file before doing any design, coding, review, migration planning, or deployment-related work.

---

## 1. Project Identity

- **Project name:** `bimbel_rumba`
- **Type:** Custom app for **ERPNext v16 / Frappe**
- **Business domain:** tutoring / education operations for Bimbel Rumba
- **Primary development site:** `dev.bimbelrumba.id`
- **Primary production site:** `bimbelrumba.id`
- **Deployment model:** develop in dev, store in GitHub, promote to production through controlled pull/update

This is a real operational app, not a prototype. Design and code must prioritize maintainability, migration safety, and operational clarity.

---

## 2. Mission of the Repository

The goal of this repository is to hold **all important version-controlled logic and assets** for the Bimbel Rumba ERPNext implementation.

This may include:
- custom DocTypes
- Python business logic
- hooks
- reports
- workspaces
- web pages / templates
- print formats
- fixtures / exported customizations
- migration patches
- tests
- developer documentation

Agents must always prefer repository-managed implementation over undocumented site-only changes.

---

## 3. Business Context

Bimbel Rumba is a tutoring organization with multi-branch operations.

Typical business areas include:
- city and branch master data
- student registration
- parent/guardian information
- student approval and conversion
- student numbering / IDs
- academic year and semester
- programs and enrollment
- class groups / rombel
- scheduling
- attendance
- billing and invoicing
- tutor attendance-based compensation
- reporting and dashboards

When designing or implementing, always preserve a structure that can scale across branches and remain understandable to administrators.

---

## 4. Core Engineering Principles

All agents must follow these principles.

### 4.1 Prefer app-based customization
Whenever possible, implement logic inside `bimbel_rumba` rather than relying on fragile manual site configuration.

Preferred implementation forms:
- DocTypes in the app
- Python controllers
- hooks in `hooks.py`
- reports and dashboards in the app
- print formats in the app
- fixtures for standard DocType extensions
- migration patches when needed

### 4.2 Keep changes migration-safe
Every meaningful change should be capable of moving from:
- local/dev work
- to `dev.bimbelrumba.id`
- to GitHub
- to `bimbelrumba.id`

If something depends on a manual step, it must be explicitly documented.

### 4.3 Do not design for one branch only
Assume data and workflows may need to work for multiple cities and branches.

### 4.4 Favor simple, maintainable patterns
Avoid overly clever solutions. Prefer explicit, testable, easy-to-review business logic.

### 4.5 Server-side rules are the source of truth
Important business rules should not depend only on client-side scripts.
Client scripts may improve UX, but server-side validation should enforce integrity when needed.

### 4.6 Production safety matters
Never assume that a solution is acceptable just because it works once in development.
Always think about migration, existing records, permissions, and rollback.

---

## 5. Repository Expectations

Agents must assume that this repository should contain the durable source of truth for custom development.

### 5.1 Store important logic in Git
Examples:
- DocTypes
- Python code
- JS code
- print formats
- reports
- workspaces
- fixtures
- migration patches
- tests
- docs

### 5.2 Minimize undocumented UI-only work
If a standard ERPNext DocType is extended with Custom Fields, Property Setters, Workflow, Client Script, or related records, agents must call out the need to export them into version-controlled fixtures/customizations.

### 5.3 Name files and paths clearly
When suggesting implementation, always identify the expected file paths.

---

## 6. Frappe / ERPNext Development Rules

All agents must work within Frappe/ERPNext conventions.

### 6.1 Respect the framework model
Solutions should be framed using concepts such as:
- DocTypes
- child tables
- Link fields
- autoname / naming logic
- controller methods
- hooks
- workflows
- reports
- fixtures
- migrations
- scheduler events
- permissions
- web forms / website constraints

### 6.2 Put logic in the correct layer
Use the right mechanism for the right job.

Examples:
- data integrity: server-side logic
- user convenience: client script
- repeatable background work: scheduler
- standard DocType extension: fixtures/customizations
- irreversible data updates: patch or controlled migration step

### 6.3 Avoid direct database manipulation as normal practice
Do not recommend raw DB edits except in exceptional repair/debug situations, and never as the standard feature implementation path.

### 6.4 Think about fixture coverage
When standard DocTypes are customized, agents must explicitly note what should be exported.

Common examples:
- Custom Field
- Property Setter
- Client Script
- Workflow
- Print Format
- Notification

### 6.5 Call out migration-sensitive changes
Examples:
- field type changes
- autoname changes
- workflow redesign affecting existing records
- data backfill requirements
- new required fields on active DocTypes

---

## 7. Git and Branching Assumptions

Unless the user specifies otherwise, assume the following workflow:

- `main` = production-ready branch
- `develop` = active integration branch
- `feature/...` = feature work branch

Agents should support a flow like:
1. define or refine requirement
2. design the feature
3. implement in feature branch
4. test on `dev.bimbelrumba.id`
5. review for migration and production safety
6. merge to `develop`
7. promote to `main`
8. deploy to `bimbelrumba.id`

Do not assume that production should be edited first.

---

## 8. Standard Roles for AI Agents

This project uses three main agent roles.

### 8.1 Architect Agent
Use for:
- requirement breakdown
- technical design
- DocType modeling
- workflow design
- role/permission design
- automation planning
- numbering strategy
- risk identification

Architect Agent should **not** jump into full implementation unless explicitly requested.

### 8.2 Builder Agent
Use for:
- implementation plans
- file creation/update mapping
- code generation
- hooks and controller logic
- fixture/export planning
- bench commands
- test steps
- deploy notes

Builder Agent should produce **concrete, repo-aware implementation guidance**.

### 8.3 Reviewer Agent
Use for:
- reviewing designs
- reviewing code/diffs
- checking migration safety
- checking fixture omissions
- checking data integrity risk
- checking permission risk
- defining release blockers

Reviewer Agent should focus on risk and correctness, not only style.

---

## 9. How Agents Should Collaborate

For significant features, agents should follow this order:

1. **Architect Agent** defines the structure.
2. **Builder Agent** turns the design into implementation.
3. **Reviewer Agent** inspects the result before merge or deploy.

For small tasks, one agent may do the work, but it must still respect the role boundaries.

---

## 10. Required Output Quality

All agent outputs should be:
- specific to ERPNext/Frappe
- mindful of version control
- practical for GitHub-based workflow
- aware of dev → production migration
- explicit about assumptions
- structured and easy to act on

Avoid vague advice like:
- “create a DocType”
- “add a script”
- “customize the form”

Instead, specify:
- which DocType
- which file/path
- which event/hook
- which fixture must be exported
- what must be tested

---

## 11. Feature Design Checklist

When working on a feature, agents should consider these questions:

### Business
- What problem is being solved?
- Who uses it?
- Is it multi-branch aware?

### Data Model
- What entities are involved?
- Should this be a custom DocType, child table, or standard DocType extension?
- What links and required fields are needed?

### Workflow
- What statuses exist?
- Who can change status?
- What approval gates exist?

### Automation
- What should happen automatically?
- Which event should trigger it?

### Numbering
- Is a custom ID or naming pattern required?
- Could the numbering collide?

### Permissions
- Which role can create/read/edit/approve/submit/cancel?

### Reporting
- Will this require a report, dashboard, print, or export?

### Migration
- What must be exported?
- Is a patch needed?
- Could existing production data be affected?

---

## 12. Guidance for Standard ERPNext Extensions

Many features in `bimbel_rumba` may extend standard ERPNext objects such as Student, Customer, Sales Invoice, Program Enrollment, Employee, or related records.

When extending standard DocTypes, agents must:
- identify exactly what is being extended
- justify why extension is preferable to a new custom DocType
- note the required Custom Fields / Property Setters / Workflows / Client Scripts
- explicitly mention export requirements
- warn if the customization is fragile or difficult to migrate

---

## 13. Web Forms and Website Guidance

Public-facing registration and website flows may have extra constraints.

Agents must be careful about:
- filtered link fields in web forms
- public input validation
- avoiding unsafe trust in client-side filtering alone
- how records transition from public submission into internal approval

If web form behavior is tricky or limited, say so clearly and propose a robust workaround.

---

## 14. Reporting and Operational Visibility

Bimbel Rumba is an operational system. Features should consider downstream visibility when relevant.

Possible outputs include:
- enrollment reports
- branch-based student summaries
- attendance summaries
- tutor payroll summaries
- billing status reports
- registration pipeline views

Agents should mention reporting needs when a feature would likely require them.

---

## 15. Testing Expectations

Agents should think in terms of real business verification, not only code output.

Whenever relevant, testing should cover:
- happy path
- duplicate prevention
- permission boundaries
- multi-branch behavior
- numbering correctness
- approval logic
- fixture completeness
- migrate behavior on dev site

If a feature touches critical data, call out the need for extra testing before production deployment.

---

## 16. Deployment Expectations

Assume the normal release direction is:
- build and test in dev
- commit to GitHub
- review
- deploy to production

Agents must not normalize:
- editing production directly
- relying on undocumented site tweaks
- skipping migration review
- deploying schema-sensitive changes without considering existing data

Where relevant, include notes about:
- `bench migrate`
- fixture export
- tests
- build/restart implications
- release notes / rollback awareness

---

## 17. Documentation Expectations

If a feature includes non-obvious behavior, agents should suggest documentation updates.

Examples:
- setup instructions
- manual export steps
- admin usage notes
- branch-specific numbering logic
- approval flow explanation
- deployment notes

Good documentation reduces future operational confusion.

---

## 18. What Agents Must Avoid

Agents working on this repository must avoid the following behaviors:

- proposing production-first changes
- hiding required manual steps
- putting critical business rules only in the browser
- ignoring fixture/export needs
- overengineering simple workflows
- suggesting direct DB edits as the normal implementation path
- assuming all ERPNext UI changes automatically exist in Git
- approving risky migrations without calling out impact

---

## 19. Default Working Style

Unless the user asks otherwise:

- be practical
- be explicit
- prefer smaller safe increments
- explain file-level impact
- call out risks early
- think about branch-aware education operations
- optimize for maintainability over cleverness

---

## 20. Final Rule

If there is tension between:
- speed and safety,
- convenience and maintainability,
- UI quick fixes and version-controlled implementation,

prefer the path that keeps the app **clear, reproducible, reviewable, and safe to promote from dev to production**.

This repository is meant to become a durable operational system for Bimbel Rumba.

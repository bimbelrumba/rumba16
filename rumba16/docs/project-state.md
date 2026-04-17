# Project State — bimbel_rumba (ERPNext v16)

This document records the **current known state** of the `bimbel_rumba` project.

Its purpose is to provide a stable shared context for all AI agents working on this repository, especially:
- Inventory Agent
- Architect Agent
- Builder Agent
- Reviewer Agent

This file should be updated whenever the project state changes in a meaningful way.

---

## 1. Project Identity

- **App name:** `bimbel_rumba`
- **Framework:** ERPNext v16 / Frappe
- **Development site:** `dev.bimbelrumba.id`
- **Production site:** `bimbelrumba.id`
- **Source control:** GitHub
- **Development approach:** build in dev, commit to repo, review, then promote to production

---

## 2. Current Development Goal

The current goal is to continue building the `bimbel_rumba` module in a more structured, version-controlled, and agent-assisted way.

The project is moving from:
- partially UI-driven customization
- partially repo-backed development

toward:
- clearer architecture
- GitHub-driven workflow
- safer dev-to-production promotion
- repeatable multi-agent collaboration

---

## 3. Current Known Custom DocTypes

The following DocTypes are currently known to exist in the `bimbel_rumba` module:

- `Rumba Pendaftaran`
- `Ruangan`
- `Semester`
- `Tahun Ajaran`
- `Program Belajar`
- `Provinsi`
- `Unit`
- `Kota`

These DocTypes were created through the ERPNext v16 UI.

---

## 4. Known Repo / GitHub State

Current known state based on available information:

- The DocTypes listed above, **except `Rumba Pendaftaran`**, have already been sent to the repo folder through the server terminal and uploaded to GitHub.
- The status of `Rumba Pendaftaran` still requires verification.
- The repository already contains agent guidance documents such as:
  - `AGENTS.md`
  - `docs/agents/architect.md`
  - `docs/agents/builder.md`
  - `docs/agents/reviewer.md`
  - `docs/agents/inventory.md`

The exact Git state should still be verified whenever a new development cycle begins.

---

## 5. Current Known Uncertainties

The following items are not yet fully verified:

### A. `Rumba Pendaftaran`
It is not yet fully confirmed whether `Rumba Pendaftaran` is:
- fully file-backed in the app
- Git-tracked
- already pushed to GitHub
- safe to extend further without cleanup

### B. Standard DocType Customizations
It is not yet fully confirmed whether there are existing customizations on standard ERPNext DocTypes such as:
- Custom Fields
- Property Setters
- Workflows
- Client Scripts
- Print Formats
- Notifications

that still exist only in the site and have not yet been exported.

### C. Fixture Coverage
It is not yet confirmed whether any fixtures/customizations need to be exported and committed.

### D. Branch / Commit Cleanliness
It is not yet confirmed whether the local repo, dev server, and GitHub are fully aligned.

---

## 6. Current Development Rules

Until stated otherwise, all agents should follow these working rules:

1. Do not assume that ERPNext UI state is automatically version-controlled.
2. Prefer app-based, Git-backed implementation for all future work.
3. Do not change production directly.
4. Treat the dev site as the environment for testing and controlled iteration.
5. If a change involves standard ERPNext DocTypes, check whether export/fixtures are needed.
6. If baseline inventory is unclear, run Inventory Agent before designing or building new features.
7. Keep future implementation migration-safe for dev → production promotion.

---

## 7. Current Priority Focus

The current practical focus is not to redesign the whole system from zero, but to continue development based on the existing foundation.

### Priority 1
- Verify baseline project inventory
- Confirm file-backed status of `Rumba Pendaftaran`
- Confirm Git / GitHub alignment
- Identify any missing fixtures or site-only customizations

### Priority 2
- Design workflow for `Rumba Pendaftaran`
- Design approval flow
- Design automatic student ID generation
- Design Student creation after approved registration

### Priority 3
- Strengthen academic structure and operational flow around:
  - Unit
  - Program Belajar
  - Semester
  - Tahun Ajaran
  - Ruangan

### Priority 4
- Continue toward:
  - rombel / class grouping
  - scheduling
  - attendance
  - invoicing
  - tutor compensation

---

## 8. Recommended Agent Workflow

Until project maturity improves, the preferred sequence is:

1. **Inventory Agent**
   - audit current baseline
   - identify repo/UI mismatches
   - flag missing exports or unclear status

2. **Architect Agent**
   - design the next feature based on verified existing objects

3. **Builder Agent**
   - implement the approved design in a version-controlled way

4. **Reviewer Agent**
   - review migration safety, deployment safety, and hidden risks

Agents should avoid skipping Inventory when the current state is uncertain.

---

## 9. Working Assumptions for Agents

Unless newer information is provided, agents should assume:

- `bimbel_rumba` is an actively evolving custom ERPNext app
- the current system already has meaningful business structure
- not all existing objects may be equally safe in version control yet
- future work should reduce technical ambiguity, not increase it
- every important feature should eventually be reproducible from the repository

---

## 10. What This File Is For

This file should be used as a shared baseline when prompting agents.

Typical uses:
- pasted into AI chat as project context
- referenced before architecture work
- referenced before implementation planning
- referenced during audit and review
- updated after major changes to the project state

This file is not a feature design document.  
It is a **living baseline context document**.

---

## 11. Update Rules

This file should be updated when any of the following changes happen:

- a new core DocType is added
- a major DocType is confirmed as file-backed
- standard DocType customizations are exported
- a major workflow is implemented
- a feature changes the project baseline significantly
- Git/GitHub structure changes
- dev/prod deployment strategy changes

---

## 12. Current Baseline Summary

At the moment, the known project baseline is:

- the `bimbel_rumba` app already has several core custom DocTypes
- these were initially created through the ERPNext UI
- most of them appear to have already been moved into the repo and GitHub
- `Rumba Pendaftaran` still needs verification
- the project has begun using a structured multi-agent method
- the next important step is to stabilize inventory and then design the registration approval flow

---

## 13. Immediate Next Step

The safest immediate next step is:

- run the Inventory Agent against the current known DocTypes
- verify `Rumba Pendaftaran`
- confirm repo and GitHub alignment
- only then move into deeper feature design and implementation

This will provide a safer baseline for Architect, Builder, and Reviewer to work effectively.

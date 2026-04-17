# Backlog — bimbel_rumba (ERPNext v16)

This document records the **current development backlog** for the `bimbel_rumba` project.

Its purpose is to help:
- organize upcoming work
- clarify priorities
- support AI agent collaboration
- separate immediate tasks from later tasks
- keep development aligned with the current project state

This file should be updated regularly as priorities change.

---

## 1. Project Scope of This Backlog

This backlog is focused on the structured development of the `bimbel_rumba` custom app on **ERPNext v16 / Frappe**.

It assumes:
- development happens first on `dev.bimbelrumba.id`
- important changes should be version-controlled in GitHub
- future work should be safe to promote to `bimbelrumba.id`
- AI agents are used to support inventory, design, implementation, and review

---

## 2. Current Backlog Strategy

The current strategy is to develop in layers.

The project should not jump directly into advanced operational automation before the baseline is stable.

The recommended order is:

1. stabilize baseline and inventory
2. secure registration flow
3. establish student creation and numbering logic
4. strengthen academic structure
5. build class operations
6. build attendance and finance workflow
7. expand reporting and operational control

---

## 3. Priority Levels

This backlog uses the following priority interpretation:

- **P0** = must be clarified immediately before safe development can continue
- **P1** = highest implementation priority
- **P2** = important next-layer work
- **P3** = useful but can wait until core workflow is stable
- **P4** = later optimization / enhancement work

---

## 4. P0 — Baseline Stabilization

These tasks should be handled first so future development is grounded in reality.

### 4.1 Verify `Rumba Pendaftaran` status
- confirm whether it is file-backed in the app
- confirm whether it is Git-tracked
- confirm whether it is already pushed to GitHub
- confirm whether it is safe to extend further

### 4.2 Audit all current custom DocTypes
Audit the current known DocTypes:
- `Rumba Pendaftaran`
- `Ruangan`
- `Semester`
- `Tahun Ajaran`
- `Program Belajar`
- `Provinsi`
- `Unit`
- `Kota`

Check:
- ERPNext UI existence
- app source existence
- Git tracking
- GitHub status
- extension readiness

### 4.3 Identify hidden standard customizations
Check whether any standard ERPNext DocTypes have been customized through:
- Custom Fields
- Property Setters
- Workflows
- Client Scripts
- Print Formats
- Notifications

Determine whether export is needed.

### 4.4 Confirm fixture/export requirements
- identify what must be exported
- identify what is still site-only
- identify migration risks caused by missing exports

### 4.5 Confirm repo baseline cleanliness
- verify active branch strategy
- verify working tree cleanliness
- verify local repo vs GitHub alignment

---

## 5. P1 — Registration Workflow Core

These tasks form the most important functional next step.

### 5.1 Design `Rumba Pendaftaran` lifecycle
Define:
- statuses
- transitions
- who can move each status
- what approval rules apply

### 5.2 Add missing fields to `Rumba Pendaftaran`
Identify whether more fields are needed for:
- student identity
- parent identity
- branch/unit relation
- program relation
- academic placement
- approval handling
- remarks / rejection notes

### 5.3 Design approval workflow
Define what happens when a registration is:
- submitted
- reviewed
- approved
- rejected
- revised

### 5.4 Design Student creation flow
Define whether approved registration should:
- create `Student`
- create linked records
- copy selected fields
- prevent duplicates
- mark source registration as converted

### 5.5 Design student ID / numbering logic
Define:
- format
- uniqueness rules
- whether it depends on branch
- whether numbering is global or segmented
- how collisions are prevented

### 5.6 Define permission model for registration flow
Clarify roles such as:
- parent/public submitter
- admin pendaftaran
- admin cabang
- system manager
- finance
- academic staff

---

## 6. P2 — Academic Structure Strengthening

These tasks strengthen the learning structure around the existing foundation.

### 6.1 Review `Tahun Ajaran`
Define:
- code format
- date range logic
- active/inactive status
- relation to semester and program operations

### 6.2 Review `Semester`
Define:
- code format
- start/end period
- status logic
- relation to academic year

### 6.3 Review `Program Belajar`
Define:
- purpose and scope
- duration structure
- relation to branch/unit
- relation to student placement
- relation to fees if needed later

### 6.4 Review `Unit`
Clarify whether `Unit` means:
- branch
- school/tutoring unit
- academic unit
- operational business unit

Confirm data model accordingly.

### 6.5 Review `Ruangan`
Define:
- branch/unit relation
- capacity
- scheduling relevance
- availability logic

### 6.6 Review region structure
Clarify the intended relationship between:
- `Provinsi`
- `Kota`
- `Unit`

Make sure this supports branch operations cleanly.

---

## 7. P2 — Student Placement and Class Preparation

These tasks prepare the system for class operations.

### 7.1 Define enrollment structure
Determine how students are linked to:
- program
- academic year
- semester
- branch/unit

### 7.2 Design class group / rombel structure
Define whether a new DocType is needed for:
- class group
- level/group naming
- tutor assignment
- room assignment
- schedule grouping

### 7.3 Define schedule model
Determine how to represent:
- day
- time
- room
- tutor
- class group
- recurring session structure

### 7.4 Define student placement workflow
Clarify how a student moves from:
- approved registration
- to student record
- to enrollment
- to assigned class group

---

## 8. P3 — Attendance and Operational Flow

These tasks become important once class structure is stable.

### 8.1 Design attendance model
Clarify attendance for:
- students
- tutors
- class sessions

### 8.2 Define class session logic
Determine whether attendance is attached to:
- schedule templates
- generated sessions
- live meeting records

### 8.3 Define tutor attendance-to-payroll flow
Clarify whether tutor compensation depends on:
- number of attended sessions
- completed sessions
- validated teaching records

### 8.4 Define exceptions handling
Plan how to handle:
- tutor replacement
- class cancellation
- room changes
- make-up classes
- absent students

---

## 9. P3 — Finance and Billing Flow

These tasks should come after registration and academic structure are stable.

### 9.1 Define billing trigger rules
Clarify when invoices should be created:
- after approval
- after enrollment
- per term
- per month
- by selected fee templates

### 9.2 Define fee model
Determine how fees relate to:
- program
- branch/unit
- academic period
- registration type

### 9.3 Define registration fee flow
Clarify whether registration approval also creates:
- invoice
- payment entry expectation
- finance follow-up state

### 9.4 Define recurring tuition flow
Clarify how tuition is generated and tracked.

---

## 10. P4 — Reporting, Dashboard, and Optimization

These tasks improve operational visibility and maturity.

### 10.1 Registration pipeline reporting
Useful views may include:
- pending registrations
- approved registrations
- rejected registrations
- conversion to student status

### 10.2 Student distribution reporting
Possible reports:
- by branch/unit
- by program
- by academic year
- by semester

### 10.3 Attendance reporting
Possible reports:
- student attendance summary
- tutor attendance summary
- class session summary

### 10.4 Finance reporting
Possible reports:
- unpaid registration fees
- tuition status
- branch billing summary

### 10.5 Workspace / dashboard improvement
Future dashboards may be needed for:
- admissions admin
- academic operations
- branch admin
- finance

---

## 11. Current Recommended Execution Order

At this stage, the recommended practical order is:

### Phase 1
- complete baseline inventory
- verify `Rumba Pendaftaran`
- verify Git / GitHub alignment
- identify missing exports

### Phase 2
- design and stabilize registration workflow
- define approval statuses
- define Student creation logic
- define student numbering

### Phase 3
- strengthen academic and placement structure
- clarify Unit / Program / Semester / Tahun Ajaran usage
- prepare rombel and schedule design

### Phase 4
- build attendance flow
- connect operational class records
- prepare tutor compensation logic

### Phase 5
- build finance automation
- invoicing
- recurring billing
- reporting and dashboards

---

## 12. Agent Usage Guidance for This Backlog

The following agent sequence is recommended for each major task:

### Inventory Agent
Use for:
- baseline verification
- repo/UI mismatch detection
- export/fixture risk identification

### Architect Agent
Use for:
- feature design
- data model decisions
- workflow logic
- permission logic
- numbering strategy

### Builder Agent
Use for:
- implementation planning
- code generation
- file/path decisions
- fixtures and migration planning

### Reviewer Agent
Use for:
- risk checking
- migration/deployment safety
- hidden dependency detection
- validation of implementation readiness

---

## 13. Current Most Important Next Task

The current most important next task is:

- verify the project baseline, especially `Rumba Pendaftaran`
- then design the registration approval flow
- then define Student creation and student numbering logic

This should be treated as the immediate bridge from current setup into structured development.

---

## 14. Update Rules

This backlog should be updated when:

- a high-priority task is completed
- priorities shift
- new DocTypes are added
- architecture decisions change future implementation order
- hidden baseline issues are discovered
- deployment strategy changes

---

## 15. Current Summary

At the current stage of the project:

- the project already has several foundational custom DocTypes
- the baseline still needs partial verification
- the registration workflow should become the next core feature
- future work should proceed in a structured agent-assisted sequence
- stability and version control should come before advanced automation

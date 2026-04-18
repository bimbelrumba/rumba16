# Backlog — bimbel_rumba

## 1. Purpose
This file tracks the active and upcoming work for the `bimbel_rumba` project.

It is used to:
- keep priorities visible
- define what should happen next
- prevent work from jumping ahead without enough baseline clarity
- help agents and the human operator stay aligned

This file is not the place for deep architecture discussion.  
It is a working task list.

---

## 2. Status Labels
Use these labels consistently:

- **Backlog** — identified but not started
- **Ready** — clear enough to begin
- **In review** — being reviewed by an agent
- **Planned** — implementation approach is defined
- **Blocked** — cannot safely continue yet
- **In progress** — currently being executed manually
- **Needs verification** — work may exist but still needs proof
- **Done** — completed and sufficiently verified
- **Deferred** — intentionally postponed

---

## 3. Priority Labels
Use these priority labels:

- **P1** — immediate / high importance
- **P2** — important but not urgent
- **P3** — useful later
- **P4** — low priority / future idea

---

## 4. Current Backlog Overview

| ID | Task | Priority | Status | Depends on | Notes |
|---|---|---:|---|---|---|
| BR-001 | Refresh baseline inventory of current project state | P1 | Ready | — | Reconfirm ERPNext UI vs repo vs GitHub alignment where needed |
| BR-002 | Review design of DocType `Rumba Pendaftaran` | P1 | Ready | BR-001 (recommended) | Use Architect Agent to assess current structure before further expansion |
| BR-003 | Define approved improvement scope for `Rumba Pendaftaran` | P1 | Backlog | BR-002 | Convert review findings into approved decisions |
| BR-004 | Prepare Builder implementation plan for `Rumba Pendaftaran` improvements | P1 | Backlog | BR-003 | Manual ERPNext UI guidance + repo sync guidance |
| BR-005 | Review Builder plan for safety and completeness | P1 | Backlog | BR-004 | Use Reviewer Agent before manual execution |
| BR-006 | Execute approved `Rumba Pendaftaran` changes in ERPNext dev UI | P1 | Backlog | BR-005 | Manual operator task |
| BR-007 | Verify repo/source impact after `Rumba Pendaftaran` UI changes | P1 | Backlog | BR-006 | Check app source, Git status, and sync cleanliness |
| BR-008 | Push verified `Rumba Pendaftaran` state to GitHub | P1 | Backlog | BR-007 | Only after verification is clear |
| BR-009 | Review current relationships among `Unit`, `Program Belajar`, `Semester`, `Tahun Ajaran`, and `Kota` | P2 | Backlog | BR-001 | Clarify structural consistency across supporting DocTypes |
| BR-010 | Identify any standard ERPNext customizations already in use | P1 | Backlog | BR-001 | Needed to reduce site-only risk |
| BR-011 | Decide fixture/export handling approach for standard customizations | P1 | Backlog | BR-010 | Only if such customizations are confirmed |
| BR-012 | Define student-approval-to-student-creation target flow | P2 | Backlog | BR-003 | Architectural step after registration structure is clearer |
| BR-013 | Define duplicate-prevention strategy for registration records | P2 | Backlog | BR-002 | Should remain simple and practical |
| BR-014 | Review broader module growth priorities after registration baseline improves | P3 | Deferred | BR-001 to BR-008 | Later planning phase |

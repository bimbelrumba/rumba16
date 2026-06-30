# Project State — bimbel_rumba

## 1. Project Identity
- **Project name:** bimbel_rumba
- **Framework:** ERPNext v16 / Frappe
- **Development site:** dev.bimbelrumba.id
- **Production site:** bimbelrumba.id
- **Repository role:** source-controlled reference for reproducible work
- **Primary working reality:** many DocType changes are performed manually through the ERPNext UI on the development site

---

## 2. Working Rules
- ERPNext UI, local repo, and GitHub must not be assumed to be automatically synchronized.
- Important changes should be made traceable and reproducible.
- GitHub should remain the long-term source of truth for tracked work.
- AI agents are used for planning, auditing, implementation guidance, and review.
- AI agents must not default to writing directly into the local repository working tree.
- Manual ERPNext UI work must be followed by repo/source verification when relevant.
- Standard ERPNext customizations may require export / fixtures / explicit tracking.

---

## 3. Current Project Goal
The current goal is to continue developing the `bimbel_rumba` module in a controlled way using a multi-agent workflow, while keeping the ERPNext development site, repository, and GitHub reasonably aligned.

Near-term focus:
- verify current project baseline
- review and refine existing DocType structures
- improve implementation workflow between ERPNext UI and GitHub
- prepare selected DocTypes for safer next-phase development

---

## 4. Multi-Agent Workflow in Use
The project uses these agents:

- **Inventory Agent**  
  Used to classify baseline status, identify verification gaps, and detect repo/site mismatch risk.

- **Architect Agent**  
  Used to review or design feature structure, field model, workflow, and scope boundaries.

- **Builder Agent**  
  Used to translate approved design into manual ERPNext UI actions, repo verification steps, sync warnings, and testing guidance.

- **Reviewer Agent**  
  Used to assess safety, completeness, sync risk, test adequacy, and production-readiness of proposed work.

---

## 5. Known Functional Context
The project is being developed for the Bimbel Rumba operational context.

Known direction includes:
- student registration flow
- academic structure support
- branch/unit-related data structure
- future approval workflow needs
- future student creation flow after approval
- future operational expansion through controlled module growth

Verified development-site registration workflow as of 2026-05-26:
- `Rumba Pendaftaran` can move through: registration created -> Customer created -> Sales Invoice created -> invoice paid -> payment manually synchronized -> registration approved -> `Rumba Murid` created.
- Minimum payment-control fields added to `Rumba Pendaftaran`: `sales_invoice`, `status_pembayaran`, and `tanggal_pembayaran`.
- Server-side validation is active on the development site: `status_pendaftaran` cannot be changed to `Disetujui` unless `status_pembayaran` is `Lunas`.
- Current payment sync behavior is intentionally manual: after ERPNext marks the linked `Sales Invoice` as paid, the operator uses the `Sinkronkan Pembayaran` button on `Rumba Pendaftaran` to update `status_pembayaran` to `Lunas`.
- Current active client-script actions on `Rumba Pendaftaran` include: `Buat Customer`, `Buat Invoice`, `Buka Invoice`, `Sinkronkan Pembayaran`, and `Buat Murid`.
- These site-side changes should be exported and committed to GitHub before being treated as source-controlled baseline.

---

## 6. Known Existing Custom DocTypes
The following custom DocTypes are known to already exist in the project:

- Rumba Pendaftaran
- Ruangan
- Semester
- Tahun Ajaran
- Program Belajar
- Provinsi
- Unit
- Kota

Important note:
- These DocTypes were created through the ERPNext UI.
- Except **Rumba Pendaftaran**, the other DocTypes were reported as already sent to the repo folder and pushed to GitHub.
- This status should still be treated as **reported state** unless re-verified during baseline checks.

---

## 7. Baseline Confidence Level
Current baseline confidence is **partial**.

Reason:
- some objects are known by user report
- some objects are reported as already synced to repo/GitHub
- full verification between ERPNext UI state, app source state, Git state, and GitHub state may still be incomplete

This means:
- feature work can continue carefully
- but baseline-sensitive features should still be checked before implementation decisions become deeper

---

## 8. Known Workflow Constraint
A critical constraint in this project is:

- DocType creation and modification are often performed manually through the ERPNext web UI
- AI agents do not directly execute those changes
- the local repository must be protected from uncontrolled AI-generated edits
- repo/GitHub synchronization must be handled deliberately

Because of this, the Builder Agent should be used mainly for:
- manual implementation guidance
- repo follow-up guidance
- fixture/export risk awareness
- testing and deployment caution

---

## 9. Current Known Risks
The following risks are currently relevant:

### A. Repo vs site mismatch risk
ERPNext UI changes may exist that are not yet safely reflected in source control.

### B. GitHub freshness risk
Some project state may be assumed to be pushed, but not recently re-verified.

### C. Site-only customization risk
Standard ERPNext customizations may exist in the site without proper export or fixture tracking.

### D. Baseline ambiguity risk
Some future design decisions may become weak if they rely on assumptions rather than verified state.

### E. Local repo drift risk
If AI-generated local code or uncontrolled edits are used carelessly, repo synchronization may become unreliable.

---

## 10. Current Operating Preference
Preferred working sequence:

1. establish or refresh baseline with Inventory Agent when needed
2. review/design with Architect Agent
3. translate approved design into manual implementation guidance with Builder Agent
4. validate safety and readiness with Reviewer Agent
5. execute carefully in ERPNext UI and verify repository impact
6. synchronize to GitHub in a controlled way

---

## 11. What Is Considered “Safe to Continue”
A task is considered reasonably safe to continue when:
- the relevant current state is sufficiently understood
- the target DocType or feature is not relying on major hidden assumptions
- repo/site mismatch risk is acknowledged
- any likely export/customization risk is at least identified
- the next action is small, controlled, and reversible

---

## 12. Current Documentation Status
The project currently uses these core coordination documents:

- `AGENTS.md`
- `docs/project-state.md`
- `docs/backlog.md`
- `docs/agents/inventory.md`
- `docs/agents/architect.md`
- `docs/agents/builder.md`
- `docs/agents/reviewer.md`

---

## 13. Immediate Next Priority
Immediate priority:
- continue using the multi-agent workflow in a disciplined way
- review important DocTypes before deeper implementation
- keep manual ERPNext UI work and repo synchronization under tighter control
- reduce ambiguity in the current project baseline over time

---

## 14. Update Rule for This Document
Update this file when any of the following changes materially:
- major project workflow rule
- known system architecture direction
- verified baseline status
- key existing DocTypes
- core risk profile
- working method between ERPNext UI, repo, and GitHub

This file should remain:
- short
- stable
- factual
- easy for agents to read
- focused on current project reality

# Decision Log - Rumba16

Catatan keputusan arsitektur dan desain penting untuk proyek Rumba16.

Format setiap entri (ADR-style ringan):

- **ID** — nomor urut, tidak pernah dipakai ulang.
- **Tanggal** — tanggal keputusan dibuat.
- **Status** — Proposed / Accepted / Superseded by ADR-XXX / Rejected.
- **Konteks** — masalah / situasi yang memicu keputusan.
- **Keputusan** — apa yang diputuskan.
- **Alasan** — kenapa pilihan itu yang diambil.
- **Konsekuensi** — efek positif & negatif, follow-up yang dibutuhkan.
- **Referensi** — link ke dokumen / file terkait.

Setiap entri **append-only**. Jangan menghapus atau menulis ulang entri lama. Jika keputusan berubah, tambahkan entri baru dan ubah status entri lama menjadi `Superseded by ADR-XXX`.

---

## ADR-0001 — Branch `dev` sebagai working branch

- **Tanggal:** 2026-05-27 (recorded retroactively)
- **Status:** Accepted
- **Konteks:** Perlu kejelasan branch mana yang dipakai untuk pengembangan aktif vs rilis.
- **Keputusan:** `dev` dipakai sebagai working branch di GitHub. `main` belum dipakai untuk app.
- **Alasan:** Memisahkan ruang eksperimen dari rilis stabil; konsisten dengan workflow multi-agen.
- **Konsekuensi:**
  - Semua PR target `dev`.
  - `main` baru dipakai ketika ada rilis pertama yang stabil.
- **Referensi:** memori user `project_branch_strategy.md`.

## ADR-0002 — Naming convention `rumba16` / `bimbel_rumba_v16` dipertahankan

- **Tanggal:** 2026-05-27 (recorded retroactively)
- **Status:** Accepted
- **Konteks:** Ada peluang rename repo/app untuk konsistensi penamaan, tapi sudah ada referensi internal & eksternal.
- **Keputusan:** Tidak melakukan rename. Pertahankan `rumba16` (repo) dan `bimbel_rumba_v16` (app slug).
- **Alasan:** Cost rename > benefit; banyak path internal yang tergantung.
- **Konsekuensi:** Dokumentasi & onboarding harus menjelaskan dual-naming ini.
- **Referensi:** memori user `project_naming_convention.md`.

## ADR-0003 — Multi-agent workflow (4 agen)

- **Tanggal:** 2026-05-27 (recorded retroactively)
- **Status:** Accepted
- **Konteks:** Proyek dikembangkan dengan bantuan beberapa peran agen AI agar tanggung jawab jelas.
- **Keputusan:** Pakai 4 agen: Inventory, Architect, Builder, Reviewer. Aturan detail ada di `rumba16/docs/agents/`.
- **Alasan:** Memisahkan fase audit, desain, implementasi, dan review mengurangi konflik dan menghasilkan dokumen jejak yang jelas.
- **Konsekuensi:**
  - Setiap fase menghasilkan dokumen tertulis (inventory, review, plan, dst.).
  - Builder tidak boleh memulai sebelum Architect menyelesaikan review/keputusan.
- **Referensi:** memori user `project_agent_workflow.md`, folder `rumba16/docs/agents/`.

## ADR-0004 — Adopsi audit DocType sebagai baseline arsitektur

- **Tanggal:** 2026-05-27
- **Status:** Accepted
- **Konteks:** Sebelum melakukan refactor, perlu baseline tertulis tentang struktur DocType saat ini.
- **Keputusan:** [current-doctype-inventory.md](current-doctype-inventory.md) menjadi sumber kebenaran untuk kondisi sekarang. Review-nya didokumentasikan di [architecture-review.md](architecture-review.md).
- **Alasan:** Memisahkan "apa yang ada" dari "apa yang seharusnya" supaya diskusi desain tidak campur dengan diskusi fakta.
- **Konsekuensi:**
  - Setiap perubahan DocType wajib memperbarui inventory.
  - Diskusi refactor merujuk ke architecture-review.md, bukan re-audit ulang.
- **Referensi:** [current-doctype-inventory.md](current-doctype-inventory.md), [architecture-review.md](architecture-review.md).

## ADR-0005 — Prioritaskan fix bug P0 sebelum refactor besar

- **Tanggal:** 2026-05-27
- **Status:** Accepted
- **Konteks:** Architecture review menemukan tiga bug blocking (F-01 `set_kode_unit`, F-02 fungsi sync hilang, F-03 Client Script Semester) bersamaan dengan kebutuhan refactor struktural besar (Orang Tua, Anak, Kelas, Enrollment).
- **Keputusan:** Selesaikan F-01..F-03 dan item P0 multi-unit lainnya **sebelum** memulai refactor struktural atau penambahan DocType baru.
- **Alasan:** Refactor di atas bug akan menyamarkan akar masalah dan membuat regresi sulit dilacak.
- **Konsekuensi:**
  - Roadmap dibagi: fase Fix → fase Refactor data → fase Domain split.
  - Builder akan dialokasikan ke perbaikan kecil dulu.
- **Referensi:** [architecture-review.md §5](architecture-review.md#5-ringkasan-prioritas).

## ADR-0006 — Server-side menjadi sumber kebenaran untuk normalisasi & fetch

- **Tanggal:** 2026-05-27
- **Status:** Accepted
- **Konteks:** Banyak logic penting (normalisasi kode, perhitungan kapasitas, fetch nama kota/provinsi, generate kode/semester) hanya berjalan di Client Script. Import data, API, patch, dan server script melewati logic ini → data inconsistency.
- **Keputusan:** Semua normalisasi, perhitungan derivasi, dan pengisian field read-only **wajib** ada di controller server-side (`validate`, `before_insert`, atau `fetch_from`). Client Script hanya untuk UX feedback (live preview, indicator color, filter dropdown).
- **Alasan:** Frappe menjalankan controller pada semua path tulis; Client Script tidak. Memilih server-side menghilangkan satu kelas bug.
- **Konsekuensi:**
  - Sebagian fixture Client Script yang berisi logic data harus dipindahkan / diduplikasi ke Python.
  - Code review checklist Reviewer harus memuat item ini.
- **Referensi:** [architecture-review.md §4.5](architecture-review.md#45-normalisasi-yang-hanya-client-side).

## ADR-0007 — Workflow Frappe untuk approval Pendaftaran

- **Tanggal:** 2026-05-27
- **Status:** Proposed
- **Konteks:** `status_pendaftaran` saat ini hanya field Select dengan beberapa validasi server (Approve butuh Lunas). Tidak ada audit trail, tidak ada role-based transition, status bisa diubah manual.
- **Keputusan (usulan):** Pindahkan transisi status ke dokumen `Workflow` Frappe. Pertimbangkan juga `is_submittable = 1` untuk mendapatkan amend/cancel standard ERPNext.
- **Alasan:** Workflow memberi audit trail, role gating, dan UI tombol-aksi yang konsisten dengan ERPNext lain.
- **Konsekuensi:**
  - Migrasi data pendaftaran lama: state lama → state Workflow.
  - Validasi `Disetujui butuh Lunas` dipindah ke kondisi transisi Workflow.
  - Pilihan `is_submittable` akan memengaruhi banyak script/hook → keputusan terpisah jika diputuskan ya.
- **Referensi:** [architecture-review.md §3.6](architecture-review.md#36-workflow-frappe-untuk-pendaftaran).

## ADR-0008 — Pisahkan biodata, enrollment, dan jadwal menjadi DocType terpisah (long-term)

- **Tanggal:** 2026-05-27
- **Status:** Proposed
- **Konteks:** `Rumba Pendaftaran` & `Rumba Murid` mencampur biodata permanen, identitas ortu, enrollment per tahun ajaran, dan jadwal mingguan. Duplikasi data tinggi; history tidak terjaga.
- **Keputusan (usulan):**
  - Tambah `Rumba Orang Tua / Wali` (master, link ke Customer).
  - Tambah `Rumba Anak` (master biodata permanen).
  - Tambah `Rumba Kelas / Sesi Belajar` (unit + ruangan + jadwal + program + kapasitas + guru).
  - Tambah `Rumba Enrollment` (per tahun ajaran / semester, link Anak ↔ Kelas).
  - `Rumba Pendaftaran` dipertahankan sebagai DocType intake, tidak menyimpan jadwal permanen.
  - `Rumba Murid` dievaluasi: jadi view aktif Enrollment atau dihapus.
- **Alasan:** Memisahkan "fakta yang tidak berubah" dari "transaksi/peristiwa" mengurangi duplikasi dan memungkinkan history yang benar.
- **Konsekuensi:**
  - Migrasi data besar dari Pendaftaran/Murid existing.
  - Banyak Client Script `Tombol Buat Murid` harus ditulis ulang.
  - Hanya dimulai setelah ADR-0005 (fase Fix) selesai.
- **Referensi:** [architecture-review.md §3](architecture-review.md#3-doctype-yang-kurang).

## ADR-0009 — Tarif Program & item ERPNext sebagai sumber harga

- **Tanggal:** 2026-05-27
- **Status:** Proposed
- **Konteks:** Saat ini `buat_sales_invoice` di Pendaftaran memilih Item manual; tidak ada mapping resmi antara `Rumba Program Belajar` dan Item/harga.
- **Keputusan (usulan):** Tambah DocType `Rumba Tarif Program` dengan kombinasi (program × jenis_kelas × periode) → Item + harga. Invoice dibuat otomatis dari tarif yang berlaku.
- **Alasan:** Revenue per program bisa di-roll-up via GL ERPNext standar; harga tidak hardcoded di kode.
- **Konsekuensi:**
  - Perlu UI manajemen tarif & periode berlaku.
  - Migrasi: tarif berjalan yang sekarang inline di invoice perlu di-backfill.
- **Referensi:** [architecture-review.md §3.5](architecture-review.md#35-rumba-tarif-program).

## ADR-0010 — User Permission per `Rumba Unit` sebelum multi-unit live

- **Tanggal:** 2026-05-27
- **Status:** Accepted
- **Konteks:** Belum ada permission filter per unit. Tanpa ini, staf unit A bisa melihat / mengedit data unit B.
- **Keputusan:** Sebelum sistem dioperasikan di lebih dari satu unit secara produksi, setup User Permission per `Rumba Unit` + role profile (mis. Admin Unit, Koordinator, Finance HQ, Akademik HQ) wajib selesai.
- **Alasan:** Multi-tenant tanpa permission isolation adalah risiko data leak antar cabang.
- **Konsekuensi:**
  - Test plan multi-unit harus memverifikasi isolation.
  - Beberapa DocType (Pendaftaran, Murid, Kelas, Enrollment) butuh field `unit` yang konsisten untuk dipakai sebagai filter permission.
- **Referensi:** [architecture-review.md §5](architecture-review.md#5-ringkasan-prioritas).

---

## Template untuk Entri Baru

```
## ADR-XXXX — <Judul singkat>

- **Tanggal:** YYYY-MM-DD
- **Status:** Proposed | Accepted | Superseded by ADR-YYYY | Rejected
- **Konteks:** <masalah yang memicu>
- **Keputusan:** <apa yang diputuskan>
- **Alasan:** <kenapa pilihan itu>
- **Konsekuensi:** <efek + follow-up>
- **Referensi:** <link dokumen/file>
```

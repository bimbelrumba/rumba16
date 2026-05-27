# Architecture Review - Rumba16

Dokumen ini merangkum hasil audit terhadap [current-doctype-inventory.md](current-doctype-inventory.md).
Fokus: relasi bermasalah, duplikasi data, DocType yang kurang, dan field yang perlu diperbaiki.

Tanggal review: 2026-05-27.
Branch sumber: `dev`.

---

## 1. Relasi yang Bermasalah

### 1.1 `Rumba Pendaftaran` sebagai "god object"

`Rumba Pendaftaran` saat ini menanggung 5 tanggung jawab sekaligus:

1. Identitas anak (nama, tanggal lahir, jenis kelamin, ABK, dst.)
2. Identitas + kontak orang tua/wali
3. Pilihan jadwal (`senin..sabtu`, `jam_belajar`) & program
4. Workflow approval (`status_pendaftaran`)
5. Lifecycle finance (Customer, Sales Invoice, Payment Entry sync)

**Dampak:** satu form jadi titik kegagalan tunggal, sulit diuji, sulit dimaintain, dan rawan regresi.

### 1.2 `Rumba Murid` mencampur biodata + enrollment aktif

Biodata permanen (NIM, nama, tanggal lahir) digabung dengan data enrollment yang berubah per tahun ajaran (tahun ajaran, jadwal, program, status). Akan rumit saat:

- Murid pindah program belajar.
- Murid naik tahun ajaran.
- Murid cuti / berhenti / aktif kembali.
- Murid pindah unit.

History tidak terjaga karena field di-overwrite.

### 1.3 `Rumba Ruangan` tidak terhubung ke `Rumba Unit`

Ruangan tampak global. Akibatnya:

- `kode_ruangan` bisa bentrok antar cabang.
- Tidak bisa dipakai untuk perencanaan kapasitas per unit.
- Tidak bisa dipakai untuk penjadwalan kelas per unit.

### 1.4 Tidak ada DocType "Kelas / Sesi Belajar"

Jadwal disimpan sebagai 6 field check di Pendaftaran dan Murid. Konsekuensi:

- Tidak bisa hitung kapasitas kelas aktual.
- Tidak bisa lihat daftar murid per sesi.
- Tidak bisa pasang ruangan / guru ke sesi.
- Validasi bentrok jadwal tidak mungkin.

### 1.5 Customer dibuat per pendaftaran tanpa de-duplikasi ortu

Satu orang tua dengan 2 anak akan menghasilkan 2 Customer. Akibatnya:

- Statement piutang per keluarga pecah.
- Sulit lihat total AR per ortu.
- Tidak ada link Anak ↔ Ortu yang persistent.

### 1.6 Hook `doc_events` menunjuk fungsi yang tidak ada

`hooks.py` memanggil `sync_status_pembayaran_from_sales_invoice` dan `sync_status_pembayaran_from_payment_entry`, tetapi fungsi tersebut tidak ada di `rumba_pendaftaran.py`. Setiap submit/cancel Sales Invoice atau Payment Entry berisiko error → memblok operasi finance.

### 1.7 Naming field Link membingungkan

Beberapa field Link diberi nama `nama_xxx` padahal yang tersimpan adalah document name / kode:

- `Rumba Pendaftaran.nama_kota` → Link ke `Rumba Kota` (isinya `kode_kota`).
- `Rumba Pendaftaran.nama_unit` → Link ke `Rumba Unit` (isinya `nama_unit` sebagai naming).
- `Rumba Murid.nama_unit` bertipe **Data** padahal `options = Rumba Unit` → harusnya Link.

---

## 2. Duplikasi Data

| Field / kelompok | Disimpan di | Sumber kebenaran seharusnya |
|---|---|---|
| `nama_lengkap`, `nama_panggilan`, `tanggal_lahir`, `jenis_kelamin`, `anak_berkebutuhan_khusus` | `Rumba Pendaftaran` **dan** `Rumba Murid` | `Rumba Anak` (DocType baru) |
| `nama_orang_tua_wali`, `hubungan_dengan_anak`, `nomor_handphone`, `alamat_email`, `alamat` | `Rumba Pendaftaran` **dan** `Rumba Murid` | `Rumba Orang Tua / Wali` (DocType baru) |
| `senin..sabtu`, `jam_belajar`, `jenis_kelas` | `Rumba Pendaftaran` **dan** `Rumba Murid` | `Rumba Kelas / Sesi Belajar` (DocType baru) |
| `nama_kota`, `nama_provinsi` | `Rumba Kota`, `Rumba Unit`, `Rumba Pendaftaran` | `Rumba Provinsi` / `Rumba Kota` saja (pakai `fetch_from`) |
| `kode_unit` | `Rumba Unit`, `Rumba Pendaftaran`, `Rumba Murid` | `Rumba Unit` saja |
| `status_pembayaran`, `tanggal_pembayaran` | denormalisasi di `Rumba Pendaftaran` | `Sales Invoice` (dibaca on-demand, bukan disimpan) |
| `tahun_ajaran`, `program_belajar` | `Rumba Pendaftaran` **dan** `Rumba Murid` | `Rumba Enrollment` (DocType baru) |

**Prinsip yang dilanggar:** banyak field disalin saat pembuatan murid via Client Script `Tombol Buat Murid`. Setelah disalin, tidak ada sync balik → Pendaftaran asli & Murid bisa berbeda.

---

## 3. DocType yang Kurang

Prioritas tinggi → rendah:

### 3.1 `Rumba Orang Tua / Wali`

Identitas ortu/wali sebagai master tersendiri. Satu ortu bisa punya banyak anak. Link ke `Customer` melekat di sini.

### 3.2 `Rumba Anak` (biodata permanen)

Pisahkan dari Pendaftaran & Murid. Biodata tidak berubah per semester.

### 3.3 `Rumba Kelas` (atau `Rumba Sesi Belajar`)

Kombinasi: `unit` × `ruangan` × `hari` × `jam` × `program` × `jenis_kelas` × `tahun_ajaran` / `semester` × `guru` × `kapasitas`. Pendaftaran & Murid cukup Link ke kelas.

### 3.4 `Rumba Enrollment`

Catatan per semester / tahun ajaran (program, jadwal, status: Aktif/Cuti/Lulus/Berhenti). Memisahkan biodata permanen dari status akademik yang berubah.

### 3.5 `Rumba Tarif Program`

Mapping `Rumba Program Belajar` × `jenis_kelas` × periode → `Item` ERPNext + harga. Menghilangkan pemilihan item manual saat buat invoice; mendukung revenue-per-program via GL.

### 3.6 Workflow Frappe untuk Pendaftaran

Bukan DocType baru, tapi dokumen `Workflow` Frappe. Saat ini `status_pendaftaran` hanya field Select dengan validasi parsial; audit trail lemah, role-based transition tidak terkontrol.

---

## 4. Field yang Perlu Diperbaiki

### 4.1 Bug/Inkonsistensi yang harus difix dulu

| # | Lokasi | Masalah | Fix yang disarankan |
|---|---|---|---|
| F-01 | `rumba_pendaftaran.py::set_kode_unit()` | Mencari field `unit`/`cabang`/`rumba_cabang` yang tidak ada di metadata | Baca dari `nama_unit` (field Link unit aktual) |
| F-02 | `hooks.py` | Memanggil `sync_status_pembayaran_from_sales_invoice` & `sync_status_pembayaran_from_payment_entry` yang belum ada | Implementasi kedua fungsi di `rumba_pendaftaran.py` |
| F-03 | Client Script `Generate Nama Semester` | Memakai `frappe.ui.form.on('Semester', ...)` bukan `Rumba Semester` | Ganti string DocType |
| F-04 | `Rumba Unit` list formatter | Memetakan `Crowdfunding` (bukan opsi) & tidak memetakan `Partnership` | Sesuaikan ke opsi metadata: `YRKI`, `Franchise`, `Partnership` |
| F-05 | `Rumba Murid.nama_unit` | Tipe `Data` tapi `options = Rumba Unit` | Ubah ke `Link` |
| F-06 | `Rumba Murid.nomor_induk_murid` | Unik tapi tidak wajib, dipakai sebagai naming | Tambah `reqd = 1` atau ubah strategi naming |

### 4.2 Field read-only tanpa logic pengisi

| Field | DocType | Status |
|---|---|---|
| `kode_unit` | `Rumba Unit` | Read-only & unik, tidak terlihat logic server/client pengisinya |
| `kode_tahun_ajaran` | `Rumba Tahun Ajaran` | Sama |
| `kode_semester`, `nama_semester`, `tanggal_mulai_semester`, `tanggal_akhir_semester` | `Rumba Semester` | Diisi oleh Client Script yang broken (lihat F-03) |
| `nama_kota`, `nama_provinsi` | `Rumba Kota`, `Rumba Unit` | Read-only tanpa `fetch_from` eksplisit → rawan stale |
| `tanggal_pendaftaran` | `Rumba Pendaftaran` | Read-only tanpa default jelas |

**Fix:** pindahkan ke server-side (controller `before_insert`/`validate`) atau gunakan `fetch_from` untuk field mirror.

### 4.3 Field status yang berpotensi kontradiktif

`Rumba Tahun Ajaran` punya dua flag status: `status` (Aktif/Arsip) **dan** `nonaktif` (Check). Bisa saling bertentangan. Pilih salah satu sebagai sumber kebenaran.

### 4.4 Naming series yang akan overflow

`Rumba Pendaftaran` autoname = `kode_unit + YY + MM + series 2 digit`. Max 99 pendaftaran/bulan/unit. Naikkan ke minimal 4 digit, atau pakai `naming_series` Frappe standard.

### 4.5 Normalisasi yang hanya client-side

Hanya berjalan dari UI; tidak berjalan untuk import, API, patch, server script.

- `Rumba Program Belajar.kode_program_belajar` (uppercase + trim).
- `Rumba Provinsi.kode_provinsi` (perlu normalisasi, belum ada).
- `Rumba Unit` kapasitas (`kapasitas_max_sesi_belajar_minggu`, `kapasitas_max_murid`).
- `Rumba Tahun Ajaran.tanggal_selesai` (auto 30 Juni tahun berikutnya).

**Fix:** pindahkan ke `validate()` server-side, biarkan Client Script jadi UX feedback saja.

### 4.6 Customer & Invoice hardcoded values

`buat_sales_invoice` & pembuatan Customer di `Rumba Pendaftaran`:

- `customer_group = "Individual"` hardcoded → reporting per segmen tidak fleksibel.
- `territory = "Indonesia"` hardcoded → tidak pakai Territory hierarchy ERPNext.
- Default Company global, bukan dari `Rumba Unit` → `cost_center` & `warehouse` unit tidak ikut → konsolidasi P&L per cabang manual.
- Item dipilih manual user → tidak ada mapping ke `Rumba Program Belajar`.

---

## 5. Ringkasan Prioritas

| Prioritas | Item | Alasan |
|---|---|---|
| **P0 - Fix dulu** | F-01, F-02, F-03 | Blocking operasional. Tanpa ini approve pendaftaran & semester broken. |
| **P0 - Multi-unit** | User Permission per `Rumba Unit`, fix `kode_unit`, naikkan series autoname | Wajib sebelum multi-unit live. |
| **P1 - Refactor data** | Hilangkan duplikasi `nama_kota`/`nama_provinsi`/`kode_unit` via `fetch_from`, pindahkan normalisasi ke server | Mengurangi data inconsistency. |
| **P1 - Finance integrity** | Hentikan denormalisasi `status_pembayaran`, pakai `Rumba Tarif Program` + Item resmi, cost center dari Unit | Reporting & rekonsiliasi finance konsisten. |
| **P2 - Domain split** | DocType baru: `Rumba Orang Tua`, `Rumba Anak`, `Rumba Kelas`, `Rumba Enrollment` | Skala jangka panjang, history yang benar. |
| **P2 - Workflow** | Workflow Frappe untuk Pendaftaran (+ pertimbangkan `is_submittable`) | Audit trail & role-based transition. |
| **P3 - Polish** | Naming field Link (`nama_kota` → `kota`), unify status `Tahun Ajaran` | Konsistensi & maintainability. |

---

## 6. Yang Sebaiknya TIDAK Dilakukan Sekaligus

- **Jangan refactor besar sebelum P0 dibetulkan.** Refactor menumpuk di atas bug akan menyamarkan akar masalah.
- **Jangan tambah DocType baru (Kelas, Enrollment, Tarif) sebelum data Pendaftaran/Murid existing dirapikan.** Migrasi data akan jadi mahal.
- **Jangan ganti naming convention DocType yang sudah eksis** (mis. `Rumba Pendaftaran` → `Rumba Enrollment`) dalam langkah yang sama dengan refactor isi. Pisahkan rename dari restruktur.

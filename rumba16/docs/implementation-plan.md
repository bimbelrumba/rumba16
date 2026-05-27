# Implementation Plan - Modul Bimbel Rumba ERPNext v16

Dokumen ini disusun dari:

- `rumba16/docs/current-doctype-inventory.md`
- `rumba16/docs/architecture-review.md`
- konteks kerja proyek di `rumba16/docs/project-state.md`

Prinsip utama:

- Kerjakan perubahan kecil, terverifikasi, dan mudah rollback.
- Jangan mencampur bug fix operasional dengan refactor besar.
- Perubahan DocType yang dilakukan lewat ERPNext UI harus diekspor/ditarik kembali ke repo dan diverifikasi sebelum dianggap baseline.
- Untuk perubahan yang menyentuh data existing, siapkan backup dan uji dulu di development site.

## 1. Perubahan DocType yang Perlu Dilakukan

### Phase 0 - Stabilkan Baseline Operasional

Prioritas ini wajib sebelum restruktur besar.

| DocType / area | Perubahan | Tujuan |
| --- | --- | --- |
| `Rumba Pendaftaran` | Perbaiki pengambilan `kode_unit` dari field Link unit yang benar. | Autoname pendaftaran tidak gagal saat `kode_unit` belum terisi. |
| `Rumba Pendaftaran` | Tambahkan fungsi hook pembayaran yang direferensikan `hooks.py`, atau sementara nonaktifkan hook sampai fungsi siap. | Mencegah error pada submit/cancel `Sales Invoice` dan `Payment Entry`. |
| `Rumba Semester` | Perbaiki Client Script dari target `Semester` menjadi `Rumba Semester`. | Field semester otomatis terisi kembali. |
| `Rumba Unit` | Perbaiki formatter `kepemilikan` agar sesuai opsi metadata. | Tampilan list konsisten dengan data. |
| `Rumba Murid` | Ubah `nama_unit` dari Data menjadi Link, atau buat field Link baru yang aman. | Relasi murid ke unit menjadi valid. |
| `Rumba Murid` | Jadikan `nomor_induk_murid` wajib jika tetap dipakai sebagai naming field. | Mencegah record dengan name kosong/tidak valid. |

### Phase 1 - Rapikan Master Data dan Normalisasi Server-Side

| DocType / area | Perubahan | Tujuan |
| --- | --- | --- |
| `Rumba Provinsi` | Tambahkan normalisasi server-side untuk `kode_provinsi`. | Konsistensi kode saat input UI, import, API, atau patch. |
| `Rumba Kota` | Pastikan `nama_provinsi` memakai `fetch_from` atau diisi server-side dari `kode_provinsi`. | Menghindari mirror field kosong/stale. |
| `Rumba Unit` | Tambahkan logic server-side untuk `kode_unit`, kapasitas, dan mirror wilayah. | Perhitungan tetap berjalan di luar UI. |
| `Rumba Program Belajar` | Pindahkan uppercase/trim `kode_program_belajar` ke controller. | Normalisasi tidak hanya bergantung Client Script. |
| `Rumba Tahun Ajaran` | Pindahkan perhitungan `kode_tahun_ajaran` dan `tanggal_selesai` ke controller. | Tahun ajaran konsisten di semua jalur input. |
| `Rumba Semester` | Pindahkan generasi `kode_semester`, `nama_semester`, dan tanggal semester ke controller. | Menghilangkan ketergantungan pada Client Script yang rapuh. |

### Phase 2 - Perbaiki Model Akademik dan Relasi

Tambahkan DocType baru setelah Phase 0 dan Phase 1 stabil.

| DocType baru | Jenis | Tujuan |
| --- | --- | --- |
| `Rumba Orang Tua Wali` | Master | Menyimpan identitas orang tua/wali dan link ke ERPNext `Customer`. |
| `Rumba Anak` | Master | Menyimpan biodata permanen anak/murid. |
| `Rumba Kelas` atau `Rumba Sesi Belajar` | Master/Transaction ringan | Menyimpan unit, ruangan, hari, jam, program, jenis kelas, tahun ajaran/semester, guru, dan kapasitas. |
| `Rumba Enrollment` | Transaction | Menyimpan status akademik anak per periode: unit, kelas/sesi, program, tahun ajaran, semester, status aktif/cuti/lulus/berhenti. |
| `Rumba Tarif Program` | Master | Mapping program, jenis kelas, periode, item ERPNext, harga, dan akun/cost center bila perlu. |

### Phase 3 - Workflow dan Finance yang Lebih Terkontrol

| Area | Perubahan | Tujuan |
| --- | --- | --- |
| `Rumba Pendaftaran` | Buat Workflow Frappe untuk `Menunggu`, `Disetujui`, `Ditolak`, `Batal`. | Role-based transition dan audit trail. |
| Finance pendaftaran | Gunakan `Rumba Tarif Program` untuk memilih `Item` dan harga invoice. | Mengurangi input manual dan salah item/harga. |
| Unit accounting | Ambil `cost_center` dari `Rumba Unit` saat membuat invoice. | Laporan cabang lebih akurat. |
| Customer orang tua | Hubungkan Customer ke `Rumba Orang Tua Wali`, bukan dibuat berulang per pendaftaran. | Piutang keluarga tidak pecah. |

## 2. Field yang Perlu Ditambah, Diubah, atau Dihapus

### Field yang Perlu Ditambah

| DocType | Field | Type | Catatan |
| --- | --- | --- | --- |
| `Rumba Orang Tua Wali` | `nama_orang_tua_wali` | Data | Wajib. |
| `Rumba Orang Tua Wali` | `nomor_handphone` | Phone/Data | Normalisasi ke format Indonesia server-side. |
| `Rumba Orang Tua Wali` | `alamat_email` | Data / Email | Opsional atau wajib sesuai proses. |
| `Rumba Orang Tua Wali` | `alamat` | Small Text | Alamat keluarga/wali. |
| `Rumba Orang Tua Wali` | `customer` | Link -> Customer | Satu Customer untuk satu wali/keluarga. |
| `Rumba Anak` | `nama_lengkap`, `nama_panggilan`, `tanggal_lahir`, `jenis_kelamin` | Sesuai data existing | Biodata permanen. |
| `Rumba Anak` | `orang_tua_wali` | Link -> Rumba Orang Tua Wali | Relasi anak ke wali utama. |
| `Rumba Anak` | `anak_berkebutuhan_khusus`, `catatan_kebutuhan_khusus` | Check/Select + Small Text | Pindahkan dari pendaftaran. |
| `Rumba Kelas/Sesi Belajar` | `unit`, `ruangan`, `hari`, `jam_belajar`, `program_belajar`, `jenis_kelas`, `tahun_ajaran`, `semester`, `kapasitas` | Link/Select/Int | Basis jadwal dan kapasitas. |
| `Rumba Enrollment` | `anak`, `pendaftaran`, `unit`, `kelas_sesi`, `tahun_ajaran`, `semester`, `program_belajar`, `status_enrollment` | Link/Select | Menggantikan status akademik di `Rumba Murid`. |
| `Rumba Tarif Program` | `program_belajar`, `jenis_kelas`, `tahun_ajaran`, `item`, `rate`, `aktif` | Link/Select/Currency/Check | Sumber tarif invoice. |
| `Rumba Ruangan` | `unit` | Link -> Rumba Unit | Ruangan harus milik unit. |
| `Rumba Ruangan` | `kapasitas`, `status_ruangan` | Int/Select | Untuk validasi kelas/sesi. |

### Field yang Perlu Diubah

| DocType | Field | Perubahan |
| --- | --- | --- |
| `Rumba Murid` | `nama_unit` | Ubah ke Link -> `Rumba Unit`, atau buat field baru `unit` lalu migrasikan data. |
| `Rumba Pendaftaran` | `nama_kota` | Rekomendasi jangka panjang: rename konseptual ke `kota`. Jika data sudah banyak, tunda rename dan perbaiki label/deskripsi dulu. |
| `Rumba Pendaftaran` | `nama_unit` | Rekomendasi jangka panjang: rename konseptual ke `unit`. Jika belum aman, tetap gunakan field lama dan dokumentasikan. |
| `Rumba Pendaftaran` | `status_pendaftaran` | Jadikan `workflow_state`/Workflow sebagai pengendali, atau tetap Select tetapi transisi dikunci server-side. |
| `Rumba Pendaftaran` | `status_pembayaran`, `tanggal_pembayaran` | Tentukan: tetap denormalisasi dengan hook yang benar, atau hitung on-demand dari `Sales Invoice`. Untuk tahap aman, tetap simpan tetapi sinkronisasi harus valid. |
| `Rumba Tahun Ajaran` | `status` dan `nonaktif` | Pilih satu sumber kebenaran. Rekomendasi: pakai `nonaktif` untuk filter master, atau pakai `status` saja. |
| `Rumba Pendaftaran` | autoname series | Naikkan series dari 2 digit ke minimal 4 digit. |

### Field yang Perlu Dihapus atau Didepresiasi

Jangan hapus langsung pada fase awal. Tandai sebagai deprecated dulu, migrasikan data, baru hapus setelah validasi.

| DocType | Field / kelompok | Rekomendasi |
| --- | --- | --- |
| `Rumba Pendaftaran` | Biodata anak yang permanen | Setelah `Rumba Anak` stabil, field ini menjadi snapshot saat pendaftaran atau deprecated. |
| `Rumba Murid` | Biodata anak yang read-only hasil salinan | Setelah `Rumba Anak` dan `Rumba Enrollment` stabil, jadikan fetch/snapshot terbatas atau hapus bertahap. |
| `Rumba Pendaftaran` dan `Rumba Murid` | `senin` sampai `sabtu`, `jam_belajar` | Setelah `Rumba Kelas/Sesi Belajar` stabil, ganti dengan Link ke sesi/kelas. |
| `Rumba Pendaftaran` dan `Rumba Murid` | `kode_unit` mirror | Gunakan Link `unit` dan fetch dari `Rumba Unit`; jangan jadikan sumber kebenaran. |
| `Rumba Unit`, `Rumba Kota` | `nama_kota`, `nama_provinsi` mirror | Pakai `fetch_from` atau pertahankan sebagai read-only derived field; jangan diisi manual. |

## 3. Relasi Link yang Perlu Diperbaiki

| Dari | Field | Ke | Perbaikan |
| --- | --- | --- | --- |
| `Rumba Murid` | `nama_unit` | `Rumba Unit` | Ubah dari Data menjadi Link, idealnya rename konseptual ke `unit`. |
| `Rumba Ruangan` | `unit` | `Rumba Unit` | Tambahkan relasi agar ruangan tidak global. |
| `Rumba Pendaftaran` | `orang_tua_wali` | `Rumba Orang Tua Wali` | Tambahkan setelah DocType wali siap; link ke Customer lewat wali. |
| `Rumba Pendaftaran` | `anak` | `Rumba Anak` | Tambahkan setelah DocType anak siap; pendaftaran menjadi proses, bukan master biodata. |
| `Rumba Pendaftaran` | `kelas_sesi` | `Rumba Kelas/Sesi Belajar` | Ganti pilihan hari/jam manual secara bertahap. |
| `Rumba Enrollment` | `anak` | `Rumba Anak` | Menyimpan history akademik. |
| `Rumba Enrollment` | `kelas_sesi` | `Rumba Kelas/Sesi Belajar` | Menyimpan jadwal aktual yang diikuti. |
| `Rumba Tarif Program` | `item` | `Item` | Invoice memakai item resmi, bukan pilihan manual bebas. |
| `Rumba Unit` | `cost_center`, `warehouse` | ERPNext core | Gunakan saat membuat invoice/stock-related operation. |

## 4. Script yang Perlu Dibuat atau Direvisi

### Server-Side Controller

| File | Perubahan |
| --- | --- |
| `rumba_pendaftaran.py` | Perbaiki `set_kode_unit()` agar membaca `nama_unit`. |
| `rumba_pendaftaran.py` | Tambahkan `sync_status_pembayaran_from_sales_invoice(doc, method=None)` dan `sync_status_pembayaran_from_payment_entry(doc, method=None)` sesuai hook. |
| `rumba_pendaftaran.py` | Pertimbangkan pindahkan pembuatan `Rumba Murid` dari Client Script ke whitelisted server method. |
| `rumba_pendaftaran.py` | Validasi transisi `status_pendaftaran` agar tidak bisa lompat status tanpa syarat. |
| `rumba_unit.py` | Isi/normalisasi `kode_unit`, hitung kapasitas, fetch nama kota/provinsi saat validate. |
| `rumba_program_belajar.py` | Uppercase/trim `kode_program_belajar` saat validate. |
| `rumba_provinsi.py` | Uppercase/trim `kode_provinsi` saat validate. |
| `rumba_tahun_ajaran.py` | Generate `kode_tahun_ajaran` dan `tanggal_selesai` saat validate. |
| `rumba_semester.py` | Generate `kode_semester`, `nama_semester`, tanggal mulai/akhir dari tahun ajaran dan periode. |
| Controller DocType baru | Tambahkan validasi unik dan kapasitas untuk `Rumba Kelas/Sesi Belajar`, serta validasi enrollment tidak melebihi kapasitas. |

### Client Script / JS

| Script | Perubahan |
| --- | --- |
| `Generate Nama Semester` | Ganti target dari `Semester` ke `Rumba Semester`; setelah server-side siap, jadikan hanya UX preview. |
| `Warna Status Unit dan Kepemilikan` | Ganti map `Crowdfunding` menjadi opsi yang benar, termasuk `Partnership`. |
| `Pilihan Kota dan Unit` | Pertahankan filter unit, tetapi pastikan field dan filter memakai nama konseptual yang jelas. |
| `Tombol Buat Murid` | Revisi agar memanggil server method, bukan `frappe.client.insert` langsung. |
| `Tombol Customer Orang Tua` | Revisi agar mencari/menghubungkan `Rumba Orang Tua Wali` dan `Customer` existing sebelum membuat baru. |
| `Tombol Buat Invoice` | Ambil item/rate dari `Rumba Tarif Program`; user cukup konfirmasi, bukan pilih item manual bebas. |

### Hooks dan Fixtures

| File | Perubahan |
| --- | --- |
| `hooks.py` | Pastikan setiap `doc_events` menunjuk fungsi yang benar-benar ada dan idempotent. |
| `hooks.py` | Tambahkan fixture untuk Workflow jika Workflow Pendaftaran dibuat lewat UI. |
| `fixtures/client_script.json` | Export ulang setelah revisi Client Script di dev site. |

## 5. Risiko Migrasi Data

| Risiko | Dampak | Mitigasi |
| --- | --- | --- |
| Mengubah `Rumba Murid.nama_unit` dari Data ke Link | Nilai existing yang bukan nama dokumen `Rumba Unit` bisa gagal validasi. | Audit distinct value dulu; buat field baru `unit`, isi via patch mapping, baru depresiasi `nama_unit`. |
| Menambah `unit` ke `Rumba Ruangan` | Ruangan existing tidak punya unit. | Isi default/manual mapping sebelum field dibuat wajib. |
| Mengubah naming pendaftaran dari 2 digit ke 4 digit | Nomor baru berbeda format dari nomor lama. | Jangan rename data lama; terapkan untuk dokumen baru saja dan dokumentasikan. |
| Membuat `Rumba Anak` dan `Rumba Orang Tua Wali` dari data pendaftaran | Duplikasi orang tua/anak bisa salah merge. | Matching konservatif: anak berdasarkan nama+tanggal lahir+orang tua/HP; wali berdasarkan nomor HP/email yang sudah dinormalisasi. Review manual untuk kandidat duplikat. |
| Membuat `Rumba Enrollment` dari `Rumba Murid` | Data jadwal/program existing mungkin tidak lengkap. | Buat enrollment awal dengan status dan periode dari data terbaik yang tersedia; beri flag `migrated_from_murid`. |
| Mengganti field hari/jam menjadi `kelas_sesi` | Pendaftaran lama tidak otomatis punya sesi. | Fase transisi: field lama tetap ada sebagai snapshot sampai semua data punya sesi. |
| Mengubah status pembayaran menjadi on-demand | Report/list filter yang memakai field lama bisa berubah. | Tahap awal tetap pertahankan field denormalisasi, tetapi sinkronisasi dibuat benar. |
| Workflow Frappe pada pendaftaran existing | Dokumen lama mungkin tidak punya workflow state valid. | Set workflow state awal lewat patch sesuai `status_pendaftaran` existing. |
| Hardcoded Customer Group/Territory | Site yang tidak punya master tersebut akan gagal membuat Customer. | Jadikan setting atau validasi master sebelum tombol dijalankan. |

## 6. Urutan Pengerjaan Paling Aman

1. **Freeze baseline singkat**
   - Pull/rebase branch `dev` dari GitHub.
   - Pastikan dev site, local repo, dan GitHub berada pada baseline yang diketahui.
   - Backup database development sebelum perubahan DocType besar.

2. **Fix P0 tanpa ubah model besar**
   - Fix `set_kode_unit()` di `Rumba Pendaftaran`.
   - Implementasikan atau nonaktifkan hook pembayaran yang menunjuk fungsi tidak ada.
   - Fix target Client Script `Rumba Semester`.
   - Fix map formatter `Rumba Unit`.
   - Export perubahan Client Script/DocType ke repo.

3. **Server-side normalisasi master**
   - Tambahkan validate logic di master kecil: Provinsi, Program Belajar, Tahun Ajaran, Semester, Unit.
   - Biarkan Client Script tetap ada sebagai bantuan UX, tetapi bukan sumber kebenaran utama.
   - Test input via UI dan bench console/API jika tersedia.

4. **Perbaiki relasi paling kecil**
   - Tambah field `unit` Link di `Rumba Murid` bila perubahan langsung `nama_unit` terlalu berisiko.
   - Migrasikan data dari `nama_unit` ke `unit`.
   - Tambah `unit` di `Rumba Ruangan`; isi data existing; baru jadikan wajib jika semua terisi.

5. **Perbaiki proses finance minimum**
   - Pastikan sinkronisasi pembayaran manual dan hook sama-sama idempotent.
   - Validasi approval hanya bisa setelah lunas.
   - Ambil `cost_center` dari Unit saat membuat invoice jika data Unit sudah lengkap.

6. **Tambahkan master baru yang paling independen**
   - Buat `Rumba Orang Tua Wali`.
   - Buat `Rumba Anak`.
   - Migrasi dari pendaftaran/murid secara konservatif, tanpa menghapus field lama.

7. **Tambahkan struktur kelas dan enrollment**
   - Buat `Rumba Kelas/Sesi Belajar`.
   - Buat `Rumba Enrollment`.
   - Buat enrollment awal dari `Rumba Murid`.
   - Mulai arahkan pendaftaran baru ke kelas/sesi, sementara field lama tetap sebagai snapshot.

8. **Tambahkan tarif program**
   - Buat `Rumba Tarif Program`.
   - Revisi tombol invoice agar item dan rate berasal dari tarif.
   - Test finance dari pendaftaran sampai pembayaran.

9. **Aktifkan Workflow Pendaftaran**
   - Buat Workflow Frappe di dev site.
   - Export fixture Workflow.
   - Migrasikan state dokumen lama.
   - Uji role transition.

10. **Depresiasi field lama**
   - Setelah data baru stabil, tandai field lama sebagai read-only/hidden.
   - Hapus hanya setelah ada backup, patch migrasi, dan konfirmasi tidak dipakai report/script.

## 7. Checklist Testing Setelah Perubahan

### Baseline dan Repo

- `git status` bersih sebelum mulai batch perubahan.
- Setelah perubahan UI ERPNext, export fixtures/DocType dan pastikan file berubah sesuai ekspektasi.
- `git diff` dicek manual sebelum commit.
- Tidak ada hook di `hooks.py` yang menunjuk fungsi tidak ada.

### Master Data

- Buat dan edit `Rumba Provinsi`; kode tersimpan uppercase/trim.
- Buat dan edit `Rumba Kota`; provinsi terhubung dan nama provinsi tampil benar.
- Buat dan edit `Rumba Unit`; kode unit, kota/provinsi, kapasitas sesi, dan kapasitas murid terisi benar.
- Buat dan edit `Rumba Program Belajar`; kode program uppercase/trim.
- Buat `Rumba Tahun Ajaran`; tanggal selesai dan kode tahun ajaran terisi benar.
- Buat `Rumba Semester`; kode, nama, tanggal mulai, dan tanggal akhir semester terisi benar.
- Buat `Rumba Ruangan`; ruangan terikat ke unit dan kapasitas valid.

### Pendaftaran

- Buat pendaftaran baru dari UI dengan kota, unit, program, tahun ajaran, dan data wali lengkap.
- Nomor pendaftaran terbentuk dari unit dan periode yang benar.
- Validasi duplikasi pendaftaran tetap berjalan.
- Nomor HP wali dinormalisasi.
- Status `Disetujui` ditolak jika pembayaran belum `Lunas`.
- Setelah invoice lunas dan sinkronisasi, status bisa menjadi `Disetujui`.
- Alasan penolakan/batal wajib/terisi sesuai aturan jika status `Ditolak` atau `Batal` diterapkan.

### Customer dan Finance

- Tombol `Buat Customer` tidak membuat Customer duplikat untuk wali yang sama.
- Customer terhubung ke `Rumba Orang Tua Wali` jika DocType tersebut sudah aktif.
- Tombol `Buat Invoice` mengambil `Item` dan harga dari `Rumba Tarif Program`.
- Invoice memakai Company valid dan, jika tersedia, cost center dari `Rumba Unit`.
- `Sinkronkan Pembayaran` menghasilkan status: `Menunggu Pembayaran`, `Dibayar Sebagian`, `Lunas`, dan `Dibatalkan` sesuai kondisi invoice.
- Submit/cancel `Sales Invoice` dan submit/cancel `Payment Entry` tidak error.

### Murid, Anak, dan Enrollment

- `Buat Murid` hanya bisa dilakukan dari pendaftaran yang valid dan disetujui.
- Tidak bisa membuat lebih dari satu murid/enrollment dari pendaftaran yang sama.
- `Rumba Murid.unit` atau field Link unit baru terisi benar.
- `Rumba Anak` tidak terduplikasi untuk anak yang sama.
- `Rumba Enrollment` tercipta dengan tahun ajaran, semester, program, kelas/sesi, dan status yang benar.
- Perubahan enrollment baru tidak merusak biodata anak.

### Kelas/Sesi dan Kapasitas

- Sesi hanya bisa dibuat untuk unit dan ruangan yang valid.
- Kapasitas sesi tidak boleh melebihi kapasitas ruangan/unit.
- Enrollment tidak bisa melebihi kapasitas sesi.
- Daftar murid per sesi dapat ditampilkan/filter.

### Workflow dan Permission

- Role yang benar bisa melakukan transisi `Menunggu` -> `Disetujui`, `Ditolak`, atau `Batal`.
- Role yang tidak berwenang tidak bisa mengubah status approval.
- Workflow state dokumen lama valid setelah migrasi.
- User cabang/unit hanya melihat atau memproses data unit yang sesuai jika User Permission diterapkan.

### Regression

- List view `Rumba Unit`, `Rumba Tahun Ajaran`, dan `Rumba Murid` tetap menampilkan indikator warna.
- Import/API insert tetap menjalankan normalisasi server-side.
- Report atau filter yang memakai field lama masih berjalan selama fase transisi.
- Tidak ada error browser console pada form Pendaftaran, Unit, Tahun Ajaran, Semester, dan Murid.

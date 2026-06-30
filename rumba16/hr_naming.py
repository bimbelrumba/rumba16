import frappe
from frappe.model.naming import make_autoname

PENDIDIK = {"Tutor", "Lead Tutor"}
MG_MAP = {"YRKI": "01", "Franchise": "02", "Partnership": "03"}

# Pemetaan Designation -> kategori_karyawan untuk pengisian otomatis.
# Designation unit dipetakan 1:1; seluruh jabatan Pusat -> "Staf Pusat".
DESIG_TO_KATEGORI = {
    "Tutor": "Tutor",
    "Lead Tutor": "Lead Tutor",
    "Kepala Unit": "Kepala Unit",
    "Admin Unit": "Admin Unit",
    "Staf Pendukung": "Staf Pendukung",
}
PUSAT_DESIG = {
    "Manajer Operasional",
    "Koordinator Personalia & Umum",
    "Koordinator Kurikulum & Akademik",
    "Koordinator Keuangan",
    "Koordinator Teknologi & Sistem",
    "Koordinator Pengembangan Usaha",
    "Staf Keuangan",
    "Staf Pemasaran & Pengembangan Usaha",
}

def set_employee_kategori(doc, method=None):
    """Isi kategori_karyawan dari designation bila kosong.

    Dipasang di doc_events Employee `before_insert`, yang berjalan SEBELUM
    `autoname`, sehingga penomoran 10-angka (employee_autoname) tetap jalan
    walau Employee dibuat dari Employee Onboarding (kategori tidak ikut
    otomatis dari onboarding). Tidak menimpa nilai yang sudah diisi manual.
    """
    if doc.kategori_karyawan or not doc.designation:
        return
    kategori = DESIG_TO_KATEGORI.get(doc.designation)
    if not kategori and doc.designation in PUSAT_DESIG:
        kategori = "Staf Pusat"
    if kategori:
        doc.kategori_karyawan = kategori

def employee_autoname(doc, method=None):
    # Jaring pengaman: bila kategori masih kosong namun designation bisa
    # dipetakan, isi di sini sebelum guard (mis. jalur pembuatan yang tak
    # memicu before_insert).
    if not doc.kategori_karyawan and doc.designation:
        set_employee_kategori(doc)
    if not doc.date_of_joining or not doc.kategori_karyawan:
        frappe.throw("date_of_joining dan kategori_karyawan wajib diisi sebelum simpan Employee.")
    s = str(doc.date_of_joining)              # 'YYYY-MM-DD'
    yy, mm = s[2:4], s[5:7]
    et = "01" if doc.kategori_karyawan in PENDIDIK else "02"
    if doc.kategori_karyawan == "Staf Pusat" or not doc.rumba_unit:
        mg = "01"
    else:
        kep = frappe.db.get_value("Rumba Unit", doc.rumba_unit, "kepemilikan")
        mg = MG_MAP.get(kep, "01")
    doc.name = make_autoname(yy + mm + et + mg + ".##")
    doc.employee = doc.name   # samakan field employee dgn name (HRMS set employee=name)

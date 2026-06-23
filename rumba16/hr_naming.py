import frappe
from frappe.model.naming import make_autoname

PENDIDIK = {"Tutor", "Lead Tutor"}
MG_MAP = {"YRKI": "01", "Franchise": "02", "Partnership": "03"}

def employee_autoname(doc, method=None):
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

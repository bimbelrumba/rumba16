# apps/rumba16/rumba16/rumba16/hr_snapshot.py
import frappe
from frappe.utils import getdate, get_first_day, get_last_day, now_datetime, add_months, today

PENDIDIK = ("Tutor", "Lead Tutor")

@frappe.whitelist()
def generate_hr_snapshot(bulan=None):
    """Snapshot SDM bulanan org-wide, idempoten per bulan.
    bulan = tanggal apa pun dalam bulan target; kosong = bulan lalu (dipakai scheduler)."""
    if not (set(frappe.get_roles()) & {"Rumba Personalia", "System Manager"}):
        frappe.throw("Anda tidak berhak membuat snapshot SDM.")

    first = get_first_day(getdate(bulan) if bulan else add_months(today(), -1))
    last = get_last_day(first)

    def count_active(extra="", params=None):
        p = {"last": last}; p.update(params or {})
        return frappe.db.sql(
            """SELECT COUNT(*) FROM `tabEmployee`
               WHERE date_of_joining <= %(last)s
                 AND (relieving_date IS NULL OR relieving_date > %(last)s) """ + extra, p)[0][0]

    total = count_active()
    pendidik = count_active("AND kategori_karyawan IN %(kat)s", {"kat": PENDIDIK})
    masuk = frappe.db.count("Employee", {"date_of_joining": ["between", [first, last]]})
    keluar = frappe.db.count("Employee", {"relieving_date": ["between", [first, last]]})

    name = f"SDM-SNAP-{first}"
    doc = (frappe.get_doc("Rumba Snapshot SDM", name)
           if frappe.db.exists("Rumba Snapshot SDM", name)
           else frappe.new_doc("Rumba Snapshot SDM"))
    doc.bulan = first
    doc.tanggal_ambil = now_datetime()
    doc.total_karyawan_aktif = total
    doc.jumlah_pendidik = pendidik
    doc.jumlah_non_pendidik = total - pendidik
    doc.karyawan_masuk = masuk
    doc.karyawan_keluar = keluar
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return doc.name

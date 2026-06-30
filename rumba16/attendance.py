import frappe
from frappe import _
from frappe.utils import getdate, get_last_day


ALLOWED_ROLES = {"Rumba Personalia", "Rumba Akademik", "System Manager"}


@frappe.whitelist()
def generate_pendidik_attendance(bulan, unit=None):
    """Buat Attendance 'Present' untuk Pendidik dari sesi Terlaksana.

    bulan : 'YYYY-MM'
    unit  : opsional; bila diisi, hanya kelas di unit itu.
    Satu Attendance per (pengajar, tanggal) yang punya >=1 sesi Terlaksana.
    Sesi 'Diganti' dikreditkan ke guru_pengganti. Idempoten. Tidak menyentuh payroll.
    """
    if not (ALLOWED_ROLES & set(frappe.get_roles())):
        frappe.throw(_("Hanya Personalia/Akademik yang boleh menjalankan proses ini."))
    if not bulan:
        frappe.throw(_("Bulan (YYYY-MM) wajib diisi."))

    start = getdate(bulan + "-01")
    end = get_last_day(start)

    filters = {
        "status_sesi": ["in", ["Terlaksana", "Diganti"]],
        "tanggal_sesi": ["between", [start, end]],
    }
    if unit:
        kelas = frappe.get_all("Rumba Kelas", filters={"nama_unit": unit}, pluck="name")
        if not kelas:
            return {"bulan": bulan, "info": "Tidak ada kelas untuk unit ini.",
                    "created": [], "skipped": []}
        filters["kelas"] = ["in", kelas]

    sesi = frappe.get_all(
        "Rumba Sesi Kelas", filters=filters,
        fields=["status_sesi", "guru", "guru_pengganti", "tanggal_sesi"],
    )

    pairs = set()
    for s in sesi:
        pengajar = s.guru_pengganti if s.status_sesi == "Diganti" else s.guru
        if pengajar and s.tanggal_sesi:
            pairs.add((pengajar, str(s.tanggal_sesi)))

    created, skipped = [], []
    for emp, tgl in sorted(pairs):
        if frappe.db.exists("Attendance",
                            {"employee": emp, "attendance_date": tgl, "docstatus": ["<", 2]}):
            skipped.append({"employee": emp, "date": tgl, "alasan": "sudah ada"})
            continue
        doc = frappe.get_doc({
            "doctype": "Attendance",
            "employee": emp,
            "attendance_date": tgl,
            "status": "Present",
            "company": frappe.db.get_value("Employee", emp, "company"),
        })
        doc.insert()
        doc.submit()
        created.append({"employee": emp, "date": tgl, "attendance": doc.name})

    frappe.db.commit()
    return {"bulan": bulan, "created": created, "skipped": skipped}

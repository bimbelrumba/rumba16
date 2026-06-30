import frappe
from frappe import _
from frappe.utils import getdate, get_last_day


ALLOWED_ROLES = {"Rumba Finance", "Rumba Personalia", "System Manager"}


@frappe.whitelist()
def generate_honor_mengajar(unit, bulan):
    """Buat draft Additional Salary 'Honor Mengajar' per tutor untuk satu unit & bulan.

    unit  : nama Rumba Unit
    bulan : 'YYYY-MM'
    Hanya menghitung sesi terverifikasi (workflow_state='Disetujui').
    Sesi 'Diganti' dikreditkan ke guru_pengganti. Honor = jumlah pertemuan x tarif per tutor.
    Membuat DRAFT (docstatus 0) — verifikasi & submit oleh Finance.
    """
    if not (ALLOWED_ROLES & set(frappe.get_roles())):
        frappe.throw(_("Hanya Finance/Personalia yang boleh menjalankan proses ini."))
    if not unit or not bulan:
        frappe.throw(_("Unit dan bulan (YYYY-MM) wajib diisi."))

    start = getdate(bulan + "-01")
    end = get_last_day(start)

    kelas_list = frappe.get_all("Rumba Kelas", filters={"nama_unit": unit}, pluck="name")
    if not kelas_list:
        return {"unit": unit, "bulan": bulan, "info": "Tidak ada kelas untuk unit ini.",
                "created": [], "skipped": []}

    sesi = frappe.get_all(
        "Rumba Sesi Kelas",
        filters={
            "kelas": ["in", kelas_list],
            "workflow_state": "Disetujui",
            "status_sesi": ["in", ["Terlaksana", "Diganti"]],
            "tanggal_sesi": ["between", [start, end]],
        },
        fields=["name", "status_sesi", "guru", "guru_pengganti"],
    )

    # jumlah pertemuan per pengajar (Diganti -> guru_pengganti)
    counts = {}
    for s in sesi:
        pengajar = s.guru_pengganti if s.status_sesi == "Diganti" else s.guru
        if pengajar:
            counts[pengajar] = counts.get(pengajar, 0) + 1

    created, skipped = [], []
    for emp, jml in counts.items():
        tarif = frappe.db.get_value("Employee", emp, "tarif_honor_per_pertemuan") or 0
        if not tarif:
            skipped.append({"employee": emp, "alasan": "tarif honor kosong"})
            continue
        # idempoten: lewati bila sudah ada (non-cancel) utk emp + bulan
        existing = frappe.db.exists("Additional Salary", {
            "employee": emp,
            "salary_component": "Honor Mengajar",
            "payroll_date": end,
            "docstatus": ["<", 2],
        })
        if existing:
            skipped.append({"employee": emp, "alasan": "sudah ada: " + existing})
            continue
        doc = frappe.get_doc({
            "doctype": "Additional Salary",
            "employee": emp,
            "salary_component": "Honor Mengajar",
            "amount": jml * tarif,
            "payroll_date": end,
            "company": frappe.db.get_value("Employee", emp, "company"),
            "overwrite_salary_structure_amount": 0,
        })
        doc.insert()  # DRAFT
        created.append({"employee": emp, "pertemuan": jml, "tarif": tarif,
                        "amount": jml * tarif, "additional_salary": doc.name})

    frappe.db.commit()
    return {"unit": unit, "bulan": bulan, "created": created, "skipped": skipped}

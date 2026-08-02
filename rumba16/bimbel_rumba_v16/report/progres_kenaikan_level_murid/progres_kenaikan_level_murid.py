# Copyright (c) 2026, Yayasan Rumba Kita Indonesia and contributors
import frappe
from frappe import _


def execute(filters=None):
    filters = filters or {}
    return get_columns(), get_data(filters)


def get_columns():
    return [
        {"label": _("Nama Murid"), "fieldname": "nama_murid", "fieldtype": "Data", "width": 180},
        {"label": _("Rombel"), "fieldname": "rombel", "fieldtype": "Link", "options": "Rumba Kelas", "width": 150},
        {"label": _("Program"), "fieldname": "program", "fieldtype": "Data", "width": 90},
        {"label": _("Level Saat Ini"), "fieldname": "level_saat_ini", "fieldtype": "Data", "width": 100},
        {"label": _("Level Lulus"), "fieldname": "level_lulus", "fieldtype": "Int", "width": 90},
        {"label": _("Ujian Terakhir"), "fieldname": "ujian_tgl", "fieldtype": "Date", "width": 110},
        {"label": _("Level Diuji"), "fieldname": "ujian_level", "fieldtype": "Data", "width": 90},
        {"label": _("Hasil Ujian"), "fieldname": "ujian_hasil", "fieldtype": "Data", "width": 100},
        {"label": _("Status Murid"), "fieldname": "status_murid", "fieldtype": "Data", "width": 100},
        {"label": _("Tanggal Keluar"), "fieldname": "tanggal_keluar", "fieldtype": "Date", "width": 110},
        {"label": _("Sertifikat"), "fieldname": "sertifikat", "fieldtype": "Data", "width": 90},
    ]


def _scope(params):
    """Batasi ke murid milik Tutor (roster rombel wali_kelas=dia).

    System Manager/Administrator → semua (untuk uji). Tutor tanpa Employee →
    tak lihat apa pun (aman-gagal), konsisten scoping per-guru permissions.py.
    """
    roles = set(frappe.get_roles(frappe.session.user))
    if "System Manager" in roles or frappe.session.user == "Administrator":
        return "1=1"
    emp = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
    if not emp:
        return "1=0"
    params["emp"] = emp
    return "k.wali_kelas = %(emp)s"


def get_data(filters):
    params = {}
    cond = _scope(params)

    prog_cond = ""
    if filters.get("program"):
        prog_cond = "AND m.program_belajar = %(program)s"
        params["program"] = filters["program"]

    return frappe.db.sql(
        f"""
        SELECT
            m.nama_lengkap    AS nama_murid,
            k.name            AS rombel,
            m.program_belajar AS program,
            m.level_saat_ini  AS level_saat_ini,
            m.status_murid    AS status_murid,
            ak.tanggal_keluar AS tanggal_keluar,
            (SELECT COUNT(DISTINCT u.level_diuji) FROM `tabRumba Ujian Kenaikan Level` u
               WHERE u.murid = m.name AND u.status_ujian = 'Final' AND u.hasil = 'Lulus') AS level_lulus,
            (SELECT ut.tanggal_ujian FROM `tabRumba Ujian Kenaikan Level` ut
               WHERE ut.murid = m.name AND ut.status_ujian = 'Final'
               ORDER BY ut.tanggal_ujian DESC LIMIT 1) AS ujian_tgl,
            (SELECT ul.level_diuji FROM `tabRumba Ujian Kenaikan Level` ul
               WHERE ul.murid = m.name AND ul.status_ujian = 'Final'
               ORDER BY ul.tanggal_ujian DESC LIMIT 1) AS ujian_level,
            (SELECT uh.hasil FROM `tabRumba Ujian Kenaikan Level` uh
               WHERE uh.murid = m.name AND uh.status_ujian = 'Final'
               ORDER BY uh.tanggal_ujian DESC LIMIT 1) AS ujian_hasil,
            (SELECT 'Terbit' FROM `tabRumba Sertifikat` s
               WHERE s.murid = m.name AND s.status = 'Diterbitkan' LIMIT 1) AS sertifikat
        FROM `tabRumba Anggota Kelas` ak
        INNER JOIN `tabRumba Kelas` k ON k.name = ak.parent AND ak.parenttype = 'Rumba Kelas'
        INNER JOIN `tabRumba Murid` m ON m.name = ak.murid
        WHERE {cond} {prog_cond}
        ORDER BY m.status_murid, m.nama_lengkap
        """,
        params,
        as_dict=True,
    )

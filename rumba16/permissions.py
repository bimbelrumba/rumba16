import frappe

UNIT_ALLOW = "Rumba Unit"


def _user_units(user):
    """Daftar Rumba Unit yang membatasi user (kosong = tak dibatasi / pusat)."""
    return frappe.get_all(
        "User Permission",
        filters={"user": user, "allow": UNIT_ALLOW},
        pluck="for_value",
    )


def mutasi_query_conditions(user=None):
    """permission_query_conditions untuk Rumba Mutasi.

    Tampilkan baris bila unit_asal ATAU unit_tujuan termasuk unit user.
    Pusat (tanpa User Permission unit) melihat semua.
    """
    user = user or frappe.session.user
    if user == "Administrator":
        return ""
    units = _user_units(user)
    if not units:
        return ""
    in_list = ", ".join(frappe.db.escape(u) for u in units)
    return (
        "(`tabRumba Mutasi`.`unit_asal` in ({0}) "
        "or `tabRumba Mutasi`.`unit_tujuan` in ({0}))".format(in_list)
    )


def mutasi_has_permission(doc, user=None, permission_type=None):
    """Akses dokumen tunggal Rumba Mutasi: izinkan bila salah satu unit cocok."""
    user = user or frappe.session.user
    if user == "Administrator":
        return True
    units = _user_units(user)
    if not units:
        return True
    return (doc.get("unit_asal") in units) or (doc.get("unit_tujuan") in units)


# ---------------------------------------------------------------------------
# Scoping per-guru untuk role Rumba Tutor (ERP-PERM-006, Jul 2026)
#
# Tutor murni (hanya ber-role Rumba Tutor, tanpa role Rumba lain yang lebih
# luas) hanya boleh melihat:
#   - Rumba Kelas      : kelas yang wali_kelas = Employee miliknya
#   - Rumba Sesi Kelas : sesi di mana ia guru ATAU guru_pengganti
#   - Rumba BKM Entry  : entri di mana ia guru ATAU paraf_guru
#
# Kondisi ini digabung (AND) oleh Frappe dengan scoping unit via
# User Permission Rumba Unit — jadi tetap terbatas di unitnya juga.
# Role lain (ARU/Kepala Unit/pusat) tidak terpengaruh.
# ---------------------------------------------------------------------------

TUTOR_ROLE = "Rumba Tutor"

# Role yang membebaskan user dari pembatasan per-guru (lihat ERP-ROLE-001):
TUTOR_EXEMPT_ROLES = {
    "System Manager",
    "Rumba Admin Unit",
    "Rumba Kepala Unit",
    "Rumba Akademik",
    "Rumba Founder",
    "Rumba Finance",
    "Rumba Personalia",
    "Rumba Bisnis",
}

# Sentinel: tutor murni yang belum tertaut Employee tidak melihat apa pun
# (aman-gagal; blok "Sesi Saya Hari Ini" sudah menampilkan pesan tuntunan).
_TANPA_EMPLOYEE = "__TUTOR_TANPA_EMPLOYEE__"


def _tutor_employee(user):
    """Kembalikan name Employee bila user adalah tutor murni; selain itu None.

    None = user TIDAK dibatasi per-guru (bukan tutor, atau punya role lebih luas).
    """
    if user == "Administrator":
        return None
    roles = set(frappe.get_roles(user))
    if TUTOR_ROLE not in roles or roles & TUTOR_EXEMPT_ROLES:
        return None
    return (
        frappe.db.get_value("Employee", {"user_id": user}, "name")
        or _TANPA_EMPLOYEE
    )


def _kondisi_satu_field(doctype, field, emp):
    return "`tab{0}`.`{1}` = {2}".format(doctype, field, frappe.db.escape(emp))


def _kondisi_dua_field(doctype, field1, field2, emp):
    e = frappe.db.escape(emp)
    return "(`tab{0}`.`{1}` = {2} or `tab{0}`.`{3}` = {2})".format(
        doctype, field1, e, field2
    )


def kelas_query_conditions(user=None):
    """Rumba Kelas: tutor murni hanya melihat kelas yang diampunya."""
    emp = _tutor_employee(user or frappe.session.user)
    if not emp:
        return ""
    return _kondisi_satu_field("Rumba Kelas", "wali_kelas", emp)


def kelas_has_permission(doc, user=None, permission_type=None):
    emp = _tutor_employee(user or frappe.session.user)
    if not emp:
        return True
    if doc.get("__islocal") or not doc.get("name"):
        return True
    return doc.get("wali_kelas") == emp


def sesi_query_conditions(user=None):
    """Rumba Sesi Kelas: tutor murni hanya melihat sesi miliknya
    (sebagai guru atau guru pengganti)."""
    emp = _tutor_employee(user or frappe.session.user)
    if not emp:
        return ""
    return _kondisi_dua_field("Rumba Sesi Kelas", "guru", "guru_pengganti", emp)


def sesi_has_permission(doc, user=None, permission_type=None):
    emp = _tutor_employee(user or frappe.session.user)
    if not emp:
        return True
    if doc.get("__islocal") or not doc.get("name"):
        return True
    return emp in (doc.get("guru"), doc.get("guru_pengganti"))


def bkm_query_conditions(user=None):
    """Rumba BKM Entry: tutor murni hanya melihat entri BKM miliknya."""
    emp = _tutor_employee(user or frappe.session.user)
    if not emp:
        return ""
    return _kondisi_dua_field("Rumba BKM Entry", "guru", "paraf_guru", emp)


def bkm_has_permission(doc, user=None, permission_type=None):
    emp = _tutor_employee(user or frappe.session.user)
    if not emp:
        return True
    if doc.get("__islocal") or not doc.get("name"):
        return True
    return emp in (doc.get("guru"), doc.get("paraf_guru"))

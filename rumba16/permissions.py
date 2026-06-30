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

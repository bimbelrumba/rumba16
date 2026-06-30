import frappe

# Halaman redirect-only: tidak boleh di-cache agar selalu memakai role pengguna saat ini.
no_cache = 1

# Role unit yang mendarat langsung di workspace "Admin Unit" (quick links).
UNIT_ROLES = {"Rumba Admin Unit", "Rumba Kepala Unit"}


def get_context(context):
    """Arahkan pengguna ke tujuan yang sesuai dengan jenis akun & role-nya.

    - Belum login        -> /login
    - Akun portal ortu   -> /me (Website User, tidak punya akses desk)
    - Admin/Kepala Unit  -> /app/admin-unit (quick links unit)
    - Role lain (desk)   -> /app/rumba (landing bersama RUMBA)
    """
    user = frappe.session.user

    if not user or user == "Guest":
        target = "/login"
    elif frappe.db.get_value("User", user, "user_type") == "Website User":
        # Akun orang tua/portal: jangan dilempar ke desk. Sesuaikan bila ada
        # halaman portal khusus RUMBA.
        target = "/me"
    else:
        roles = set(frappe.get_roles())
        target = "/app/admin-unit" if (roles & UNIT_ROLES) else "/app/rumba"

    frappe.local.flags.redirect_location = target
    raise frappe.Redirect

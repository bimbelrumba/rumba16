import frappe

# Halaman redirect-only: tidak boleh di-cache agar selalu memakai role pengguna saat ini.
no_cache = 1

# Role unit yang mendarat langsung di workspace "Admin Unit" (quick links).
UNIT_ROLES = {"Rumba Admin Unit", "Rumba Kepala Unit"}

# BARU: role pengajar yang mendarat di workspace "Tutor" (sesi & presensi harian).
TUTOR_ROLES = {"Rumba Tutor", "Rumba Lead Tutor"}


def get_context(context):
    """Arahkan pengguna ke tujuan yang sesuai dengan jenis akun & role-nya.

    - Belum login        -> /login
    - Akun portal ortu   -> /me (Website User, tidak punya akses desk)
    - Admin/Kepala Unit  -> /app/admin-unit (quick links unit)
    - Tutor/Lead Tutor   -> /app/tutor (sesi saya & presensi)
    - Role lain (desk)   -> /app/rumba (landing bersama RUMBA)
    """
    user = frappe.session.user

    if not user or user == "Guest":
        target = "/login"
    elif frappe.db.get_value("User", user, "user_type") == "Website User":
        # Akun orang tua/portal: jangan dilempar ke desk.
        target = "/me"
    else:
        roles = set(frappe.get_roles())
        if roles & UNIT_ROLES:                 # BARU: blok if/elif ini
            target = "/app/admin-unit"         # menggantikan 1 baris lama:
        elif roles & TUTOR_ROLES:              # target = "/app/admin-unit" if (roles & UNIT_ROLES) else "/app/rumba"
            target = "/app/tutor"
        elif "Rumba Personalia" in roles:
            target = "/app/sdm"
        elif "Rumba Finance" in roles:
            target = "/app/keuangan-(spp)"
        elif "Rumba Bisnis" in roles:
            target = "/app/crm-&-pendaftaran"
        elif "Rumba Akademik" in roles:
            target = "/app/akademik"
        else:
            target = "/app/rumba"             # Founder & sisanya

    frappe.local.flags.redirect_location = target
    raise frappe.Redirect

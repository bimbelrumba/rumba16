# rumba16/rumba16/maintenance.py
#
# Perawatan otomatis pasca-`bench migrate`.
# Didaftarkan lewat hook `after_migrate` di hooks.py.

import frappe

# Modul milik app RUMBA. Dashboard dengan module ini TIDAK akan dihapus.
# Sesuaikan bila nama modul app berbeda (cek: bench --site <site> console →
# frappe.get_all("Module Def", {"app_name": "rumba16"}, pluck="name")).
RUMBA_MODULE = "Bimbel Rumba v16"


def remove_unused_standard_dashboards():
    """Hapus Dashboard bawaan ERPNext/HRMS yang tidak dipakai RUMBA.

    Dashboard bawaan (is_standard=1) di-impor ulang setiap `bench migrate`
    dan membebani boot desk: get_bootinfo -> get_allowed_dashboards ->
    get_permitted_cards/charts -> has_permission() untuk TIAP card/chart
    yang tertaut. Dengan puluhan dokumen, akumulasinya bisa menembus
    timeout gunicorn (120 dtk) dan memicu 504 untuk SEMUA user.

    RUMBA tidak memakai dashboard bawaan tsb (memakai blok Number Card di
    workspace sendiri), jadi dihapus otomatis setiap selesai migrate.

    Aman: dashboard buatan sendiri (is_standard=0) dan dashboard milik
    modul RUMBA (RUMBA_MODULE) TIDAK disentuh. Number Card / Dashboard
    Chart-nya sendiri tidak dihapus — hanya link ke dashboard yang hilang,
    sehingga tidak lagi dipindai saat boot.
    """
    try:
        targets = frappe.get_all(
            "Dashboard",
            filters={"is_standard": 1},
            fields=["name", "module"],
        )
    except Exception:
        # DocType belum tersedia / DB belum siap. Jangan ganggu migrate.
        return

    removed = []
    for d in targets:
        if (d.module or "") == RUMBA_MODULE:
            continue
        try:
            _delete(d.name)
            removed.append(d.name)
        except Exception:
            # Guard dokumen standar bisa menolak hapus → turunkan flag lalu hapus.
            try:
                frappe.db.set_value(
                    "Dashboard", d.name, "is_standard", 0, update_modified=False
                )
                _delete(d.name)
                removed.append(d.name)
            except Exception as e:  # noqa: BLE001
                frappe.logger("rumba16").warning(
                    f"after_migrate: gagal hapus Dashboard {d.name}: {e}"
                )

    if removed:
        frappe.db.commit()
        frappe.clear_cache()
        frappe.logger("rumba16").info(
            f"after_migrate: {len(removed)} Dashboard bawaan dihapus -> {removed}"
        )


def _delete(name):
    frappe.delete_doc(
        "Dashboard",
        name,
        force=1,
        ignore_permissions=True,
        delete_permanently=True,
    )

# ── Sembunyikan workspace bawaan yang tak dipakai RUMBA dari /desk ──────────────
# Modul bisnis/setup bawaan ERPNext/HRMS/Frappe yang tidak relevan operasional
# Bimbel RUMBA. Accounting (Invoicing, Financial Reports), Stock, Selling, dan
# paket Frappe HR/Payroll SENGAJA dibiarkan tampil (lihat ERP-WS-003 §2.2).
HIDDEN_STANDARD_WORKSPACES = [
    "Buying",
    "Assets",
    "Manufacturing",
    "Subcontracting",
    "Quality",
    "Projects",
    "Support",
    "CRM",
    "Build",
    "Welcome Workspace",
    "Home",
    "Users",
    "Integrations",
    "ERPNext Settings",
    "Website",
]


def hide_unused_standard_workspaces():
    """Set is_hidden=1 pada workspace bawaan yang tak dipakai RUMBA.

    Dipanggil dari after_migrate: `bench migrate` mengimpor ulang definisi
    Workspace bawaan (is_hidden=0), jadi kita set ulang di akhir migrate.
    Pola sama dengan remove_unused_standard_dashboards. Idempotent.
    Memakai db.set_value (bukan doc.save) agar melewati validasi — record
    "Welcome Workspace" bawaan punya field `type` kosong yang memicu
    MandatoryError bila disimpan lewat ORM biasa.
    """
    changed = 0
    for name in HIDDEN_STANDARD_WORKSPACES:
        if not frappe.db.exists("Workspace", name):
            continue
        values = {}
        if not frappe.db.get_value("Workspace", name, "is_hidden"):
            values["is_hidden"] = 1
        # rapikan field wajib yang kosong pada Welcome Workspace bawaan
        if not frappe.db.get_value("Workspace", name, "type"):
            values["type"] = "Workspace"
        if values:
            frappe.db.set_value("Workspace", name, values)
            changed += 1
    if changed:
        frappe.clear_cache()
    frappe.logger().info(
        f"[rumba16] hide_unused_standard_workspaces: {changed} workspace disembunyikan"
    )


# ── Tambahan (4 Agu 2026): sembunyikan bawaan tersisa + landing ke RUMBA ────────
# Memperbarui ERP-WS-003 §2.2: hanya Payroll & Invoicing bawaan yang dibiarkan
# tampil; sisanya disembunyikan. Plus jadikan RUMBA halaman depan /app.
EXTRA_HIDDEN_WORKSPACES = [
    "HR Setup",
    "Tenure",
    "Recruitment",
    "Shift & Attendance",
    "Leaves",
    "Financial Reports",
    "Selling",
    "Expenses",
    "Stock",
    "Performance",
    "Tax & Benefits",
]

LANDING_WORKSPACE = "RUMBA"
LANDING_SEQUENCE_ID = -1


def hide_extra_standard_workspaces():
    """Sembunyikan workspace bawaan tersisa (Payroll & Invoicing dibiarkan tampil)."""
    changed = 0
    for name in EXTRA_HIDDEN_WORKSPACES:
        if not frappe.db.exists("Workspace", name):
            continue
        if not frappe.db.get_value("Workspace", name, "is_hidden"):
            frappe.db.set_value("Workspace", name, "is_hidden", 1)
            changed += 1
    if changed:
        frappe.clear_cache()
    frappe.logger().info(
        f"[rumba16] hide_extra_standard_workspaces: {changed} workspace disembunyikan"
    )


def set_default_landing_workspace():
    """Jadikan RUMBA workspace pendaratan /app (sequence_id terkecil & unik)."""
    if not frappe.db.exists("Workspace", LANDING_WORKSPACE):
        return
    if frappe.db.get_value("Workspace", LANDING_WORKSPACE, "sequence_id") != LANDING_SEQUENCE_ID:
        frappe.db.set_value("Workspace", LANDING_WORKSPACE, "sequence_id", LANDING_SEQUENCE_ID)
        frappe.clear_cache()
    frappe.logger().info(
        f"[rumba16] set_default_landing_workspace: {LANDING_WORKSPACE} sequence_id={LANDING_SEQUENCE_ID}"
    )

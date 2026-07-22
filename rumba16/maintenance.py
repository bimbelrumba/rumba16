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

# Copyright (c) 2026, Yayasan Rumba Kita Indonesia and contributors
# ERP-LIFE-001b / ERP-KES-001 v0.2 — Migrasi sekali-jalan (idempoten).
#
# TARUH DI SERVER:
#   apps/rumba16/rumba16/patches/v0_2/migrasi_status_murid_belum_mulai.py
# DAFTARKAN di apps/rumba16/rumba16/patches.txt (bagian [post_model_sync]):
#   rumba16.patches.v0_2.migrasi_status_murid_belum_mulai
# Jalan otomatis saat `bench --site <site> migrate` (dev, lalu produksi).
#
# Tujuan:
#   1. Isi Rumba Murid.tanggal_mulai_belajar_aktual = MIN(tanggal_sesi) dari
#      presensi Hadir (sesi Disetujui, status_sesi != 'Batal') bila masih kosong.
#      Berlaku untuk SEMUA status (termasuk Cuti/Lulus/Berhenti) agar SBA & audit
#      periode lampau benar.
#   2. Murid berstatus 'Aktif' TANPA satu pun presensi Hadir → set 'Belum Mulai'.
#
# Idempoten: aman dijalankan berulang (MIN stabil; hanya mengisi yang kosong /
# menurunkan yang lebih besar; hanya menurunkan Aktif-tanpa-Hadir).

import frappe
from frappe.utils import getdate


def execute():
    meta = frappe.get_meta("Rumba Murid")
    if not meta.has_field("tanggal_mulai_belajar_aktual"):
        # Field belum tersinkron (jalankan setelah L1 ter-migrate). Aman: skip.
        return

    # --- 1. Isi tanggal_mulai_belajar_aktual dari MIN presensi Hadir ---
    rows = frappe.db.sql(
        """
        SELECT pm.murid AS murid, MIN(s.tanggal_sesi) AS tgl
        FROM `tabRumba Sesi Kelas` s
        INNER JOIN `tabRumba Presensi Murid` pm
            ON pm.parent = s.name AND pm.parenttype = 'Rumba Sesi Kelas'
        WHERE s.workflow_state = 'Disetujui' AND s.status_sesi != 'Batal'
          AND pm.status_kehadiran = 'Hadir' AND pm.murid IS NOT NULL
        GROUP BY pm.murid
        """,
        as_dict=True,
    )

    murid_ber_hadir = set()
    for r in rows:
        if not r.murid or not r.tgl:
            continue
        murid_ber_hadir.add(r.murid)
        lama = frappe.db.get_value(
            "Rumba Murid", r.murid, "tanggal_mulai_belajar_aktual"
        )
        if not lama or getdate(lama) > getdate(r.tgl):
            frappe.db.set_value(
                "Rumba Murid",
                r.murid,
                "tanggal_mulai_belajar_aktual",
                getdate(r.tgl),
                update_modified=False,
            )

    # --- 2. Murid Aktif tanpa Hadir → Belum Mulai ---
    aktif = frappe.get_all(
        "Rumba Murid", filters={"status_murid": "Aktif"}, pluck="name"
    )
    for m in aktif:
        if m not in murid_ber_hadir:
            frappe.db.set_value(
                "Rumba Murid", m, "status_murid", "Belum Mulai", update_modified=False
            )

    frappe.db.commit()
    frappe.logger().info(
        "migrasi_status_murid_belum_mulai: %d murid ber-Hadir distempel; "
        "%d murid Aktif-tanpa-Hadir → Belum Mulai."
        % (len(murid_ber_hadir), len([m for m in aktif if m not in murid_ber_hadir]))
    )

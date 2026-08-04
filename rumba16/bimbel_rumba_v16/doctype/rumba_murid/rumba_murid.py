# Copyright (c) 2026, Yayasan Rumba Kita Indonesia and contributors
# For license information, please see license.txt
#
# TARUH FILE INI DI SERVER (menimpa controller pass):
#   ~/frappe-bench/apps/rumba16/rumba16/bimbel_rumba_v16/doctype/rumba_murid/rumba_murid.py

import frappe
from frappe import _
from frappe.model.document import Document


class RumbaMurid(Document):
    def validate(self):
        self.advisory_aktif_tanpa_presensi()

    # --- ERP-LIFE-001b: advisory override manual ---
    def advisory_aktif_tanpa_presensi(self):
        """Peringatan lunak (non-blok) bila Admin men-set status 'Aktif' secara
        manual padahal belum ada presensi Hadir (tanggal_mulai_belajar_aktual
        kosong). Aktivasi seharusnya terjadi otomatis dari presensi (controller
        Rumba Sesi Kelas). Tidak menghalangi simpan — konsisten prinsip RUMBA
        menghindari birokrasi keras; basis insentif tetap aman karena
        SBA/murid_aktif membaca tanggal_mulai_belajar_aktual (ERP-KES-001 v0.2).

        Hanya ditampilkan pada transisi baru ke 'Aktif' (bukan tiap simpan),
        agar tidak spam."""
        if self.status_murid != "Aktif":
            return
        if self.get("tanggal_mulai_belajar_aktual"):
            return

        sebelumnya = self.get_doc_before_save()
        status_lama = sebelumnya.status_murid if sebelumnya else None
        if status_lama == "Aktif":
            return  # bukan transisi baru → jangan spam

        frappe.msgprint(
            _(
                "Murid ini belum tercatat hadir (Tanggal Mulai Belajar Aktual kosong); "
                "status Aktif seharusnya terjadi otomatis saat presensi Hadir pertama "
                "disetujui. Pastikan presensi dicatat agar insentif SBA/SML terhitung benar."
            ),
            title=_("Aktif Tanpa Presensi"),
            indicator="orange",
        )

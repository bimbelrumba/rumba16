# Copyright (c) 2026, Yayasan Rumba Kita Indonesia and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class RumbaLead(Document):
    def validate(self):
        self.validasi_trial()

    def validasi_trial(self):
        """Fase D / G4 — alur Trial (ERP-LIFE-001).

        Catatan: konversi ke status_lead='Terdaftar' TIDAK ditangani di sini.
        Itu tetap di controller Rumba Pendaftaran (Fase C, idempoten) agar tidak
        terjadi duplikasi logika.
        """

        # D4 — cek kapasitas referensial terhadap roster (Fase B). Lunak (non-blok).
        if self.kelas_trial:
            kelas = frappe.db.get_value(
                "Rumba Kelas",
                self.kelas_trial,
                ["kapasitas_murid", "jumlah_anggota"],
                as_dict=True,
            )
            if kelas and kelas.kapasitas_murid:
                sisa = (kelas.kapasitas_murid or 0) - (kelas.jumlah_anggota or 0)
                if sisa <= 0:
                    frappe.msgprint(
                        _(
                            "Kelas {0} sudah penuh ({1}/{2}). Jadwalkan trial di sesi lain "
                            "agar kelas tidak melebihi kapasitas (SOP-OPS-005)."
                        ).format(
                            frappe.bold(self.kelas_trial),
                            kelas.jumlah_anggota or 0,
                            kelas.kapasitas_murid,
                        ),
                        title=_("Kapasitas Kelas Trial"),
                        indicator="orange",
                    )

        # D3 — sinkron status_lead dengan alur Trial.
        if self.hasil_trial == "Tidak Jadi":
            self.status_lead = "Tidak Jadi"
        elif self.tanggal_trial and self.status_lead in ("Baru", "Dihubungi"):
            self.status_lead = "Trial"

        # Konsistensi tanggal follow-up terhadap tanggal trial (lunak, peringatan).
        if self.tanggal_trial:
            tgl_trial = getdate(self.tanggal_trial)
            for fieldname in ("tanggal_followup_1", "tanggal_followup_2"):
                nilai = self.get(fieldname)
                if nilai and getdate(nilai) < tgl_trial:
                    frappe.msgprint(
                        _("{0} ({1}) mendahului Tanggal Trial ({2}). Mohon dicek.").format(
                            self.meta.get_label(fieldname),
                            getdate(nilai),
                            tgl_trial,
                        ),
                        indicator="orange",
                    )

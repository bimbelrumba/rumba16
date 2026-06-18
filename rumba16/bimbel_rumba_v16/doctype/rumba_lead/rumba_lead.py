# Copyright (c) 2026, Yayasan Rumba Kita Indonesia and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today


class RumbaLead(Document):
    def validate(self):
        self.validasi_trial()
        self.validasi_daftar_tunggu()

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

    def validasi_daftar_tunggu(self):
        """Fase D / G5 — Daftar Tunggu (ERP-LIFE-001 v0.2).

        Target tunggu = program + unit (tanpa link kelas spesifik). FIFO via
        tanggal_masuk_tunggu. Petunjuk kursi tersedia bersifat advisory.
        """

        # FIFO — auto-stempel tanggal masuk saat status menjadi Daftar Tunggu.
        if self.status_lead == "Daftar Tunggu":
            if not self.tanggal_masuk_tunggu:
                self.tanggal_masuk_tunggu = today()

            # Petunjuk lunak: ada kelas Aktif program ini di unit yang masih ada kursi?
            if self.nama_unit and self.program_diminati:
                kelas_kosong = frappe.db.sql(
                    """
                    SELECT name, jumlah_anggota, kapasitas_murid
                    FROM `tabRumba Kelas`
                    WHERE nama_unit = %(unit)s
                      AND program_belajar = %(program)s
                      AND status_kelas = 'Aktif'
                      AND IFNULL(jumlah_anggota, 0) < IFNULL(kapasitas_murid, 0)
                    """,
                    {"unit": self.nama_unit, "program": self.program_diminati},
                    as_dict=True,
                )
                if kelas_kosong:
                    daftar = ", ".join(
                        "{0} ({1}/{2})".format(
                            k.name, k.jumlah_anggota or 0, k.kapasitas_murid or 0
                        )
                        for k in kelas_kosong
                    )
                    frappe.msgprint(
                        _(
                            "Ada kelas dengan kursi kosong untuk program ini di {0}: {1}. "
                            "Pertimbangkan menempatkan calon langsung daripada masuk daftar tunggu."
                        ).format(frappe.bold(self.nama_unit), daftar),
                        title=_("Kursi Mungkin Tersedia"),
                        indicator="blue",
                    )

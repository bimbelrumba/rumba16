# Copyright (c) 2026, Yayasan Rumba Kita Indonesia and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt


class RumbaEvent(Document):
    """Modul Event RUMBA (ERP-EVT-001).

    Tahap 1 — pendaftaran & ringkasan. Event adalah kegiatan terpusat milik
    Pemasaran & Event / Rumba Bisnis (KD-7): pengeluaran ditanggung Pusat,
    pendapatan pendaftaran ditagih via unit peserta. Status dikelola oleh
    Workflow "Alur Event RUMBA" (field `status`).

    Catatan: pembuatan Sales Invoice peserta + penarikan total_pendapatan dari
    invoice (sinkron pembayaran) adalah lingkup Tahap 2 dan belum ditangani di
    sini.
    """

    def validate(self):
        self.set_default_nominal()
        self.validasi_peserta()
        self.hitung_ringkasan()

    def set_default_nominal(self):
        """Isi nominal kontribusi peserta dari biaya_per_peserta bila kosong.

        Hanya berlaku untuk event berbayar. Nilai yang sudah diisi manual
        (mis. keringanan) tidak ditimpa.
        """
        if not self.berbayar:
            return
        for p in self.peserta or []:
            if not flt(p.nominal):
                p.nominal = flt(self.biaya_per_peserta)

    def validasi_peserta(self):
        """Anti-duplikat murid + gerbang kuota (peserta non-Batal)."""
        seen = set()
        for p in self.peserta or []:
            if not p.murid:
                continue
            if p.murid in seen:
                frappe.throw(
                    _("Murid {0} terdaftar lebih dari sekali pada event ini.").format(
                        frappe.bold(p.nama_murid or p.murid)
                    )
                )
            seen.add(p.murid)

        aktif = self._peserta_aktif()
        if cint(self.kuota) and len(aktif) > cint(self.kuota):
            frappe.throw(
                _("Jumlah peserta ({0}) melebihi kuota ({1}).").format(
                    len(aktif), cint(self.kuota)
                )
            )

    def hitung_ringkasan(self):
        """Hitung jumlah_peserta, total_pengeluaran, surplus_defisit.

        total_pendapatan ditarik dari Sales Invoice ber-tag event pada Tahap 2;
        di Tahap 1 nilainya dipertahankan apa adanya (0 bila belum ada).
        """
        self.jumlah_peserta = len(self._peserta_aktif())
        self.total_pengeluaran = sum(flt(x.jumlah) for x in self.pengeluaran or [])
        self.surplus_defisit = flt(self.total_pendapatan) - flt(self.total_pengeluaran)

    def _peserta_aktif(self):
        return [
            p
            for p in self.peserta or []
            if (p.status_kehadiran or "Terdaftar") != "Batal"
        ]

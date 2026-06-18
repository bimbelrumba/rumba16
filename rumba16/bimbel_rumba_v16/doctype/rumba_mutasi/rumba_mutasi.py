# Copyright (c) 2026, Yayasan Rumba Kita Indonesia and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import getseries
from frappe.utils import flt, fmt_money, getdate, nowdate


class RumbaMutasi(Document):
    """Fase D / G6 — Mutasi Murid antar unit (ERP-LIFE-001 v0.3, SOP-OPS-003).

    Gerbang tunggakan (M2, 18 Jun 2026): checkbox konfirmasi manual = gerbang
    nyata; tunggakan_unit_asal otomatis hanya ADVISORY. Saat G10 (SPP berulang)
    + invoice ber-tag unit tersedia, perketat jadi blokir keras (lihat memori
    pengingat G10).
    """

    def autoname(self):
        # Counter independen per-prefix (getseries), bukan format:{#####} yang
        # ber-counter global ber-share antar DocType. Pola sama Rumba Pendaftaran.
        tahun = getdate(self.tanggal_mutasi or nowdate()).strftime("%Y")
        prefix = f"MUT-{tahun}-"
        self.name = prefix + getseries(prefix, 5)

    def validate(self):
        self.set_data_murid()
        self.validasi_unit_tujuan()
        self.hitung_tunggakan()
        self.gerbang_konfirmasi()

    def on_update(self):
        self.eksekusi_mutasi()

    def set_data_murid(self):
        if not self.murid:
            return
        murid = frappe.db.get_value(
            "Rumba Murid",
            self.murid,
            ["nama_lengkap", "program_belajar", "nama_unit"],
            as_dict=True,
        )
        if not murid:
            return
        # unit_asal dikunci ke unit murid saat ini; jangan timpa bila sudah terisi
        # (agar tetap = unit asal sebenarnya setelah mutasi dieksekusi).
        if not self.unit_asal:
            self.unit_asal = murid.nama_unit
        self.nama_murid = murid.nama_lengkap
        self.program_belajar = murid.program_belajar

    def validasi_unit_tujuan(self):
        if self.unit_tujuan and self.unit_asal and self.unit_tujuan == self.unit_asal:
            frappe.throw(_("Unit Tujuan tidak boleh sama dengan Unit Asal."))

    def hitung_tunggakan(self):
        """Advisory (M2): total outstanding Sales Invoice customer (lintas unit)."""
        outstanding = 0
        customer = (
            frappe.db.get_value("Rumba Murid", self.murid, "customer")
            if self.murid
            else None
        )
        if customer:
            outstanding = frappe.db.sql(
                """
                SELECT IFNULL(SUM(outstanding_amount), 0)
                FROM `tabSales Invoice`
                WHERE customer = %s AND docstatus = 1
                """,
                customer,
            )[0][0]
        self.tunggakan_unit_asal = flt(outstanding)

        if flt(outstanding) > 0 and self.status_mutasi in ("Disetujui", "Selesai"):
            frappe.msgprint(
                _(
                    "Customer murid masih punya tagihan outstanding {0} (lintas unit). "
                    "Pastikan tunggakan di unit asal sudah lunas (SOP-OPS-003) sebelum lanjut."
                ).format(frappe.bold(fmt_money(outstanding))),
                title=_("Peringatan Tunggakan"),
                indicator="orange",
            )

    def gerbang_konfirmasi(self):
        """Gerbang nyata (M2): wajib centang konfirmasi sebelum status final."""
        if self.status_mutasi in ("Disetujui", "Selesai") and not self.konfirmasi_lunas_unit_asal:
            frappe.throw(
                _(
                    "Centang 'Konfirmasi Lunas di Unit Asal' lebih dulu (koordinasikan "
                    "dengan unit asal, SOP-OPS-003) sebelum menyetujui/menyelesaikan mutasi."
                ),
                title=_("Konfirmasi Tunggakan Diperlukan"),
            )

    def eksekusi_mutasi(self):
        """Saat status Selesai: pindahkan unit murid + tandai roster asal Keluar.

        Idempoten: berhenti bila murid sudah berada di unit tujuan.
        Penempatan kelas di unit tujuan = manual oleh ARU (di luar scope ini).
        """
        if self.status_mutasi != "Selesai":
            return

        murid_unit = frappe.db.get_value("Rumba Murid", self.murid, "nama_unit")
        if murid_unit == self.unit_tujuan:
            return  # sudah dieksekusi

        kode_tujuan = frappe.db.get_value("Rumba Unit", self.unit_tujuan, "kode_unit")
        frappe.db.set_value(
            "Rumba Murid",
            self.murid,
            {"nama_unit": self.unit_tujuan, "kode_unit": kode_tujuan},
        )
        self.tandai_roster_keluar()

    def tandai_roster_keluar(self):
        rows = frappe.db.sql(
            """
            SELECT ak.name AS row, ak.parent AS kelas
            FROM `tabRumba Anggota Kelas` ak
            INNER JOIN `tabRumba Kelas` k ON k.name = ak.parent
            WHERE ak.murid = %s AND ak.status = 'Aktif' AND k.nama_unit = %s
            """,
            (self.murid, self.unit_asal),
            as_dict=True,
        )
        kelas_terdampak = set()
        for r in rows:
            frappe.db.set_value(
                "Rumba Anggota Kelas",
                r.row,
                {"status": "Keluar", "tanggal_keluar": self.tanggal_mutasi},
            )
            kelas_terdampak.add(r.kelas)

        # Recompute jumlah_anggota (anggota Aktif) pada kelas terdampak.
        for kelas in kelas_terdampak:
            aktif = frappe.db.count(
                "Rumba Anggota Kelas", {"parent": kelas, "status": "Aktif"}
            )
            frappe.db.set_value("Rumba Kelas", kelas, "jumlah_anggota", aktif)

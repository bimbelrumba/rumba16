# Copyright (c) 2026, Yayasan Rumba Kita Indonesia and contributors
# For license information, please see license.txt

# ============================================================================
# CATATAN DEPLOY (Fase F / F9):
# File ini = controller G6 Mutasi EXISTING + pengetatan gerbang tunggakan (F9).
# Salin/timpa ke:
#   apps/rumba16/rumba16/bimbel_rumba_v16/doctype/rumba_mutasi/rumba_mutasi.py
#
# Perubahan vs versi lama (ERP-FIN-001 F9, pengingat G10):
#  1. hitung_tunggakan(): outstanding dihitung PER UNIT ASAL via tag rumba_unit
#     (bukan lagi total lintas unit). Tambahan: outstanding tak ber-tag unit
#     ditampilkan sebagai advisory terpisah (sampai invoice non-SPP ber-tag).
#  2. Gerbang: dari checkbox manual (konfirmasi_lunas_unit_asal) → BLOKIR KERAS
#     bila tunggakan_unit_asal > 0 saat status Disetujui/Selesai. Checkbox
#     DIPENSIUNKAN sebagai gerbang (field boleh tetap ada di DocType, tidak lagi
#     ditegakkan; pertimbangkan disembunyikan dari form).
# ============================================================================

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import getseries
from frappe.utils import flt, fmt_money, getdate, nowdate


class RumbaMutasi(Document):
    """Fase D / G6 — Mutasi Murid antar unit (ERP-LIFE-001, SOP-OPS-003).

    Gerbang tunggakan (F9 / G10, 23 Jun 2026): kini invoice SPP ber-tag
    rumba_unit tersedia, sehingga tunggakan_unit_asal dihitung khusus unit asal
    dan menjadi GERBANG KERAS (blokir) — menggantikan checkbox manual M2.
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
        self.gerbang_tunggakan()

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
        """F9 — tunggakan KHUSUS unit asal via tag rumba_unit (gerbang nyata).

        Juga hitung outstanding tak ber-tag unit sebagai advisory terpisah
        (mis. biaya pendaftaran yang belum di-tag; akan hilang setelah seluruh
        invoice ber-tag rumba_unit).
        """
        self.tunggakan_unit_asal = 0
        customer = (
            frappe.db.get_value("Rumba Murid", self.murid, "customer")
            if self.murid
            else None
        )
        if not customer:
            return

        # Tunggakan ber-tag unit asal — basis gerbang keras.
        tunggakan_unit = frappe.db.sql(
            """
            SELECT IFNULL(SUM(outstanding_amount), 0)
            FROM `tabSales Invoice`
            WHERE customer = %s AND docstatus = 1 AND rumba_unit = %s
            """,
            (customer, self.unit_asal),
        )[0][0]
        self.tunggakan_unit_asal = flt(tunggakan_unit)

        # Outstanding tanpa tag unit — advisory (belum bisa diatribusikan ke unit).
        tak_bertag = frappe.db.sql(
            """
            SELECT IFNULL(SUM(outstanding_amount), 0)
            FROM `tabSales Invoice`
            WHERE customer = %s AND docstatus = 1
              AND (rumba_unit IS NULL OR rumba_unit = '')
            """,
            (customer,),
        )[0][0]
        if flt(tak_bertag) > 0 and self.status_mutasi in ("Disetujui", "Selesai"):
            frappe.msgprint(
                _(
                    "Ada tagihan outstanding {0} tanpa tag unit (mis. biaya pendaftaran) "
                    "yang belum bisa diatribusikan ke unit asal. Periksa manual sesuai "
                    "SOP-OPS-003."
                ).format(frappe.bold(fmt_money(tak_bertag))),
                title=_("Tunggakan Tanpa Tag Unit"),
                indicator="orange",
            )

    def gerbang_tunggakan(self):
        """F9 — GERBANG KERAS: blokir final selama masih ada tunggakan di unit asal.

        Menggantikan gerbang checkbox manual (M2). Checkbox
        konfirmasi_lunas_unit_asal dipensiunkan — tidak lagi ditegakkan.
        """
        if self.status_mutasi in ("Disetujui", "Selesai") and flt(self.tunggakan_unit_asal) > 0:
            frappe.throw(
                _(
                    "Mutasi tidak dapat disetujui/diselesaikan: murid masih punya "
                    "tunggakan {0} di unit asal. Lunasi seluruh tagihan unit asal lebih "
                    "dulu (SOP-OPS-003)."
                ).format(frappe.bold(fmt_money(self.tunggakan_unit_asal))),
                title=_("Tunggakan Unit Asal Belum Lunas"),
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

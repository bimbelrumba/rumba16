# Copyright (c) 2026, Yayasan Rumba Kita Indonesia and contributors
# For license information, please see license.txt

# ============================================================================
# CATATAN DEPLOY (Fase F / F6):
# File ini = controller G7 Pengunduran Diri EXISTING + 1 tambahan wiring F6.
# Salin/timpa ke:
#   apps/rumba16/rumba16/bimbel_rumba_v16/doctype/rumba_pengunduran_diri/
#       rumba_pengunduran_diri.py
# Satu-satunya perubahan vs versi lama: pada eksekusi Final (setelah murid
# di-set Berhenti + roster Keluar), memanggil hanguskan_saldo_dimuka() (F6).
# Panggilan dibungkus try/except → bila penghangusan bermasalah, pengunduran
# TETAP diproses (selaras SOP-OPS-006), error dicatat ke Error Log.
# ============================================================================

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import getseries
from frappe.utils import date_diff, flt, fmt_money, getdate, nowdate


class RumbaPengunduranDiri(Document):
    """Fase D / G7 — Pengunduran Diri Murid (ERP-LIFE-001 v0.4, SOP-OPS-006).

    Notice H-14 & tunggakan = advisory (pengunduran tetap diproses, SOP).
    Drop-off (penonaktifan sepihak) butuh persetujuan Kepala Unit.
    Eksekusi (status_murid=Berhenti + roster Keluar) saat ARU finalisasi.
    Fase F/F6: saat Final, saldo SPP di muka yang tersisa dihanguskan.
    """

    def autoname(self):
        # Counter independen per-prefix (getseries) — bukan format:{#####} yang
        # ber-counter global ber-share antar DocType (pelajaran G6).
        tahun = getdate(self.tanggal_pemberitahuan or nowdate()).strftime("%Y")
        prefix = f"PDR-{tahun}-"
        self.name = prefix + getseries(prefix, 5)

    def validate(self):
        self.set_data_murid()
        self.hitung_notice()
        self.hitung_tunggakan()
        self.gerbang_dropoff()

    def on_update(self):
        self.eksekusi_pengunduran()

    def set_data_murid(self):
        if not self.murid:
            return
        m = frappe.db.get_value(
            "Rumba Murid", self.murid, ["nama_lengkap", "nama_unit"], as_dict=True
        )
        if not m:
            return
        self.nama_murid = m.nama_lengkap
        if not self.nama_unit:
            self.nama_unit = m.nama_unit

    def hitung_notice(self):
        """Advisory H-14: hitung selisih hari; peringatan bila < 14 saat Final."""
        self.selisih_notice_hari = 0
        self.notice_terpenuhi = 0
        if self.tanggal_efektif and self.tanggal_pemberitahuan:
            selisih = date_diff(self.tanggal_efektif, self.tanggal_pemberitahuan)
            self.selisih_notice_hari = selisih
            self.notice_terpenuhi = 1 if selisih >= 14 else 0
            if self.status_pengunduran == "Final" and not self.notice_terpenuhi:
                frappe.msgprint(
                    _(
                        "Notice kurang dari 14 hari (selisih {0} hari). Pengunduran tetap "
                        "diproses; sampaikan ke orang tua bahwa notice 14 hari sangat "
                        "membantu administrasi (SOP-OPS-006)."
                    ).format(selisih),
                    title=_("Notice < H-14"),
                    indicator="orange",
                )

    def hitung_tunggakan(self):
        """Advisory: total outstanding Sales Invoice customer (non-blok)."""
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
        self.tunggakan = flt(outstanding)
        if flt(outstanding) > 0 and self.status_pengunduran == "Final":
            frappe.msgprint(
                _(
                    "Murid masih punya tunggakan {0}. Informasikan ke orang tua untuk "
                    "diselesaikan (SOP-OPS-006); pengunduran tetap diproses."
                ).format(frappe.bold(fmt_money(outstanding))),
                title=_("Peringatan Tunggakan"),
                indicator="orange",
            )

    def gerbang_dropoff(self):
        """Gerbang: Drop-off final butuh persetujuan Kepala Unit (SOP-OPS-006 B.3)."""
        if (
            self.kategori == "Drop-off"
            and self.status_pengunduran == "Final"
            and not self.persetujuan_kepala_unit
        ):
            frappe.throw(
                _(
                    "Pengunduran Drop-off (penonaktifan sepihak) memerlukan Persetujuan "
                    "Kepala Unit sebelum difinalkan (SOP-OPS-006 Bagian B.3)."
                ),
                title=_("Persetujuan Kepala Unit Diperlukan"),
            )

    def eksekusi_pengunduran(self):
        """Saat status Final: nonaktifkan murid (Berhenti) + roster Keluar. Idempoten."""
        if self.status_pengunduran != "Final":
            return
        status = frappe.db.get_value("Rumba Murid", self.murid, "status_murid")
        if status == "Berhenti":
            return
        frappe.db.set_value("Rumba Murid", self.murid, "status_murid", "Berhenti")
        self.tandai_roster_keluar()
        self.hanguskan_saldo_spp_dimuka()

    def hanguskan_saldo_spp_dimuka(self):
        """Fase F/F6 — hanguskan sisa SPP di muka (SOP-FIN-012 §4.4). Non-blok:
        kegagalan dicatat ke Error Log, pengunduran tetap final."""
        try:
            from rumba16.spp_dimuka import hanguskan_saldo_dimuka

            hanguskan_saldo_dimuka(self.murid, self.tanggal_efektif)
        except Exception:
            frappe.log_error(
                title=f"Hangus saldo SPP di muka gagal: {self.murid}",
                message=frappe.get_traceback(),
            )

    def tandai_roster_keluar(self):
        # Murid keluar dari RUMBA → tandai semua keanggotaan kelas Aktif (lintas kelas).
        rows = frappe.db.sql(
            """
            SELECT name AS row, parent AS kelas
            FROM `tabRumba Anggota Kelas`
            WHERE murid = %s AND status = 'Aktif'
            """,
            self.murid,
            as_dict=True,
        )
        kelas_terdampak = set()
        for r in rows:
            frappe.db.set_value(
                "Rumba Anggota Kelas",
                r.row,
                {"status": "Keluar", "tanggal_keluar": self.tanggal_efektif},
            )
            kelas_terdampak.add(r.kelas)
        for kelas in kelas_terdampak:
            aktif = frappe.db.count(
                "Rumba Anggota Kelas", {"parent": kelas, "status": "Aktif"}
            )
            frappe.db.set_value("Rumba Kelas", kelas, "jumlah_anggota", aktif)

# Copyright (c) 2026, Yayasan Rumba Kita Indonesia and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, cint, flt, nowdate


class RumbaEvent(Document):
    """Modul Event RUMBA (ERP-EVT-001).

    Tahap 1 — pendaftaran & ringkasan.
    Tahap 2 — kontribusi peserta via Sales Invoice (lihat fungsi modul di bawah).

    Event adalah kegiatan terpusat milik Pemasaran & Event / Rumba Bisnis
    (KD-7): pengeluaran ditanggung Pusat, pendapatan pendaftaran ditagih via
    unit peserta dan diakui di Pusat (KP-4 opsi b).
    """

    def validate(self):
        self.set_default_nominal()
        self.validasi_peserta()
        self.hitung_ringkasan()

    def set_default_nominal(self):
        """Isi nominal kontribusi peserta dari biaya_per_peserta bila kosong."""
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

        total_pendapatan ditarik dari Sales Invoice ber-tag event (Tahap 2) via
        fungsi modul; di validate hanya dipakai untuk menghitung surplus.
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


# ---------------------------------------------------------------------------
# Tahap 2 — Keuangan Peserta (Sales Invoice). Mengikuti pola Fase F
# (rumba_pendaftaran.buat_sales_invoice / sinkronkan_pembayaran).
# ---------------------------------------------------------------------------


def _hitung_pendapatan(doc):
    """Set total_pendapatan = Σ grand_total Sales Invoice ber-tag event (terbit/
    docstatus=1), lintas unit (KD-7), lalu perbarui surplus_defisit."""
    total = frappe.db.sql(
        """
        SELECT COALESCE(SUM(grand_total), 0)
        FROM `tabSales Invoice`
        WHERE rumba_event = %s AND docstatus = 1
        """,
        doc.name,
    )[0][0]
    doc.db_set("total_pendapatan", flt(total))
    doc.db_set("surplus_defisit", flt(total) - flt(doc.total_pengeluaran))


@frappe.whitelist()
def buat_invoice_peserta(event, submit_invoice=0):
    """Buat Sales Invoice per peserta untuk event berbayar (idempoten).

    - customer = peserta.customer (dari Rumba Murid, KP-2)
    - item = item_event (Item per jenis event, KP-3)
    - rate = peserta.nominal (default biaya_per_peserta)
    - tag rumba_event + rumba_unit (unit peserta = saluran penagihan) + rumba_murid
    - cost center item = cost_center_pengeluaran (Pusat) bila diisi (KP-4 b),
      agar pendapatan diakui di Pusat berdampingan dengan beban.
    Melewati peserta: status Batal, sudah punya invoice, customer kosong, nominal <= 0.
    """
    doc = frappe.get_doc("Rumba Event", event)
    doc.check_permission("write")

    if not doc.berbayar:
        frappe.throw(_("Event ini bukan event berbayar."))
    if not doc.item_event:
        frappe.throw(_("Item Event wajib diisi sebelum membuat invoice."))

    company = frappe.defaults.get_user_default("Company") or frappe.defaults.get_global_default(
        "company"
    )
    if not company:
        frappe.throw(_("Default Company belum diatur."))

    dibuat, dilewati = [], []
    for p in doc.peserta or []:
        label = p.nama_murid or p.murid
        if (p.status_kehadiran or "Terdaftar") == "Batal":
            dilewati.append([label, "status Batal"])
            continue
        if p.sales_invoice:
            dilewati.append([label, "sudah ada invoice"])
            continue
        if not p.customer:
            dilewati.append([label, "Customer kosong"])
            continue
        rate = flt(p.nominal) or flt(doc.biaya_per_peserta)
        if rate <= 0:
            dilewati.append([label, "nominal 0"])
            continue

        invoice = frappe.new_doc("Sales Invoice")
        invoice.customer = p.customer
        invoice.company = company
        invoice.posting_date = nowdate()
        invoice.due_date = add_days(nowdate(), 14)
        invoice.rumba_event = doc.name
        invoice.rumba_unit = p.unit_murid
        invoice.rumba_murid = p.murid
        item_row = {
            "item_code": doc.item_event,
            "qty": 1,
            "rate": rate,
            "description": _("Kontribusi {0} - {1}").format(doc.judul_event, label),
        }
        if doc.cost_center_pengeluaran:
            item_row["cost_center"] = doc.cost_center_pengeluaran
        invoice.append("items", item_row)
        invoice.insert()
        if cint(submit_invoice):
            invoice.submit()

        p.db_set("sales_invoice", invoice.name)
        p.db_set("status_pembayaran", "Tertagih")
        dibuat.append([label, invoice.name])

    _hitung_pendapatan(doc)
    return {"dibuat": dibuat, "dilewati": dilewati}


@frappe.whitelist()
def sinkronkan_pembayaran_event(event):
    """Tarik status pembayaran tiap peserta dari Sales Invoice-nya, lalu
    perbarui total_pendapatan & surplus_defisit."""
    doc = frappe.get_doc("Rumba Event", event)
    doc.check_permission("write")

    updated = []
    for p in doc.peserta or []:
        if not p.sales_invoice:
            if p.status_pembayaran != "Belum Ditagih":
                p.db_set("status_pembayaran", "Belum Ditagih")
            continue

        inv = frappe.db.get_value(
            "Sales Invoice",
            p.sales_invoice,
            ["docstatus", "outstanding_amount"],
            as_dict=True,
        )
        if not inv:
            # invoice terhapus — buka kembali untuk dibuat ulang
            p.db_set("sales_invoice", None)
            p.db_set("status_pembayaran", "Belum Ditagih")
            continue

        if inv.docstatus == 2:
            # invoice dibatalkan — buka kembali peserta untuk re-invoice
            p.db_set("sales_invoice", None)
            status = "Belum Ditagih"
        elif inv.docstatus == 0:
            status = "Tertagih"
        elif flt(inv.outstanding_amount) <= 0:
            status = "Lunas"
        else:
            status = "Tertagih"

        p.db_set("status_pembayaran", status)
        updated.append([p.nama_murid or p.murid, status])

    _hitung_pendapatan(doc)
    return {
        "updated": updated,
        "total_pendapatan": frappe.db.get_value("Rumba Event", doc.name, "total_pendapatan"),
    }

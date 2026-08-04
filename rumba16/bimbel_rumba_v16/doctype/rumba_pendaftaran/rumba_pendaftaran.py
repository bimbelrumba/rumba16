# Copyright (c) 2026, Yayasan Rumba Kita Indonesia and contributors
# For license information, please see license.txt

# ============================================================================
# CATATAN DEPLOY (Fase F / F4b — follow-up):
# File ini = controller Pendaftaran EXISTING + 1 baris tag unit pada invoice.
# Salin/timpa ke:
#   apps/rumba16/rumba16/bimbel_rumba_v16/doctype/rumba_pendaftaran/
#       rumba_pendaftaran.py
#
# Satu-satunya perubahan vs versi lama: di buat_sales_invoice(), invoice
# pendaftaran kini diberi tag `invoice.rumba_unit = doc.nama_unit` sebelum
# insert. Tujuan: biaya pendaftaran ikut ber-tag unit, sehingga gerbang
# tunggakan G6 Mutasi (F9) menghitung tunggakan unit asal SECARA LENGKAP
# (bukan hanya SPP). Tanpa ini, tagihan pendaftaran hanya muncul sebagai
# "advisory tak ber-tag" di rumba_mutasi.py.
# ============================================================================

import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import getseries
from frappe.utils import add_days, flt, getdate, nowdate, today


class RumbaPendaftaran(Document):
    def advisory_deteksi_masuk_lagi(self):
        """ERP-KES-001 K4: bila jenis_pendaftaran='Siswa Baru' tapi ada murid
        berstatus Berhenti dengan nomor HP ortu sama ATAU nama lengkap sama,
        ingatkan Admin agar mempertimbangkan 'Masuk Lagi' (SML) — non-blok."""
        if self.get("jenis_pendaftaran") != "Siswa Baru":
            return
        if not (self.get("nomor_handphone") or self.get("nama_lengkap")):
            return

        kandidat = []
        if self.get("nomor_handphone"):
            kandidat = frappe.get_all(
                "Rumba Murid",
                filters={"status_murid": "Berhenti", "nomor_handphone": self.nomor_handphone},
                fields=["name", "nama_lengkap", "nama_unit"],
                limit=3,
            )
        if not kandidat and self.get("nama_lengkap"):
            kandidat = frappe.get_all(
                "Rumba Murid",
                filters={"status_murid": "Berhenti", "nama_lengkap": ("like", self.nama_lengkap.strip())},
                fields=["name", "nama_lengkap", "nama_unit"],
                limit=3,
            )
 
        if kandidat:
            daftar = "<br>".join(
                "- {0} ({1}, unit {2})".format(k.nama_lengkap, k.name, k.nama_unit or "-")
                for k in kandidat
            )
            frappe.msgprint(
                msg=(
                    "Ditemukan murid berstatus <b>Berhenti</b> dengan data mirip:<br>{0}<br><br>"
                    "Bila ini murid yang sama, pertimbangkan mengubah <b>Jenis Pendaftaran</b> "
                    "menjadi <b>Masuk Lagi</b> agar terhitung SML (bukan SBA) di laporan kesiswaan."
                ).format(daftar),
                title="Kemungkinan Siswa Masuk Lagi",
                indicator="orange",
            )

    def autoname(self):
        self.set_kode_unit()
        self.validate_kode_unit()

        tanggal = getdate(self.tanggal_pendaftaran or nowdate())
        tahun = tanggal.strftime("%y")
        bulan = tanggal.strftime("%m")

        prefix = f"{self.kode_unit}{tahun}{bulan}"
        nomor_urut = getseries(prefix, 2)

        self.name = f"{prefix}{nomor_urut}"

    def validate(self):
        self.set_kode_unit()
        self.validate_kode_unit()
        self.normalize_nomor_handphone()
        self.set_duplicate_check_key()
        self.validate_duplicate_pendaftaran()
        self.validate_persetujuan_harus_lunas()
        self.advisory_deteksi_masuk_lagi()

    def set_kode_unit(self):
        if self.kode_unit:
            self.kode_unit = str(self.kode_unit).strip().upper()
            return

        # Kalau kode_unit kosong tapi ada unit/cabang, sesuaikan field ini bila perlu.
        # Contoh: self.unit, self.cabang, atau self.rumba_cabang.
        unit = self.nama_unit

        if unit:
            kode_unit = frappe.db.get_value("Rumba Unit", unit, "kode_unit")
        if kode_unit:
            self.kode_unit = str(kode_unit).strip().upper()

    def validate_kode_unit(self):
        if not self.kode_unit:
            frappe.throw(_("Kode Unit wajib diisi sebelum membuat nomor pendaftaran."))

    def normalize_nomor_handphone(self):
        if not self.nomor_handphone:
            return

        phone = re.sub(r"\D", "", self.nomor_handphone)

        if phone.startswith("0"):
            phone = "62" + phone[1:]
        elif phone.startswith("8"):
            phone = "62" + phone

        self.nomor_handphone = phone

    def set_duplicate_check_key(self):
        nama_lengkap = self.clean_duplicate_text(self.nama_lengkap)
        tanggal_lahir = str(self.tanggal_lahir or "")
        nomor_handphone = self.nomor_handphone or ""

        if not nama_lengkap or not tanggal_lahir or not nomor_handphone:
            self.duplicate_check_key = ""
            return

        self.duplicate_check_key = f"{nama_lengkap}|{tanggal_lahir}|{nomor_handphone}"

    def validate_duplicate_pendaftaran(self):
        if not self.duplicate_check_key:
            return

        existing = frappe.db.exists(
            "Rumba Pendaftaran",
            {
                "duplicate_check_key": self.duplicate_check_key,
                "name": ["!=", self.name],
                "docstatus": ["<", 2],
            },
        )

        if existing:
            frappe.throw(
                _(
                    "Pendaftaran dobel terdeteksi. Murid dengan nama lengkap, tanggal lahir, "
                    "dan nomor HP orang tua yang sama sudah pernah didaftarkan pada dokumen {0}."
                ).format(frappe.bold(existing)),
                title=_("Pendaftaran Dobel"),
            )

    def validate_persetujuan_harus_lunas(self):
        if self.status_pendaftaran != "Disetujui":
            return

        if getattr(self, "status_pembayaran", None) == "Lunas":
            return

        frappe.throw(
            _(
                "Pendaftaran hanya bisa disetujui jika Status Pembayaran sudah Lunas."
            ),
            title=_("Pembayaran Belum Lunas"),
        )

    def clean_duplicate_text(self, value):
        if not value:
            return ""

        return " ".join(str(value).strip().lower().split())

    def on_update(self):
        self.konversi_lead_jika_disetujui()

    def konversi_lead_jika_disetujui(self):
        """Saat Pendaftaran Disetujui dan tertaut ke Lead, tandai Lead sebagai
        'Terdaftar' dan catat tanggal konversi. Idempoten: tidak menimpa lead
        yang sudah Terdaftar."""
        if self.status_pendaftaran != "Disetujui" or not self.lead:
            return

        status_lead = frappe.db.get_value("Rumba Lead", self.lead, "status_lead")
        if status_lead == "Terdaftar":
            return

        frappe.db.set_value(
            "Rumba Lead",
            self.lead,
            {
                "status_lead": "Terdaftar",
                "tanggal_konversi": today(),
                "pendaftaran": self.name,
            },
        )

@frappe.whitelist()
def buat_sales_invoice(pendaftaran, item_code, rate, due_date=None, submit_invoice=0):
    doc = frappe.get_doc("Rumba Pendaftaran", pendaftaran)
    doc.check_permission("write")

    if doc.sales_invoice:
        frappe.throw(
            _("Sales Invoice {0} sudah dibuat untuk pendaftaran ini.").format(
                frappe.bold(doc.sales_invoice)
            )
        )

    if not doc.customer_orang_tua:
        frappe.throw(_("Buat Customer Orang Tua terlebih dahulu sebelum membuat invoice."))

    if doc.status_pendaftaran == "Disetujui" and doc.status_pembayaran != "Lunas":
        frappe.throw(
            _("Pendaftaran yang belum lunas tidak boleh berada dalam status Disetujui."),
            title=_("Pembayaran Belum Lunas"),
        )

    if not item_code:
        frappe.throw(_("Item invoice wajib dipilih."))

    rate = flt(rate)
    if rate <= 0:
        frappe.throw(_("Nominal invoice harus lebih besar dari 0."))

    company = frappe.defaults.get_user_default("Company") or frappe.defaults.get_global_default("company")
    if not company:
        frappe.throw(_("Default Company belum diatur."))

    invoice = frappe.new_doc("Sales Invoice")
    invoice.customer = doc.customer_orang_tua
    invoice.company = company
    invoice.posting_date = nowdate()
    invoice.due_date = due_date or add_days(nowdate(), 7)
    # F4b — tag unit pada tagihan pendaftaran (melengkapi gerbang tunggakan G6/F9).
    invoice.rumba_unit = doc.nama_unit
    cost_center = frappe.db.get_value("Rumba Unit", doc.nama_unit, "cost_center") if doc.nama_unit else None
    if cost_center:
        invoice.cost_center = cost_center
    invoice.append(
        "items",
        {
            "item_code": item_code,
            "qty": 1,
            "rate": rate,
            "cost_center": cost_center,
            "description": _("Tagihan pendaftaran {0} - {1}").format(
                doc.name, doc.nama_lengkap
            ),
        },
    )
    invoice.insert()

    if int(submit_invoice):
        invoice.submit()

    doc.db_set("sales_invoice", invoice.name)
    doc.db_set("status_pembayaran", "Menunggu Pembayaran")

    return invoice.name

@frappe.whitelist()
def sinkronkan_pembayaran(pendaftaran):
    doc = frappe.get_doc("Rumba Pendaftaran", pendaftaran)
    doc.check_permission("write")

    if not doc.sales_invoice:
        frappe.throw(_("Sales Invoice belum terhubung ke pendaftaran ini."))

    invoice = frappe.get_doc("Sales Invoice", doc.sales_invoice)

    if invoice.docstatus == 2:
        status_pembayaran = "Dibatalkan"
        tanggal_pembayaran = None
    elif invoice.docstatus == 0:
        status_pembayaran = "Menunggu Pembayaran"
        tanggal_pembayaran = None
    elif flt(invoice.outstanding_amount) <= 0:
        status_pembayaran = "Lunas"
        tanggal_pembayaran = today()
    elif flt(invoice.outstanding_amount) < flt(invoice.grand_total):
        status_pembayaran = "Dibayar Sebagian"
        tanggal_pembayaran = None
    else:
        status_pembayaran = "Menunggu Pembayaran"
        tanggal_pembayaran = None

    doc.db_set("status_pembayaran", status_pembayaran)
    doc.db_set("tanggal_pembayaran", tanggal_pembayaran)

    return {
        "sales_invoice": invoice.name,
        "invoice_status": invoice.status,
        "outstanding_amount": invoice.outstanding_amount,
        "status_pembayaran": status_pembayaran,
        "tanggal_pembayaran": tanggal_pembayaran,
    }

def sync_status_pembayaran_from_sales_invoice(doc, method=None):
    """Dipanggil oleh hooks.py saat Sales Invoice on_update_after_submit atau on_cancel."""
    pendaftaran_name = frappe.db.get_value(
        "Rumba Pendaftaran", {"sales_invoice": doc.name}, "name"
    )
    if not pendaftaran_name:
        return

    pendaftaran = frappe.get_doc("Rumba Pendaftaran", pendaftaran_name)
    pendaftaran.check_permission("write")

    from frappe.utils import flt, today

    if doc.docstatus == 2:
        status_pembayaran = "Dibatalkan"
        tanggal_pembayaran = None
    elif flt(doc.outstanding_amount) <= 0:
        status_pembayaran = "Lunas"
        tanggal_pembayaran = today()
    elif flt(doc.outstanding_amount) < flt(doc.grand_total):
        status_pembayaran = "Dibayar Sebagian"
        tanggal_pembayaran = None
    else:
        status_pembayaran = "Menunggu Pembayaran"
        tanggal_pembayaran = None

    pendaftaran.db_set("status_pembayaran", status_pembayaran)
    pendaftaran.db_set("tanggal_pembayaran", tanggal_pembayaran)


def sync_status_pembayaran_from_payment_entry(doc, method=None):
    """Dipanggil oleh hooks.py saat Payment Entry on_submit atau on_cancel."""
    for ref in doc.references or []:
        if ref.reference_doctype != "Sales Invoice":
            continue

        pendaftaran_name = frappe.db.get_value(
            "Rumba Pendaftaran", {"sales_invoice": ref.reference_name}, "name"
        )
        if not pendaftaran_name:
            continue

        invoice = frappe.get_doc("Sales Invoice", ref.reference_name)
        pendaftaran = frappe.get_doc("Rumba Pendaftaran", pendaftaran_name)
        pendaftaran.check_permission("write")

        from frappe.utils import flt, today

        if invoice.docstatus == 2:
            status_pembayaran = "Dibatalkan"
            tanggal_pembayaran = None
        elif flt(invoice.outstanding_amount) <= 0:
            status_pembayaran = "Lunas"
            tanggal_pembayaran = today()
        elif flt(invoice.outstanding_amount) < flt(invoice.grand_total):
            status_pembayaran = "Dibayar Sebagian"
            tanggal_pembayaran = None
        else:
            status_pembayaran = "Menunggu Pembayaran"
            tanggal_pembayaran = None

        pendaftaran.db_set("status_pembayaran", status_pembayaran)
        pendaftaran.db_set("tanggal_pembayaran", tanggal_pembayaran)

# Copyright (c) 2026, Yayasan Rumba Kita Indonesia and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import getseries
from frappe.utils import getdate, nowdate


class RumbaPendaftaran(Document):
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

    def set_kode_unit(self):
        if self.kode_unit:
            self.kode_unit = str(self.kode_unit).strip().upper()
            return

        # Kalau kode_unit kosong tapi ada unit/cabang, sesuaikan field ini bila perlu.
        # Contoh: self.unit, self.cabang, atau self.rumba_cabang.
        unit = getattr(self, "unit", None) or getattr(self, "cabang", None) or getattr(self, "rumba_cabang", None)

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

    def clean_duplicate_text(self, value):
        if not value:
            return ""

        return " ".join(str(value).strip().lower().split())

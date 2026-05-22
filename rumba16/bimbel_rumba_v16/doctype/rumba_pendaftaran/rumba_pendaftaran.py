# Copyright (c) 2026, Yayasan Rumba Kita Indonesia and contributors
# For license information, please see license.txt

import frappe
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

	def set_kode_unit(self):
		if self.kode_unit:
			self.kode_unit = str(self.kode_unit).strip().zfill(4)
			return

		if self.nama_unit:
			kode_unit = frappe.db.get_value("Rumba Unit", self.nama_unit, "kode_unit")
			if kode_unit:
				self.kode_unit = str(kode_unit).strip().zfill(4)

	def validate_kode_unit(self):
		if not self.kode_unit:
			frappe.throw("Kode Unit wajib terisi sebelum nomor pendaftaran dibuat.")

		if not self.kode_unit.isdigit() or len(self.kode_unit) != 4:
			frappe.throw("Kode Unit harus terdiri dari 4 angka.")

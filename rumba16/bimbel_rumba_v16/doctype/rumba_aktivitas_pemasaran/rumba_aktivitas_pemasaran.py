# Copyright (c) 2026, Bimbel RUMBA and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import getseries
from frappe.utils import getdate, today


class RumbaAktivitasPemasaran(Document):
	def autoname(self):
		"""Penomoran 10 digit (keputusan Sisco 16 Jul 2026):

		- Kegiatan UNIT : PM{YY}{kode_unit}{##}  -> mis. PM26190101 (seri per unit per tahun)
		- Kegiatan PUSAT: PMHQ{YY}{####}         -> mis. PMHQ260001 (seri pusat per tahun)
		"""
		yy = getdate(self.tanggal or today()).strftime("%y")
		if self.nama_unit:
			kode_unit = frappe.db.get_value("Rumba Unit", self.nama_unit, "kode_unit")
			if not kode_unit:
				frappe.throw(
					_("Rumba Unit {0} belum punya kode_unit — lengkapi dulu sebelum mencatat aktivitas.").format(
						self.nama_unit
					)
				)
			prefix = f"PM{yy}{kode_unit}"
			self.name = prefix + getseries(prefix, 2)
		else:
			prefix = f"PMHQ{yy}"
			self.name = prefix + getseries(prefix, 4)

# Copyright (c) 2026, Yayasan Rumba Kita Indonesia and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class RumbaKelas(Document):
	def validate(self):
		self.validasi_anggota_kelas()

	def validasi_anggota_kelas(self):
		"""Roster (Fase B / G1): cegah duplikat murid, enforce kapasitas, isi jumlah_anggota."""
		anggota = self.anggota_kelas or []

		# 1. Cegah duplikat murid dalam satu kelas yang sama
		seen = set()
		for row in anggota:
			if not row.murid:
				continue
			if row.murid in seen:
				frappe.throw(
					f"Murid <b>{row.murid}</b> tercatat lebih dari sekali di kelas ini. "
					"Setiap murid hanya boleh satu baris per kelas."
				)
			seen.add(row.murid)

		# 2. Hitung anggota AKTIF dan enforce kapasitas
		jumlah_aktif = sum(1 for row in anggota if (row.status or "Aktif") == "Aktif")
		if self.kapasitas_murid and jumlah_aktif > self.kapasitas_murid:
			frappe.throw(
				f"Jumlah anggota aktif ({jumlah_aktif}) melebihi kapasitas kelas "
				f"({self.kapasitas_murid}). Kurangi anggota aktif atau naikkan kapasitas."
			)

		# 3. Simpan jumlah anggota aktif (field read-only)
		self.jumlah_anggota = jumlah_aktif

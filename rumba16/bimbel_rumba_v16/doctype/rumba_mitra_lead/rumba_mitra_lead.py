# Copyright (c) 2026, Bimbel RUMBA and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, today


class RumbaMitraLead(Document):
	def validate(self):
		self.validasi_alasan_tidak_jadi()
		self.validasi_status_deal()

	def validasi_alasan_tidak_jadi(self):
		"""Jalur gagal wajib beralasan (ERP-EXP-001)."""
		if self.status_mitra == "Tidak Jadi" and not (self.alasan_tidak_jadi or "").strip():
			frappe.throw(_("Alasan Tidak Jadi wajib diisi bila Status Mitra = Tidak Jadi."))

	def validasi_status_deal(self):
		"""Status Deal hanya boleh lahir dari konversi (tombol), bukan di-set manual.

		Rumba Unit punya field wajib (nama_unit, telepon, email, jumlah ruang kelas)
		yang tidak tersedia di data prospek, sehingga konversi otomatis diam-diam
		saat status diubah tidak mungkin aman. Tombol "Wujudkan Unit dari Mitra"
		(muncul saat status = Perjanjian) adalah satu-satunya jalur ke Deal.
		"""
		if self.status_mitra == "Deal" and not self.unit_terbentuk:
			frappe.throw(
				_(
					"Status Deal tidak bisa di-set manual. Gunakan tombol "
					"<b>Wujudkan Unit dari Mitra</b> saat status = Perjanjian."
				)
			)


@frappe.whitelist()
def wujudkan_unit_dari_mitra(mitra_lead, nama_unit, telepon_unit=None, email_unit=None, jumlah_ruang_kelas=1):
	"""Konversi Deal: buat Rumba Unit dari prospek mitra (idempoten).

	Dipanggil tombol "Wujudkan Unit dari Mitra" (Client Script). Membuat Rumba Unit
	kepemilikan = tipe_kemitraan, status_unit = Rintisan, lalu mengisi
	unit_terbentuk + tanggal_deal + status_mitra = Deal di Mitra Lead.
	Company dibuat MANUAL oleh Finance sampai multi-company (ERP-MCOMP-001) live.
	"""
	doc = frappe.get_doc("Rumba Mitra Lead", mitra_lead)
	doc.check_permission("write")

	# Idempoten: sudah Deal + unit terbentuk -> jangan duplikasi
	if doc.status_mitra == "Deal" and doc.unit_terbentuk:
		frappe.msgprint(_("Prospek ini sudah Deal. Unit terbentuk: {0}.").format(doc.unit_terbentuk))
		return doc.unit_terbentuk

	if doc.status_mitra != "Perjanjian":
		frappe.throw(_("Konversi hanya bisa dilakukan saat status = Perjanjian (MoU sudah ditandatangani)."))

	if not doc.tipe_kemitraan:
		frappe.throw(_("Tipe Kemitraan wajib diisi sebelum konversi (menentukan kepemilikan unit)."))

	if not (doc.nama_provinsi and doc.nama_kota):
		frappe.throw(_("Provinsi Target dan Kota Target wajib diisi sebelum konversi."))

	nama_unit = (nama_unit or "").strip()
	if not nama_unit:
		frappe.throw(_("Nama Unit wajib diisi."))

	if frappe.db.exists("Rumba Unit", nama_unit):
		frappe.throw(_("Rumba Unit bernama {0} sudah ada. Pakai nama lain.").format(nama_unit))

	unit = frappe.get_doc(
		{
			"doctype": "Rumba Unit",
			"nama_unit": nama_unit,
			"kode_provinsi": doc.nama_provinsi,
			"kode_kota": doc.nama_kota,
			"kepemilikan": doc.tipe_kemitraan,
			"status_unit": "Rintisan",
			"tanggal_mulai": today(),
			"telepon_unit": telepon_unit or doc.nomor_handphone,
			"email_unit": email_unit or doc.alamat_email,
			"jumlah_ruang_kelas": cint(jumlah_ruang_kelas) or 1,
		}
	)
	unit.insert()

	# db_set: lewati validate (validasi Deal-tanpa-unit memang untuk jalur manual)
	doc.db_set("unit_terbentuk", unit.name)
	doc.db_set("tanggal_deal", today())
	doc.db_set("status_mitra", "Deal")
	doc.add_comment("Comment", _("Deal: Rumba Unit {0} terbentuk dari konversi mitra.").format(unit.name))

	frappe.msgprint(
		_("Rumba Unit <b>{0}</b> terbentuk (Rintisan, {1}). Company dibuat manual oleh Finance.").format(
			unit.name, doc.tipe_kemitraan
		)
	)
	return unit.name

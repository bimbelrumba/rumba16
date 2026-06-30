// Copyright (c) 2026, Yayasan Rumba Kita Indonesia and contributors
// For license information, please see license.txt

frappe.ui.form.on("Rumba BKM Entry", {
	refresh(frm) {
		// Indikator gerbang: BKM hanya untuk murid Hadir; konteks ter-fetch
		// dari Sesi Kelas. Tidak ada aksi tambahan di sini (approval via Workflow).
	},
});

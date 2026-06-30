// Copyright (c) 2026, Yayasan Rumba Kita Indonesia and contributors
// For license information, please see license.txt

frappe.ui.form.on("Rumba Event", {
	setup(frm) {
		// KP-1 — filter peserta. Default hanya Murid "Aktif".
		// Untuk Kelulusan CALISTUNG dilonggarkan agar mencakup yang sudah "Lulus"
		// (peserta kelulusan bisa sudah berstatus Lulus / masih Level 3 mendekati selesai).
		frm.set_query("murid", "peserta", function () {
			let statuses = ["Aktif"];
			if (frm.doc.jenis_event === "Kelulusan CALISTUNG") {
				statuses = ["Aktif", "Lulus"];
			}
			return {
				filters: {
					status_murid: ["in", statuses],
				},
			};
		});
	},
});

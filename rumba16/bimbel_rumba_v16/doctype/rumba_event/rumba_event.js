// Copyright (c) 2026, Yayasan Rumba Kita Indonesia and contributors
// For license information, please see license.txt

frappe.ui.form.on("Rumba Event", {
	setup(frm) {
		// KP-1 — filter peserta. Default hanya Murid "Aktif".
		// Untuk Kelulusan CALISTUNG dilonggarkan agar mencakup yang sudah "Lulus".
		frm.set_query("murid", "peserta", function () {
			let statuses = ["Aktif"];
			if (frm.doc.jenis_event === "Kelulusan CALISTUNG") {
				statuses = ["Aktif", "Lulus"];
			}
			return { filters: { status_murid: ["in", statuses] } };
		});
	},

	refresh(frm) {
		if (frm.is_new()) return;

		// Tahap 2 — tombol keuangan peserta.
		const status_boleh_invoice = [
			"Pendaftaran Ditutup",
			"Berlangsung",
			"Selesai",
		];

		if (frm.doc.berbayar && status_boleh_invoice.includes(frm.doc.status)) {
			frm.add_custom_button(
				__("Buat Invoice Peserta"),
				function () {
					frappe.call({
						method:
							"rumba16.bimbel_rumba_v16.doctype.rumba_event.rumba_event.buat_invoice_peserta",
						args: { event: frm.doc.name },
						freeze: true,
						freeze_message: __("Membuat invoice peserta…"),
						callback: function (r) {
							if (!r.message) return;
							const dibuat = r.message.dibuat || [];
							const dilewati = r.message.dilewati || [];
							let html = __("Invoice dibuat: {0}", [dibuat.length]);
							if (dilewati.length) {
								html +=
									"<br><b>" +
									__("Dilewati ({0}):", [dilewati.length]) +
									"</b><br>" +
									dilewati.map((d) => `• ${d[0]} — ${d[1]}`).join("<br>");
							}
							frappe.msgprint({
								title: __("Hasil Pembuatan Invoice"),
								message: html,
								indicator: dibuat.length ? "green" : "orange",
							});
							frm.reload_doc();
						},
					});
				},
				__("Keuangan")
			);
		}

		if (!frm.is_new()) {
			frm.add_custom_button(
				__("Sinkronkan Pembayaran"),
				function () {
					frappe.call({
						method:
							"rumba16.bimbel_rumba_v16.doctype.rumba_event.rumba_event.sinkronkan_pembayaran_event",
						args: { event: frm.doc.name },
						freeze: true,
						freeze_message: __("Menyinkronkan pembayaran…"),
						callback: function (r) {
							frappe.show_alert({
								message: __("Pembayaran disinkronkan."),
								indicator: "green",
							});
							frm.reload_doc();
						},
					});
				},
				__("Keuangan")
			);
		}
	},
});

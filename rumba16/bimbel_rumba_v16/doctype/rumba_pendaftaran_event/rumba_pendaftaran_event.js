// Copyright (c) 2026, Yayasan Rumba Kita Indonesia and contributors
// For license information, please see license.txt

frappe.ui.form.on("Rumba Pendaftaran Event", {
	setup(frm) {
		// Cocokkan ke Murid aktif (atau Lulus untuk peserta kelulusan).
		frm.set_query("murid", function () {
			return { filters: { status_murid: ["in", ["Aktif", "Lulus"]] } };
		});
	},

	refresh(frm) {
		if (frm.is_new()) return;
		if (frm.doc.status_intake !== "Masuk Event") {
			frm.add_custom_button(__("Masukkan ke Event"), function () {
				if (!frm.doc.murid) {
					frappe.msgprint(__("Isi field Murid dulu (cocokkan calon dengan data Murid)."));
					return;
				}
				frappe.call({
					method:
						"rumba16.bimbel_rumba_v16.doctype.rumba_pendaftaran_event.rumba_pendaftaran_event.masukkan_ke_event",
					args: { intake: frm.doc.name },
					freeze: true,
					freeze_message: __("Memasukkan ke event…"),
					callback: function (r) {
						frappe.show_alert({
							message: __("Peserta diproses."),
							indicator: "green",
						});
						frm.reload_doc();
					},
				});
			});
		}
	},
});

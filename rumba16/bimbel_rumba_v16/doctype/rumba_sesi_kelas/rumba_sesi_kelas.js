// Copyright (c) 2026, Yayasan Rumba Kita Indonesia and contributors
// For license information, please see license.txt
//
// E3: tombol "Buat BKM dari Sesi" pada form Rumba Sesi Kelas.
// TARUH FILE INI DI SERVER (menimpa boilerplate E1):
//   apps/rumba16/rumba16/bimbel_rumba_v16/doctype/rumba_sesi_kelas/rumba_sesi_kelas.js
// lalu: bench build --app rumba16  &&  bench --site dev.bimbelrumba.id clear-cache

frappe.ui.form.on("Rumba Sesi Kelas", {
	refresh(frm) {
		// Tombol hanya muncul saat sesi sudah Disetujui (gerbang sama dengan rekap).
		// Server (buat_dari_sesi) membuat 1 BKM Entry per murid Hadir, idempoten.
		if (!frm.is_new() && frm.doc.workflow_state === "Disetujui") {
			frm.add_custom_button(__("Buat BKM dari Sesi"), function () {
				frappe.call({
					method: "rumba16.bimbel_rumba_v16.doctype.rumba_bkm_entry.rumba_bkm_entry.buat_dari_sesi",
					args: { sesi_kelas: frm.doc.name },
					freeze: true,
					freeze_message: __("Membuat BKM Entry untuk murid Hadir..."),
					callback: function (r) {
						if (r.message) {
							frappe.msgprint({
								title: __("BKM Dibuat"),
								indicator: "green",
								message: __(
									"{0} BKM Entry dibuat, {1} dilewati (sudah ada).",
									[r.message.dibuat, r.message.dilewati]
								),
							});
						}
					},
				});
			});
		}
	},
});

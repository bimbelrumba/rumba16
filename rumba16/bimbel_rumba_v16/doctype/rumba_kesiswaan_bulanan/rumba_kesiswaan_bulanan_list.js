// ERP-KES-001 / B2 — tombol "Generate Snapshot" di list view.
// Taruh di apps/rumba16/rumba16/bimbel_rumba_v16/doctype/rumba_kesiswaan_bulanan/
// (file per-doctype, dimuat otomatis oleh desk — tanpa bench build)

frappe.listview_settings["Rumba Kesiswaan Bulanan"] = {
	onload(listview) {
		const boleh = ["System Manager", "Rumba Finance"].some((r) =>
			frappe.user_roles.includes(r)
		);
		if (!boleh) return;

		listview.page.add_inner_button(__("Generate Snapshot"), () => {
			frappe.prompt(
				[
					{
						fieldname: "periode",
						fieldtype: "Data",
						label: "Periode (YYYY-MM)",
						reqd: 1,
						default: frappe.datetime.now_date().slice(0, 7),
					},
					{
						fieldname: "tanggal_cutoff",
						fieldtype: "Date",
						label: "Tanggal Cut-off",
						reqd: 1,
						default: frappe.datetime.now_date(),
					},
				],
				(v) => {
					frappe.call({
						method:
							"rumba16.bimbel_rumba_v16.doctype.rumba_kesiswaan_bulanan.rumba_kesiswaan_bulanan.generate_snapshot",
						args: v,
						freeze: true,
						freeze_message: __("Menghitung snapshot kesiswaan..."),
						callback(r) {
							if (r.message) {
								frappe.msgprint(
									__("Periode {0}: {1} snapshot dibuat, {2} unit dilewati (sudah ada).", [
										r.message.periode,
										r.message.dibuat,
										r.message.dilewati,
									])
								);
								listview.refresh();
							}
						},
					});
				},
				__("Generate Snapshot Kesiswaan"),
				__("Jalankan")
			);
		});
	},
};

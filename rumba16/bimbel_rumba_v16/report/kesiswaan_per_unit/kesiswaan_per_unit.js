// ERP-KES-001 / B3 — filter + formatter warna report "Kesiswaan per Unit".
// Taruh di apps/rumba16/rumba16/bimbel_rumba_v16/report/kesiswaan_per_unit/
// (menimpa stub .js bila ada; dimuat otomatis oleh desk)

frappe.query_reports["Kesiswaan per Unit"] = {
	filters: [
		{
			fieldname: "periode",
			label: __("Periode (YYYY-MM)"),
			fieldtype: "Data",
			reqd: 1,
			default: frappe.datetime.now_date().slice(0, 7),
		},
	],

	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (!data) return value;

		const tgt = data.target_murid || 0;
		const aktif = data.murid_aktif || 0;

		// Murid Aktif & BTM: hijau capai target, merah di bawah, abu tanpa target
		if (["murid_aktif", "btm"].includes(column.fieldname)) {
			const color =
				tgt === 0 ? "#8d99a6" : aktif >= tgt ? "var(--green-600, #2e7d32)" : "var(--red-600, #c62828)";
			return `<span style="color:${color};font-weight:600">${value}</span>`;
		}

		// Δ vs bulan lalu: merah bila turun, hijau bila naik
		if (["delta", "delta_pct"].includes(column.fieldname) && data.delta != null) {
			const color = data.delta < 0 ? "var(--red-600, #c62828)" : "var(--green-600, #2e7d32)";
			return `<span style="color:${color}">${value}</span>`;
		}

		return value;
	},
};

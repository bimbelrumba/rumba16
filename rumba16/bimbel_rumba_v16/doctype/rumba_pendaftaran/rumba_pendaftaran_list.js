// Copyright (c) 2026, Yayasan Rumba Kita Indonesia and contributors
// For license information, please see license.txt

frappe.listview_settings["Rumba Pendaftaran"] = {
	// Warna indikator status di List View Rumba Pendaftaran.
	// Menunggu = merah, Disetujui = hijau.
	get_indicator: function (doc) {
		const colors = {
			Menunggu: "red",
			Disetujui: "green",
			Ditolak: "red",
			Batal: "gray",
		};
		const status = doc.status_pendaftaran;
		const color = colors[status] || "gray";
		return [__(status), color, "status_pendaftaran,=," + status];
	},
};

// Copyright (c) 2026, Yayasan Rumba Kita Indonesia and contributors
// For license information, please see license.txt

frappe.listview_settings["Rumba Pendaftaran"] = {
	// Warnai kolom Status Pendaftaran di List View (pola sama seperti Rumba Murid).
	// Field status_pendaftaran harus in_list_view=1 agar tampil sebagai kolom.
	// Menunggu = merah, Disetujui = hijau.
	formatters: {
		status_pendaftaran: function (value) {
			const colors = {
				Menunggu: "red",
				Disetujui: "green",
				Ditolak: "red",
				Batal: "gray",
			};
			const color = colors[value] || "gray";
			return `<span class="indicator-pill ${color}"><span class="indicator-dot"></span> ${__(
				value || ""
			)}</span>`;
		},
	},
};

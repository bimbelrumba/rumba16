frappe.ready(function () {
	// Tautan per-event: /daftar-event/new?event=EVT-26-00005
	// Ambil parameter `event` dari URL lalu isi field (read-only) secara otomatis.
	var params = new URLSearchParams(window.location.search);
	var ev = params.get("event");
	if (ev && frappe.web_form && frappe.web_form.set_value) {
		frappe.web_form.set_value("event", ev);
	}
});

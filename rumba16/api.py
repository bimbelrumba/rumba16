import frappe


@frappe.whitelist(allow_guest=True)
def get_rumba_units_by_kota(kode_kota=None):
    """Kembalikan daftar Rumba Unit aktif untuk sebuah kota.

    Menggantikan Server Script "Pilih Kota dan Unit" agar logikanya
    terversion di dalam kode app. Dipakai oleh web form publik
    /minat-belajar (cascade Kota -> Unit). allow_guest=True karena
    web form dapat diakses tanpa login.

    Argumen `kode_kota` boleh berupa name / kode_kota / nama_kota
    Rumba Kota; akan dinormalisasi ke name (kode, mis. "PKP").
    """
    kota_input = kode_kota
    resolved = kota_input

    if kota_input:
        kota_match = frappe.get_all(
            "Rumba Kota",
            or_filters=[
                ["Rumba Kota", "name", "=", kota_input],
                ["Rumba Kota", "kode_kota", "=", kota_input],
                ["Rumba Kota", "nama_kota", "=", kota_input],
            ],
            fields=["name", "kode_kota", "nama_kota"],
            limit_page_length=1,
            ignore_permissions=True,
        )
        if kota_match:
            resolved = kota_match[0].name

    return frappe.get_all(
        "Rumba Unit",
        filters={
            "kode_kota": resolved,
            "status_unit": ["!=", "Tutup"],
        },
        fields=["name", "nama_unit", "kode_unit", "email_unit", "kode_kota", "status_unit"],
        order_by="nama_unit asc",
        limit_page_length=100,
        ignore_permissions=True,
    )

@frappe.whitelist(allow_guest=True)
def get_rumba_wilayah_aktif():
	"""Pohon Provinsi -> Kota -> Unit untuk web form publik.
 
	Hanya menampilkan unit dengan status Aktif; provinsi/kota yang
	belum punya unit Aktif otomatis tidak muncul.
	Dipakai oleh web form: kelas-gratis & pendaftaran-murid-baru.
	"""
	units = frappe.get_all(
		"Rumba Unit",
		filters={"status_unit": "Aktif"},
		fields=[
			"name",
			"nama_unit",
			"kode_unit",
			"email_unit",
			"kode_kota",
			"nama_kota",
			"kode_provinsi",
			"nama_provinsi",
		],
		order_by="nama_unit asc",
	)
 
	provinsi_map = {}
	for unit in units:
		if not (unit.kode_provinsi and unit.kode_kota):
			continue
 
		provinsi = provinsi_map.setdefault(unit.kode_provinsi, {
			"kode_provinsi": unit.kode_provinsi,
			"nama_provinsi": unit.nama_provinsi,
			"kota": {},
		})
 
		kota = provinsi["kota"].setdefault(unit.kode_kota, {
			"kode_kota": unit.kode_kota,
			"nama_kota": unit.nama_kota,
			"unit": [],
		})
 
		kota["unit"].append({
			"name": unit.name,
			"nama_unit": unit.nama_unit,
			"kode_unit": unit.kode_unit,
			"email_unit": unit.email_unit,
		})
 
	hasil = []
	for provinsi in sorted(
		provinsi_map.values(), key=lambda p: p["nama_provinsi"] or ""
	):
		provinsi["kota"] = sorted(
			provinsi["kota"].values(), key=lambda k: k["nama_kota"] or ""
		)
		hasil.append(provinsi)
 
	return hasil

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

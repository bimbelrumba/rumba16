import frappe
from frappe.model.naming import make_autoname

# prefix per Contract Template; selain ini → penamaan bawaan (CON-.YYYY.-.#####)
PREFIX_BY_TEMPLATE = {
    "PMK Tutor RUMBA": "PMK",
    "PKWT Admin & Staf RUMBA": "PKWT",
}


def contract_autoname(doc, method=None):
    prefix = PREFIX_BY_TEMPLATE.get(doc.contract_template)
    if not prefix:
        return  # bukan PMK/PKWT → biarkan penamaan native berjalan

    if not doc.start_date:
        frappe.throw(
            "Tanggal mulai (start_date) wajib diisi sebelum menyimpan kontrak "
            "— dipakai untuk penomoran {0}-YYMM-#####.".format(prefix)
        )

    s = str(doc.start_date)          # 'YYYY-MM-DD'
    yymm = s[2:4] + s[5:7]           # '2607' utk Juli 2026
    doc.name = make_autoname("{0}-{1}-.#####".format(prefix, yymm))

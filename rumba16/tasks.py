# Copyright (c) 2026, Yayasan Rumba Kita Indonesia and contributors
# For license information, please see license.txt

"""Generator SPP bulanan berulang (Fase F / G10) — ERP-FIN-001.

Dipasang sebagai modul app: apps/rumba16/rumba16/tasks.py
Dipanggil oleh scheduler_events['monthly'] di hooks.py
("rumba16.tasks.generate_spp_bulanan"), atau manual via:

    frappe.call("rumba16.tasks.generate_spp_bulanan", {"periode": "2026-07"})

Keputusan desain yang diimplementasikan:
- F1  : tarif unit x program via Item Price (Item program x Price List unit);
        override per murid lewat Rumba Murid.nominal_spp.
- F3  : jatuh tempo = tanggal 15 bulan tagih, tanpa denda (SOP-FIN-011).
- F4  : invoice di-tag rumba_unit + rumba_murid untuk perhitungan tunggakan
        per unit (gerbang G6/G7).
- F7  : hanya murid status_murid='Aktif'; murid bersaldo di muka di-skip.
- Idempoten: lewati bila sudah ada invoice SPP untuk (murid, periode).

Prasyarat custom field (lihat README-DEPLOY-F2):
- Sales Invoice: rumba_unit (Link Rumba Unit), rumba_murid (Link Rumba Murid),
  spp_periode (Data).
- Rumba Program Belajar.item_spp, Rumba Unit.price_list_spp,
  Rumba Murid.nominal_spp, Rumba Murid.tanggal_mulai_spp (sudah dibuat F1).
- Rumba Murid.tanggal_spp_dimuka_sampai (opsional; dibaca defensif, diisi F6).
"""

import calendar
from datetime import date

import frappe
from frappe import _
from frappe.utils import flt, getdate, today

TANGGAL_JATUH_TEMPO = 15  # F3 — SOP-FIN-011: jatuh tempo tanggal 15


def _periode_sekarang():
    d = getdate(today())
    return f"{d.year:04d}-{d.month:02d}"


def _default_company():
    return frappe.defaults.get_user_default("Company") or frappe.defaults.get_global_default(
        "company"
    )


@frappe.whitelist()
def generate_spp_bulanan(periode=None, submit=1):
    """Buat tagihan SPP untuk seluruh murid Aktif pada `periode` (YYYY-MM).

    Aman dijalankan ulang (idempoten per murid+periode). Mengembalikan ringkasan
    {periode, dibuat, dilewati, gagal, ...}. Kegagalan per murid diisolasi
    (rollback + log_error) agar satu murid tidak menggagalkan batch.
    """
    periode = periode or _periode_sekarang()
    try:
        tahun, bulan = (int(x) for x in periode.split("-"))
        date(tahun, bulan, 1)
    except Exception:
        frappe.throw(_("Periode harus format YYYY-MM, mis. 2026-07."))

    submit = int(submit)
    posting_date = getdate(today())
    akhir_bulan = date(tahun, bulan, calendar.monthrange(tahun, bulan)[1])
    jatuh_tempo = date(tahun, bulan, TANGGAL_JATUH_TEMPO)
    # Hindari due_date < posting_date saat backfill periode lampau.
    if jatuh_tempo < posting_date:
        jatuh_tempo = posting_date

    company = _default_company()
    if not company:
        frappe.throw(_("Default Company belum diatur."))

    murid_list = frappe.get_all(
        "Rumba Murid",
        filters={"status_murid": "Aktif"},
        fields=[
            "name",
            "nama_lengkap",
            "customer",
            "nama_unit",
            "program_belajar",
            "nominal_spp",
            "tanggal_mulai_spp",
        ],
    )

    dibuat, dilewati, gagal = [], [], []

    for m in murid_list:
        try:
            alasan = _alasan_skip(m, akhir_bulan, periode)
            if alasan:
                dilewati.append([m.name, alasan])
                continue

            nama_inv = _buat_invoice_spp(
                m, company, posting_date, jatuh_tempo, periode, submit
            )
            dibuat.append(nama_inv)
            frappe.db.commit()
        except Exception:
            frappe.db.rollback()
            frappe.log_error(
                title=f"SPP {periode} gagal untuk {m.name}",
                message=frappe.get_traceback(),
            )
            gagal.append(m.name)

    ringkasan = {
        "periode": periode,
        "dibuat": len(dibuat),
        "dilewati": len(dilewati),
        "gagal": len(gagal),
        "detail_dilewati": dilewati[:100],
        "invoice": dibuat[:100],
    }
    frappe.logger().info(f"generate_spp_bulanan: {ringkasan}")
    return ringkasan


def _alasan_skip(m, akhir_bulan, periode):
    """Kembalikan alasan (str) bila murid harus dilewati, atau None bila ditagih."""
    if not m.get("customer"):
        return "tanpa Customer"
    if not m.get("program_belajar"):
        return "tanpa program"

    # F7 — siklus SPP belum mulai (murid baru sebelum tanggal_mulai_spp).
    mulai = m.get("tanggal_mulai_spp")
    if mulai and getdate(mulai) > akhir_bulan:
        return "siklus SPP belum mulai"

    # F6/F7 — saldo di muka menutup bulan ini (field opsional; diisi saat F6).
    dimuka = _saldo_dimuka_sampai(m["name"])
    if dimuka and getdate(dimuka) >= akhir_bulan:
        return "tercakup saldo di muka"

    # Idempoten — sudah ada invoice SPP untuk murid + periode (draft/submit).
    if frappe.db.exists(
        "Sales Invoice",
        {"rumba_murid": m["name"], "spp_periode": periode, "docstatus": ["<", 2]},
    ):
        return "sudah ada invoice periode ini"

    return None


def _saldo_dimuka_sampai(murid_name):
    """Baca tanggal_spp_dimuka_sampai secara defensif (field menyusul di F6)."""
    if frappe.get_meta("Rumba Murid").has_field("tanggal_spp_dimuka_sampai"):
        return frappe.db.get_value("Rumba Murid", murid_name, "tanggal_spp_dimuka_sampai")
    return None


def _resolve_tarif(m):
    """F1 — kembalikan (rate, item_spp). Override murid > Item Price unit x program."""
    item = frappe.db.get_value("Rumba Program Belajar", m["program_belajar"], "item_spp")
    if not item:
        frappe.throw(
            _("Program {0} belum punya Item SPP (item_spp).").format(m["program_belajar"])
        )

    # Override per murid (private/semi-private/keringanan).
    if flt(m.get("nominal_spp")) > 0:
        return flt(m["nominal_spp"]), item

    price_list = frappe.db.get_value("Rumba Unit", m["nama_unit"], "price_list_spp")
    if not price_list:
        frappe.throw(
            _("Unit {0} belum punya Price List SPP (price_list_spp).").format(m["nama_unit"])
        )

    rate = frappe.db.get_value(
        "Item Price",
        {"item_code": item, "price_list": price_list, "selling": 1},
        "price_list_rate",
    )
    if rate is None:
        frappe.throw(
            _("Item Price belum ada untuk {0} @ {1}.").format(item, price_list)
        )
    return flt(rate), item


def _buat_invoice_spp(m, company, posting_date, jatuh_tempo, periode, submit):
    rate, item = _resolve_tarif(m)
    cost_center = frappe.db.get_value("Rumba Unit", m["nama_unit"], "cost_center") if m.get("nama_unit") else None

    inv = frappe.new_doc("Sales Invoice")
    inv.customer = m["customer"]
    inv.company = company
    inv.posting_date = posting_date
    inv.set_posting_time = 1
    inv.due_date = jatuh_tempo
    # F4 — tag unit & murid untuk tunggakan per unit / per murid.
    inv.rumba_unit = m.get("nama_unit")
    inv.rumba_murid = m["name"]
    inv.spp_periode = periode
    if cost_center:
        inv.cost_center = cost_center
    inv.append(
        "items",
        {
            "item_code": item,
            "qty": 1,
            "rate": rate,
            "cost_center": cost_center,
            "description": _("SPP {0} - {1}").format(
                periode, m.get("nama_lengkap") or m["name"]
            ),
        },
    )
    inv.insert()
    if submit:
        inv.submit()
    return inv.name

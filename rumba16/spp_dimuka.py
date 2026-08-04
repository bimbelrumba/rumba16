# Copyright (c) 2026, Yayasan Rumba Kita Indonesia and contributors
# For license information, please see license.txt

"""SPP Dibayar di Muka — deferred revenue (Fase F / G10, F6) — ERP-FIN-001.

Dipasang sebagai modul app: apps/rumba16/rumba16/spp_dimuka.py

Mengimplementasikan SOP-FIN-012 (SPP Dibayar di Muka):
- 2–6 bulan; diskon 3 bln 5%, 6 bln 10%, lainnya 0%.
- Pendapatan diterima di muka = liability (akun deferred 2121.002); diakui
  bertahap tiap bulan oleh ERPNext "Process Deferred Accounting".
- Saldo hangus bila murid Berhenti sebelum periode habis (tanpa refund).

Manual / dipanggil dari controller:
    frappe.call("rumba16.spp_dimuka.buat_spp_dimuka",
                {"murid": "<id>", "jumlah_bulan": 6})
    frappe.call("rumba16.spp_dimuka.hanguskan_saldo_dimuka",
                {"murid": "<id>", "tanggal_efektif": "2026-09-30"})

Prasyarat (lihat README-DEPLOY-F6):
- Akun leaf: 2121.002 (deferred liability), 4320.000 (Pendapatan SPP),
  4330.000 (Saldo Hangus) di company.
- Custom field Rumba Murid.tanggal_spp_dimuka_sampai (Date).
- Accounts Settings: "Book Deferred Entries Based On" = Months (penyelarasan
  perhitungan hangus berbasis bulan).
- Modul rumba16.tasks (generator F2) terpasang — fungsi ini memakai
  _resolve_tarif & _default_company dari sana.
"""

import frappe
from frappe import _
from frappe.utils import (
    add_months,
    flt,
    get_first_day,
    get_last_day,
    getdate,
    today,
)

from rumba16.tasks import _default_company, _resolve_tarif

# Nomor akun leaf (di-resolve per company agar portabel lintas CoA/abbr).
AKUN_DEFERRED = "2121.002"   # Pendapatan Diterima di Muka SPP (Liability)
AKUN_HANGUS = "4330.000"     # Pendapatan SPP Saldo Hangus (Income)

# SOP-FIN-012 §4.2 — diskon hanya 3 bln & 6 bln.
DISKON_PERSEN = {3: 5.0, 6: 10.0}

MIN_BULAN, MAKS_BULAN = 2, 6


def _diskon_persen(jumlah_bulan):
    return DISKON_PERSEN.get(int(jumlah_bulan), 0.0)


def _akun(company, account_number):
    nama = frappe.db.get_value(
        "Account",
        {"account_number": account_number, "company": company, "is_group": 0},
        "name",
    )
    if not nama:
        frappe.throw(
            _("Akun leaf nomor {0} belum ada di company {1}.").format(
                account_number, company
            )
        )
    return nama


@frappe.whitelist()
def buat_spp_dimuka(murid, jumlah_bulan, mulai=None, submit=1):
    """Buat satu Sales Invoice SPP di muka (deferred revenue) untuk `murid`.

    `jumlah_bulan` 2–6; `mulai` (opsional) = bulan awal periode (YYYY-MM-DD,
    dibulatkan ke awal bulan; default bulan berjalan). Mengembalikan ringkasan.
    """
    jumlah_bulan = int(jumlah_bulan)
    submit = int(submit)
    if jumlah_bulan < MIN_BULAN or jumlah_bulan > MAKS_BULAN:
        frappe.throw(_("SPP di muka hanya {0}–{1} bulan (SOP-FIN-012).").format(
            MIN_BULAN, MAKS_BULAN))

    m = frappe.db.get_value(
        "Rumba Murid",
        murid,
        ["name", "nama_lengkap", "customer", "nama_unit", "program_belajar", "nominal_spp"],
        as_dict=True,
    )
    if not m:
        frappe.throw(_("Murid {0} tidak ditemukan.").format(murid))
    if not m.customer:
        frappe.throw(_("Murid {0} belum punya Customer.").format(murid))

    company = _default_company()
    rate, item = _resolve_tarif(m)  # tarif per bulan (override murid > Item Price)
    cost_center = frappe.db.get_value("Rumba Unit", m.nama_unit, "cost_center") if m.nama_unit else None

    mulai_date = get_first_day(getdate(mulai) if mulai else getdate(today()))
    akhir_date = get_last_day(add_months(mulai_date, jumlah_bulan - 1))
    diskon_pct = _diskon_persen(jumlah_bulan)
    deferred_acc = _akun(company, AKUN_DEFERRED)

    # Diskon dihitung eksplisit ke tarif net (deterministik). discount_percentage
    # bawaan ERPNext bekerja atas price_list_rate, bukan rate manual — jadi tidak
    # dipakai di sini agar diskon pasti terterap.
    rate_net = flt(flt(rate) * (1 - diskon_pct / 100.0), 2)

    inv = frappe.new_doc("Sales Invoice")
    inv.customer = m.customer
    inv.company = company
    inv.posting_date = getdate(today())
    inv.set_posting_time = 1
    inv.due_date = getdate(today())  # dibayar di muka — jatuh tempo saat transaksi
    inv.rumba_unit = m.nama_unit
    inv.rumba_murid = m.name
    inv.spp_periode = f"DIMUKA {mulai_date:%Y-%m}..{akhir_date:%Y-%m}"
    if cost_center:
        inv.cost_center = cost_center
    inv.append(
        "items",
        {
            "item_code": item,
            "qty": jumlah_bulan,
            "rate": rate_net,  # tarif per bulan setelah diskon
            "cost_center": cost_center,
            # F6 — deferred revenue per baris (BUKAN global di Item; SPP bulanan
            # reguler tetap diakui langsung).
            "enable_deferred_revenue": 1,
            "deferred_revenue_account": deferred_acc,
            "service_start_date": mulai_date,
            "service_end_date": akhir_date,
            "description": _(
                "SPP di muka {0} bln ({1} s.d. {2}) — tarif normal {3}/bln, "
                "diskon {4}% (SOP-FIN-012) - {5}"
            ).format(
                jumlah_bulan,
                mulai_date.strftime("%Y-%m"),
                akhir_date.strftime("%Y-%m"),
                flt(rate),
                diskon_pct,
                m.nama_lengkap or m.name,
            ),
        },
    )
    inv.insert()
    if submit:
        inv.submit()

    # Tandai murid tercakup s.d. akhir periode → generator bulanan (F2) skip.
    frappe.db.set_value("Rumba Murid", m.name, "tanggal_spp_dimuka_sampai", akhir_date)

    return {
        "invoice": inv.name,
        "jumlah_bulan": jumlah_bulan,
        "diskon_persen": diskon_pct,
        "tarif_normal_per_bulan": flt(rate),
        "tarif_net_per_bulan": rate_net,
        "service_start": str(mulai_date),
        "service_end": str(akhir_date),
        "total_setelah_diskon": flt(inv.grand_total),
    }

@frappe.whitelist()
def hanguskan_saldo_dimuka(murid, tanggal_efektif=None):
    """Hanguskan sisa SPP di muka saat murid Berhenti (SOP-FIN-012 §4.4/§6.7).

    Untuk tiap invoice SPP di muka murid yang periodenya belum habis:
    - Setel service_stop_date = tanggal_efektif (hentikan pengakuan lanjutan).
    - Hitung sisa belum diakui (proporsi bulan) → Journal Entry:
      Debit  Pendapatan Diterima di Muka SPP (liability)
      Kredit Pendapatan SPP Saldo Hangus (income).
    TANPA refund. Idempoten lewat field service_stop_date.
    """
    tgl = getdate(tanggal_efektif) if tanggal_efektif else getdate(today())
    company = _default_company()
    deferred_acc = _akun(company, AKUN_DEFERRED)
    hangus_acc = _akun(company, AKUN_HANGUS)

    invoices = frappe.get_all(
        "Sales Invoice",
        filters={"rumba_murid": murid, "docstatus": 1},
        fields=["name"],
    )

    total_hangus = 0.0
    diproses = []
    for si in invoices:
        doc = frappe.get_doc("Sales Invoice", si.name)
        for it in doc.items:
            if not it.get("enable_deferred_revenue"):
                continue
            if not it.service_end_date or getdate(it.service_end_date) <= tgl:
                continue  # periode sudah habis — tidak ada yang hangus
            if it.get("service_stop_date"):
                continue  # sudah pernah dihanguskan (idempoten)

            sisa = _sisa_belum_diakui(it, tgl)
            if sisa <= 0:
                continue

            # Hentikan pengakuan lanjutan oleh Process Deferred Accounting.
            it.db_set("service_stop_date", tgl)

            _buat_je_hangus(company, deferred_acc, hangus_acc, sisa, murid, doc.name, tgl)
            total_hangus += sisa
            diproses.append([doc.name, sisa])

    return {"murid": murid, "tanggal_efektif": str(tgl),
            "total_hangus": total_hangus, "detail": diproses}


def _sisa_belum_diakui(item, tgl):
    """Sisa nilai deferred yang belum diakui (proporsi bulan layanan)."""
    total_net = flt(item.base_net_amount or item.net_amount or item.amount)
    mulai = getdate(item.service_start_date)
    akhir = getdate(item.service_end_date)
    total_bulan = _hitung_bulan(mulai, akhir)
    if total_bulan <= 0:
        return 0.0
    if tgl <= mulai:
        bulan_diakui = 0
    else:
        bulan_diakui = min(_hitung_bulan(mulai, tgl), total_bulan)
    sisa = total_net * (total_bulan - bulan_diakui) / total_bulan
    return flt(sisa, 2)


def _hitung_bulan(d1, d2):
    return (d2.year - d1.year) * 12 + (d2.month - d1.month) + 1


def _buat_je_hangus(company, deferred_acc, hangus_acc, jumlah, murid, invoice, tgl):
    je = frappe.new_doc("Journal Entry")
    je.posting_date = tgl
    je.company = company
    je.user_remark = _(
        "Saldo SPP di muka hangus — murid {0}, invoice {1} (SOP-FIN-012 4.4, tanpa refund)"
    ).format(murid, invoice)
    je.append("accounts", {"account": deferred_acc, "debit_in_account_currency": jumlah})
    je.append("accounts", {"account": hangus_acc, "credit_in_account_currency": jumlah})
    je.insert()
    je.submit()
    return je.name

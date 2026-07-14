# Copyright (c) 2026, RUMBA
# ERP-KES-001 / B3 — Script Report "Kesiswaan per Unit".
# GANTIKAN stub kesiswaan_per_unit.py di
#   apps/rumba16/rumba16/bimbel_rumba_v16/report/kesiswaan_per_unit/
# Indentasi SPASI (4). Timpa file UTUH.
#
# Perilaku:
# - Periode ber-snapshot -> baca snapshot (angka beku).
# - Periode berjalan tanpa snapshot -> hitung LIVE (reuse _hitung_angka_unit
#   dari controller B2) + banner PRA-FINAL.
# - Periode lampau tanpa snapshot -> kosong + pesan.
# - Kolom pembanding: murid aktif 1 & 2 periode sebelumnya (dari snapshot).
# - Baris TOTAL + report_summary (Total Aktif, N/T vs bulan lalu, %).
# - Juga memuat method Number Card "Unit Belum Capai Target".
# - SCOPING (keputusan Sisco 14 Jul 2026): memakai frappe.get_list (menghormati
#   User Permission) — Admin/Kepala Unit ber-User Permission Rumba Unit hanya
#   melihat unitnya; Finance/Pusat tanpa UP melihat semua (pola ERP-PERM-001).

import frappe
from frappe import _
from frappe.utils import getdate, today

from rumba16.bimbel_rumba_v16.doctype.rumba_kesiswaan_bulanan.rumba_kesiswaan_bulanan import (
    _hitung_angka_unit,
    _periode_sebelumnya,
)

ANGKA = [
    "sba", "sml", "pu", "bd", "off", "lulus", "cuti", "cuti_p",
    "murid_aktif", "target_murid", "btm", "estimasi_bulan_depan",
]


def execute(filters=None):
    filters = frappe._dict(filters or {})
    periode = (filters.get("periode") or today()[:7]).strip()

    rows, mode = _get_rows(periode)
    prev1 = _snap_map(_periode_sebelumnya(periode))
    prev2 = _snap_map(_periode_sebelumnya(_periode_sebelumnya(periode)))

    data = []
    tot = {k: 0 for k in ANGKA}
    tot_lalu = 0
    ada_lalu = False

    for r in sorted(rows, key=lambda x: (x.get("unit") or "")):
        a1 = prev1.get(r["unit"])
        r["aktif_lalu"] = a1
        r["aktif_2lalu"] = prev2.get(r["unit"])
        if a1 is not None:
            ada_lalu = True
            tot_lalu += a1
            r["delta"] = (r.get("murid_aktif") or 0) - a1
            r["delta_pct"] = f"{round(r['delta'] / a1 * 100)}%" if a1 else None
        for k in ANGKA:
            tot[k] += r.get(k) or 0
        data.append(r)

    # Baris TOTAL
    if data:
        total_row = dict(tot)
        total_row["unit"] = _("TOTAL")
        total_row["aktif_lalu"] = tot_lalu if ada_lalu else None
        if ada_lalu:
            total_row["delta"] = tot["murid_aktif"] - tot_lalu
            total_row["delta_pct"] = (
                f"{round(total_row['delta'] / tot_lalu * 100)}%" if tot_lalu else None
            )
        data.append(total_row)

    message = None
    if mode == "live":
        message = _(
            "PRA-FINAL: periode {0} belum di-snapshot — angka dihitung live dan masih bisa berubah. "
            "Jalankan Generate Snapshot pada tanggal cut-off untuk membekukan."
        ).format(periode)
    elif mode == "kosong":
        message = _(
            "Tidak ada snapshot untuk periode {0}. Snapshot periode lampau dapat diinput manual "
            "(status Manual) untuk saldo awal."
        ).format(periode)

    report_summary = _summary(tot, tot_lalu, ada_lalu) if data else None

    return _columns(), data, message, None, report_summary


def _get_rows(periode):
    # get_list (BUKAN get_all): menerapkan permission + User Permission per unit
    snaps = frappe.get_list(
        "Rumba Kesiswaan Bulanan",
        filters={"periode": periode},
        fields=["unit", "status_snapshot"] + ANGKA,
    )
    if snaps:
        return snaps, "snapshot"

    if periode == today()[:7]:
        cutoff = getdate(today())
        rows = []
        for u in frappe.get_list("Rumba Unit", fields=["name", "target_murid_minimal"]):
            angka = _hitung_angka_unit(u, periode, cutoff)
            angka["unit"] = u.name
            angka["btm"] = (angka.get("murid_aktif") or 0) - (angka.get("target_murid") or 0)
            rows.append(angka)
        return rows, "live"

    return [], "kosong"


def _snap_map(periode):
    return {
        s.unit: s.murid_aktif or 0
        for s in frappe.get_list(
            "Rumba Kesiswaan Bulanan",
            filters={"periode": periode},
            fields=["unit", "murid_aktif"],
        )
    }


def _summary(tot, tot_lalu, ada_lalu):
    summary = [
        {"value": tot["murid_aktif"], "label": _("Total Murid Aktif"), "datatype": "Int"},
    ]
    if ada_lalu:
        delta = tot["murid_aktif"] - tot_lalu
        summary.append(
            {
                "value": delta,
                "label": _("N/T vs Bulan Lalu"),
                "datatype": "Int",
                "indicator": "Red" if delta < 0 else "Green",
            }
        )
        if tot_lalu:
            summary.append(
                {
                    "value": f"{round(delta / tot_lalu * 100)}%",
                    "label": _("N/T %"),
                    "datatype": "Data",
                    "indicator": "Red" if delta < 0 else "Green",
                }
            )
    return summary


def _columns():
    def c(fieldname, label, fieldtype="Int", width=70, options=None):
        col = {"fieldname": fieldname, "label": label, "fieldtype": fieldtype, "width": width}
        if options:
            col["options"] = options
        return col

    return [
        c("unit", _("Unit"), "Link", 140, "Rumba Unit"),
        c("sba", _("SBA")),
        c("sml", _("SML")),
        c("pu", _("PU")),
        c("bd", _("BD")),
        c("off", _("OFF")),
        c("lulus", _("LULUS")),
        c("cuti", _("CUTI")),
        c("cuti_p", _("CUTI (P)"), width=80),
        c("murid_aktif", _("Murid Aktif"), width=95),
        c("target_murid", _("Target"), width=75),
        c("btm", _("BTM"), width=70),
        c("estimasi_bulan_depan", _("Est. Bln Depan"), width=110),
        c("aktif_lalu", _("Aktif Bln Lalu"), width=105),
        c("aktif_2lalu", _("Aktif 2 Bln Lalu"), width=115),
        c("delta", _("Δ"), width=60),
        c("delta_pct", _("Δ %"), "Data", 60),
    ]


# ---------------------------------------------------------------------------
# Number Card "Unit Belum Capai Target" (type Custom)
# ---------------------------------------------------------------------------

@frappe.whitelist()
def unit_belum_capai_target():
    """Jumlah unit ber-target yang belum capai target pada periode snapshot terbaru.
    Memakai get_list → ikut ter-scope User Permission (Admin Unit: unitnya saja)."""
    terbaru = frappe.get_list(
        "Rumba Kesiswaan Bulanan",
        fields=["periode"],
        order_by="periode desc",
        limit_page_length=1,
    )
    if not terbaru:
        return {"value": 0, "fieldtype": "Int"}
    n = len(
        frappe.get_list(
            "Rumba Kesiswaan Bulanan",
            filters={
                "periode": terbaru[0].periode,
                "target_tercapai": 0,
                "target_murid": (">", 0),
            },
            fields=["name"],
        )
    )
    return {"value": n, "fieldtype": "Int"}

# Copyright (c) 2026, RUMBA
# ERP-KES-001 / B2 — Controller & generator snapshot kesiswaan bulanan.
# GANTIKAN stub rumba_kesiswaan_bulanan.py di
#   apps/rumba16/rumba16/bimbel_rumba_v16/doctype/rumba_kesiswaan_bulanan/
# Indentasi file ini SPASI (4) — aman ditimpa utuh (jangan tempel sebagian).

import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import getseries
from frappe.utils import add_days, add_months, get_last_day, getdate, today

# Field angka yang dibekukan untuk snapshot Final (guard_beku)
ANGKA_FIELDS = [
    "murid_aktif", "sba", "sml", "pu", "bd", "off", "lulus",
    "cuti", "cuti_p", "target_murid", "estimasi_bulan_depan",
]


class RumbaKesiswaanBulanan(Document):
    def autoname(self):
        # KSW-{YYMM}{###}, contoh KSW-2607001 = snapshot Juli 2026 urutan 1.
        # Counter getseries independen per bulan (pola ERP-CRM-002 / Fase D).
        self.validasi_periode()  # nama bergantung periode -> validasi lebih awal
        yymm = self.periode[2:4] + self.periode[5:7]
        self.name = f"KSW-{yymm}" + getseries(f"KSW-{yymm}", 3)

    def validate(self):
        self.validasi_periode()
        self.validasi_duplikat()
        self.hitung_derived()
        self.guard_beku()

    def validasi_periode(self):
        if not re.match(r"^\d{4}-(0[1-9]|1[0-2])$", self.periode or ""):
            frappe.throw(_("Periode harus berformat YYYY-MM, contoh 2026-07."))

    def validasi_duplikat(self):
        dup = frappe.db.exists(
            "Rumba Kesiswaan Bulanan",
            {"unit": self.unit, "periode": self.periode, "name": ("!=", self.name or "")},
        )
        if dup:
            frappe.throw(
                _("Snapshot {0} periode {1} sudah ada ({2}). Hapus dulu bila perlu regenerate.").format(
                    self.unit, self.periode, dup
                )
            )

    def hitung_derived(self):
        self.btm = (self.murid_aktif or 0) - (self.target_murid or 0)
        self.target_tercapai = (
            1 if (self.target_murid or 0) > 0 and (self.murid_aktif or 0) >= self.target_murid else 0
        )

    def guard_beku(self):
        """Snapshot Final = beku. Koreksi angka -> hapus record lalu generate ulang.
        Catatan tetap boleh diedit; snapshot Manual bebas diedit."""
        if self.is_new() or self.status_snapshot != "Final":
            return
        db_doc = frappe.db.get_value(
            "Rumba Kesiswaan Bulanan", self.name, ANGKA_FIELDS + ["unit", "periode"], as_dict=True
        )
        if not db_doc:
            return
        berubah = [f for f in ANGKA_FIELDS if (self.get(f) or 0) != (db_doc.get(f) or 0)]
        if self.unit != db_doc.unit or self.periode != db_doc.periode:
            berubah.append("unit/periode")
        if berubah:
            frappe.throw(
                _("Snapshot Final bersifat beku (basis insentif/audit). Field berubah: {0}. "
                  "Untuk koreksi: hapus record ini lalu Generate Snapshot ulang.").format(", ".join(berubah))
            )


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

@frappe.whitelist()
def generate_snapshot(periode=None, tanggal_cutoff=None):
    """Buat snapshot kesiswaan utk SEMUA unit pada `periode` (YYYY-MM).
    Idempoten: unit yang sudah punya snapshot periode itu dilewati."""
    frappe.only_for(("System Manager", "Rumba Finance"))

    cutoff = getdate(tanggal_cutoff or today())
    periode = periode or cutoff.strftime("%Y-%m")

    dibuat, dilewati = [], []
    for u in frappe.get_all("Rumba Unit", fields=["name", "target_murid_minimal"]):
        if frappe.db.exists("Rumba Kesiswaan Bulanan", {"unit": u.name, "periode": periode}):
            dilewati.append(u.name)
            continue
        angka = _hitung_angka_unit(u, periode, cutoff)
        doc = frappe.get_doc(
            dict(
                doctype="Rumba Kesiswaan Bulanan",
                unit=u.name,
                periode=periode,
                tanggal_cutoff=cutoff,
                status_snapshot="Final",
                **angka,
            )
        )
        doc.insert(ignore_permissions=False)
        dibuat.append(u.name)

    return {"periode": periode, "dibuat": len(dibuat), "dilewati": len(dilewati)}


def _periode_sebelumnya(periode):
    tahun, bulan = int(periode[:4]), int(periode[5:7])
    return f"{tahun - 1}-12" if bulan == 1 else f"{tahun}-{bulan - 1:02d}"


def _window(unit, periode, cutoff):
    """Window transaksional: > cutoff snapshot periode sebelumnya unit ini,
    <= cutoff berjalan. Fallback: 1 bulan kalender ke belakang."""
    prev_cutoff = frappe.db.get_value(
        "Rumba Kesiswaan Bulanan",
        {"unit": unit, "periode": _periode_sebelumnya(periode)},
        "tanggal_cutoff",
    )
    start_eksklusif = getdate(prev_cutoff) if prev_cutoff else add_months(cutoff, -1)
    return add_days(start_eksklusif, 1), cutoff  # inklusif start..end


def _hitung_angka_unit(u, periode, cutoff):
    unit = u.name
    w_start, w_end = _window(unit, periode, cutoff)

    murid_aktif = frappe.db.count("Rumba Murid", {"status_murid": "Aktif", "nama_unit": unit})

    # SBA / SML — pendaftaran Disetujui dalam window (basis tanggal_persetujuan)
    pendaftaran_window = {
        "status_pendaftaran": "Disetujui",
        "nama_unit": unit,
        "tanggal_persetujuan": ("between", [str(w_start), str(w_end) + " 23:59:59"]),
    }
    total_disetujui = frappe.db.count("Rumba Pendaftaran", pendaftaran_window)
    sml = frappe.db.count(
        "Rumba Pendaftaran", dict(pendaftaran_window, jenis_pendaftaran="Masuk Lagi")
    )
    sba = total_disetujui - sml  # jenis kosong (record lama) terhitung Siswa Baru

    # PU masuk — mutasi Selesai ke unit ini
    pu = frappe.db.count(
        "Rumba Mutasi",
        {
            "status_mutasi": "Selesai",
            "unit_tujuan": unit,
            "tanggal_mutasi": ("between", [w_start, w_end]),
        },
    )

    # BD — sudah bayar, mulai belajar setelah cut-off
    bd = frappe.db.count(
        "Rumba Pendaftaran",
        {
            "nama_unit": unit,
            "status_pendaftaran": ("in", ["Menunggu", "Disetujui"]),
            "status_pembayaran": ("in", ["Lunas", "Dibayar Sebagian"]),
            "tanggal_mulai_belajar": (">", w_end),
        },
    )

    # OFF — pengunduran diri Final efektif dalam window
    off = frappe.db.count(
        "Rumba Pengunduran Diri",
        {
            "status_pengunduran": "Final",
            "nama_unit": unit,
            "tanggal_efektif": ("between", [w_start, w_end]),
        },
    )

    # LULUS — ujian kenaikan Level 3 Final+Lulus dalam window (Calistung / E2)
    lulus = frappe.db.sql(
        """
        SELECT COUNT(*)
        FROM `tabRumba Ujian Kenaikan Level` uj
        INNER JOIN `tabRumba Murid` m ON m.name = uj.murid
        WHERE uj.status_ujian = 'Final' AND uj.hasil = 'Lulus'
          AND uj.level_diuji = 'Level 3'
          AND uj.tanggal_ujian BETWEEN %(ws)s AND %(we)s
          AND m.nama_unit = %(unit)s
        """,
        {"ws": w_start, "we": w_end, "unit": unit},
    )[0][0]

    # CUTI / CUTI (P) — potret saat snapshot
    cuti = frappe.db.count(
        "Rumba Murid", {"status_murid": "Cuti", "nama_unit": unit, "biaya_cuti_lunas": 1}
    )
    cuti_p = frappe.db.count(
        "Rumba Murid", {"status_murid": "Cuti", "nama_unit": unit, "biaya_cuti_lunas": 0}
    )

    # Estimasi bulan depan = aktif + BD yang mulai bulan depan - pengunduran Diajukan efektif s.d. akhir bulan depan
    akhir_bulan_depan = get_last_day(add_months(w_end, 1))
    bd_bulan_depan = frappe.db.count(
        "Rumba Pendaftaran",
        {
            "nama_unit": unit,
            "status_pendaftaran": ("in", ["Menunggu", "Disetujui"]),
            "status_pembayaran": ("in", ["Lunas", "Dibayar Sebagian"]),
            "tanggal_mulai_belajar": ("between", [add_days(w_end, 1), akhir_bulan_depan]),
        },
    )
    off_diajukan = frappe.db.count(
        "Rumba Pengunduran Diri",
        {
            "status_pengunduran": "Diajukan",
            "nama_unit": unit,
            "tanggal_efektif": ("<=", akhir_bulan_depan),
        },
    )

    return {
        "murid_aktif": murid_aktif,
        "sba": sba,
        "sml": sml,
        "pu": pu,
        "bd": bd,
        "off": off,
        "lulus": lulus,
        "cuti": cuti,
        "cuti_p": cuti_p,
        "target_murid": u.target_murid_minimal or 0,
        "estimasi_bulan_depan": murid_aktif + bd_bulan_depan - off_diajukan,
    }

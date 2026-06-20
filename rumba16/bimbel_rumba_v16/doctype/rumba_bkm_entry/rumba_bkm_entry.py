# Copyright (c) 2026, Yayasan Rumba Kita Indonesia and contributors
# For license information, please see license.txt
#
# TARUH FILE INI DI SERVER:
#   ~/frappe-bench/apps/rumba16/rumba16/bimbel_rumba_v16/doctype/rumba_bkm_entry/rumba_bkm_entry.py
# lalu `bench --site dev.bimbelrumba.id migrate` atau restart; controller aktif.

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import getseries
from frappe.utils import getdate, nowdate


def recompute_saldo_bintang(murid):
    """Hitung ulang saldo bintang murid = SUM bintang dari BKM Entry yang sudah
    'Disetujui' (idempoten). Dipanggil tiap BKM disimpan/diubah/dihapus.

    Pendekatan recompute (bukan increment) dipilih agar tahan terhadap edit
    bintang, perubahan workflow_state (Disetujui -> Revisi), dan penghapusan —
    nilai selalu konsisten dengan data sumber. Konsisten keputusan user E3:
    saldo hidup di Rumba Murid + Query Report rekap bintang.
    """
    if not murid:
        return
    total = frappe.db.sql(
        """
        SELECT COALESCE(SUM(bintang), 0)
        FROM `tabRumba BKM Entry`
        WHERE murid = %s AND workflow_state = 'Disetujui'
        """,
        murid,
    )[0][0]
    frappe.db.set_value(
        "Rumba Murid", murid, "saldo_bintang", int(total or 0), update_modified=False
    )


class RumbaBKMEntry(Document):
    """Fase E / E3 — BKM & Bintang (ERP-ACAD-001, B1-B3).

    DocType terpisah (keputusan A4) yang menaut ke Rumba Sesi Kelas. Satu record
    per murid per sesi KBM. Gerbang: murid wajib berstatus 'Hadir' pada presensi
    sesi terkait (B1). Approval ARU via Workflow 'Persetujuan BKM' (workflow_state,
    keputusan user E3 — sejalan A7 presensi). Saldo bintang di Rumba Murid
    di-recompute dari entri 'Disetujui'.

    Cara input utama (keputusan user E3): auto-generate dari Sesi Kelas yang sudah
    Disetujui via tombol "Buat BKM dari Sesi" (lihat buat_dari_sesi()). Entry
    manual tetap diperbolehkan untuk koreksi/susulan.
    """

    def autoname(self):
        # getseries per-prefix (pelajaran G6/G7; pola Fase D & E1/E2).
        tahun = getdate(self.tanggal_sesi or nowdate()).strftime("%Y")
        prefix = f"BKM-{tahun}-"
        self.name = prefix + getseries(prefix, 5)

    def validate(self):
        self.set_konteks_dari_sesi()
        self.set_data_murid()
        self.set_paraf_default()
        self.validasi_murid_hadir()
        self.validasi_kelengkapan_saat_ajukan()

    def on_update(self):
        recompute_saldo_bintang(self.murid)

    def after_delete(self):
        recompute_saldo_bintang(self.murid)

    # ------------------------------------------------------------------ helpers

    def set_konteks_dari_sesi(self):
        """fetch_from menangani UI; isi eksplisit di server agar tahan
        pembuatan via API/bulk (buat_dari_sesi)."""
        if not self.sesi_kelas:
            return
        sesi = frappe.db.get_value(
            "Rumba Sesi Kelas",
            self.sesi_kelas,
            ["kelas", "tanggal_sesi", "guru"],
            as_dict=True,
        )
        if not sesi:
            return
        if not self.kelas:
            self.kelas = sesi.kelas
        if not self.tanggal_sesi:
            self.tanggal_sesi = sesi.tanggal_sesi
        if not self.guru:
            self.guru = sesi.guru

    def set_data_murid(self):
        if not self.murid:
            return
        m = frappe.db.get_value(
            "Rumba Murid",
            self.murid,
            ["nama_lengkap", "program_belajar", "level_saat_ini"],
            as_dict=True,
        )
        if not m:
            return
        self.nama_murid = m.nama_lengkap
        self.program = m.program_belajar
        # Level default dari level murid (untuk Calistung "Lv.x") bila kosong;
        # tetap editable oleh guru.
        if not self.level and m.level_saat_ini:
            self.level = m.level_saat_ini

    def set_paraf_default(self):
        if not self.paraf_guru and self.guru:
            self.paraf_guru = self.guru

    # --- B1 gerbang: BKM hanya untuk murid berstatus Hadir di sesi ---
    def validasi_murid_hadir(self):
        if not (self.sesi_kelas and self.murid):
            return
        rows = frappe.db.sql(
            """
            SELECT status_kehadiran
            FROM `tabRumba Presensi Murid`
            WHERE parent = %s AND parenttype = 'Rumba Sesi Kelas' AND murid = %s
            LIMIT 1
            """,
            (self.sesi_kelas, self.murid),
        )
        if not rows:
            frappe.throw(
                _("Murid {0} tidak terdaftar pada presensi sesi {1}.").format(
                    frappe.bold(self.nama_murid or self.murid),
                    frappe.bold(self.sesi_kelas),
                ),
                title=_("Murid Bukan Anggota Sesi"),
            )
        status = rows[0][0]
        if status != "Hadir":
            frappe.throw(
                _(
                    "BKM hanya untuk murid berstatus Hadir. Status {0} pada sesi "
                    "ini: {1}."
                ).format(
                    frappe.bold(self.nama_murid or self.murid),
                    frappe.bold(status or "kosong"),
                ),
                title=_("Murid Tidak Hadir"),
            )

    # --- gerbang approval: kegiatan wajib sebelum diajukan/disetujui ---
    def validasi_kelengkapan_saat_ajukan(self):
        state = (self.get("workflow_state") or "").strip()
        if state not in ("Diajukan", "Disetujui"):
            return
        if not (self.kegiatan or "").strip():
            frappe.throw(
                _(
                    "Kolom Kegiatan wajib diisi sebelum BKM diajukan/disetujui."
                ),
                title=_("Kegiatan Belum Diisi"),
            )


@frappe.whitelist()
def buat_dari_sesi(sesi_kelas):
    """Auto-generate BKM Entry (status awal Draft) untuk setiap murid berstatus
    'Hadir' pada sesi yang SUDAH Disetujui (keputusan user E3 — mitigasi A4).

    Idempoten: melewati murid yang sudah punya BKM untuk sesi ini. Dipanggil
    dari tombol "Buat BKM dari Sesi" di form Rumba Sesi Kelas.
    """
    sesi = frappe.get_doc("Rumba Sesi Kelas", sesi_kelas)
    if (sesi.get("workflow_state") or "") != "Disetujui":
        frappe.throw(
            _("BKM hanya dapat dibuat dari sesi yang sudah Disetujui (ARU).")
        )

    dibuat = 0
    dilewati = 0
    for row in sesi.presensi:
        if row.status_kehadiran != "Hadir":
            continue
        if frappe.db.exists(
            "Rumba BKM Entry", {"sesi_kelas": sesi.name, "murid": row.murid}
        ):
            dilewati += 1
            continue
        doc = frappe.new_doc("Rumba BKM Entry")
        doc.sesi_kelas = sesi.name
        doc.murid = row.murid
        doc.insert()
        dibuat += 1

    frappe.db.commit()
    return {"dibuat": dibuat, "dilewati": dilewati}

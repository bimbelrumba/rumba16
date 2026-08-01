# Copyright (c) 2026, Yayasan Rumba Kita Indonesia and contributors
# For license information, please see license.txt
#
# TARUH FILE INI DI SERVER:
#   ~/frappe-bench/apps/rumba16/rumba16/bimbel_rumba_v16/doctype/rumba_sesi_kelas/rumba_sesi_kelas.py
# (menimpa controller default class-pass). Lalu `bench --site dev.bimbelrumba.id migrate`
# atau cukup restart; controller langsung aktif.

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import getseries
from frappe.utils import getdate, today


class RumbaSesiKelas(Document):
    """Fase E / E1 — Sesi Kelas + Presensi Murid (ERP-ACAD-001, A1-A8).

    Dwifungsi: presensi murid (child) + jam mengajar tutor (guru/durasi/status)
    untuk rekap F-GAJ-01. Approval ARU ditangani Workflow "Persetujuan Presensi
    Sesi" (A7); rekap hanya menghitung sesi workflow_state == 'Disetujui'.
    """

    def autoname(self):
        tahun = getdate(self.tanggal_sesi or nowdate()).strftime("%Y")
        prefix = f"SES-{tahun}-"
        self.name = prefix + getseries(prefix, 5)

    def before_insert(self):
        self.set_default_awal()
        self.set_guru_default()

    def onload(self):
        self.set_guru_default()

    def validate(self):
        self.set_default_awal()
        self.set_guru_default()
        self.set_durasi_menit()
        self.cegah_duplikat_sesi()
        self.isi_presensi_dari_roster()
        self.hitung_rekap()
        self.validasi_status_sesi()
        self.validasi_kelengkapan_saat_ajukan()
        self._kunci_tanggal_sesi_untuk_tutor()

    def on_update(self):
        # ERP-LIFE-001b — aktivasi murid dari presensi Hadir pada sesi Disetujui.
        self.aktivasi_murid_dari_presensi()

    def set_default_awal(self):
        if not self.tanggal_sesi:
            self.tanggal_sesi = nowdate()
        if not self.status_sesi:
            self.status_sesi = "Terlaksana"

    # --- Durasi menit deterministik dari jenis kelas (read-only, auto) ---
    # Reguler & Semi-Private = 75 menit; Private = 60 menit (aturan RUMBA).
    def set_durasi_menit(self):
        jenis = (
            frappe.db.get_value("Rumba Kelas", self.kelas, "jenis_kelas")
            if self.kelas
            else None
        )
        self.durasi_menit = 60 if jenis == "Private" else 75

    # --- A8: default guru = Employee dari user yang login ---
    def set_guru_default(self):
        if self.guru:
            return
        emp = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
        if emp:
            self.guru = emp

    # --- A5: satu sesi per kelas + tanggal + jam ---
    def cegah_duplikat_sesi(self):
        if not (self.kelas and self.tanggal_sesi):
            return
        filters = {
            "kelas": self.kelas,
            "tanggal_sesi": self.tanggal_sesi,
            "jam_sesi": self.jam_sesi or "",
            "name": ["!=", self.name or ""],
        }
        if frappe.db.exists("Rumba Sesi Kelas", filters):
            frappe.throw(
                _("Sudah ada Sesi Kelas untuk kelas {0} pada {1} jam {2}.").format(
                    frappe.bold(self.kelas),
                    frappe.bold(str(self.tanggal_sesi)),
                    frappe.bold(self.jam_sesi or "-"),
                ),
                title=_("Sesi Duplikat"),
            )

    # --- A1/A5: auto-isi presensi dari roster Fase B (idempoten) ---
    def isi_presensi_dari_roster(self):
        if self.presensi or not self.kelas:
            return
        anggota = frappe.db.sql(
            """
            SELECT ak.murid AS murid, ak.nama_murid AS nama_murid
            FROM `tabRumba Anggota Kelas` ak
            WHERE ak.parent = %s AND ak.parenttype = 'Rumba Kelas'
              AND ak.status = 'Aktif'
            ORDER BY ak.idx
            """,
            self.kelas,
            as_dict=True,
        )
        for a in anggota:
            self.append("presensi", {"murid": a.murid, "nama_murid": a.nama_murid, "status_kehadiran": "Hadir"},)

    def hitung_rekap(self):
        self.jumlah_hadir = sum(
            1 for r in self.presensi if r.status_kehadiran == "Hadir"
        )
        self.jumlah_anggota_roster = len(self.presensi)

    def validasi_status_sesi(self):
        if self.status_sesi == "Diganti" and not self.guru_pengganti:
            frappe.msgprint(
                _("Status sesi 'Diganti' tetapi Guru Pengganti belum diisi."),
                title=_("Guru Pengganti Kosong"),
                indicator="orange",
            )

    # --- A7: presensi harus lengkap sebelum diajukan/disetujui ---
    def validasi_kelengkapan_saat_ajukan(self):
        state = (self.get("workflow_state") or "").strip()
        if state not in ("Diajukan", "Disetujui"):
            return
        if self.status_sesi == "Batal":
            return
        kosong = [r for r in self.presensi if not r.status_kehadiran]
        if kosong:
            frappe.throw(
                _(
                    "Masih ada {0} murid yang belum ditandai kehadirannya. "
                    "Lengkapi status presensi sebelum mengajukan/menyetujui."
                ).format(len(kosong)),
                title=_("Presensi Belum Lengkap"),
            )

    # --- ERP-LIFE-001b: aktivasi murid dari kehadiran pertama ---
    def aktivasi_murid_dari_presensi(self):
        """Saat sesi berada di workflow_state 'Disetujui' dan benar-benar
        berlangsung (status_sesi != 'Batal'), untuk tiap baris presensi 'Hadir':
          1. Stempel Rumba Murid.tanggal_mulai_belajar_aktual = MIN(nilai lama,
             tanggal_sesi) — tanggal mulai belajar sesungguhnya.
          2. Bila status_murid == 'Belum Mulai' → set 'Aktif'.

        Idempoten & aman: memakai MIN (stabil bila sesi lama baru disetujui
        belakangan); pembalikan status HANYA 'Belum Mulai' → 'Aktif' (tidak
        pernah menyentuh Cuti/Lulus/Berhenti/Aktif). Ditulis via frappe.db
        (tanpa memicu ulang siklus dokumen). Aturan sama menangani murid baru
        (SBA) maupun Masuk Lagi (SML: Admin men-set 'Belum Mulai' saat
        re-enroll → Hadir pertama membalik ke Aktif)."""
        state = (self.get("workflow_state") or "").strip()
        if state != "Disetujui" or self.status_sesi == "Batal":
            return

        tgl_sesi = getdate(self.tanggal_sesi)
        for r in self.presensi:
            if r.status_kehadiran != "Hadir" or not r.murid:
                continue
            info = frappe.db.get_value(
                "Rumba Murid",
                r.murid,
                ["status_murid", "tanggal_mulai_belajar_aktual"],
                as_dict=True,
            )
            if not info:
                continue
            updates = {}
            lama = info.tanggal_mulai_belajar_aktual
            if not lama or getdate(lama) > tgl_sesi:
                updates["tanggal_mulai_belajar_aktual"] = tgl_sesi
            if info.status_murid == "Belum Mulai":
                updates["status_murid"] = "Aktif"
            if updates:
                frappe.db.set_value("Rumba Murid", r.murid, updates)

    def _kunci_tanggal_sesi_untuk_tutor(self):
        # Default hari ini bila kosong (jaring pengaman selain Property Setter)
        if not self.tanggal_sesi:
            self.tanggal_sesi = today()

        # Tutor murni tak boleh mencatat Sesi Kelas untuk tanggal selain hari ini.
        # Admin Unit / Kepala Unit (approver) dibebaskan agar bisa mengoreksi.
        roles = set(frappe.get_roles(frappe.session.user))
        EXEMPT = {"System Manager", "Administrator",
                  "Rumba Admin Unit", "Rumba Kepala Unit"}
        if "Rumba Tutor" in roles and roles.isdisjoint(EXEMPT):
            if getdate(self.tanggal_sesi) != getdate(today()):
                frappe.throw(
                    "Tutor hanya boleh mencatat Sesi Kelas untuk hari ini "
                    "({0}). Untuk koreksi tanggal, hubungi Admin Unit.".format(today())
                )


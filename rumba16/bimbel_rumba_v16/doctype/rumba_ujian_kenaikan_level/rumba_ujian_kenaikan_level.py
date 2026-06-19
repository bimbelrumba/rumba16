# Copyright (c) 2026, Yayasan Rumba Kita Indonesia and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import getseries
from frappe.utils import add_days, getdate, nowdate


class RumbaUjianKenaikanLevel(Document):
    """Fase E / E2 — Ujian Kenaikan Level (ERP-ACAD-001 v0.9, L1–L4).

    Cakupan iterasi ini: Calistung (Level 1 Bunyi → Level 2 Kata → Level 3
    Cerita, ACD-CUR-001 v1.1). Penguji = tutor lain (bukan wali kelas) —
    penegakan ADVISORY (deteksi wali kelas belum tersedia, menyusul).

    Kenaikan level dieksekusi di on_update() saat status_ujian == 'Final' dan
    hasil == 'Lulus' (idempoten). Lulus Level 3 = kelulusan program →
    status_murid = 'Lulus' + advisory sertifikat (SOP-ACD-005 §6).
    """

    # Rantai kenaikan level Calistung.
    NEXT_LEVEL = {"Level 1": "Level 2", "Level 2": "Level 3"}

    def autoname(self):
        # Counter independen per-prefix (getseries) — bukan format:{#####} yang
        # ber-counter global antar DocType (pelajaran G6/G7, pola Fase D).
        tahun = getdate(self.tanggal_ujian or nowdate()).strftime("%Y")
        prefix = f"UJI-{tahun}-"
        self.name = prefix + getseries(prefix, 5)

    def validate(self):
        self.set_data_murid()
        self.advisory_ujian_ulang()

    def on_update(self):
        self.eksekusi_kenaikan()

    # ------------------------------------------------------------------ helpers

    def set_data_murid(self):
        if not self.murid:
            return
        murid = frappe.db.get_value(
            "Rumba Murid",
            self.murid,
            ["nama_lengkap", "program_belajar"],
            as_dict=True,
        )
        if not murid:
            return
        self.nama_murid = murid.nama_lengkap
        self.program = murid.program_belajar

    def advisory_ujian_ulang(self):
        """Advisory interval ujian ulang minimal 2 minggu (SOP-ACD-005 §4)."""
        if self.hasil == "Belum Lulus" and self.tanggal_ujian and self.tanggal_ujian_ulang:
            batas = add_days(getdate(self.tanggal_ujian), 14)
            if getdate(self.tanggal_ujian_ulang) < batas:
                frappe.msgprint(
                    _(
                        "Tanggal ujian ulang sebaiknya minimal 2 minggu setelah ujian "
                        "({0} atau lebih), sesuai SOP-ACD-005 §4."
                    ).format(frappe.bold(batas)),
                    title=_("Interval Ujian Ulang"),
                    indicator="orange",
                )

    def _is_calistung(self, program) -> bool:
        """Guard L4: kenaikan level otomatis hanya untuk program Calistung.

        BSD = kenaikan kelas sekolah; EMFK/EFPS level belum matang → di luar
        iterasi. Deteksi sederhana berdasar nama program; model tetap
        program-aware agar mudah diperluas.
        """
        return bool(program) and "calistung" in str(program).lower()

    def eksekusi_kenaikan(self):
        """Eksekusi kenaikan saat Final + Lulus (idempoten)."""
        if self.status_ujian != "Final" or self.hasil != "Lulus":
            return

        murid = frappe.db.get_value(
            "Rumba Murid",
            self.murid,
            ["level_saat_ini", "program_belajar", "status_murid"],
            as_dict=True,
        )
        if not murid:
            return

        if not self._is_calistung(murid.program_belajar):
            frappe.msgprint(
                _(
                    "Program murid bukan Calistung — kenaikan level otomatis "
                    "dilewati. Perbarui level/kelas secara manual sesuai "
                    "SOP-ACD-005 (BSD = kelas sekolah; EMFK/EFPS belum matang)."
                ),
                title=_("Kenaikan Otomatis Dilewati"),
                indicator="blue",
            )
            return

        current = murid.level_saat_ini or ""

        # Lulus Level 3 = kelulusan program (SOP-ACD-005 §6).
        if self.level_diuji == "Level 3":
            updates = {}
            if current != "Level 3":
                updates["level_saat_ini"] = "Level 3"
            if murid.status_murid != "Lulus":
                updates["status_murid"] = "Lulus"
            if updates:
                frappe.db.set_value("Rumba Murid", self.murid, updates)
                frappe.msgprint(
                    _(
                        "{0} LULUS Level 3 Calistung — program selesai. "
                        "Siapkan sertifikat & diskusikan program lanjutan "
                        "(SOP-ACD-005 §6)."
                    ).format(frappe.bold(self.nama_murid or self.murid)),
                    title=_("Kelulusan Program"),
                    indicator="green",
                )
            return

        # Level 1/2: naikkan ke level berikutnya bila belum naik (idempoten).
        target = self.NEXT_LEVEL.get(self.level_diuji)
        if not target:
            return
        if current in ("", self.level_diuji):
            frappe.db.set_value("Rumba Murid", self.murid, "level_saat_ini", target)
            frappe.msgprint(
                _("Level {0} naik ke {1}.").format(
                    frappe.bold(self.nama_murid or self.murid), frappe.bold(target)
                ),
                indicator="green",
            )

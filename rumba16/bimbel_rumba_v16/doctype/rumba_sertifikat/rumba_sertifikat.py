import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import nowdate


class RumbaSertifikat(Document):
    def autoname(self):
        # Scoped per unit + tahun (counter terpisah per prefix)
        kode = self.kode_unit
        if not kode and self.murid:
            kode = frappe.db.get_value("Rumba Murid", self.murid, "kode_unit")
        kode = (kode or "NA").strip().upper().replace(" ", "")
        self.name = make_autoname(f"CERT-{kode}-{nowdate()[:4]}-.####.")

    def validate(self):
        self.fetch_konteks()
        self.validasi_jenis_vs_ujian()
        self.cegah_duplikat()
        self.default_judul()

    def fetch_konteks(self):
        # Jaga-jaga bila dibuat via API (fetch_from hanya jalan di form UI)
        if not self.murid:
            return
        m = frappe.db.get_value(
            "Rumba Murid", self.murid,
            ["nama_lengkap", "nama_unit", "kode_unit", "tahun_ajaran"],
            as_dict=True,
        )
        if not m:
            return
        self.nama_murid = m.nama_lengkap
        self.nama_unit = self.nama_unit or m.nama_unit
        self.kode_unit = self.kode_unit or m.kode_unit
        self.tahun_ajaran = self.tahun_ajaran or m.tahun_ajaran

    def validasi_jenis_vs_ujian(self):
        # Penegak struktural akademik vs non-akademik (advisory; lihat ERP-CERT-001 C4)
        if self.jenis_sertifikat == "Kelulusan" and not self.ujian_sumber:
            frappe.msgprint(
                "Sertifikat Kelulusan sebaiknya menaut Ujian Sumber.",
                indicator="orange", alert=True,
            )
        if self.jenis_sertifikat == "Penyelesaian" and self.ujian_sumber:
            frappe.msgprint(
                "Sertifikat Penyelesaian (non-akademik) tidak memerlukan Ujian Sumber.",
                indicator="orange", alert=True,
            )

    def cegah_duplikat(self):
        # KOREKSI v1.1: level_tahap kosong tersimpan NULL ≠ "" di SQL → filter
        # langsung gagal. Ambil kandidat lalu samakan di Python (normalisasi or "").
        candidates = frappe.get_all(
            "Rumba Sertifikat",
            filters={
                "murid": self.murid,
                "program": self.program,
                "jenis_sertifikat": self.jenis_sertifikat,
                "status": "Diterbitkan",
                "name": ["!=", self.name or ""],
            },
            fields=["name", "level_tahap"],
        )
        for c in candidates:
            if (c.level_tahap or "") == (self.level_tahap or ""):
                frappe.throw(
                    f"Sertifikat untuk capaian ini sudah diterbitkan ({c.name})."
                )

    def default_judul(self):
        if self.judul_capaian:
            return
        parts = [f"Sertifikat {self.jenis_sertifikat}".strip()]
        if self.program:
            parts.append(str(self.program))
        if self.level_tahap:
            parts.append(f"— {self.level_tahap}")
        self.judul_capaian = " ".join(parts).strip()

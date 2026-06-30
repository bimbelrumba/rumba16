# Copyright (c) 2026, Yayasan Rumba Kita Indonesia and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class RumbaPendaftaranEvent(Document):
    """Intake pendaftaran event via web form publik /daftar-event (ERP-EVT-001, KD-6).

    Satu submission = satu pendaftaran satu anak. Orang tua memilih event lewat
    tautan ber-parameter (?event=...). Staf mencocokkan ke Rumba Murid lalu
    menjalankan `masukkan_ke_event` (cascade ke tabel peserta Rumba Event).
    """

    def validate(self):
        self.validasi_event()

    def validasi_event(self):
        if not self.event:
            return
        ev = frappe.db.get_value(
            "Rumba Event", self.event, ["status", "judul_event"], as_dict=True
        )
        if not ev:
            frappe.throw(_("Event tidak ditemukan."))
        # Submission baru (mis. dari web form) hanya boleh untuk event yang masih buka.
        if self.is_new() and ev.status != "Pendaftaran Dibuka":
            frappe.throw(
                _("Pendaftaran untuk event {0} sudah ditutup.").format(
                    frappe.bold(ev.judul_event)
                )
            )


@frappe.whitelist()
def masukkan_ke_event(intake):
    """Cascade: tambahkan murid (hasil pencocokan) sebagai peserta event terpilih.

    Idempoten (lewati bila murid sudah jadi peserta), hormati gerbang kuota.
    """
    doc = frappe.get_doc("Rumba Pendaftaran Event", intake)
    doc.check_permission("write")

    if not doc.murid:
        frappe.throw(
            _("Cocokkan dulu ke Murid (isi field Murid) sebelum memasukkan ke event.")
        )
    if doc.status_intake == "Masuk Event":
        frappe.throw(_("Pendaftaran ini sudah dimasukkan ke event."))

    event = frappe.get_doc("Rumba Event", doc.event)

    # Idempoten — murid sudah jadi peserta?
    for p in event.peserta or []:
        if p.murid == doc.murid:
            doc.db_set("status_intake", "Masuk Event")
            frappe.msgprint(
                _("Murid sudah terdaftar sebagai peserta event {0}.").format(event.name)
            )
            return {"event": event.name, "sudah_ada": 1}

    # Gerbang kuota (peserta non-Batal)
    aktif = [
        p for p in (event.peserta or []) if (p.status_kehadiran or "Terdaftar") != "Batal"
    ]
    if cint(event.kuota) and len(aktif) >= cint(event.kuota):
        frappe.throw(
            _("Kuota event {0} sudah penuh.").format(frappe.bold(event.judul_event))
        )

    event.append("peserta", {"murid": doc.murid})
    event.save()
    doc.db_set("status_intake", "Masuk Event")
    return {"event": event.name, "ditambahkan": 1}

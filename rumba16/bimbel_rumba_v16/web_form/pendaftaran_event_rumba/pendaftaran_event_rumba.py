import frappe
from frappe import _


def get_context(context):
    """Web form /daftar-event — validasi parameter ?event=... .

    Tautan per-event: orang tua membuka /daftar-event?event=EVT-26-00005.
    Field `event` ter-prefill otomatis dari query param. Di sini kita validasi
    bahwa event ada & masih 'Pendaftaran Dibuka', dan menyiapkan judulnya untuk
    ditampilkan. Penegakan akhir tetap di controller validate() saat submit.
    """
    event = frappe.form_dict.get("event")
    context.event_valid = False
    context.event_title = None

    if event:
        ev = frappe.db.get_value(
            "Rumba Event", event, ["judul_event", "status"], as_dict=True
        )
        if ev and ev.status == "Pendaftaran Dibuka":
            context.event_valid = True
            context.event_id = event
            context.event_title = ev.judul_event

import math
import frappe
from frappe.utils import now_datetime

def _haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dlmb/2)**2
    return 2 * R * math.asin(min(1.0, math.sqrt(a)))

def _default_radius():
    return frappe.db.get_single_value("Rumba Pengaturan Presensi", "radius_default_meter") or 150

def _candidate_units(emp):
    """Unit kandidat = unit induk Employee + semua unit dari User Permission (tutor lintas unit)."""
    units = set()
    if emp.get("rumba_unit"):
        units.add(emp["rumba_unit"])
    units.update(frappe.get_all(
        "User Permission",
        filters={"user": frappe.session.user, "allow": "Rumba Unit"},
        pluck="for_value") or [])
    return list(units)

@frappe.whitelist()
def submit_checkin(log_type, latitude=None, longitude=None, accuracy=None):
    if log_type not in ("IN", "OUT"):
        frappe.throw("log_type harus IN atau OUT.")
    emp = frappe.db.get_value("Employee",
        {"user_id": frappe.session.user, "status": "Active"},
        ["name", "rumba_unit"], as_dict=True)
    if not emp:
        frappe.throw("Akun Anda belum tertaut ke data Pegawai aktif.")

    lat = float(latitude) if latitude not in (None, "") else None
    lon = float(longitude) if longitude not in (None, "") else None

    status, jarak = "Tanpa GPS", None
    if lat is not None and lon is not None:
        refs = []  # (lat, lon, radius) tiap acuan berkoordinat
        for u in _candidate_units(emp):
            d = frappe.db.get_value("Rumba Unit", u,
                ["latitude", "longitude", "radius_meter"], as_dict=True)
            if d and d.latitude and d.longitude:
                refs.append((d.latitude, d.longitude, d.radius_meter or _default_radius()))
        if not refs:  # fallback: kantor Pusat (staf pusat / tanpa unit)
            s = frappe.get_single("Rumba Pengaturan Presensi")
            if s.pusat_latitude and s.pusat_longitude:
                refs.append((s.pusat_latitude, s.pusat_longitude,
                             s.pusat_radius_meter or _default_radius()))
        if refs:
            best = min(((_haversine_m(lat, lon, r[0], r[1]), r[2]) for r in refs),
                       key=lambda x: x[0])  # acuan TERDEKAT
            jarak = int(round(best[0]))
            status = "Di Lokasi" if jarak <= best[1] else "Di Luar Lokasi"

    doc = frappe.new_doc("Employee Checkin")
    doc.employee = emp.name
    doc.log_type = log_type
    doc.time = now_datetime()
    if lat is not None:
        doc.latitude = lat
    if lon is not None:
        doc.longitude = lon
    doc.rumba_jarak_meter = jarak
    doc.rumba_status_lokasi = status
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return {"name": doc.name, "status_lokasi": status, "jarak_meter": jarak}

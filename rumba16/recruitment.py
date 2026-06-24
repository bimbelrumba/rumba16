import frappe


def set_job_applicant_source(doc, method=None):
    """Tandai sumber=Web untuk Job Applicant yang masuk lewat web form publik."""
    if doc.get("sumber"):
        return
    form = getattr(frappe.local, "form_dict", None)
    if form and form.get("web_form"):
        doc.sumber = "Web"

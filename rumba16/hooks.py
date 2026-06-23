app_name = "rumba16"
app_title = "Bimbel Rumba v16"
app_publisher = "Yayasan Rumba Kita Indonesia"
app_description = "Modul Bimbel Rumba untuk ERPNext v16."
app_email = "rumba.united@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "rumba16",
# 		"logo": "/assets/rumba16/logo.png",
# 		"title": "Bimbel Rumba v16",
# 		"route": "/rumba16",
# 		"has_permission": "rumba16.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/rumba16/css/rumba16.css"
# app_include_js = "/assets/rumba16/js/rumba16.js"

# include js, css files in header of web template
# web_include_css = "/assets/rumba16/css/rumba16.css"
# web_include_js = "/assets/rumba16/js/rumba16.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "rumba16/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "rumba16/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "rumba16.utils.jinja_methods",
# 	"filters": "rumba16.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "rumba16.install.before_install"
# after_install = "rumba16.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "rumba16.uninstall.before_uninstall"
# after_uninstall = "rumba16.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "rumba16.utils.before_app_install"
# after_app_install = "rumba16.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "rumba16.utils.before_app_uninstall"
# after_app_uninstall = "rumba16.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "rumba16.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {

# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

scheduler_events = {
# 	"all": [
# 		"rumba16.tasks.all"
# 	],
# 	"daily": [
# 		"rumba16.tasks.daily"
# 	],
# 	"hourly": [
# 		"rumba16.tasks.hourly"
# 	],
# 	"weekly": [
# 		"rumba16.tasks.weekly"
# 	],
 	"monthly": [
 		"rumba16.tasks.generate_spp_bulanan"
 	],
 }

# Testing
# -------

# before_tests = "rumba16.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "rumba16.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "rumba16.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "rumba16.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["rumba16.utils.before_request"]
# after_request = ["rumba16.utils.after_request"]

# Job Events
# ----------
# before_job = ["rumba16.utils.before_job"]
# after_job = ["rumba16.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"rumba16.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

fixtures = [
    {"dt": "Client Script"},
    {"dt": "Server Script", "filters": [["module", "=", "Bimbel Rumba v16"]]},
    {"dt": "Notification", "filters": [["module", "=", "Bimbel Rumba v16"]]},
    {"dt": "Report", "filters": [["module", "=", "Bimbel Rumba v16"]]},
    {"dt": "Number Card", "filters": [["module", "=", "Bimbel Rumba v16"]]},
    {"dt": "Dashboard Chart", "filters": [["module", "=", "Bimbel Rumba v16"]]},
    {"dt": "Role", "filters": [["name", "in", ["Rumba Kepala Unit","Rumba Admin Unit","Rumba Lead Tutor","Rumba Tutor","Rumba Finance","Rumba Personalia","Rumba Akademik","Rumba Bisnis","Rumba Mitra","Rumba Founder"]]]},
    {"dt": "Workflow", "filters": [["name","in",["Persetujuan Presensi Sesi","Persetujuan BKM"]]]},
    {"dt": "Workflow State", "filters": [["name", "in", ["Draft","Diajukan","Disetujui","Revisi"]]]},
    {"dt": "Workflow Action Master", "filters": [["name", "in", ["Ajukan","Setujui","Minta Revisi","Ajukan Ulang"]]]},
    {"dt": "Custom Field", "filters": [["name", "in", [
        "Rumba Program Belajar-item_spp",
        "Rumba Unit-price_list_spp",
        "Rumba Murid-nominal_spp",
        "Rumba Murid-tanggal_mulai_spp",
        "Rumba Murid-tanggal_spp_dimuka_sampai",
        "Sales Invoice-rumba_unit",
        "Sales Invoice-rumba_murid",
        "Sales Invoice-spp_periode"
    ]]]},
]


doc_events = {
    "Sales Invoice": {
        "on_update_after_submit": "rumba16.bimbel_rumba_v16.doctype.rumba_pendaftaran.rumba_pendaftaran.sync_status_pembayaran_from_sales_invoice",
        "on_cancel": "rumba16.bimbel_rumba_v16.doctype.rumba_pendaftaran.rumba_pendaftaran.sync_status_pembayaran_from_sales_invoice",
    },
    "Payment Entry": {
        "on_submit": "rumba16.bimbel_rumba_v16.doctype.rumba_pendaftaran.rumba_pendaftaran.sync_status_pembayaran_from_payment_entry",
        "on_cancel": "rumba16.bimbel_rumba_v16.doctype.rumba_pendaftaran.rumba_pendaftaran.sync_status_pembayaran_from_payment_entry",
    },
# ... entri Sales Invoice & Payment Entry yang sudah ada — JANGAN buat dict doc_events kedua ...
    "Employee": {
        "before_naming": "rumba16.hr_naming.employee_autoname",
    },
}

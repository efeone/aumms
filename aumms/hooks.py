
app_name = "aumms"
app_title = "AuMMS"
app_publisher = "efeone"
app_description = "AuMMS is an Frappe App to facilitate the Operations in Gold Manufacturing"
app_email = "info@efeone.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/aumms/css/aumms.css"
# app_include_js = "/assets/aumms/js/aumms.js"

# include js, css files in header of web template
# web_include_css = "/assets/aumms/css/aumms.css"
# web_include_js = "/assets/aumms/js/aumms.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "aumms/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	'Item': 'public/js/item.js',
	'Sales Invoice':'public/js/sales_invoice.js',
	'Item Group': 'public/js/item_group.js',
	'Purchase Receipt': 'public/js/purchase_receipt.js',
	'Purchase Invoice': 'public/js/purchase_invoice.js',
	'Stock Settings': 'public/js/stock_settings.js',
	'Purchase Order': 'public/js/purchase_order.js',
	'Sales Order' : 'public/js/sales_order.js',
    'Job Card' : 'public/js/job_card.js'

	}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#	"methods": "aumms.utils.jinja_methods",
#	"filters": "aumms.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "aumms.install.before_install"


after_install = [
		'aumms.setup.setup_aumms_defaults',
        'aumms.setup.after_install'
	]

after_migrate = [
		'aumms.setup.setup_aumms_defaults',
		'aumms.aumms.utils.increase_precision',
        'aumms.setup.after_migrate'
       
	]


# Uninstallation
# ------------

fixtures = [
	{
		"dt": "Role",
		"filters": [["name", "in", ["Design Analyst", "Supervisor","Smith","Head of Smith", "AuMMS Manager", "Sales Officer", "Sales Manager"]]]
	},
	{
		"dt":"Designation",
		"filters":[["name","in",["Smith"]]]
	},
	{
		"dt":"Email Template",
		"filters":[["name","in",["Design Request Assignment"]]]
	},
	{
		"dt":"Workflow",
		"filters":[["name","in",["Feasibility check"]]]
	},
	{
		"dt":"Workflow Action Master",
		"filters":[["name","in",["Submit for Feasibility check", "Approve", "Reject", "Submit", "Cancel"]]]
	},
	{
		"dt":"Workflow State",
		"filters":[["name","in",["Draft", "Submitted for feasibility", "Feasible", "Not Feasible", "Submitted", "Cancelled"]]]
	},
	{
		"dt":"Custom Field",
		"filters": [["name", "in",["Department-head_of_department", "Employee-custom_warehouse", "Item Group-is_aumms_item_group", "Item Group-item_type", "Item Group-is_purity_item", "Item Group-making_charge_based_on", "Item Group-percentage", "Item Group-currency", "Item Group-is_sales_item", "Item Group-is_purchase_item", "Item-item_type", "Item-making_charge_based_on", "Item-making_charge_percentage", "Item-making_charge", "Item-purity_percentage", "Item-is_aumms_item", "Item-custom_item_qr_code", "Item-gold_weight", "Item-has_stone", "Item-stone_charge","Jewellery Invoice-custom_taxes_and_charges", "Jewellery Invoice-custom_sales_taxes_and_charges", "Jewellery Invoice-custom_total_taxes_and_charges_company_currency", "Jewellery Invoice-custom_total_taxes_and_charges", "Job Card-assigned_to", "Job Card-assigned_employee", "Purchase Invoice-keep_metal_ledger", "Purchase Receipt-party_link", "Purchase Receipt-keep_metal_ledger", "Purchase Receipt-create_invoice_on_submit", "Sales Invoice-keep_metal_ledger", "Sales Order-keep_metal_ledger", "Work Order-assigned_to", "Work Order-smith_name", "UOM-is_purity_uom", "Item-custom_is_raw_material","Purchase Invoice Item-item_type", "Purchase Invoice Item-is_purity_item", "Purchase Invoice Item-purity_percentage", "Purchase Invoice Item-purity", "Purchase Order Item-is_purity_item", "Purchase Order Item-purity", "Purchase Order Item-purity_percentage","Purchase Receipt Item-purity","Purchase Receipt Item-purity_percentage","Purchase Receipt Item-is_purity_item","Sales Invoice Item-purity","Sales Invoice Item-purity_percentage","Sales Invoice Item-is_purity_item","Sales Order Item-purity", "Sales Order Item-is_purity_item"]]]
	}
	]

# before_uninstall = "aumms.uninstall.before_uninstall"
# after_uninstall = "aumms.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "aumms.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	'Item': {
        'validate': 'aumms.aumms.doc_events.item.validate_item',
		'before_save': [
			'aumms.aumms.doc_events.item.check_conversion_factor_for_uom',
			'aumms.aumms.doc_events.item.create_qr'
		],
		'on_update': 'aumms.aumms.doc_events.item.update_uoms_table'
	},
	'Purchase Receipt': {
		'on_submit': [
			'aumms.aumms.utils.create_metal_ledger_entries',
			'aumms.aumms.doc_events.purchase_receipt.purchase_receipt_on_submit'
			],
		'on_cancel': 'aumms.aumms.utils.cancel_metal_ledger_entries'
	},
	'Sales Invoice': {
		'on_submit': [
			  'aumms.aumms.utils.create_metal_ledger_entries'
		],
		'on_cancel': 'aumms.aumms.utils.cancel_metal_ledger_entries'
	},
	'Stock Settings' : {
		'validate': 'aumms.aumms.doc_events.stock_settings.disable_price_list_default'
	},
	'Item Price':{
		'validate': 'aumms.aumms.doc_events.item_price.check_is_purity'
	},
	'Payment Entry':{
		'on_submit': 'aumms.aumms.doc_events.payment_entry.payment_entry_on_submit',
		'on_cancel': 'aumms.aumms.doc_events.payment_entry.payment_entry_on_cancel'
	},
    'Work Order':{
        'after_insert' : 'aumms.aumms.doc_events.work_order.change_design_analysis_status'
	},
    'Stock Reconciliation': {
		'on_submit': 'aumms.aumms.doc_events.stock_reconciliation.create_mle_against_sr',
		'on_cancel': 'aumms.aumms.doc_events.stock_reconciliation.reverse_mle_against_sr',
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
#	"all": [
#		"aumms.tasks.all"
#	],
#	"daily": [
#		"aumms.tasks.daily"
#	],
#	"hourly": [
#		"aumms.tasks.hourly"
#	],
#	"weekly": [
#		"aumms.tasks.weekly"
#	],
#	"monthly": [
#		"aumms.tasks.monthly"
#	],
# }

# Testing
# -------

# before_tests = "aumms.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "aumms.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "aumms.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]


# User Data Protection
# --------------------

# user_data_fields = [
#	{
#		"doctype": "{doctype_1}",
#		"filter_by": "{filter_by}",
#		"redact_fields": ["{field_1}", "{field_2}"],
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_2}",
#		"filter_by": "{filter_by}",
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_3}",
#		"strict": False,
#	},
#	{
#		"doctype": "{doctype_4}"
#	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"aumms.auth.validate"
# ]

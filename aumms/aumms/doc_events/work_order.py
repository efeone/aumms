import frappe

@frappe.whitelist()
def change_design_analysis_status(doc, method):
    if doc.bom_no:
        design_analysis_doc = frappe.get_doc("Design Analysis", {'bom_no': doc.bom_no})
        design_analysis_doc.status = "Work Order Created"
        design_analysis_doc.save(ignore_permissions=True)
        frappe.db.commit()
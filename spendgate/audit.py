
import frappe
def log_change(doc,method=None):
    doc = frappe.get_doc(
        {
            "doctype": "Audit Log",
            "doctype_name": doc.doctype,
            "document_name": doc.name,
            "action": method,
            "user": frappe.session.user,
            "timestamp": frappe.utils.now()
        }
    )
    doc.insert(ignore_permissions=True)

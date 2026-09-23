import frappe

import frappe


def expense_claim_query(user):
    if not user:
        user = frappe.session.user
    roles = frappe.get_roles(user)
    if "Staff" in roles:
        return f"`tabExpense Claim`.employee = {frappe.db.escape(user)}"
    if "Department Head" in roles:
        department = frappe.db.get_value(
            "Department",
            {"department_head": user},
            "name"
        )
        if department:
            return f"`tabExpense Claim`.department = {frappe.db.escape(department)}"

        return "1=0"
    if "Finance Manager" in roles:
        return ""
    return "1=0"
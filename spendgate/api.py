import frappe
from frappe.query_builder import DocType

@frappe.whitelist()
def get_claims_pending_approval():

    EC = DocType("Expense Claim")
    result = (
            frappe.qb.from_(EC)
            .select(
                EC.name,
                EC.employee,
                EC.department,
                EC.total_amount,
                EC.expense_date
            )
            .where(EC.status == "Pending Approval")
            .orderby(EC.expense_date)
        ).run(as_dict=True)

    return result

@frappe.whitelist()
def reassign_department_claims(from_dept, to_dept):
    try:
        result = frappe.db.sql(
            f"""
            UPDATE `tabExpense Claim`
            SET department = %s
            WHERE department = %s AND docstatus = 0 AND status = 'Draft'
            """
            ,(to_dept,from_dept)
        )
        frappe.db.commit()

        return {
            "success":True
        }
    except:
        frappe.db.rollback()

        frappe.log_error(
            title="reassign_department_claims Failure",
            message=frappe.get_traceback()
        )

@frappe.whitelist()
def share_expense_claim(claim_name, user_email):

    frappe.share.add(
        
    )
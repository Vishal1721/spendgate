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
            """
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
    except Exception:
        frappe.db.rollback()

        frappe.log_error(
            title="reassign_department_claims Failure",
            message=frappe.get_traceback()
        )
        raise

@frappe.whitelist()
def share_expense_claim(claim_name, user_email):

    frappe.share.add(
        
    )


@frappe.whitelist()
def approve_expense_claim(claim_name):
    doc = frappe.get_doc("Expense Claim", claim_name)
    if doc.status != "Pending Approval":
        frappe.throw("Only Pending Approval claims can be approved.")
    doc.status = "Approved"
    doc.save()
    frappe.publish_realtime(
        "doc_update",
        {
            "doctype": "Expense Claim",
            "name": doc.name,
            "status": doc.status
        },
    )
    return {"success": True}

@frappe.whitelist()
def reimburse_expense_claim(claim_name):
    doc = frappe.get_doc("Expense Claim", claim_name)
    if doc.status != "Approved":
        frappe.throw("Only Approved claims can be reimbursed.")
    doc.status = "Reimbursed"
    doc.save()
    frappe.publish_realtime(
        "doc_update",
        {
            "doctype": "Expense Claim",
            "name": doc.name,
            "status": doc.status
        },
    )
    return {"success": True}


@frappe.whitelist()
def reject_claim(claim,reason):
    if not claim:
        frappe.throw("Claim not exists")
    if not reason:
        frappe.throw("Reason not exists")
    doc = frappe.get_doc('Expense Claim',claim)
    doc.status = "Rejected"
    # doc.rejection_reason = reason
    doc.save()
    frappe.db.commit()

    return {
        "success": True,
        "message": "Expense Claim rejected successfully"
    }

@frappe.whitelist()
def reassign_department(claim,department):
    if not claim:
        frappe.throw("Claim not exists")
    if not reason:
        frappe.throw("Department not exists")

    doc = frappe.get_doc('Expense Claim',claim)
    doc.department = department 
    doc.save()
     return {
        "success": True,
        "message": "Department reassigned successfully",
        "department": department
    }

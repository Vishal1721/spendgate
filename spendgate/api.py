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
    doc.rejection_reason = reason
    doc.docstatus = 2
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
    if not department:
        frappe.throw("Department not exists")

    doc = frappe.get_doc('Expense Claim',claim)
    doc.department = department
    
    doc.save()
    return {
        "success": True,
        "message": "Department reassigned successfully",
        "department": department
    }

# //get_all
@frappe.whitelist()
def unsafe_get_expense_claims():
    claims = frappe.get_all(
        "Expense Claim",
        fields="*"
    )

    for claim in claims:
        claim["expense_lines"] = frappe.get_all(
            "Expense Line",
            filters={
                "parent": claim["name"]
            },
            fields="*"
        )

    return claims

# //get_list
@frappe.whitelist()
def safe_get_expense_claims():
    claims = frappe.get_list("Expense Claims",
    fields = ["name", "employee" , "department" , "total_amount" , "expense_date", "status"])

    user_department = frappe.db.get_value(
        "Department",
        {"department_head": frappe.session.user},
        "name"
    )
    for claim in claims:
        if claim.department == user_department:
            claim["expense_lines"] = frappe.get_list(
                "Expense Line",
                filters={
                    "parent": claim.name
                },
                fields=[
                    "expense_category",
                    "description",
                    "amount"
                ]
            )

        else:
            claim["expense_lines"] = frappe.get_list(
                "Expense Line",
                filters={
                    "parent": claim.name
                },
                fields=[
                    "expense_category",
                    "description"
                ]
            )

    return claims


@frappe.whitelist()
def get_budget_status(budget):
    if not budget:
        frappe.throw("Buget is none")
    
    total_allocated = frappe.db.get_value('Budget',budget,'total_allocated')
    if total_allocated is None:
        frappe.throw("total_allocated not exists")
    
    spent = frappe.db.sql(
        """
        SELECT COALESCE(SUM(total_amount), 0)
        FROM `tabExpense Claim`
        WHERE budget = %s
          AND docstatus = 1
        """,
        (budget,)
    )[0][0]

    remaining = total_allocated - spent

    return {
        "remaining":remaining
    }



#rate limit
@frappe.whitelist(allow_guest=True)
def public_budget_status():
    ip = frappe.local.request_ip
    cache_key = f"spendgate:rate_limit:{ip}"
    count = frappe.cache.get_value(cache_key)
    if count is None:
        count = 1
    else:
        count = int(count)+1
    
    frappe.cache.set_value(cache_key,count,expires_in_sec = 20)

    if count > 10:
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = "/rate-limited"
        return

    frappe.respond_as_web_page(
        "Request Successful",
        "Hey Man! You didn't Catch yet so enjoy!!",
        indicator_color="green"
    )

# //Rest API For expense claim
@frappe.whitelist()
def get_budget():
    budget_name = frappe.form_dict.get("budget_name")

    if not budget_name or not frappe.db.exists("Budget", budget_name):
        frappe.local.response["http_status_code"] = 404
        return {"error": "Not found"}

    allocated = frappe.db.get_value("Budget",budget_name,"total_allocated")

    spent = frappe.db.sql(
            """
            SELECT COALESCE(SUM(total_amount), 0)
            FROM `tabExpense Claim`
            WHERE budget = %s
              AND docstatus = 1
            """,
            (budget_name,)
        )[0][0]
        

    remaining = allocated - spent

    utilization_percent = ((spent / allocated) * 100)

    return {
        "allocated": allocated,
        "spent": spent,
        "remaining": remaining,
        "utilization_percent": utilization_percent
    }
    
#curl -G "http://localhost:8007/api/method/spendgate.api.get_budget"   -H "Authorization: token 022c14c561404bf:aae27041bfa76ab"   --data-urlencode "budget_name=BUD-2026-0001"

#http://localhost:8007/api/method/spendgate.api.get_budget?budget_name=BUD-2026-0001
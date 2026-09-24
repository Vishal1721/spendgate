import frappe
from frappe.utils import today


def check_budget_thresholds():
    last_run = frappe.db.get_value(
        "Audit Log",
        {
            "action": "budget_threshold_check",
            "date": today()
        },
        "name"
    )
    if last_run:
        return
    threshold = frappe.db.get_single_value("SpendGate Settings","low_budget_alert_threshold_percent")

    if threshold is None:
        threshold = 90
    budgets = frappe.get_all(
        "Budget",
        filters={
            "is_active": 1
        },
        fields=[
            "name",
            "department",
            "total_allocated"
        ]
    )
    for budget in budgets:
        spent = frappe.db.sql(
            """
            SELECT COALESCE(SUM(total_amount), 0)
            FROM `tabExpense Claim`
            WHERE budget = %s
              AND docstatus = 1
            """,
            (budget.name,)
        )[0][0]

        if not budget.total_allocated:
            continue

        utilization = (spent / budget.total_allocated) * 100

        if utilization >= threshold:
            department_head = frappe.db.get_value(
                "Department",
                budget.department,
                "department_head"
            )

            if not department_head:
                continue

            frappe.sendmail(
                recipients=[department_head],
                subject=f"Budget Threshold Alert - {budget.name}",
                message=f"""
                    <h3>Budget Threshold Alert</h3>

                    <p><b>Budget:</b> {budget.name}</p>
                    <p><b>Department:</b> {budget.department}</p>
                    <p><b>Allocated:</b> ₹{budget.total_allocated}</p>
                    <p><b>Spent:</b> ₹{spent}</p>
                    <p><b>Utilization:</b> {utilization:.2f}%</p>
                    <p><b>Threshold:</b> {threshold}%</p>
                """
            )
            
    frappe.get_doc({
        "doctype": "Audit Log",
        "action": "budget_threshold_check",
        "date": today()
    }).insert(ignore_permissions=True)

    frappe.db.commit()
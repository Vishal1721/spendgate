# Copyright (c) 2026, vishal and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ExpenseClaim(Document):
    def validate(self):
        self.expense_validate()
    
    def before_submit(self):

        spent_so_far = frappe.db.sql(
            """
            SELECT COALESCE(SUM(total_amount), 0)
            FROM `tabExpense Claim`
            WHERE budget = %s
            AND docstatus = 1
            AND name != %s
            """,
            (self.budget, self.name))[0][0]

        budget_amount = frappe.db.get_value(
            "Budget",self.budget,"total_allocated"
        )

        spend = spent_so_far + self.total_amount

        if spend > budget_amount:
            overage = spend - budget_amount
            remaining = budget_amount - spent_so_far
            department = frappe.db.get_value(
                "Budget",self.budget,"department"
            )
            frappe.throw(
                f"{department} budget exceeded by ₹{overage}. "
                f"Remaining budget:₹{remaining}."
            )

    def on_submit(self):
        spent_so_far = frappe.db.sql(
            """
            SELECT COALESCE(SUM(total_amount), 0)
            FROM `tabExpense Claim`
            WHERE budget = %s
            AND docstatus = 1
            AND name != %s
            """,
            (self.budget, self.name))[0][0]

        budget_amount = frappe.db.get_value("Budget",self.budget,"total_allocated")
        self.remaining_budget_at_submission = budget_amount - spent_so_far
        if not self.approved_by:
            self.approved_by = frappe.session.user
        self.db_set({
            "remaining_budget_at_submission":self.remaining_budget_at_submission,
            "approved_by":self.approved_by
        })
        self.db_set("status", "Pending Approval")
        frappe.enqueue(
            "spendgate.notification.notify_finance_of_new_claim", 
            claim_name = self.name,
            queue="default",
            is_async=True,
            now=False,
            job_name=None,
        )
        frappe.enqueue(
            "spendgate.webhook.send_webhook",
            claim_name=self.name,
            queue="default",
        )

    def on_cancel(self):
        if self.status == "Reimbursed":
            frappe.throw("Reimbursed Expense Claims cannot be cancelled.")
        self.db_set("status", "Cancelled")

    def on_trash(self):
        if self.status not in ("Cancelled","Draft"):
            frappe.throw('Delete will mot be allowed for status cancelled or draft')

    def expense_validate(self):
        total_amount = 0
        for row in self.expense_line:
            if row.amount <= 0:
                frappe.throw('Amount must be greater than zero')
            total_amount += row.amount
        
        self.total_amount = total_amount
        department = frappe.get_value('Budget',self.budget,'department')

        if department != self.department:
            frappe.throw("Budget Department Not match to expense claim department")


    def before_print(self, print_format=None, doc=None):
        self.print_summary = (f"{self.employee} - {self.department} - {self.expense_date}")
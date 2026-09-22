# Copyright (c) 2026, vishal and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ExpenseClaim(Document):
    def validate(self):
        self.expense_validate()

    def before_submit(self):
    	total_Amount =0
        doc = frappe.get_all('Expense Claim',filters={"docstatus":1},fields=["amount"])

    	for row in doc:
            total_amount += row.amount

        budget_amount = frappe.get_value('Budget',self.budget,total_allocated)
        if  self.total_amount > budget_amount:
            

    def expense_validate(self):
        doc = frappe.get_doc('Expense Claim',self.name)
        total_amount = 0
        for row in doc.expense_line:
            if row.amount <= 0:
                frappe.throw('Amount must be greater than zero')
            total_amount += row.amount
        

        department = frappe.get_value('Budget',self.budget,'department')

        if department != self.department:
            frappe.throw("Budget Department Not match to expense claim department")
    

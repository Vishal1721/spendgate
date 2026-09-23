# Copyright (c) 2026, vishal and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Budget(Document):
    def validate(self):
        if self.total_allocated <=0:
            frappe.throw("Total Allocated must be greater than 0")
        
    def before_insert(self):
        doc = frappe.db.exists("Budget",
        {
            "department":self.department,
            "fiscal_year":self.fiscal_year,
            "fiscal_quarter":self.fiscal_quarter
        })

        if doc:
            frappe.throw(
            f"Budget already exists for {self.department}, "
            f"{self.fiscal_year} {self.fiscal_quarter}")
        

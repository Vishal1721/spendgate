
import frappe 


def after_install():
    departments = ["Marketing", "Software & Equipment", "Client Entertainment", "Training"]
    for dept_name in departments:
        if not frappe.db.exists('Department', dept_name):
            doc = frappe.new_doc('Department')
            doc.department_name = dept_name  
            doc.insert()

    expense_categories = ["Travel", "Software & Equipment", "Client Entertainment", "Training"]
    
    for cat_name in expense_categories:
        if not frappe.db.exists('Expense Category', cat_name):
            doc = frappe.new_doc('Expense Category')
            doc.category_name = cat_name  
            doc.insert()

    if not frappe.db.exists('Spendgate Settings'):
        doc = frappe.new_doc('Spendgate Settings')
        doc.finance_email = "vishal17@work"
        doc.low_budget_alert_threshold_percent = 90
        doc.fiscal_year_start_month = "January"
        doc.insert()

    frappe.msgprint("Spendgate setup completed successfullyand  Default Departments, Expense Categories, and Settings have been Created.")

import frappe


def notify_finance_of_new_claim(claim_name):
    doc = frappe.get_doc("Expense Claim", claim_name)
    finance_email = frappe.db.get_single_value("Spendgate Settings","finance_email")
    if not finance_email:
        return
    frappe.sendmail(
        recipients=[finance_email],
        subject=f"New Expense Claim: {doc.name}",
        message=f"""
            <h3>New Expense Claim Submitted</h3>

            <p><b>Claim:</b> {doc.name}</p>
            <p><b>Employee:</b> {doc.employee}</p>
            <p><b>Department:</b> {doc.department}</p>
            <p><b>Amount:</b> ₹{doc.total_amount}</p>
            <p><b>Status:</b> {doc.status}</p>
        """
    )
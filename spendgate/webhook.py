import frappe
import requests

frappe.utils.logger.set_log_level("INFO")
logger = frappe.logger("spendgate")


def send_webhook(claim_name):
    finance_webhook_url = frappe.db.get_single_value("Spendgate Settings","finance_webhook_url")
    if not finance_webhook_url:
        return
    doc = frappe.get_doc("Expense Claim", claim_name)

    payload = {"event": "claim_submitted","claim": doc.name,"amount": doc.total_amount,}

    try:
        response = requests.post(finance_webhook_url,json=payload,timeout=5,)
        r = response.raise_for_status()
        logger.info(f"Webhook sent successfully for Expense Claim {doc.name}")

    except Exception as e:
        frappe.log_error(f"Webhook failed: {e}","Webhook Error",)
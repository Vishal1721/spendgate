// Copyright (c) 2026, vishal and contributors
// For license information, please see license.txt

frappe.ui.form.on("Expense Claim", {
	refresh(frm) {
        if(frm.doc.status=="Pending Approval" && (frappe.user.has_role('Department Head')|| 
            frappe.user.has_role('Finance Manager'))) {
            frm.add_custom_button('Approve', function() {
                frappe.call({
                    method:"spendgate.api.approve_expense_claim",
                    args : {
                        "claim_name":frm.doc.name
                    },
                    callback : function(r) {
                        frappe.msgprint("Expense Claim is Approved")
                    }
                })
            }, "Action")

            frm.add_custom_button('Reject', function() {
                frm.set_value('status',"Rejected")
                frm.save().then(()=>{
                    frappe.msgprint('Status is Rejected')
                })
            }, 'Action')

        }
        if(frm.doc.status=="Approved" && (frappe.user.has_role('Finance Manager'))) {
            frm.add_custom_button('Approve', function() {
                frappe.call({
                    method:"spendgate.api.reimburse_expense_claim",
                    args : {
                        "claim_name":frm.doc.name
                    },
                    callback : function(r) {
                        frappe.msgprint("Expense Claim is Reimbursed")
                    }
                })
            }, "Action")
        }
	},
});

frappe.ui.form.on("Expense Claim", {
    setup(frm) {
        frm.set_query("budget", () => {
            return {
                filters: {
                    department: frm.doc.department,
                    fiscal_year: frm.doc.fiscal_year,
                    fiscal_quarter: frm.doc.fiscal_quarter
                }
            };
        });
        
        frappe.realtime.on("doc_update", (data) => {
            if (data.doctype === "Expense Claim" &&data.name === frm.doc.name) {
                if (data.status && data.status !== frm.doc.status) {
                    console.log("Realtime Status",data.status)
                    frm.set_value('status',data.status)
                  frappe.show_alert({
                    message: `Status updated: ${data.status}`,
                    indicator: "blue"
                });
            }
        }
    });
    },
});
frappe.ui.form.on("Expense Claim", {
    refresh(frm) {
     if(frm.doc.status=="Pending Approval" && (frappe.user.has_role('Department Head')|| frappe.user.has_role('Adminsitrator') ||
            frappe.user.has_role('Finance Manager'))) {
                frm.add_custom_button("Reject Claim", ()=>{
                    let d = new frappe.ui.Dialog({
                    title: "Reject Claim",
                    fields: [
                        {
                            label: "Rejection Reason",
                            fieldname: "rejection_reason",
                            fieldtype: "Small Text",
                            reqd: 1
                        }
                    ],
                    size: 'small', 
                    primary_action_label: 'Reject',
                    primary_action(values) {
                        frm.call( {
                             method: "spendgate.api.reject_claim",
                                args: {
                                    claim: frm.doc.name,
                                    reason: values.rejection_reason
                                },
                                callback() {
                                    dialog.hide();
                                    frm.reload_doc();
                                }
                        })
                        d.hide();
                    }
                });

                d.show();

                })
        }
    }
})

frappe.ui.form.on("Expense Claim", {
    refresh(frm) {
        if(frm.doc.status=="Pending Approval" && (frappe.user.has_role('Adminsitrator') ||
            frappe.user.has_role('Finance Manager'))) {
        frm.add_custom_button("Reassign Department", () => {
            frappe.prompt(
                [
                    {
                        label: "Department",
                        fieldname: "department",
                        fieldtype: "Link",
                        options: "Department",
                        reqd: 1
                    }
                ],
                (values) => {
                    frappe.confirm(
                        `Are you sure you want to reassign this claim to ${values.department}?`,
                        () => {
                                frappe.call({
                                method: "spendgate.api.reassign_department",
                                args: {
                                    claim: frm.doc.name,
                                    department: values.department
                                },
                                callback() {
                                    frm.set_value("department",values.department);
                                    frm.trigger("department");
                                }
                            });
                        },
                        () => {
                            frappe.show_alert({
                                message: "Department reassignment cancelled",
                                indicator: "orange"
                            });
                        }
                    );

                },
                "Reassign Department",
                "Continue"
            );
        });
    }
    }
});
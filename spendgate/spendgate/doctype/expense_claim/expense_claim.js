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
     if(frm.doc.status=="Pending Approval" && (frappe.user.has_role('Department Head')|| frappe.user.has_role('Administrator') ||
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
                             method:"spendgate.api.reject_claim",
                                args: {
                                    claim: frm.doc.name,
                                    reason: values.rejection_reason
                                },
                                callback() {
                                    d.hide();
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
        if(frm.doc.status=="Pending Approval" && (frappe.user.has_role('Administrator') ||
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


frappe.ui.form.on("Expense Line", {
    amount(frm, cdt, cdn) {
        console.log("Amount changed");

        calculate_total_amount(frm);
        check_remaining_budget(frm);
    }
});


function get_expense_lines(frm) {
    let expense_lines = [];

    for (const fieldname in frm.doc) {
        const value = frm.doc[fieldname];

        if (Array.isArray(value)) {
            const rows = value.filter(row => {
                return row.doctype === "Expense Line";
            });

            if (rows.length) {
                expense_lines = rows;
                break;
            }
        }
    }

    return expense_lines;
}


function calculate_total_amount(frm) {
    const expense_lines = get_expense_lines(frm);

    let total = 0;

    expense_lines.forEach(row => {
        total += flt(row.amount);
    });

    console.log("Calculated total:", total);

    frm.set_value("total_amount", total);
}


function check_remaining_budget(frm) {
    const expense_lines = get_expense_lines(frm);

    let running_total = 0;

    expense_lines.forEach(row => {
        running_total += flt(row.amount);
    });

    if (!frm.doc.budget) {
        console.log("No budget selected");
        return;
    }

    frappe.db.get_value(
        "Budget",
        frm.doc.budget,
        "total_allocated"
    ).then(r => {

        const allocated_budget = flt(r.message.total_allocated);

        console.log("Running total:", running_total);
        console.log("Allocated budget:", allocated_budget);

        if (running_total > allocated_budget) {
            frappe.msgprint({
                title: __("Budget Exceeded"),
                message: __(
                    "The total expense amount ({0}) exceeds the allocated budget ({1}).",
                    [
                        format_currency(running_total),
                        format_currency(allocated_budget)
                    ]
                ),
                indicator: "red"
            });
        }
    });
}
frappe.ui.form.on("Expense Claim", {
    refresh(frm) {
        
       if(frm.doc.status == "Draft") {
            frm.dashboard.add_indicator("Draft", "orange");
        }
        else if (frm.doc.status == "Pending Approval") {
            frm.dashboard.add_indicator("Pending Approval", "blue");
        }
        else if (frm.doc.status == "Approved") {
            frm.dashboard.add_indicator("Approved", "green");
        }
        else if (frm.doc.status == "Rejected") {
            frm.dashboard.add_indicator("Rejected", "red");
        }
        else if (frm.doc.status == "Reimbursed") {
            frm.dashboard.add_indicator("Reimbursed", "green");
        }
        else if (frm.doc.status == "Cancelled") {
            frm.dashboard.add_indicator("Cancelled", "red");
        }

        if (frm.doc.budget) {

            frappe.call({
                method: "spendgate.api.get_budget_status",
                args: {
                    budget: frm.doc.budget
                },
                callback: function(r) {
                    if (r.message) {
                        let remaining = r.message.remaining;
                        frm.dashboard.add_indicator(
                            `Budget Remaining: ₹${remaining}`,
                            remaining <= 0 ? "red" : "green"
                        );
                    }
                }
            });
        }
    }
})
`1.B2c — Dangerous Patterns why a stored counter is the wrong design 3 pts`
The snippet below has two bugs. One is generic (you've seen its shape before). The other is specific to this app and explains exactly why SpendGate computes spend with a live aggregate query instead of a running balance field. Identify both and write the corrected version inREADME_internals.md:

def validate(self):
    self.total_amount = sum(r.amount for r in self.expense_lines)
    self.save()
    budget = frappe.get_doc("Budget", self.budget)
    budget.total_allocated -= self.total_amount
    budget.save()
Hint for the second bug: what happens to total_allocated when this claim is later cancelled? What happens if two claims against the same budget are being edited at once?
#####
Bug 1 — self.save() inside validate()
def validate(self):
    self.total_amount = sum(r.amount for r in self.expense_lines)
    self.save()

self.save() runs inside the validate(), it will lead to loop recycle
It causing recursive execution

validate should only do set or calculate values
def validate(self):
    self.total_amount = sum(r.amount for r in self.expense_lines)

####
Bug 2 — total_allocated is being used as a running balance

budget.total_allocated -= self.total_amount
budget.save()

total_allocated represents the budget allocation. It should not be mutated every time an Expense Claim is created or changed.

so for example Claims is cancelled we cant back to the total budget 
this will lead to concurrency problem



`2.B2d — The Race Condition Question`
TOCTOU, concurrent submits
1 pt
In README_internals.md: two employees submit Expense Claims against the same Budget within the same second. Both controllers compute spent_so_far before either transaction commits. Could both submissions succeed even though, combined, they exceed the budget? Explain why or why not, and name the Frappe/MariaDB mechanism (if any) that protects against it. (One paragraph — this is a real question, not a trick; it's fine if your honest answer is "nothing currently protects against this.")

####
## B2d — The Race Condition Question

Yes, both claims could succeed if both check the budget before either one commits. Both may see the same spent_so_far, so together they could exceed the budget.

Frappe provides for_update=True, which uses a database row lock. If SpendGate locks the same Budget row before checking the budget, the second transaction waits until the first finishes, preventing this race. If SpendGate does not currently use for_update=True, then nothing currently protects against this race.

For your README_internals.md:

query = frappe.qb.get_query(
    "Stock Ledger Entry",
    fields=["name", "qty_after_transaction"],
    filters={"item_code": "ITEM001", "warehouse": "WH001"},
    for_update=True
)
Adds FOR UPDATE clause, will wait if rows are locked.


`3.In README_internals.md: rename a test Department record. Does department on linked Budgets and Expense Claims update automatically? Why or why not?`

####
No. If you rename a Department record, the department value in linked Budget and Expense Claim records does not automatically update.

The reason is that a Frappe Link field stores the linked document's name. Renaming the Department changes its document name, so linked records need Frappe's rename/linked-document update mechanism to update those references.

`4.on_update() — the recursion pitfall`
Call self.save() inside on_update and observe what breaks. Explain it and correct the pattern in README_internals.md.

##### on_update() — The Recursion Pitfall

Calling `self.save()` inside `on_update()` causes recursion because `save()` triggers `on_update()` again.

python
def on_update(self):
    self.some_field = "value"
    self.save()  # Wrong

this will lead to recursive execution
with error


`5.In README_internals.md: why does a frappe.call inside the validate client event not work, and why must async fetches happen in onload/refresh instead?`

####
The client-side `validate` event is expected to finish the validation process synchronously. A `frappe.call()` is asynchronous, so the server response does not return before the validation handler finishes.

Async data should  be fetched in events such as onload or refresh, where the data can be retrieved before the user submits the document.

fetch the data by async and validate it.


`6.In README_internals.md: show the f-string version side by side with the parameterized version, and explain why the latter is always preferred.`

### F-string version

python
department = filters.get("department")

query = f"""
    SELECT
        name,
        employee,
        department,
        total_amount,
        expense_date
    FROM `tabExpense Claim`
    WHERE status = 'Pending Approval'
"""

if department:
    query += f" AND department = '{department}'"

data = frappe.db.sql(query, as_dict=True)


K2 — Spot the N+1
bulk fetch vs per-row query
3 pts
The snippet below has an N+1 query problem. Identify it and rewrite it:


`7.E3 — One Performance Judgment Call`
frappe.db.get_value vs get_doc
2 pts
Somewhere in your controller you need just the low_budget_alert_threshold_percent value from SpendGate Settings. Which pattern would you use and why?

doc = frappe.get_doc("SpendGate Settings", "SpendGate Settings")
threshold = doc.low_budget_alert_threshold_percent

threshold = frappe.db.get_value("SpendGate Settings", None, "low_budget_alert_threshold_percent")

####
threshold = frappe.db.get_value("SpendGate Settings", None, "low_budget_alert_threshold_percent")
I would prefer this compare to get_doc
beacause get_doc will load the the document object and we get the data from the project.
Instead we can took the single value from frappe.db.get_value()


`8.# N+1 PROBLEM - fix this`
claims = frappe.get_all("Expense Claim", fields=["name","department"])
for c in claims:
    dept = frappe.get_doc("Department", c.department)
    print(dept.department_name, dept.department_head)
Bulk operations, manual indexing, and report query-profiling are real skills too — they're in Bonus once this pattern is second nature.

###
claims = frappe.get_all("Expense Claim", fields=["name","department",`tabDepartment.department_name`,`tabDepartment.department_head])
for c in claims:
    <!-- dept = frappe.get_doc("Department", c.department) -->
    print(c.department_name, c.department_head)

Hitting the database n+1 time inside loop will lead to N+1 PROBLEM. so we want to avoid the db hits.


`9.explain the difference between putting a frappe.get_all() call directly inside the Jinja template versus pre-computing in before_print() and referencing doc.precomputed_field.`

going frappe.get_all() in the jinja directly will do both fecthing and print formating
this is good for small or simple queries not for larger retriving data queries

per compute in before_print() will be good for larger queries.Fetching data in controller
will not increase the work of jinja templating

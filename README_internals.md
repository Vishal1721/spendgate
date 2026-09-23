1.B2c — Dangerous Patterns
why a stored counter is the wrong design
3 pts
The snippet below has two bugs. One is generic (you've seen its shape before). The other is specific to this app and explains exactly why SpendGate computes spend with a live aggregate query instead of a running balance field. Identify both and write the corrected version in README_internals.md:

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



2.B2d — The Race Condition Question
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


3.In README_internals.md: rename a test Department record. Does department on linked Budgets and Expense Claims update automatically? Why or why not?

####
No. If you rename a Department record, the department value in linked Budget and Expense Claim records does not automatically update.

The reason is that a Frappe Link field stores the linked document's name. Renaming the Department changes its document name, so linked records need Frappe's rename/linked-document update mechanism to update those references.

4.on_update() — the recursion pitfall
Call self.save() inside on_update and observe what breaks. Explain it and correct the pattern in README_internals.md.

##### on_update() — The Recursion Pitfall

Calling `self.save()` inside `on_update()` causes recursion because `save()` triggers `on_update()` again.

python
def on_update(self):
    self.some_field = "value"
    self.save()  # Wrong

this will lead to recursive execution
with error


5.In README_internals.md: why does a frappe.call inside the validate client event not work, and why must async fetches happen in onload/refresh instead?

####
The client-side `validate` event is expected to finish the validation process synchronously. A `frappe.call()` is asynchronous, so the server response does not return before the validation handler finishes.

Async data should  be fetched in events such as onload or refresh, where the data can be retrieved before the user submits the document.

fetch the data by async and validate it.


6.In README_internals.md: show the f-string version side by side with the parameterized version, and explain why the latter is always preferred.

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
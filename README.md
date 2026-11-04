# Expense Splitter

Split hostel and trip costs fairly, then settle with the fewest payments.

## What it does

- Groups with members
- Each group picks one Asian currency at creation (50 countries,
  e.g. Bangladesh — Bangladeshi taka ৳, India — Indian rupee ₹,
  Japan — Japanese yen ¥), shown in the group title and on every amount
- Expenses with a category and a payer, in the group's currency
- Equal split over chosen participants, or a custom split per member
- Balances: what each person paid vs their share
- Debt simplification: a chain like A → B, B → C collapses to a direct
  payment, so a group of n members needs at most n − 1 payments
- Bar chart of paid vs share (Chart.js)

## How money is handled

Amounts are stored as integer poisha, never as floats, so splits and
balances never drift by rounding. An equal split distributes leftover
poisha to the earliest members, so shares always sum exactly to the total.
A custom split is rejected unless its shares add up to the expense amount.

## Run locally

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
```

Then open http://127.0.0.1:5001

## Honest limits (v1)

- No login: anyone with the link can see and edit a group. This is a
  personal splitter, not a multi-user service yet.
- On Vercel the database lives in /tmp, so history there is ephemeral,
  the same limit Project 1 (Password Leak Checker) has.
- A group's currency is fixed at creation and is a label, not a
  conversion: amounts are never converted by exchange rate. To use
  another currency, create a new group in that currency.

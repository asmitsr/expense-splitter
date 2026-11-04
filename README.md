<div align="center">

# Expense Splitter

<p>Split hostel and trip costs fairly, then settle with the fewest payments.</p>

[![Live Site](https://img.shields.io/badge/Live_Site-Open_Website-2ea44f?style=for-the-badge)](https://expense-splitter-lovat-iota.vercel.app/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)

</div>

---

## What it does

| Feature | Details |
| --- | --- |
| Groups | Create a group, add members, track expenses together |
| Currency | Each group picks one Asian currency at creation (50 countries) |
| Expenses | Category and payer, in the group's currency |
| Equal split | Split over chosen participants, not forced over everyone |
| Custom split | A custom share per member, rejected unless shares sum exactly to the amount |
| Balances | What each person paid vs their share |
| Debt simplification | A chain like A → B, B → C collapses to a direct payment, so a group of n members needs at most n − 1 payments |
| Chart | Bar chart of paid vs share (Chart.js) |

## Currencies

A group's currency is chosen at creation from a dropdown showing country, currency name, symbol and code — for example Bangladesh — Bangladeshi taka (৳), India — Indian rupee (₹), Japan — Japanese yen (¥). The chosen symbol appears in the group title and on every amount.

## How money is handled

Amounts are stored as **integer poisha, never as floats**, so splits and balances never drift by rounding. An equal split distributes leftover poisha to the earliest members, so shares always sum exactly to the total. A custom split is rejected unless its shares add up to the expense amount.

## Run locally

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
```

Then open http://127.0.0.1:5001

## Project structure

```
app.py                 # Flask app: groups, members, expenses, splits, settlements
templates/index.html   # Frontend + Chart.js chart
api/index.py           # Vercel entry point
vercel.json            # Vercel rewrite, same pattern as the Password Leak Checker
requirements.txt       # flask
```

## Honest limits (v1)

- **No login:** anyone with the link can see and edit a group. This is a personal splitter, not a multi-user service yet.
- **Ephemeral history on Vercel:** the database lives in `/tmp`, so history resets when Vercel restarts — the same limit Project 1 (Password Leak Checker) has.
- **Currency is a label, not a conversion:** a group's currency is fixed at creation and amounts are never converted by exchange rate. To use another currency, create a new group in that currency.

## Meet the developer

**Asmit Sarkar** — first-year CSE student from Bangladesh, building web and Android projects step by step.

- GitHub: https://github.com/asmitsr
- More projects: https://showcase-topaz-seven.vercel.app/

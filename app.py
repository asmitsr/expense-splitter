import os
import sqlite3

from flask import Flask, g, jsonify, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)


def _rate_limit_key():
    """Client IP for rate limiting.

    Prefer X-Forwarded-For (set by Vercel's edge) so each visitor gets
    their own bucket; fall back to the direct remote address locally.
    """
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address()


# Rate limiting (Flask-Limiter, in-memory storage).
# On Vercel serverless the storage is per-instance and resets on cold
# start — acceptable for this low-traffic tool; it still blunts bursts
# and abuse from a single IP within an instance's lifetime.
limiter = Limiter(
    key_func=_rate_limit_key,
    app=app,
    default_limits=["60 per minute"],
    storage_uri="memory://",
)

# Asian currencies: (id, country, currency name, symbol, ISO code).
# The id is usually the ISO code; Palestine shares ILS with Israel, so
# it gets its own id. The currency is a label for the group, not a
# conversion: amounts are entered and shown in the chosen currency,
# never converted by rate.
CURRENCIES = [
    ("AFN", "Afghanistan", "Afghan afghani", "؋", "AFN"),
    ("AMD", "Armenia", "Armenian dram", "֏", "AMD"),
    ("AZN", "Azerbaijan", "Azerbaijani manat", "₼", "AZN"),
    ("BHD", "Bahrain", "Bahraini dinar", ".د.ب", "BHD"),
    ("BDT", "Bangladesh", "Bangladeshi taka", "৳", "BDT"),
    ("BTN", "Bhutan", "Bhutanese ngultrum", "Nu.", "BTN"),
    ("BND", "Brunei", "Brunei dollar", "$", "BND"),
    ("KHR", "Cambodia", "Cambodian riel", "៛", "KHR"),
    ("CNY", "China", "Chinese yuan", "¥", "CNY"),
    ("EUR", "Cyprus", "Euro", "€", "EUR"),
    ("GEL", "Georgia", "Georgian lari", "₾", "GEL"),
    ("INR", "India", "Indian rupee", "₹", "INR"),
    ("IDR", "Indonesia", "Indonesian rupiah", "Rp", "IDR"),
    ("IRR", "Iran", "Iranian rial", "﷼", "IRR"),
    ("IQD", "Iraq", "Iraqi dinar", "ع.د", "IQD"),
    ("ILS", "Israel", "Israeli new shekel", "₪", "ILS"),
    ("JPY", "Japan", "Japanese yen", "¥", "JPY"),
    ("JOD", "Jordan", "Jordanian dinar", "د.ا", "JOD"),
    ("KZT", "Kazakhstan", "Kazakhstani tenge", "₸", "KZT"),
    ("KWD", "Kuwait", "Kuwaiti dinar", "د.ك", "KWD"),
    ("KGS", "Kyrgyzstan", "Kyrgyzstani som", "сом", "KGS"),
    ("LAK", "Laos", "Lao kip", "₭", "LAK"),
    ("LBP", "Lebanon", "Lebanese pound", "ل.ل", "LBP"),
    ("MYR", "Malaysia", "Malaysian ringgit", "RM", "MYR"),
    ("MVR", "Maldives", "Maldivian rufiyaa", "Rf", "MVR"),
    ("MNT", "Mongolia", "Mongolian tögrög", "₮", "MNT"),
    ("MMK", "Myanmar", "Myanmar kyat", "K", "MMK"),
    ("NPR", "Nepal", "Nepalese rupee", "₨", "NPR"),
    ("KPW", "North Korea", "North Korean won", "₩", "KPW"),
    ("OMR", "Oman", "Omani rial", "ر.ع.", "OMR"),
    ("PKR", "Pakistan", "Pakistani rupee", "₨", "PKR"),
    ("PSE", "Palestine", "Israeli new shekel", "₪", "ILS"),
    ("PHP", "Philippines", "Philippine peso", "₱", "PHP"),
    ("QAR", "Qatar", "Qatari riyal", "ر.ق", "QAR"),
    ("RUB", "Russia", "Russian ruble", "₽", "RUB"),
    ("SAR", "Saudi Arabia", "Saudi riyal", "ر.س", "SAR"),
    ("SGD", "Singapore", "Singapore dollar", "$", "SGD"),
    ("KRW", "South Korea", "South Korean won", "₩", "KRW"),
    ("LKR", "Sri Lanka", "Sri Lankan rupee", "₨", "LKR"),
    ("SYP", "Syria", "Syrian pound", "£", "SYP"),
    ("TWD", "Taiwan", "New Taiwan dollar", "NT$", "TWD"),
    ("TJS", "Tajikistan", "Tajikistani somoni", "SM", "TJS"),
    ("THB", "Thailand", "Thai baht", "฿", "THB"),
    ("USD", "Timor-Leste", "US dollar", "$", "USD"),
    ("TRY", "Turkey", "Turkish lira", "₺", "TRY"),
    ("TMT", "Turkmenistan", "Turkmenistani manat", "T", "TMT"),
    ("AED", "United Arab Emirates", "UAE dirham", "د.إ", "AED"),
    ("UZS", "Uzbekistan", "Uzbekistani som", "so'm", "UZS"),
    ("VND", "Vietnam", "Vietnamese dong", "₫", "VND"),
    ("YER", "Yemen", "Yemeni rial", "﷼", "YER"),
]
CURRENCY_IDS = {c[0] for c in CURRENCIES}


def currency_for(currency_id):
    for entry in CURRENCIES:
        if entry[0] == (currency_id or "BDT"):
            return {
                "id": entry[0],
                "country": entry[1],
                "name": entry[2],
                "symbol": entry[3],
                "code": entry[4],
            }
    return currency_for("BDT")

# Vercel's serverless filesystem is read-only except /tmp, so the
# database lives there when deployed and beside the app locally.
if os.environ.get("VERCEL"):
    DB_PATH = "/tmp/expense.db"
else:
    DB_PATH = os.path.join(os.path.dirname(__file__), "expense.db")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL REFERENCES groups(id),
            name TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL REFERENCES groups(id),
            payer_id INTEGER NOT NULL REFERENCES members(id),
            amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
            description TEXT NOT NULL DEFAULT '',
            category TEXT NOT NULL DEFAULT 'General',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS expense_shares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expense_id INTEGER NOT NULL REFERENCES expenses(id),
            member_id INTEGER NOT NULL REFERENCES members(id),
            share_cents INTEGER NOT NULL CHECK (share_cents >= 0)
        );
        """
    )
    # Groups created before currencies existed have no such column.
    try:
        db.execute(
            "ALTER TABLE groups ADD COLUMN currency_id TEXT NOT NULL DEFAULT 'BDT'"
        )
    except sqlite3.OperationalError:
        pass
    db.commit()


with app.app_context():
    init_db()


def to_cents(amount):
    """Taka as typed (e.g. 12.50) -> integer poisha, so money never
    suffers binary float rounding in splits or balances."""
    return int(round(float(amount) * 100))


def fmt(cents):
    return f"{cents / 100:.2f}"


def group_or_404(db, group_id):
    group = db.execute("SELECT * FROM groups WHERE id = ?", (group_id,)).fetchone()
    if group is None:
        return None, (jsonify({"error": "group not found"}), 404)
    return group, None


def members_of(db, group_id):
    return db.execute(
        "SELECT * FROM members WHERE group_id = ? ORDER BY id", (group_id,)
    ).fetchall()


def compute_balances(db, group_id):
    members = members_of(db, group_id)
    paid = {m["id"]: 0 for m in members}
    share = {m["id"]: 0 for m in members}
    for row in db.execute(
        "SELECT payer_id, amount_cents FROM expenses WHERE group_id = ?",
        (group_id,),
    ):
        paid[row["payer_id"]] += row["amount_cents"]
    for row in db.execute(
        """
        SELECT es.member_id, es.share_cents FROM expense_shares es
        JOIN expenses e ON e.id = es.expense_id
        WHERE e.group_id = ?
        """,
        (group_id,),
    ):
        share[row["member_id"]] += row["share_cents"]
    balances = []
    for m in members:
        balances.append(
            {
                "id": m["id"],
                "name": m["name"],
                "paid_cents": paid[m["id"]],
                "share_cents": share[m["id"]],
                "balance_cents": paid[m["id"]] - share[m["id"]],
            }
        )
    return balances


def simplify_debts(balances):
    """Greedy creditor/debtor matching. A chain A->B, B->C collapses to
    a direct payment, so a group of n members needs at most n-1
    payments instead of one per expense."""
    creditors = sorted(
        (b for b in balances if b["balance_cents"] > 0),
        key=lambda b: -b["balance_cents"],
    )
    debtors = sorted(
        (b for b in balances if b["balance_cents"] < 0),
        key=lambda b: b["balance_cents"],
    )
    payments = []
    i = j = 0
    while i < len(creditors) and j < len(debtors):
        creditor = dict(creditors[i])
        debtor = dict(debtors[j])
        amount = min(creditor["balance_cents"], -debtor["balance_cents"])
        payments.append(
            {"from": debtor["name"], "to": creditor["name"], "amount_cents": amount}
        )
        creditor["balance_cents"] -= amount
        debtor["balance_cents"] += amount
        creditors[i] = creditor
        debtors[j] = debtor
        if creditor["balance_cents"] == 0:
            i += 1
        if debtor["balance_cents"] == 0:
            j += 1
    return payments


def group_detail(db, group):
    members = members_of(db, group["id"])
    expenses = []
    for e in db.execute(
        """
        SELECT e.*, m.name AS payer_name FROM expenses e
        JOIN members m ON m.id = e.payer_id
        WHERE e.group_id = ? ORDER BY e.id DESC
        """,
        (group["id"],),
    ):
        shares = db.execute(
            """
            SELECT es.member_id, m.name, es.share_cents FROM expense_shares es
            JOIN members m ON m.id = es.member_id
            WHERE es.expense_id = ? ORDER BY es.member_id
            """,
            (e["id"],),
        ).fetchall()
        expenses.append(
            {
                "id": e["id"],
                "payer": e["payer_name"],
                "amount": fmt(e["amount_cents"]),
                "description": e["description"],
                "category": e["category"],
                "shares": [
                    {"name": s["name"], "amount": fmt(s["share_cents"])} for s in shares
                ],
            }
        )
    balances = compute_balances(db, group["id"])
    return {
        "id": group["id"],
        "name": group["name"],
        "currency": currency_for(group["currency_id"] if "currency_id" in group.keys() else "BDT"),
        "members": [{"id": m["id"], "name": m["name"]} for m in members],
        "expenses": expenses,
        "balances": [
            {
                "name": b["name"],
                "paid": fmt(b["paid_cents"]),
                "share": fmt(b["share_cents"]),
                "balance": fmt(b["balance_cents"]),
            }
            for b in balances
        ],
        "settlements": [
            {"from": p["from"], "to": p["to"], "amount": fmt(p["amount_cents"])}
            for p in simplify_debts(balances)
        ],
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/currencies", methods=["GET"])
def currencies():
    return jsonify([currency_for(c[0]) for c in CURRENCIES])


@app.route("/api/groups", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def groups():
    db = get_db()
    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        name = (data.get("name") or "").strip()
        currency_id = (data.get("currency_id") or "BDT").strip().upper()
        if not name:
            return jsonify({"error": "group name is required"}), 400
        if currency_id not in CURRENCY_IDS:
            return jsonify({"error": "unknown currency"}), 400
        cur = db.execute(
            "INSERT INTO groups (name, currency_id) VALUES (?, ?)",
            (name, currency_id),
        )
        db.commit()
        return jsonify({"id": cur.lastrowid, "name": name, "currency_id": currency_id}), 201
    rows = db.execute("SELECT * FROM groups ORDER BY id DESC").fetchall()
    return jsonify(
        [
            {
                "id": r["id"],
                "name": r["name"],
                "currency": currency_for(r["currency_id"] if "currency_id" in r.keys() else "BDT"),
            }
            for r in rows
        ]
    )


@app.route("/api/groups/<int:group_id>", methods=["GET"])
def one_group(group_id):
    db = get_db()
    group, err = group_or_404(db, group_id)
    if err:
        return err
    return jsonify(group_detail(db, group))


@app.route("/api/groups/<int:group_id>/members", methods=["POST"])
@limiter.limit("10 per minute")
def add_member(group_id):
    db = get_db()
    group, err = group_or_404(db, group_id)
    if err:
        return err
    data = request.get_json(force=True, silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "member name is required"}), 400
    cur = db.execute(
        "INSERT INTO members (group_id, name) VALUES (?, ?)", (group_id, name)
    )
    db.commit()
    return jsonify({"id": cur.lastrowid, "name": name}), 201


@app.route("/api/groups/<int:group_id>/expenses", methods=["POST"])
@limiter.limit("10 per minute")
def add_expense(group_id):
    db = get_db()
    group, err = group_or_404(db, group_id)
    if err:
        return err
    data = request.get_json(force=True, silent=True) or {}
    members = members_of(db, group_id)
    member_ids = {m["id"] for m in members}
    try:
        amount_cents = to_cents(data.get("amount"))
        payer_id = int(data.get("payer_id"))
    except (TypeError, ValueError):
        return jsonify({"error": "amount and payer_id must be valid"}), 400
    if amount_cents <= 0:
        return jsonify({"error": "amount must be greater than zero"}), 400
    if payer_id not in member_ids:
        return jsonify({"error": "payer must be a member of this group"}), 400
    if not members:
        return jsonify({"error": "add members before adding an expense"}), 400

    split_type = data.get("split_type", "equal")
    shares = {}
    if split_type == "custom":
        raw = data.get("shares") or {}
        try:
            for key, value in raw.items():
                mid = int(key)
                if mid in member_ids:
                    shares[mid] = to_cents(value)
        except (TypeError, ValueError):
            return jsonify({"error": "custom shares must be valid amounts"}), 400
        if sum(shares.values()) != amount_cents:
            return jsonify({"error": "custom shares must add up to the expense amount"}), 400
        for mid in member_ids:
            shares.setdefault(mid, 0)
    else:
        # Equal split over the chosen participants only (default: all
        # members), in whole poisha: the leftover poisha go to the
        # earliest participants, so shares sum exactly to the total.
        raw_parts = data.get("participants")
        if raw_parts:
            try:
                participants = [int(p) for p in raw_parts]
            except (TypeError, ValueError):
                return jsonify({"error": "participants must be member ids"}), 400
            participants = [p for p in participants if p in member_ids]
            if not participants:
                return jsonify({"error": "at least one participant is required"}), 400
        else:
            participants = [m["id"] for m in members]
        base, remainder = divmod(amount_cents, len(participants))
        for mid in member_ids:
            shares[mid] = 0
        for idx, mid in enumerate(participants):
            shares[mid] = base + (1 if idx < remainder else 0)

    cur = db.execute(
        """
        INSERT INTO expenses (group_id, payer_id, amount_cents, description, category)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            group_id,
            payer_id,
            amount_cents,
            (data.get("description") or "").strip(),
            (data.get("category") or "General").strip() or "General",
        ),
    )
    expense_id = cur.lastrowid
    for mid, share_cents in shares.items():
        db.execute(
            "INSERT INTO expense_shares (expense_id, member_id, share_cents)"
            " VALUES (?, ?, ?)",
            (expense_id, mid, share_cents),
        )
    db.commit()
    return jsonify({"id": expense_id}), 201


@app.route("/api/index", methods=["GET", "POST"])
@app.route("/api/index.py", methods=["GET", "POST"])
def vercel_dispatcher():
    """On Vercel every request reaches the function as /api/index, so
    the original path arrives as ?original=<path> and is routed here
    to the real view, the same pattern Project 1 needed."""
    original = (request.args.get("original") or request.args.get("path") or "").strip().strip("/")
    parts = [p for p in original.split("/") if p]
    if not parts:
        return index()
    if parts == ["api", "currencies"]:
        return currencies()
    if parts == ["api", "groups"]:
        return groups()
    if len(parts) == 3 and parts[0] == "api" and parts[1] == "groups":
        try:
            return one_group(int(parts[2]))
        except ValueError:
            return jsonify({"error": "invalid group id"}), 400
    if len(parts) == 4 and parts[0] == "api" and parts[1] == "groups":
        try:
            gid = int(parts[2])
        except ValueError:
            return jsonify({"error": "invalid group id"}), 400
        if parts[3] == "members" and request.method == "POST":
            return add_member(gid)
        if parts[3] == "expenses" and request.method == "POST":
            return add_expense(gid)
    return jsonify({"error": "not found"}), 404


@app.errorhandler(429)
def _ratelimited(e):
    return (
        jsonify({"error": "Too many requests. Please wait a minute and try again."}),
        429,
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=False)

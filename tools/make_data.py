"""Make the fake Finance data for the invoice-flow demo.

Writes three CSV files into data/:
  suppliers.csv    - who sends us invoices            (a "dimension" table)
  departments.csv  - which team the cost belongs to   (a "dimension" table)
  invoices.csv     - one row per invoice              (the "fact" table)

The data is made up but behaves like a real accounts-payable team, with a few
stories hidden in it for the dashboard to find, and a few deliberate mistakes
for Power Query to clean. Same seed = same data every run.

Run:  python3 tools/make_data.py
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(1891)

TODAY = date(2026, 9, 26)          # the day the "export" was taken
START = date(2026, 1, 1)
OUT = Path(__file__).resolve().parent.parent / "data"

SUPPLIERS = [
    # id, name, category, payment terms (days)
    ("S001", "Cahaya Office Supplies Sdn Bhd", "Office Supplies", 30),
    ("S002", "Mega Logistik Sdn Bhd", "Logistics", 30),
    ("S003", "Pantas Courier Sdn Bhd", "Logistics", 30),
    ("S004", "Awan Cloud Services Sdn Bhd", "IT Services", 45),
    ("S005", "Teknik Jaya IT Solutions", "IT Services", 30),
    ("S006", "Kilau Cleaning Services", "Facilities", 30),
    ("S007", "Seri Kenari Catering", "Catering", 14),
    ("S008", "Bintang Media Agency Sdn Bhd", "Marketing", 60),
    ("S009", "Ombak Printing Works", "Marketing", 30),
    ("S010", "Tenaga Utiliti Harian", "Utilities", 14),
    ("S011", "Perdana Legal & Associates", "Professional Fees", 30),
    ("S012", "Sinar Audit PLT", "Professional Fees", 45),
    ("S013", "Rimba Furniture Trading", "Facilities", 30),
    ("S014", "Delima Travel & Tours", "Travel", 30),
    ("S015", "Nusantara Training Centre", "Training", 30),
]

DEPARTMENTS = [
    # id, name, cost centre, approver, typical days to approve
    ("D01", "Finance", "CC100", "Aina Rahman", 2),
    ("D02", "Human Resources", "CC200", "Farid Ismail", 3),
    ("D03", "IT", "CC300", "Kavitha Nair", 3),
    ("D04", "Operations", "CC400", "Wong Mei Ling", 4),
    ("D05", "Marketing", "CC500", "Hafiz Omar", 11),   # story: Marketing is the bottleneck
    ("D06", "Facilities", "CC600", "Rajesh Kumar", 3),
]

# how big a typical invoice is, per supplier category (MYR, min-max)
AMOUNT_RANGE = {
    "Office Supplies": (80, 2500), "Logistics": (300, 9000),
    "IT Services": (1500, 45000), "Facilities": (200, 12000),
    "Catering": (150, 4000), "Marketing": (2000, 60000),
    "Utilities": (400, 6000), "Professional Fees": (3000, 35000),
    "Travel": (300, 8000), "Training": (1000, 15000),
}

# which departments usually buy from which category
BUYERS = {
    "Office Supplies": ["D01", "D02", "D03", "D04", "D05", "D06"],
    "Logistics": ["D04"], "IT Services": ["D03"], "Facilities": ["D06"],
    "Catering": ["D02", "D05", "D04"], "Marketing": ["D05"],
    "Utilities": ["D06"], "Professional Fees": ["D01"],
    "Travel": ["D02", "D05", "D04"], "Training": ["D02"],
}


def random_invoice_date():
    """Most days are quiet; the last week of each month is busy (month-end rush)."""
    while True:
        d = START + timedelta(days=random.randint(0, (TODAY - START).days))
        next_month = (d.replace(day=28) + timedelta(days=4)).replace(day=1)
        month_end_week = (next_month - d).days <= 7
        if month_end_week or random.random() < 0.55:
            return d


def make_invoices():
    dept_by_id = {d[0]: d for d in DEPARTMENTS}
    rows = []
    for n in range(1, 1601):
        sup_id, _, category, terms = random.choice(SUPPLIERS)
        dept_id = random.choice(BUYERS[category])
        approve_typical = dept_by_id[dept_id][4]

        invoice_date = random_invoice_date()
        received_date = invoice_date + timedelta(days=random.randint(0, 6))
        due_date = invoice_date + timedelta(days=terms)
        lo, hi = AMOUNT_RANGE[category]
        amount = round(random.uniform(lo, hi), 2)

        # how long approval and payment take
        approve_days = max(0, int(random.gauss(approve_typical, approve_typical * 0.5)))
        approved_date = received_date + timedelta(days=approve_days)
        pay_days = random.randint(2, 20)
        if category == "Logistics":             # story: logistics suppliers get paid late
            pay_days += random.randint(10, 30)
        paid_date = approved_date + timedelta(days=pay_days)

        # what the status is on the day of the export
        roll = random.random()
        if roll < 0.03:
            status, approved_date, paid_date = "Rejected", None, None
        elif roll < 0.05:
            status, approved_date, paid_date = "On Hold", None, None
        elif received_date > TODAY:
            continue                            # not arrived yet, skip
        elif approved_date > TODAY:
            status, approved_date, paid_date = "Pending Approval", None, None
        elif paid_date > TODAY:
            status, paid_date = "Approved", None
        else:
            status = "Paid"

        rows.append({
            "invoice_no": f"INV-{26000 + n}",
            "supplier_id": sup_id,
            "dept_id": dept_id,
            "invoice_date": invoice_date,
            "received_date": received_date,
            "due_date": due_date,
            "amount_myr": amount,
            "status": status,
            "approved_date": approved_date,
            "paid_date": paid_date,
        })

    # two credit notes: a supplier refunding us, so the amount is negative (real, not a mistake)
    for row in random.sample([r for r in rows if r["status"] == "Paid"], 2):
        row["amount_myr"] = -abs(row["amount_myr"])
    return rows


def add_mistakes(rows):
    """The kind of mess a real export from a Finance system has. Power Query cleans these."""
    for row in rows:
        r = random.random()
        if r < 0.15:                            # some dates typed the Malaysian way, dd/mm/yyyy
            row["invoice_date"] = row["invoice_date"].strftime("%d/%m/%Y")
        if random.random() < 0.05:              # some amounts exported as text, "RM 1,234.50"
            row["amount_myr"] = f"RM {row['amount_myr']:,.2f}"
        if random.random() < 0.02:              # some rows missing their department
            row["dept_id"] = ""
    for row in random.sample(rows, 18):         # some invoices exported twice
        rows.append(dict(row))
    random.shuffle(rows)
    return rows


def write(name, header, rows):
    OUT.mkdir(exist_ok=True)
    with open(OUT / name, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for row in rows:
            w.writerow(["" if v is None else v for v in row])
    print(f"wrote data/{name}: {len(rows)} rows")


if __name__ == "__main__":
    write("suppliers.csv", ["supplier_id", "supplier_name", "category", "payment_terms_days"],
          [(i, n + ("  " if random.random() < 0.2 else ""), c, t) for i, n, c, t in SUPPLIERS])
    write("departments.csv", ["dept_id", "dept_name", "cost_centre", "approver"],
          [d[:4] for d in DEPARTMENTS])
    invoices = add_mistakes(make_invoices())
    header = list(invoices[0].keys())
    write("invoices.csv", header, [[r[h] for h in header] for r in invoices])

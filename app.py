from __future__ import annotations
import argparse, sys, os
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List

from dateutil import parser as dateparser
from sqlalchemy import (create_engine, Column, Integer, String, Date, Numeric,
                        ForeignKey, UniqueConstraint, func)
from sqlalchemy.orm import declarative_base, relationship, Session
from tabulate import tabulate
import smtplib
from email.message import EmailMessage
from email_utils import send_budget_alert  
import os

DB_URL = os.getenv("DB_URL", "sqlite:////data/expenses.db")
ALERT_THRESHOLD_DEFAULT = 0.10
ALERT_EMAIL = os.getenv("ALERT_EMAIL")
ALERT_EMAIL_PASSWORD = os.getenv("ALERT_EMAIL_PASSWORD")

Base = declarative_base()

def to_decimal(val) -> Decimal:
    return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def send_email_alert(recipient, subject, body):
    if not ALERT_EMAIL or not ALERT_EMAIL_PASSWORD:
        return
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = ALERT_EMAIL
    msg["To"] = recipient
    msg.set_content(body)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(ALERT_EMAIL, ALERT_EMAIL_PASSWORD)
        smtp.send_message(msg)


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    budgets = relationship("Budget", back_populates="category")
    expenses = relationship("Expense", back_populates="category")

class Budget(Base):
    __tablename__ = "budgets"
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    amount = Column(Numeric(12,2), nullable=False)
    month = Column(String, nullable=True)  
    alert_threshold = Column(Numeric(4,2), nullable=True)  
    category = relationship("Category", back_populates="budgets")
    __table_args__ = (UniqueConstraint("category_id", "month", name="_cat_month_uc"),)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String)

class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

class GroupMember(Base):
    __tablename__ = "group_members"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    __table_args__ = (UniqueConstraint("user_id", "group_id"),)

class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    amount = Column(Numeric(12,2), nullable=False)
    note = Column(String, nullable=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    paid_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    category = relationship("Category", back_populates="expenses")

    def __repr__(self):
        return (
            f"<Expense id={self.id}, category_id={self.category_id}, "
            f"amount={float(self.amount)}, date={self.date}, note='{self.note}'>"
        )

engine = create_engine(DB_URL, echo=False, future=True)
def init_db():
    Base.metadata.create_all(engine)

def get_or_create_category(session: Session, name: str) -> Category:
    name = name.strip().title()
    cat = session.query(Category).filter_by(name=name).one_or_none()
    if not cat:
        cat = Category(name=name)
        session.add(cat)
        session.commit()
    return cat

def get_or_create_user(session: Session, name: str, email: Optional[str] = None) -> User:
    user = session.query(User).filter_by(name=name).one_or_none()
    if not user:
        user = User(name=name, email=email)
        session.add(user)
        session.commit()
    return user

def get_or_create_group(session: Session, name: str) -> Group:
    group = session.query(Group).filter_by(name=name).one_or_none()
    if not group:
        group = Group(name=name)
        session.add(group)
        session.commit()
    return group


def add_expense(amount: float, category: str, date_str: Optional[str], note: Optional[str],
                group_name: Optional[str] = None, paid_by: Optional[str] = None):
    dt = dateparser.parse(date_str).date() if date_str else date.today()
    amt = to_decimal(amount)
    with Session(engine) as s:
        cat = get_or_create_category(s, category)
        group = get_or_create_group(s, group_name) if group_name else None
        user = get_or_create_user(s, paid_by) if paid_by else None
        exp = Expense(date=dt, category=cat, amount=amt, note=note,
                      group_id=group.id if group else None,
                      paid_by_user_id=user.id if user else None)
        s.add(exp)
        s.commit()
        print(f"Added expense: {exp}")

def set_budget(category: str, amount: float, month: Optional[str], alert_threshold: Optional[float] = None):
    amt = to_decimal(amount)
    with Session(engine) as s:
        cat = get_or_create_category(s, category)
        m = month.strip() if month else None
        b = s.query(Budget).filter_by(category_id=cat.id, month=m).one_or_none()
        if b:
            b.amount = amt
            b.alert_threshold = alert_threshold
            print(f"Updated budget for {cat.name} / {m}: {amt}")
        else:
            b = Budget(category=cat, amount=amt, month=m, alert_threshold=alert_threshold)
            s.add(b)
            print(f"Set budget for {cat.name} / {m}: {amt}")
        s.commit()

def list_expenses(month: Optional[str] = None):
    with Session(engine) as s:
        q = s.query(Expense).join(Category)
        if month:
            dt_start = datetime.strptime(month + "-01", "%Y-%m-%d").date()
            dt_end = date(dt_start.year + (dt_start.month // 12), ((dt_start.month % 12) + 1), 1)
            q = q.filter(Expense.date >= dt_start, Expense.date < dt_end)
        rows = [[e.id, e.date.isoformat(), e.category.name, float(e.amount), e.note or ""] for e in q.order_by(Expense.date.desc()).all()]
        print(tabulate(rows, headers=["ID", "Date", "Category", "Amount", "Note"], tablefmt="grid"))

def total_spending_per_month(month: str) -> Decimal:
    dt_start = datetime.strptime(month + "-01", "%Y-%m-%d").date()
    dt_end = date(dt_start.year + (dt_start.month // 12), ((dt_start.month % 12) + 1), 1)
    with Session(engine) as s:
        total = s.query(func.coalesce(func.sum(Expense.amount), 0)).filter(Expense.date >= dt_start, Expense.date < dt_end).scalar()
        return to_decimal(total)

def compare_spending_vs_budget(month: str):
    dt_start = datetime.strptime(month + "-01", "%Y-%m-%d").date()
    dt_end = date(dt_start.year + (dt_start.month // 12), ((dt_start.month % 12) + 1), 1)
    with Session(engine) as s:
        cats = s.query(Category).all()
        rows = []
        for c in cats:
            spent = to_decimal(s.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
                Expense.category_id == c.id, Expense.date >= dt_start, Expense.date < dt_end).scalar())
            b = s.query(Budget).filter_by(category_id=c.id, month=month).one_or_none()
            if not b:
                b = s.query(Budget).filter_by(category_id=c.id, month=None).one_or_none()
            budget_amt = to_decimal(b.amount) if b else None
            pct = (spent / budget_amt * 100) if (budget_amt and budget_amt > 0) else None
            rows.append([c.name, float(spent), float(budget_amt) if budget_amt else "-", f"{pct:.1f}%" if pct else "-"])
        print(tabulate(rows, headers=["Category", "Spent", "Budget", "% used"], tablefmt="grid"))
  

def check_alerts(month: str):
    dt_start = datetime.strptime(month + "-01", "%Y-%m-%d").date()
    dt_end = date(dt_start.year + (dt_start.month // 12), ((dt_start.month % 12) + 1), 1)
    alerts = []

    with Session(engine) as s:
        cats = s.query(Category).all()
        for c in cats:
            spent = to_decimal(s.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
                Expense.category_id == c.id, Expense.date >= dt_start, Expense.date < dt_end).scalar())
            b = s.query(Budget).filter_by(category_id=c.id, month=month).one_or_none()
            if not b:
                b = s.query(Budget).filter_by(category_id=c.id, month=None).one_or_none()
            if not b:
                continue
            budget_amt = to_decimal(b.amount)
            threshold = float(b.alert_threshold) if getattr(b, "alert_threshold", None) else ALERT_THRESHOLD_DEFAULT
            remaining = budget_amt - spent
            if spent > budget_amt:
                alerts.append((c.name, "EXCEEDED", float(spent), float(budget_amt), float(remaining)))
            elif budget_amt > 0 and (remaining / budget_amt) <= threshold:
                alerts.append((c.name, f"LOW ({(remaining/budget_amt)*100:.1f}% left)", float(spent), float(budget_amt), float(remaining)))

    if not alerts:
        print("No alerts for", month)
        return

    print(tabulate(alerts, headers=["Category", "Alert", "Spent", "Budget", "Remaining"], tablefmt="grid"))

    user_email = os.getenv("USER_EMAIL")  
    if ALERT_EMAIL and ALERT_EMAIL_PASSWORD and user_email:
        body = "\n".join([
            f"{cat}: {status} (Spent: {spent}, Budget: {budget}, Remaining: {remaining})"
            for cat, status, spent, budget, remaining in alerts
        ])
        try:
            send_budget_alert(user_email, month + " alerts", body)
        except Exception as e:
            print("Failed to send email alert:", e)
    else:
        if not user_email:
            print("USER_EMAIL not set; email will not be sent.")


def main(argv: List[str]):
    parser = argparse.ArgumentParser(description="Expense Tracker CLI")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("init-db")
    p = sub.add_parser("add-expense")
    p.add_argument("--amount", type=float, required=True)
    p.add_argument("--category", type=str, required=True)
    p.add_argument("--date", type=str, required=False)
    p.add_argument("--note", type=str, required=False)
    p.add_argument("--group", type=str, required=False)
    p.add_argument("--paid-by", type=str, required=False)

    p = sub.add_parser("set-budget")
    p.add_argument("--category", type=str, required=True)
    p.add_argument("--amount", type=float, required=True)
    p.add_argument("--month", type=str, required=False)
    p.add_argument("--alert-threshold", type=float, required=False)

    sub.add_parser("list-expenses")
    p = sub.add_parser("show-monthly")
    p.add_argument("--month", type=str, required=True)
    p = sub.add_parser("compare")
    p.add_argument("--month", type=str, required=True)
    p = sub.add_parser("check-alerts")
    p.add_argument("--month", type=str, required=True)

    args = parser.parse_args(argv)

    if args.cmd == "init-db": init_db(); print("DB Initialized")
    elif args.cmd == "add-expense": add_expense(args.amount, args.category, args.date, args.note, args.group, args.paid_by)
    elif args.cmd == "set-budget": set_budget(args.category, args.amount, args.month, args.alert_threshold)
    elif args.cmd == "list-expenses": list_expenses()
    elif args.cmd == "show-monthly": print(total_spending_per_month(args.month))
    elif args.cmd == "compare": compare_spending_vs_budget(args.month)
    elif args.cmd == "check-alerts": check_alerts(args.month)
    else: parser.print_help()

if __name__ == "__main__":
    main(sys.argv[1:])

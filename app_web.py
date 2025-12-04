from flask import Flask, request, jsonify
from app import add_expense, list_expenses, total_spending_per_month, set_budget, compare_spending_vs_budget, check_alerts

app = Flask(__name__)

@app.route("/add-expense", methods=["POST"])
def add_expense_route():
    data = request.json
    add_expense(data['amount'], data['category'], data.get('date'), data.get('note'), data.get('group'), data.get('paid_by'))
    return jsonify({"status": "success"})

@app.route("/list-expenses", methods=["GET"])
def list_expenses_route():
    month = request.args.get("month")
    list_expenses(month)
    return jsonify({"status": "success"})

@app.route("/set-budget", methods=["POST"])
def set_budget_route():
    data = request.json
    set_budget(data['category'], data['amount'], data.get('month'), data.get('alert_threshold'))
    return jsonify({"status": "success"})

@app.route("/show-monthly", methods=["GET"])
def show_monthly():
    month = request.args.get("month")
    total = total_spending_per_month(month)
    return jsonify({"month": month, "total": float(total)})

@app.route("/compare", methods=["GET"])
def compare():
    month = request.args.get("month")
    compare_spending_vs_budget(month)
    return jsonify({"status": "success"})

@app.route("/check-alerts", methods=["GET"])
def alerts():
    month = request.args.get("month")
    check_alerts(month)
    return jsonify({"status": "success"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

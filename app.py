from flask import jsonify
import json

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    expenses = Expense.query.filter_by(user_id=user_id).all()

    total = sum(e.amount for e in expenses)

    # Categories for chart
    categories = {}
    for e in expenses:
        if e.category in categories:
            categories[e.category] += e.amount
        else:
            categories[e.category] = e.amount

    # Ensure at least some data exists to avoid empty JS error
    if not categories:
        categories = {"No Data": 0}

    return render_template("dashboard.html",
                           expenses=expenses,
                           total=total,
                           categories=json.dumps(categories))

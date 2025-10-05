from flask import Flask, render_template, request, redirect, session
import pandas as pd
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = "library_secret_key"

# ----------------- Load CSVs -----------------
login_df = pd.read_csv("login.csv")
books_df = pd.read_csv("books.csv")

# Clean borrowed/prebook columns
books_df['Borrowed By'] = pd.to_numeric(books_df['Borrowed By'], errors='coerce')
books_df['Prebook'] = pd.to_numeric(books_df['Prebook'], errors='coerce')
books_df['Due Date'] = pd.to_datetime(books_df['Due Date'], errors='coerce')

# Admin credentials
ADMIN_CREDENTIALS = {"admin": "admin123"}

# ----------------- Login Route -----------------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        reg_no = request.form["reg_no"]
        dob = request.form["dob"]

        # Admin login
        if reg_no == "admin" and dob == ADMIN_CREDENTIALS["admin"]:
            session["admin"] = True
            return redirect("/admin_dashboard")

        # Student login
        user = login_df[(login_df["Register Number"].astype(str) == reg_no) &
                        (login_df["date of birth"] == dob)]
        if not user.empty:
            session["reg_no"] = float(reg_no)
            session["name"] = user.iloc[0]["Name"]
            return redirect("/dashboard")
        else:
            return render_template("login.html", error="Invalid Register Number or DOB")
    return render_template("login.html")

# ----------------- Student Dashboard -----------------
@app.route("/dashboard", methods=["GET"])
def dashboard():
    if "reg_no" not in session:
        return redirect("/")
    reg_no = session["reg_no"]
    name = session["name"]

    df = books_df.copy()
    search_query = request.args.get("search", "")
    if search_query:
        df = df[df["Book Name"].str.contains(search_query, case=False, na=False)]

    # Notifications: Prebooked for this student and now available
    notifications = df[(df["Prebook"] == reg_no) & (df["Status"] == "Available")]

    return render_template(
        "dashboard.html",
        name=name,
        books=df.to_dict(orient="records"),
        notifications=notifications.to_dict(orient="records")
    )

# ----------------- Borrow Book -----------------
@app.route("/borrow/<int:book_id>")
def borrow(book_id):
    if "reg_no" not in session:
        return redirect("/")
    reg_no = session["reg_no"]
    global books_df

    idx = books_df.index[books_df["S.No"] == book_id][0]
    if books_df.at[idx, "Status"] == "Available":
        books_df.at[idx, "Status"] = "Borrowed"
        books_df.at[idx, "Borrowed By"] = reg_no
        books_df.at[idx, "Due Date"] = datetime.now() + timedelta(days=14)
        history = f"{int(reg_no)} ({datetime.now().strftime('%d-%m-%Y')})"
        if pd.isna(books_df.at[idx, "Borrow History"]):
            books_df.at[idx, "Borrow History"] = history
        else:
            books_df.at[idx, "Borrow History"] += "; " + history
    return redirect("/dashboard")

# ----------------- Return Book -----------------
@app.route("/return/<int:book_id>")
def return_book(book_id):
    if "reg_no" not in session:
        return redirect("/")
    reg_no = session["reg_no"]
    global books_df

    idx = books_df.index[books_df["S.No"] == book_id][0]
    if books_df.at[idx, "Status"] == "Borrowed" and books_df.at[idx, "Borrowed By"] == reg_no:
        books_df.at[idx, "Status"] = "Available"
        books_df.at[idx, "Borrowed By"] = None
        books_df.at[idx, "Due Date"] = None
    return redirect("/dashboard")

# ----------------- Prebook Book -----------------
@app.route("/prebook/<int:book_id>")
def prebook(book_id):
    if "reg_no" not in session:
        return redirect("/")
    reg_no = session["reg_no"]
    global books_df

    idx = books_df.index[books_df["S.No"] == book_id][0]
    if pd.isna(books_df.at[idx, "Prebook"]):
        books_df.at[idx, "Prebook"] = reg_no
    return redirect("/dashboard")

# ----------------- Admin Dashboard -----------------
@app.route("/admin_dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect("/")
    df = books_df.copy()
    return render_template("admin_dashboard.html", books=df.to_dict(orient="records"))

# ----------------- Logout -----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ----------------- Run App (Render Compatible) -----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render assigns the port automatically
    app.run(host="0.0.0.0", port=port, debug=True)

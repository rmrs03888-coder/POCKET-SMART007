import json
import os
import sqlite3
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from gemini_utils import (
    generate_home_recommendations,
    generate_party_recommendations,
    generate_jewelry_recommendations,
)

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "pocketsmart.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "pocketsmart-demo-secret")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            planner_type TEXT NOT NULL,
            title TEXT NOT NULL,
            budget REAL NOT NULL,
            remaining REAL NOT NULL,
            input_json TEXT NOT NULL,
            result_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )
    conn.commit()
    conn.close()


init_db()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_recommendation(planner_type, data, result):
    username = session.get("user")
    if not username or not result:
        return
    conn = get_db()
    conn.execute(
        """
        INSERT INTO recommendations
        (username, planner_type, title, budget, remaining, input_json, result_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            username,
            planner_type,
            result.get("title", f"{planner_type.title()} Budget Plan"),
            float(data.get("total_budget", 0)),
            float(result.get("remaining_budget", 0)),
            json.dumps(data),
            json.dumps(result),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    conn.commit()
    conn.close()


@app.context_processor
def inject_user():
    return {"user": session.get("user")}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not email or not password or not confirm_password:
            flash("Please fill in all fields.", "error")
            return render_template("register.html")
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html")
        if len(password) < 6:
            flash("Password must contain at least 6 characters.", "error")
            return render_template("register.html")

        conn = get_db()
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (username, email),
        ).fetchone()
        if existing:
            conn.close()
            flash("Username or email already exists. Please use another one.", "error")
            return render_template("register.html")

        conn.execute(
            "INSERT INTO users (username, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (username, email, generate_password_hash(password), datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        conn.close()

        session["user"] = username
        flash("Account created successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        conn = get_db()
        user_row = conn.execute(
            "SELECT username, password_hash FROM users WHERE username = ?", (username,)
        ).fetchone()
        conn.close()

        if user_row and check_password_hash(user_row["password_hash"], password):
            session["user"] = username
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "error")

    return render_template("login.html")


@app.route("/forgot-password")
def forgot_password():
    flash("Password recovery is a demo placeholder. Use the registered password for this student project.", "error")
    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
def dashboard():
    if not session.get("user"):
        return redirect(url_for("login"))
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM recommendations WHERE username = ? ORDER BY id DESC LIMIT 3",
        (session["user"],),
    ).fetchall()
    conn.close()
    return render_template("dashboard.html", recent=rows)


@app.route("/history")
def history():
    if not session.get("user"):
        return redirect(url_for("login"))
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM recommendations WHERE username = ? ORDER BY id DESC",
        (session["user"],),
    ).fetchall()
    conn.close()
    return render_template("history.html", recommendations=rows)


@app.route("/history/<int:recommendation_id>")
def history_detail(recommendation_id):
    if not session.get("user"):
        return redirect(url_for("login"))
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM recommendations WHERE id = ? AND username = ?",
        (recommendation_id, session["user"]),
    ).fetchone()
    conn.close()
    if not row:
        flash("Recommendation not found.", "error")
        return redirect(url_for("history"))
    result = json.loads(row["result_json"])
    return render_template("history_detail.html", record=row, result=result)


@app.route("/home-planner", methods=["GET", "POST"])
def home_planner():
    result = None
    form_data = {}
    if request.method == "POST":
        try:
            form_data = {
                "total_budget": float(request.form.get("total_budget", 0)),
                "rooms": request.form.getlist("rooms"),
                "num_lights": int(request.form.get("num_lights", 0)),
                "num_fans": int(request.form.get("num_fans", 0)),
                "num_furniture": int(request.form.get("num_furniture", 0)),
                "num_dining_tables": int(request.form.get("num_dining_tables", 0)),
                "additional_requirements": request.form.get("additional_requirements", "").strip(),
            }
            if form_data["total_budget"] <= 0:
                raise ValueError
            result = generate_home_recommendations(form_data)
            save_recommendation("home", form_data, result)
        except (ValueError, TypeError):
            flash("Please enter valid budget and quantity values.", "error")
    return render_template("home_planner.html", result=result, form_data=form_data)


@app.route("/party-planner", methods=["GET", "POST"])
def party_planner():
    result = None
    form_data = {}
    if request.method == "POST":
        try:
            form_data = {
                "total_budget": float(request.form.get("total_budget", 0)),
                "party_type": request.form.get("party_type", "Birthday"),
                "num_guests": int(request.form.get("num_guests", 0)),
                "venue_type": request.form.get("venue_type", "Home"),
                "needs_catering": request.form.get("needs_catering") == "yes",
                "needs_decoration": request.form.get("needs_decoration") == "yes",
                "needs_entertainment": request.form.get("needs_entertainment") == "yes",
                "additional_requirements": request.form.get("additional_requirements", "").strip(),
            }
            if form_data["total_budget"] <= 0 or form_data["num_guests"] <= 0:
                raise ValueError
            result = generate_party_recommendations(form_data)
            save_recommendation("party", form_data, result)
        except (ValueError, TypeError):
            flash("Please enter valid budget and guest values.", "error")
    return render_template("party_planner.html", result=result, form_data=form_data)


@app.route("/jewelry-planner", methods=["GET", "POST"])
def jewelry_planner():
    result = None
    uploaded_image = None
    form_data = {}

    if request.method == "POST":
        try:
            budget = float(request.form.get("total_budget", 0))
            occasion = request.form.get("occasion", "Birthday")
            style = request.form.get("style", "Traditional")
            additional_requirements = request.form.get("additional_requirements", "").strip()
            if budget <= 0:
                raise ValueError

            image_path = None
            file = request.files.get("outfit_image")
            if file and file.filename:
                if not allowed_file(file.filename):
                    flash("Only PNG, JPG, JPEG and WEBP images are allowed.", "error")
                    return render_template("jewelry_planner.html", result=None, uploaded_image=None, form_data=request.form)
                safe_name = secure_filename(file.filename)
                unique_name = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{safe_name}"
                save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
                file.save(save_path)
                image_path = save_path
                uploaded_image = url_for("static", filename=f"uploads/{unique_name}")

            form_data = {
                "total_budget": budget,
                "occasion": occasion,
                "style": style,
                "additional_requirements": additional_requirements,
            }
            result = generate_jewelry_recommendations(form_data, image_path)
            save_recommendation("jewelry", form_data, result)
        except (ValueError, TypeError):
            flash("Please enter a valid budget.", "error")

    return render_template("jewelry_planner.html", result=result, uploaded_image=uploaded_image, form_data=form_data)


@app.errorhandler(413)
def too_large(_error):
    flash("Image is too large. Please upload an image below 5 MB.", "error")
    return redirect(url_for("jewelry_planner"))


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)

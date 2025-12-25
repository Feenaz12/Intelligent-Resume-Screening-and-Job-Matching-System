# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session
from main import match_resumes
from resume_parser import parse_resume
from jd_parser import extract_job_title, extract_job_title_from_text
import os
import PyPDF2
from functools import wraps
from database import create_user, verify_user, get_user_history

# ------------------- App Setup -------------------
app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# ------------------- Helpers -------------------
RESUME_DATA = {}  # {path: parsed_data}
JD_RESULTS = []   # [{jd_name, jd_path, results}]

def get_resume_name_from_filename(filename):
    return " ".join(part.capitalize() for part in os.path.splitext(filename)[0].replace("_", " ").split())

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "danger")
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper

# ------------------- Auth Routes -------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash("Passwords do not match", "danger")
            return redirect(url_for("signup"))

        try:
            create_user(username, email, password)
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
            return redirect(url_for("signup"))

        flash("Signup successful! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("identifier")  # email or username
        password = request.form.get("password")

        user = verify_user(identifier, password)
        if not user:
            flash("Invalid username/email or password", "danger")
            return redirect(url_for("login"))

        session["user_id"] = user["id"]
        session["username"] = user["username"]

        flash(f"Welcome {user['username']}!", "success")
        return redirect(url_for("index"))

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))

# ------------------- Index / Upload & Matching -------------------
@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    global JD_RESULTS
    if request.method == "POST":
        jd_files = request.files.getlist("job_description")
        jd_text_input = request.form.get("job_description_text", "").strip()

        if not jd_files and not jd_text_input:
            flash("Please provide at least one Job Description.", "danger")
            return redirect(url_for("index"))

        resume_files = []
        for resume in request.files.getlist("resumes"):
            if not resume.filename:
                continue
            rpath = os.path.join(app.config["UPLOAD_FOLDER"], resume.filename)
            resume.save(rpath)
            if os.path.getsize(rpath) == 0:
                continue
            resume_files.append(rpath)
            parsed = parse_resume(rpath)
            parsed["resume_name"] = get_resume_name_from_filename(resume.filename)
            parsed["file_name"] = resume.filename
            RESUME_DATA[rpath] = parsed

        if not resume_files:
            flash("No valid resumes uploaded.", "danger")
            return redirect(url_for("index"))

        jd_results = []

        # ---------- Process JD PDFs ----------
        for jd_file in jd_files:
            if not jd_file.filename:
                continue
            jd_path = os.path.join(app.config["UPLOAD_FOLDER"], jd_file.filename)
            jd_file.save(jd_path)
            if os.path.getsize(jd_path) == 0:
                continue
            try:
                results = match_resumes(resume_files, jd_path, user_id=session["user_id"])
                jd_title = extract_job_title(jd_path).strip()
            except PyPDF2.errors.EmptyFileError:
                continue

            results.sort(key=lambda x: x["factor_scores"]["overall_score"], reverse=True)
            jd_results.append({"jd_name": jd_title, "jd_path": jd_path, "results": results})

        # ---------- Process pasted JD ----------
        if jd_text_input:
            jd_path = os.path.join(app.config["UPLOAD_FOLDER"], "pasted_jd.txt")
            with open(jd_path, "w", encoding="utf-8") as f:
                f.write(jd_text_input)

            results = match_resumes(resume_files, jd_path, user_id=session["user_id"])
            jd_title = extract_job_title_from_text(jd_text_input).strip()

            results.sort(key=lambda x: x["factor_scores"]["overall_score"], reverse=True)
            jd_results.append({"jd_name": jd_title, "jd_path": jd_path, "results": results})

        JD_RESULTS = jd_results
        flash("Matching completed! Results are saved in your history.", "success")
        return render_template("results.html", jd_results=jd_results, viewing_history=False)

    return render_template("index.html")

# ------------------- Replace Resume -------------------
@app.route("/replace_resume", methods=["POST"])
@login_required
def replace_resume():
    global JD_RESULTS, RESUME_DATA
    old_file_name = request.form.get("file_name")
    new_resume = request.files.get("new_resume")

    if not JD_RESULTS or not old_file_name or not new_resume or not new_resume.filename:
        flash("Invalid replace request.", "danger")
        return redirect(url_for("index"))

    # Find the old path
    old_path = next((path for path, data in RESUME_DATA.items() if data["file_name"] == old_file_name), None)
    if not old_path:
        flash("Resume not found.", "danger")
        return redirect(url_for("index"))

    # Save new file
    new_path = os.path.join(app.config["UPLOAD_FOLDER"], new_resume.filename)
    new_resume.save(new_path)
    if os.path.exists(old_path):
        os.remove(old_path)

    # Parse new resume
    parsed = parse_resume(new_path)
    parsed["resume_name"] = get_resume_name_from_filename(new_resume.filename)
    parsed["file_name"] = new_resume.filename

    # Update RESUME_DATA
    RESUME_DATA.pop(old_path)
    RESUME_DATA[new_path] = parsed

    # Update JD_RESULTS only for this resume
    for jd in JD_RESULTS:
        for idx, res in enumerate(jd["results"]):
            if res["file_name"] == old_file_name:
                # Re-match this single resume
                single_result = match_resumes([new_path], jd["jd_path"], user_id=session["user_id"])
                if single_result:
                    jd["results"][idx] = single_result[0]

    flash("Resume replaced successfully!", "success")
    return render_template("results.html", jd_results=JD_RESULTS, viewing_history=False)

# ------------------- Delete Resume -------------------
@app.route("/delete_resume", methods=["POST"])
@login_required
def delete_resume():
    global JD_RESULTS, RESUME_DATA
    file_name = request.form.get("file_name")

    if not JD_RESULTS or not file_name:
        flash("Invalid delete request.", "danger")
        return redirect(url_for("index"))

    resume_path = next((path for path, data in RESUME_DATA.items() if data["file_name"] == file_name), None)
    if resume_path and os.path.exists(resume_path):
        os.remove(resume_path)
    if resume_path:
        RESUME_DATA.pop(resume_path)

    # Remove from JD_RESULTS
    for jd in JD_RESULTS:
        jd["results"] = [res for res in jd["results"] if res["file_name"] != file_name]

    flash("Resume deleted successfully.", "success")
    return render_template("results.html", jd_results=JD_RESULTS, viewing_history=False)

# ------------------- History Page with Job Title & Date -------------------
@app.route("/history")
@login_required
def history():
    rows = get_user_history(session["user_id"])
    if not rows:
        return render_template("results.html", jd_results=[], viewing_history=True)

    jd_map = {}
    for r in rows:
        # Extract only the Job Title
        jd_name = r["job_description"].split("\n")[0].replace("Job Title:", "").strip()
        created_at = r.get("created_at")
        created_at_str = created_at.strftime("%Y-%m-%d %H:%M:%S") if created_at else "N/A"

        jd_map.setdefault(jd_name, []).append({
            "resume_name": r["resume_name"],
            "file_name": "",  # No actions in history
            "created_at": created_at_str,
            "factor_scores": {
                "overall_score": float(r["match_score"]),
                "skills_matched": r["skills_matched"].split(", ") if r["skills_matched"] else [],
                "skills_missing": r["skills_missing"].split(", ") if r["skills_missing"] else [],
                "education_score": r["education_score"],
                "experience_score": r["experience_score"],
                "semantic_score": float(r["semantic_score"])
            }
        })

    # Prepare jd_results like current results
    jd_results = [{"jd_name": jd, "results": res_list, "is_history": True} for jd, res_list in jd_map.items()]

    return render_template("results.html", jd_results=jd_results, viewing_history=True)

# ------------------- Current Results Page -------------------
@app.route("/current_results")
@login_required
def current_results():
    if not JD_RESULTS:
        flash("No current results available. Please upload resumes and job descriptions.", "info")
        return redirect(url_for("index"))
    return render_template("results.html", jd_results=JD_RESULTS, viewing_history=False)

# ------------------- Run App -------------------
if __name__ == "__main__":
    app.run(debug=True)

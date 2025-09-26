# app.py
import os
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import jwt
from functools import wraps
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Import your helper functions (these must exist in synth.py & db_connection.py)
from synth import (
    save_upload_metadata,
    generate_synthetic_from_csv,
    plot_real_vs_synthetic_single,
    save_synthetic_to_mysql
)
from db_connection import init_db

# ---------------- CONFIG ----------------
UPLOAD_FOLDER = "data/raw"
SYN_FOLDER = "data/synthetic"
PLOTS_FOLDER = "plots"
ALLOWED_EXTENSIONS = {"csv"}

JWT_SECRET = os.getenv("JWT_SECRET", "replace-with-strong-secret")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SYN_FOLDER, exist_ok=True)
os.makedirs(PLOTS_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
CORS(app)

init_db()
print("✅ Database initialized successfully!") # ensure DB tables exist

# ---------------- AUTH ----------------
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            parts = request.headers["Authorization"].split()
            if len(parts) == 2 and parts[0] == "Bearer":
                token = parts[1]
        if not token:
            return jsonify({"message": "Token is missing!"}), 401
        try:
            jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except Exception as e:
            return jsonify({"message": "Token is invalid!", "error": str(e)}), 401
        return f(*args, **kwargs)
    return decorated


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if username == "admin" and password == "admin123":
        token = jwt.encode(
            {"user": username, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=12)},
            JWT_SECRET,
            algorithm="HS256",
        )
        return jsonify({"status": "success", "token": token})
    return jsonify({"status": "fail", "message": "Invalid credentials"}), 401


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------------- FILE UPLOADS ----------------
@app.route("/api/upload", methods=["POST"])
@token_required
def upload_file():
    if "file" not in request.files:
        return jsonify({"message": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"message": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(save_path)
        save_upload_metadata(filename)
        return jsonify({"message": "File uploaded", "filename": filename}), 200
    return jsonify({"message": "Invalid file type"}), 400


@app.route("/api/datasets", methods=["GET"])
@token_required
def list_datasets():
    files = os.listdir(UPLOAD_FOLDER)
    csvs = [f for f in files if f.lower().endswith(".csv")]
    return jsonify({"datasets": csvs})


@app.route("/api/dataset/<filename>", methods=["GET"])
@token_required
def dataset_preview(filename):
    path = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
    if not os.path.exists(path):
        return jsonify({"message": "Not found"}), 404
    df = pd.read_csv(path, nrows=50)
    return jsonify({"preview": df.to_dict(orient="records")})

# ---------------- SYNTHETIC GENERATION ----------------
@app.route("/api/generate", methods=["POST"])
@token_required
def generate():
    payload = request.get_json() or {}
    filename = payload.get("filename")
    n_rows = int(payload.get("n_rows", 1000))
    epochs = int(payload.get("epochs", 100))

    if not filename:
        return jsonify({"message": "filename required"}), 400

    csv_path = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
    if not os.path.exists(csv_path):
        return jsonify({"message": "file not found"}), 404

    try:
        synthetic_df, out_csv, real_df = generate_synthetic_from_csv(csv_path, n_rows=n_rows, epochs=epochs)

        # Save to MySQL
        inserted = save_synthetic_to_mysql(synthetic_df)

        # Save plot
        numeric_columns = [col for col in real_df.columns if pd.api.types.is_numeric_dtype(real_df[col])]
        plot_path = os.path.join(PLOTS_FOLDER, f"{os.path.splitext(filename)[0]}_real_vs_synth_{n_rows}.png")
        plot_real_vs_synthetic_single(real_df, synthetic_df, numeric_columns, out_path=plot_path)

        return jsonify({
            "message": "Synthetic generated",
            "synthetic_csv": out_csv,
            "plot": plot_path,
            "rows_inserted_to_db": inserted
        })
    except Exception as e:
        return jsonify({"message": "Error during generation", "error": str(e)}), 500


@app.route("/api/results", methods=["GET"])
@token_required
def results():
    files = os.listdir(SYN_FOLDER)
    csvs = [f for f in files if f.lower().endswith(".csv")]
    return jsonify({"synthetic_files": csvs})


@app.route("/api/download", methods=["GET"])
@token_required
def download():
    path = request.args.get("path")
    if not path:
        return jsonify({"message": "path param required"}), 400
    full = os.path.abspath(path)
    if not os.path.exists(full):
        return jsonify({"message": "file not available"}), 404
    return send_file(full, as_attachment=True)

# ---------------- EXTRA ENDPOINTS for dataset.js ----------------
@app.route("/api/sample", methods=["GET"])
@token_required
def get_sample():
    """Return first 10 rows of the first uploaded dataset."""
    files = os.listdir(UPLOAD_FOLDER)
    if not files:
        return jsonify([])
    path = os.path.join(UPLOAD_FOLDER, files[0])
    df = pd.read_csv(path)
    return jsonify(df.head(10).to_dict(orient="records"))

@app.route("/api/synthetic-preview", methods=["GET"])
@token_required
def get_synthetic_preview():
    """Return first 10 rows of the latest synthetic dataset."""
    files = sorted(os.listdir(SYN_FOLDER))
    if not files:
        return jsonify([])
    path = os.path.join(SYN_FOLDER, files[-1])
    df = pd.read_csv(path)
    return jsonify(df.head(10).to_dict(orient="records"))


# backend connection to database.
@app.route("/api/test-db")
def test_db():
    try:
        from db_connection import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DATABASE();")
        db_name = cursor.fetchone()
        cursor.close()
        conn.close()
        return jsonify({"status": "connected", "database": db_name})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})


# ---------------- MAIN ----------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)

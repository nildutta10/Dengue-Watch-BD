from flask import Flask, jsonify, request
import sqlite3
from datetime import datetime

app = Flask(__name__)

DATABASE = "dengue.db"
from contextlib import closing
import sqlite3
from flask import jsonify, request


def _parse_non_negative_int(value):
    if isinstance(value, bool) or value is None:
        raise ValueError("Boolean or null is not a valid integer.")
    if isinstance(value, str):
        value = value.strip()
        if not value:
            raise ValueError("Empty string is not a valid integer.")
    parsed = int(value)
    if parsed < 0:
        raise ValueError("Value must be non-negative.")
    return parsed


def _validate_report_payload(data, require_all_fields=True):
    if not isinstance(data, dict):
        return None, (jsonify({"error": "Invalid JSON payload."}), 400)

    required = ["district", "area", "report_date", "affected", "deaths", "recovered"]
    if require_all_fields:
        missing = []
        for field in required:
            val = data.get(field)
            if val is None or (isinstance(val, str) and not val.strip()):
                missing.append(field)
        if missing:
            return None, (jsonify({"error": "Missing or blank required fields.", "fields": missing}), 400)

    try:
        affected = _parse_non_negative_int(data["affected"])
        deaths = _parse_non_negative_int(data["deaths"])
        recovered = _parse_non_negative_int(data["recovered"])
    except (TypeError, ValueError):
        return None, (
            jsonify({"error": "affected, deaths, and recovered must be non-negative integers."}),
            400,
        )

    if deaths > affected or recovered > affected or (deaths + recovered) > affected:
        return None, (
            jsonify({"error": "deaths and recovered cannot exceed affected, and their sum cannot exceed affected."}),
            400,
        )

    district = str(data["district"]).strip()
    area = str(data["area"]).strip()
    report_date = str(data["report_date"]).strip()

    if not district or not area or not report_date:
        return None, (jsonify({"error": "district, area, and report_date cannot be empty."}), 400)

    raw_source = data.get("source")
    source = str(raw_source).strip() if raw_source is not None else "Demo / manually entered"
    if not source:
        source = "Demo / manually entered"

    raw_notes = data.get("notes")
    notes = str(raw_notes).strip() if raw_notes is not None else ""

    active_cases = affected - deaths - recovered

    return {
        "district": district,
        "area": area,
        "report_date": report_date,
        "affected": affected,
        "deaths": deaths,
        "recovered": recovered,
        "active_cases": active_cases,
        "source": source,
        "notes": notes,
    }, None

app = Flask(__name__)

@app.get("/api/districts")
def districts():
    try:
        with closing(get_db()) as db:
            rows = db.execute("""
                SELECT district,
                       COALESCE(SUM(affected), 0) AS affected,
                       COALESCE(SUM(deaths), 0) AS deaths,
                       COALESCE(SUM(recovered), 0) AS recovered,
                       COALESCE(SUM(active_cases), 0) AS active_cases,
                       MAX(report_date) AS last_updated
                FROM reports
                GROUP BY district
                ORDER BY affected DESC
            """).fetchall()
        return jsonify([dict(r) for r in rows])
    except sqlite3.Error as exc:
        return jsonify({"error": "Database error while fetching districts.", "detail": str(exc)}), 500

app = Flask(__name__)

@app.get("/api/reports")
def reports():
    district = request.args.get("district", type=str)
    district = district.strip() if district else None
    try:
        with closing(get_db()) as db:
            if district:
                rows = db.execute(
                    "SELECT * FROM reports WHERE district = ? ORDER BY report_date DESC, id DESC",
                    (district,),
                ).fetchall()
            else:
                rows = db.execute(
                    "SELECT * FROM reports ORDER BY report_date DESC, id DESC"
                ).fetchall()
        return jsonify([dict(r) for r in rows])
    except sqlite3.Error as exc:
        return jsonify({"error": "Database error while fetching reports.", "detail": str(exc)}), 500

app = Flask(__name__)

@app.get("/api/prediction")
def prediction():
    district_param = request.args.get("district", type=str)
    district = district_param.strip() if district_param and district_param.strip() else "Bangladesh"
    try:
        with closing(get_db()) as db:
            if district == "Bangladesh":
                rows = db.execute("""
                    SELECT report_date, COALESCE(SUM(affected), 0) AS affected
                    FROM reports
                    GROUP BY report_date
                    ORDER BY report_date DESC
                    LIMIT 8
                """).fetchall()
            else:
                rows = db.execute("""
                    SELECT report_date, COALESCE(SUM(affected), 0) AS affected
                    FROM reports
                    WHERE district = ?
                    GROUP BY report_date
                    ORDER BY report_date DESC
                    LIMIT 8
                """, (district,)).fetchall()

        chronological_history = [dict(r) for r in reversed(rows)]
        result = estimate_risk(chronological_history)
        if not isinstance(result, dict):
            result = {"prediction": result}
        result["district"] = district
        return jsonify(result)
    except sqlite3.Error as exc:
        return jsonify({"error": "Database error while generating prediction.", "detail": str(exc)}), 500
    except Exception as exc:
        return jsonify({"error": "Error computing risk prediction.", "detail": str(exc)}), 500

app = Flask(__name__)

@app.post("/api/reports")
def create_report():
    data = request.get_json(silent=True)
    cleaned, err_response = _validate_report_payload(data, require_all_fields=True)
    if err_response is not None:
        return err_response

    try:
        with closing(get_db()) as db:
            cur = db.execute("""
                INSERT INTO reports (
                    district, area, report_date, affected, deaths,
                    recovered, active_cases, source, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cleaned["district"],
                cleaned["area"],
                cleaned["report_date"],
                cleaned["affected"],
                cleaned["deaths"],
                cleaned["recovered"],
                cleaned["active_cases"],
                cleaned["source"],
                cleaned["notes"],
            ))
            db.commit()
            record = db.execute("SELECT * FROM reports WHERE id = ?", (cur.lastrowid,)).fetchone()

        if record is None:
            return jsonify({"error": "Report created but could not be retrieved."}), 500
        return jsonify(dict(record)), 201
    except sqlite3.Error as exc:
        return jsonify({"error": "Database error while creating report.", "detail": str(exc)}), 500

app = Flask(__name__)

@app.put("/api/reports/<int:report_id>")
def update_report(report_id):
    if report_id <= 0:
        return jsonify({"error": "Invalid report ID."}), 400

    data = request.get_json(silent=True)
    cleaned, err_response = _validate_report_payload(data, require_all_fields=True)
    if err_response is not None:
        return err_response

    try:
        with closing(get_db()) as db:
            exists = db.execute("SELECT id FROM reports WHERE id = ?", (report_id,)).fetchone()
            if not exists:
                return jsonify({"error": "Report not found."}), 404

            db.execute("""
                UPDATE reports
                SET district = ?, area = ?, report_date = ?, affected = ?,
                    deaths = ?, recovered = ?, active_cases = ?, source = ?, notes = ?
                WHERE id = ?
            """, (
                cleaned["district"],
                cleaned["area"],
                cleaned["report_date"],
                cleaned["affected"],
                cleaned["deaths"],
                cleaned["recovered"],
                cleaned["active_cases"],
                cleaned["source"],
                cleaned["notes"],
                report_id,
            ))
            db.commit()
            row = db.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()

        if row is None:
            return jsonify({"error": "Report not found after update."}), 404
        return jsonify(dict(row))
    except sqlite3.Error as exc:
        return jsonify({"error": "Database error while updating report.", "detail": str(exc)}), 500

app = Flask(__name__)

@app.delete("/api/reports/<int:report_id>")
def delete_report(report_id):
    if report_id <= 0:
        return jsonify({"error": "Invalid report ID."}), 400

    try:
        with closing(get_db()) as db:
            cur = db.execute("DELETE FROM reports WHERE id = ?", (report_id,))
            db.commit()
        if cur.rowcount == 0:
            return jsonify({"error": "Report not found."}), 404
        return jsonify({"message": "Report deleted."})
    except sqlite3.Error as exc:
        return jsonify({"error": "Database error while deleting report.", "detail": str(exc)}), 500

app = Flask(__name__)

@app.get("/api/areas")
def areas():
    district = request.args.get("district", type=str)
    district = district.strip() if district else None
    try:
        with closing(get_db()) as db:
            if district:
                rows = db.execute("""
                    SELECT area, district,
                           COALESCE(SUM(affected), 0) AS affected,
                           COALESCE(SUM(deaths), 0) AS deaths,
                           MAX(report_date) AS last_updated
                    FROM reports
                    WHERE district = ?
                    GROUP BY district, area
                    ORDER BY affected DESC
                """, (district,)).fetchall()
            else:
                rows = db.execute("""
                    SELECT area, district,
                           COALESCE(SUM(affected), 0) AS affected,
                           COALESCE(SUM(deaths), 0) AS deaths,
                           MAX(report_date) AS last_updated
                    FROM reports
                    GROUP BY district, area
                    ORDER BY affected DESC
                """).fetchall()
        return jsonify([dict(r) for r in rows])
    except sqlite3.Error as exc:
        return jsonify({"error": "Database error while fetching areas.", "detail": str(exc)}), 500


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=5000)
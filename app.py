def districts():
    db = get_db()
    rows = db.execute("""
        SELECT district, SUM(affected) affected, SUM(deaths) deaths,
               SUM(recovered) recovered, SUM(active_cases) active_cases,
               MAX(report_date) last_updated
        FROM reports GROUP BY district ORDER BY affected DESC
    """).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.get("/api/reports")
def reports():
    district = request.args.get("district")
    db = get_db()
    if district:
        rows = db.execute("SELECT * FROM reports WHERE district=? ORDER BY report_date DESC", (district,)).fetchall()
    else:
        rows = db.execute("SELECT * FROM reports ORDER BY report_date DESC, id DESC").fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.get("/api/prediction")
def prediction():
    district = request.args.get("district", "Bangladesh")
    db = get_db()
    if district == "Bangladesh":
        rows = db.execute("""
            SELECT report_date, SUM(affected) AS affected FROM reports
            GROUP BY report_date ORDER BY report_date DESC LIMIT 8
        """).fetchall()
    else:
        rows = db.execute("""
            SELECT report_date, SUM(affected) AS affected FROM reports
            WHERE district=? GROUP BY report_date ORDER BY report_date DESC LIMIT 8
        """, (district,)).fetchall()
    db.close()
    result = estimate_risk([dict(r) for r in rows])
    result["district"] = district
    return jsonify(result)

@app.post("/api/reports")
def create_report():
    data = request.get_json(silent=True) or {}
    required = ["district", "area", "report_date", "affected", "deaths", "recovered"]
    missing = [k for k in required if data.get(k) in (None, "")]
    if missing:
        return jsonify({"error": "Missing fields", "fields": missing}), 400
    try:
        affected = int(data["affected"])
        deaths = int(data["deaths"])
        recovered = int(data["recovered"])
        if min(affected, deaths, recovered) < 0 or deaths > affected or recovered > affected:
            raise ValueError()
    except (TypeError, ValueError):
        return jsonify({"error": "Counts must be non-negative integers; deaths and recovered cannot exceed affected."}), 400

    active = max(affected - deaths - recovered, 0)
    db = get_db()
    cur = db.execute("""
        INSERT INTO reports (district, area, report_date, affected, deaths, recovered, active_cases, source, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (data["district"].strip(), data["area"].strip(), data["report_date"],
          affected, deaths, recovered, active,
          data.get("source", "Demo / manually entered"), data.get("notes", "")))
    db.commit()
    record = db.execute("SELECT * FROM reports WHERE id=?", (cur.lastrowid,)).fetchone()
    db.close()
    return jsonify(dict(record)), 201

@app.put("/api/reports/<int:report_id>")
def update_report(report_id):
    data = request.get_json(silent=True) or {}
    required = ["district", "area", "report_date", "affected", "deaths", "recovered"]
    if any(data.get(k) in (None, "") for k in required):
        return jsonify({"error": "All required fields must be supplied."}), 400
    try:
        affected, deaths, recovered = int(data["affected"]), int(data["deaths"]), int(data["recovered"])
        if min(affected, deaths, recovered) < 0 or deaths > affected or recovered > affected:
            raise ValueError()
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid case counts."}), 400
    db = get_db()
    exists = db.execute("SELECT id FROM reports WHERE id=?", (report_id,)).fetchone()
    if not exists:
        db.close()
        return jsonify({"error": "Report not found."}), 404
    db.execute("""
        UPDATE reports SET district=?, area=?, report_date=?, affected=?, deaths=?,
        recovered=?, active_cases=?, source=?, notes=? WHERE id=?
    """, (data["district"], data["area"], data["report_date"], affected, deaths,
          recovered, max(affected-deaths-recovered, 0), data.get("source", ""),
          data.get("notes", ""), report_id))
    db.commit()
    row = db.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone()
    db.close()
    return jsonify(dict(row))

@app.delete("/api/reports/<int:report_id>")
def delete_report(report_id):
    db = get_db()
    cur = db.execute("DELETE FROM reports WHERE id=?", (report_id,))
    db.commit()
    db.close()
    if cur.rowcount == 0:
        return jsonify({"error": "Report not found."}), 404
    return jsonify({"message": "Report deleted."})

@app.get("/api/areas")
def areas():
    district = request.args.get("district")
    db = get_db()
    rows = db.execute("""
        SELECT area, district, SUM(affected) affected, SUM(deaths) deaths,
               MAX(report_date) last_updated
        FROM reports WHERE (? IS NULL OR district=?)
        GROUP BY district, area ORDER BY affected DESC
    """, (district, district)).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)

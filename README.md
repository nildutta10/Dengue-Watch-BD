# Dengue Watch BD

A beginner-friendly Dengue Surveillance & Risk Monitoring web app built with HTML, CSS, JavaScript, Python Flask, REST API and SQLite.

## Features
- Dashboard totals: affected, deaths, recovered and active cases
- District and area summaries
- Search/filter reports
- Add, edit and delete reports (demo admin panel; no authentication yet)
- Demonstration risk index for the next four weeks
- Chart.js visualizations
- Leaflet map with approximate district markers

## Important data notice
The included database is seeded with **illustrative demo data only**. It is not official Bangladesh dengue data and must not be presented as real statistics. The prediction is a simple demonstration score, **not a medically validated probability or forecast**. Replace sample data with verified, dated official reports. For a real forecast, collect sufficient historical time-series data and relevant factors (population, rainfall, temperature, mosquito/vector surveillance), then validate a suitable model with public-health experts.

## Requirements
- Python 3.10 or newer
- VS Code (recommended)
- Internet connection for CDN-hosted Chart.js and Leaflet assets

## Run locally (Windows)
1. Extract the ZIP and open the `dengue_watch_bd` folder in VS Code.
2. Open Terminal in VS Code.
3. Create a virtual environment:

   ```bash
   py -m venv .venv
   .venv\\Scripts\\activate
   ```

4. Install packages:

   ```bash
   pip install -r requirements.txt
   ```

5. Start the server:

   ```bash
   python app.py
   ```

6. Open this address in your browser:

   `http://127.0.0.1:5000`

The SQLite database `dengue.db` is created automatically on first run. Stop the server with `Ctrl + C`.

## API endpoints
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | API status |
| GET | `/api/summary` | Dashboard totals |
| GET | `/api/districts` | District-wise totals |
| GET | `/api/areas?district=Chattogram` | Area-wise totals |
| GET | `/api/reports` | All reports |
| GET | `/api/reports?district=Dhaka` | Filter reports |
| GET | `/api/prediction?district=Chattogram` | Demonstration risk index |
| POST | `/api/reports` | Add report |
| PUT | `/api/reports/1` | Update report ID 1 |
| DELETE | `/api/reports/1` | Delete report ID 1 |

### Example POST body
```json
{
  "district": "Chattogram",
  "area": "Panchlaish",
  "report_date": "2026-11-20",
  "affected": 35,
  "deaths": 1,
  "recovered": 28,
  "source": "Verified source name",
  "notes": "Optional notes"
}
```

Use Postman or the dashboard form to test the API. POST and PUT accept JSON.

## Project structure
```text
dengue_watch_bd/
├── app.py
├── database.py
├── predictor.py
├── requirements.txt
├── README.md
├── .gitignore
└── frontend/
    ├── index.html
    ├── style.css
    └── app.js
```

## Push to GitHub
From the project folder:

```bash
git init
git add .
git commit -m "Initial Dengue Watch BD project"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/dengue-watch-bd.git
git push -u origin main
```

Do not commit private credentials or real personal health information. `dengue.db` is ignored by Git; the app creates it locally.

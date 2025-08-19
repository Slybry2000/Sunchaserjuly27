---
name: Sprint 0 — Setup & Foundation
labels: [sprint0, setup]
---

Title: Sprint 0 — Setup & Foundation

Body:

Tasks:
- Create project environment (Firebase project or clear VPS plan)
- Register 2–3 weather APIs and store keys in `.env` (Open-Meteo, OpenWeatherMap, Weatherbit)
- Upload initial locations dataset (use `data/pnw.csv` or import GeoNames subset)
- Verify local dev server runs (`uvicorn main:app --reload`)

Acceptance criteria:
- Environment and API keys available
- Dataset accessible to backend tests
- Basic health endpoint responds

Notes:
- If using Firebase, consider Firestore rules and indexing later (Phase C).

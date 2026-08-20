# Birthlight - Human Design Blueprint Calculator

## Product overview
Aplikasi mobile untuk menghitung blueprint Human Design (Type, Authority, Profile)
berdasarkan tanggal lahir, jam lahir, dan tempat kelahiran. Perhitungan sepenuhnya
berbasis efemeris astronomi (Swiss Ephemeris) - bukan aproksimasi AI.

## Core features (MVP)
- Form input: nama, tanggal (DD-MM-YYYY), jam (HH:MM 24h), kota.
- City picker global (~24k kota) dengan pencarian real-time via geonamescache.
- Timezone otomatis via timezonefinder berdasarkan lat/lon kota.
- Kalkulasi Human Design real:
  - pyswisseph (Swiss Ephemeris) dengan `TRUE_NODE`.
  - 13 activation bodies (Sun, Earth, Moon, Nodes, 5 planet klasik, 3 planet luar).
  - Design chart = 88 derajat busur matahari sebelum kelahiran (binary search presisi).
  - Rave Mandala offset 302° (Gate 41 di 302° tropis).
  - 64 gates x 6 lines dengan urutan mandala.
  - 36 kanal, undirected graph BFS untuk konektivitas center.
  - Type, Authority, Profile ditentukan mengikuti hierarki resmi Human Design.
- Output: Type, Authority, Profile, Strategy.
- Bilingual: Bahasa Indonesia & English.
- Regression test suite (5 chart) di `backend/tests/test_human_design.py`.

## Non goals (tidak diimplementasi sesuai instruksi user)
- Visual BodyGraph.
- Incarnation Cross, Variables, interpretasi AI.
- Autentikasi, pembayaran, database persistence.

## Tech stack
- Backend: FastAPI + Python (pyswisseph, geonamescache, timezonefinder).
- Frontend: React Native (Expo Router).
- Database: MongoDB (tersedia namun tidak digunakan untuk MVP).

## Key files
- `backend/human_design.py` - mesin kalkulasi.
- `backend/server.py` - API endpoints.
- `backend/tests/test_human_design.py` - regression tests.
- `frontend/app/index.tsx` - single-screen UI.

## API endpoints
- `GET /api/cities` - kota default (curated global).
- `GET /api/cities?q=<query>&limit=<n>` - pencarian global.
- `GET /api/cities/{city_id}` - detail kota.
- `POST /api/blueprint` - hitung blueprint dari (name, birth_date, birth_time, city_id).

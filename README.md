# Trip Planner & ELD Log Generator

A full-stack application designed to generate FMCSA-compliant driver's daily log sheets and compute routes for property-carrying commercial motor vehicles.

## Overview

This application takes basic trip inputs (origin, pickup, drop-off, and cycle hours used) and automatically generates an accurate, minute-by-minute Hours of Service (HOS) itinerary. It plots the route on an interactive map and renders standard Driver's Daily Log sheets with proper duty status lines, vertical connectors, remarks brackets, and recap boxes.

### Features
*   **HOS Rules Engine**: Fully implements the property-carrying 70-hour/8-day cycle rules, including the 11-hour driving limit, 14-hour window, 30-minute break, 10-hour daily resets, and 34-hour cycle restarts.
*   **Intelligent Routing**: Uses OpenRouteService (with the `driving-hgv` heavy vehicle profile) to calculate accurate driving times. Automatically falls back to OSRM if no API key is provided.
*   **Pixel-Perfect Log Sheets**: Renders multi-day logs as scalable SVGs exactly matching the FMCSA reference grid, complete with 45° angled activity remarks under brackets for stationary segments.
*   **Modern Tech Stack**: Django REST Framework backend, React + Vite + TypeScript frontend styled with Tailwind CSS v4.

## Setup Instructions

### Backend (Django)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment (optional but recommended).
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run migrations:
   ```bash
   python manage.py migrate
   ```
5. Set your OpenRouteService API key in the environment (optional, but recommended for accurate HGV routing. If absent, the app falls back to a free public OSRM router):
   ```bash
   export ORS_API_KEY="your-api-key"
   ```
6. Start the development server:
   ```bash
   python manage.py runserver 8000
   ```

### Frontend (React + Vite)

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Ensure the `.env` file or environment variables point to the backend (by default it proxies `/api` to `http://localhost:8000` via Vite config).
4. Start the development server:
   ```bash
   npm run dev
   ```
5. Open your browser to `http://localhost:5173`.

## Assumptions & Simplifications

*   **70-Hour / 8-Day Cycle**: This app models the 70-hour/8-day limit. Because it doesn't have historical logs for the past 7 days, it treats the "Current Cycle Used" input as a single running total that only resets via a 34-hour restart. (It does not implement rolling day drop-offs).
*   **Adverse Driving Conditions**: The 2-hour adverse driving extension is not modeled.
*   **Breaks & Stops**: The app schedules a 1-hour "On Duty (Not Driving)" stop at both the pickup and drop-off locations. It also schedules a 30-minute fuel stop every 1,000 miles.

## Testing

The core HOS engine is written in pure Python without Django dependencies so it can be thoroughly unit-tested.

Run the HOS engine tests:
```bash
cd backend
python -m unittest hos.tests -v
```

## Deployment

*   **Backend**: Pre-configured for deployment on Render. Uses `dj-database-url` for PostgreSQL and `whitenoise` for static file serving. A `Procfile` is included.
*   **Frontend**: Designed to be deployed on Vercel. A `vercel.json` is included to handle SPA routing rewrites.

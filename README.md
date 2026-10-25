# Car Dealership Inventory System

## Overview
A full-stack inventory application built with FastAPI, SQLite,
React, and Tailwind CSS.

## Features
- Registration and JWT login
- Protected vehicle endpoints
- Vehicle creation, listing, editing, and deletion
- Search by make, model, category, and price range
- Purchasing with atomic stock updates
- Admin-only deletion and restocking
- Responsive member and administrator interfaces

## Project Structure
Explain the backend/app, backend/tests, frontend/src/api,
frontend/src/components, and docs folders.

## Local Setup
Include prerequisites, virtual environment activation, dependency
installation, JWT_SECRET configuration, and both server commands.

## Administrator Setup
Register an account, then run from backend:
python -m app.admin your-email@example.com

Sign out and sign in again to refresh the displayed role.

## Running Tests
Backend:
python -m pytest -q --cov=app --cov-report=term-missing

Frontend:
npm test

Production build:
npm run build

## Test Results
- Backend: 78 passed
- Backend statement coverage: 92%
- Frontend: enter the verified result
- Production build: passed

Reports are available under docs/.

## Design Decisions
- SQLite provides persistent local storage without a separate server.
- Prices use Decimal validation and integer cents in the database.
- Conditional SQL updates prevent purchasing more than available stock.
- Passwords use salted scrypt hashes.
- JWTs expire after one hour.
- Tokens remain in browser memory; refreshing requires signing in.
- Backend permission checks enforce administrator access.


## Known Limitations
- No payment processing or purchase-history ledger.
- SQLite has limited concurrent write throughput.
- PUT replaces quantity and can overwrite concurrent stock changes.
- Existing database schema changes require a migration.
- The application has not undergone a production security audit.

## My AI Usage
Write your own honest account of which AI tools you used,
how you used them, what you reviewed or changed, and what you learned.
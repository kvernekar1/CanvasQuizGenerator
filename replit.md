# QTI Converter

A browser-based tool that converts PDF or DOCX files into QTI (Question & Test Interoperability) XML packages, with no server uploads required.

## Run & Operate

- **Start**: `python3 -m http.server 5000 --bind 0.0.0.0`
- No environment variables required for the frontend.
- `main.py` is a standalone script (requires `GOOGLE_API_KEY` and `pdfplumber`) — not part of the web server.

## Stack

- Pure static frontend: HTML, CSS, vanilla JavaScript
- Python 3.12 (for serving static files via `http.server`)
- No build step, no bundler, no package manager

## Where things live

- `index.html` — main page
- `styles.css` — all styles
- `app.js` — frontend logic (drag/drop, conversion, download)
- `json_to_qti.py` — Python library for generating QTI XML + ZIP packages
- `main.py` — standalone CLI script using Gemini AI to convert a PDF quiz to QTI

## Architecture decisions

- The frontend conversion is a placeholder (generates stub QTI XML client-side).
- Real conversion uses `main.py` + Google Gemini AI + `json_to_qti.py` as a CLI pipeline.
- Static deployment is appropriate since the web UI runs entirely in the browser.

## Product

Users drop a PDF or DOCX file into the web interface, click Convert, and download a `.qti` XML file. The Python CLI pipeline (`main.py`) performs real AI-powered conversion using Google Gemini.

## User preferences

_Populate as you build_

## Gotchas

- `main.py` has a hardcoded PDF filename and API key — it is a dev script, not production code.
- The web frontend generates placeholder QTI XML (not a real conversion).

## Pointers

- QTI spec: http://www.imsglobal.org/xsd/ims_qtiasiv1p2

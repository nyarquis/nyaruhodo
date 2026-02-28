# Nyaruhodo!

Nyaruhodo! is a Flask web application that detects mismatches between a file's declared extension and its true binary format. It does this by reading the file's magic bytes (its binary signature), extracting embedded metadata from supported types, and optionally querying the VirusTotal database by SHA-256 hash.

The project is licensed under the GNU Affero General Public License v3.0. Source code is at [github.com/nyarquis/nyaruhodo](https://github.com/nyarquis/nyaruhodo).

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [How It Works](#how-it-works)
- [Supported File Types](#supported-file-types)
- [VirusTotal Integration](#virustotal-integration)
- [User Accounts and Scan History](#user-accounts-and-scan-history)
- [Theming](#theming)
- [Licence](#licence)

---

## Overview

A file can be renamed to carry any extension. A PNG saved as `document.pdf`, or a Windows executable disguised as `archive.zip`, will pass a naive extension check. Nyaruhodo! reads the first bytes of the uploaded file, matches them against a database of known magic byte sequences, and reports whether the claimed extension agrees with the detected format.

The back end is Flask with an SQLite database for user accounts and scan logs. The front end is plain HTML and vanilla JavaScript with no build toolchain.

---

## Features

**Binary signature detection** reads the file header and matches it against a curated set of magic byte sequences covering over 60 file types.

**Compound format resolution** disambiguates formats that share a common header: RIFF containers are resolved into WEBP, AVI, or WAV; ZIP containers are resolved into DOCX, XLSX, PPTX, or plain ZIP.

**Metadata extraction** parses embedded data from the following formats: JPEG (EXIF, GPS, JFIF), PNG (IHDR, pHYs, tEXt, iTXt, tIME, gAMA), MP3 (ID3v1, ID3v2.2, ID3v2.3, ID3v2.4), PDF (Info dictionary), HTML and XML (meta tags, XML declaration), ZIP-based Office formats (core.xml, app.xml), SQLite (page size, encoding, table and index counts), and ELF and PE executables (architecture, entry point, sections, compile timestamp).

**VirusTotal integration** computes the SHA-256 hash of the file and queries the VirusTotal `/files/{hash}` endpoint for existing analysis results. The file itself is never uploaded to VirusTotal.

**User accounts** support registration, login, and session management. Passwords are hashed with PBKDF2-HMAC-SHA256 via Werkzeug. Users can store a personal VirusTotal API key in the database.

**Scan history** records each scan performed while authenticated, including the filename, detected type, match status, and UTC timestamp. Entries are displayed in the dashboard in reverse chronological order, with timestamps formatted to the browser's local timezone.

**Light and night themes** use the Catppuccin Latte and Catppuccin Mocha palettes respectively, driven entirely by CSS custom properties. The active theme is saved to `localStorage` and restored before the DOM is parsed to prevent a flash of the default theme.

**Unauthenticated scanning** is supported. The scan endpoint does not require a login; results are returned as JSON and rendered client-side. Only authenticated users have their scans logged.

---

## Project Structure

```
nyaruhodo/
├── main.py                          # Flask application, routes, and database initialisation
├── data/
│   ├── files/                       # Uploaded files (runtime, excluded from version control)
│   ├── telemetry/                   # Per-user activity logs written by nyaruhodo_telemetry
│   ├── signatures.json              # Magic byte signature database
│   └── properties.json              # Lookup tables for EXIF, GPS, ID3, PE, ELF, and XML fields
├── nyaruhodo/
│   ├── __init__.py                  # Package exports
│   ├── nyaruhodo_core.py            # Signature matching and scan orchestration
│   ├── nyaruhodo_initialise.py      # Start-up banner and system information display
│   ├── nyaruhodo_services.py        # VirusTotal API client
│   ├── nyaruhodo_signatures.py      # Signature loading from signatures.json
│   ├── nyaruhodo_telemetry.py       # Structured logging to data/telemetry/
│   └── nyaruhodo_properties/
│       ├── __init__.py              # Property reader dispatch table
│       ├── nyaruhodo_archive.py     # ZIP, DOCX, XLSX, PPTX, APK metadata
│       ├── nyaruhodo_audio.py       # MP3 (ID3v1 and ID3v2) metadata
│       ├── nyaruhodo_common.py      # Shared file reading and byte decoding utilities
│       ├── nyaruhodo_database.py    # SQLite metadata
│       ├── nyaruhodo_document.py    # PDF metadata
│       ├── nyaruhodo_executable.py  # PE (EXE, DLL) and ELF metadata
│       ├── nyaruhodo_image.py       # JPEG and PNG metadata
│       ├── nyaruhodo_markup.py      # HTML and XML metadata
│       └── nyaruhodo_tables.py      # Loads and exposes lookup tables from properties.json
├── static/
│   ├── favicon.png                  # Browser tab icon
│   ├── icon.png                     # Navbar logo
│   ├── script.js                    # Client-side upload, result rendering, and theme switching
│   ├── structure.css                # Layout and theme-agnostic styles (desktop)
│   ├── structure-mobile.css         # Layout overrides for mobile viewports
│   ├── light-mode.css               # Catppuccin Latte colour scheme
│   └── night-mode.css               # Catppuccin Mocha colour scheme
└── templates/
    ├── base.html                    # Shared layout, navigation, and footer
    ├── index.html                   # File upload and result display page
    ├── dashboard.html               # Scan history, account management, and API key storage
    ├── admin-dashboard.html         # User management, metrics, and event log (admin only)
    ├── sign-in.html                 # Login form
    └── create-account.html          # Registration form
```

---

## Installation

Python 3.8 or later is required. Flask and Werkzeug are the only runtime dependencies.

```bash
git clone https://github.com/nyarquis/nyaruhodo.git
cd nyaruhodo
pip install flask werkzeug
```

The application creates its SQLite database and tables automatically on first run. No migration step is needed.

---

## Configuration

Configuration is handled through environment variables.

`SECRET_KEY` sets the Flask session secret. If not set, a random 24-byte key is generated at startup, which invalidates all sessions on every restart. Set this to a fixed value for persistent sessions.

```bash
export SECRET_KEY="your-secret-key-here"
```

`VIRUS_TOTAL_API_KEY` provides a fallback VirusTotal API key for users who have not saved a personal key in their account settings. This variable is optional. VirusTotal scanning only triggers when the user opts in and a type mismatch is detected.

```bash
export VIRUS_TOTAL_API_KEY="your-virustotal-api-key"
```

---

## Running the Application

```bash
python main.py
```

The server starts on `0.0.0.0:5000` in debug mode. The start-up sequence prints a banner, system information, and a progress log of all loaded binary signatures.

For production, run behind a WSGI server such as Gunicorn with debug mode disabled:

```bash
gunicorn -w 4 -b 0.0.0.0:8000 "main:server"
```

The application accepts uploaded files up to 100 MB. Uploaded files are written to the `uploads/` directory, which is excluded from version control.

---

## How It Works

### Signature Matching

When a file is uploaded, `nyaruhodo_core.scan` reads its first 32 bytes and compares them against every entry in the loaded signature dictionary. Signatures are stored as raw bytes and compared using `str.startswith`, so longer, more specific signatures take precedence.

Two signatures receive additional treatment. Files beginning with `RIFF` are inspected at bytes 8 to 12 to distinguish WEBP, AVI, and WAV. Files beginning with `PK\x03\x04` (the ZIP local file header) are scanned for directory paths characteristic of DOCX (`word/`), XLSX (`xl/`), and PPTX (`ppt/`).

If no binary signature matches, the application attempts to read the first 1024 bytes as UTF-8 text. Success yields a classification of `TXT`; failure yields `UNKNOWN`.

The claimed extension is taken from the uploaded filename and compared against the detected type. A small set of equivalent pairs (JPG/JPEG, HTM/HTML, TIF/TIFF) is treated as valid matches.

### Metadata Extraction

After the file type is determined, `nyaruhodo_properties.read` dispatches to the appropriate reader module. Each reader is independent and returns a flat dictionary of string values. The dispatcher converts all values to strings and removes empty entries before the result is merged into the scan response.

### Scan Response

The scan endpoint returns a JSON object containing the original filename, claimed extension, detected type, description, mismatch flag, analysis message, and (where available) a `metadata` object and a `virustotal` object. The client renders this entirely in JavaScript without a page reload.

---

## Supported File Types

The signature database covers over 60 formats, including: 7Z, ACCDB, AIFF, APK, AR, BMP, BZ2, CHM, CRX, DEX, DOCX, ELF, EML, EXE/DLL, FLAC, GIF, GZ, HTML, ICO, JPEG, JXL, Mach-O (universal, 32-bit, and 64-bit), MDB, MIDI, MKV, MP3, MP4, OGG, OLE, OTF, PCX, PDF, PNG, PostScript, RAR, RIFF (WAV, AVI, WEBP), RTF, scripts with shebangs, SQLite, SVG, TIFF, TTF, VDI, VHD, VHDX, VMDK, WOFF, WOFF2, XAR, XML, XZ, Z, and ZIP (standard, empty, and spanned).

Metadata extraction is available for a subset of these: JPEG, PNG, MP3, PDF, HTML, XML, SVG, ZIP, DOCX, XLSX, PPTX, APK, SQLite, EXE, DLL, and ELF.

---

## VirusTotal Integration

VirusTotal scanning is opt-in and only triggers automatically when a mismatch is detected and the user has checked the "Check with VirusTotal" option on the upload form.

The application computes the SHA-256 hash of the uploaded file and queries the VirusTotal `/files/{hash}` endpoint. It does not upload the file to VirusTotal. If the hash is not found (HTTP 404), the response directs the user to VirusTotal's manual upload page.

API keys are resolved in order: the authenticated user's stored key, then the `VIRUS_TOTAL_API_KEY` environment variable. If neither is present, the scan returns an error.

Users can save and remove their personal API key from the dashboard. The key is stored in the `users` table and transmitted only over the connection between the browser and the application server.

---

## User Accounts and Scan History

Registration requires only a username and password. Passwords are hashed with PBKDF2-HMAC-SHA256 via `werkzeug.security.generate_password_hash`.

All scans performed while authenticated are recorded in the `logs` table with the filename, detected file type, match status (Match, Mismatch, or Unknown), and a UTC timestamp. Log entries are displayed in the dashboard in reverse chronological order, with timestamps formatted to the browser's local timezone via the `Intl.DateTimeFormat` API.

Individual log entries can be deleted from the dashboard. Account deletion requires password confirmation, removes all associated log entries, and clears the session.

---

## Theming

The application ships with two themes: light mode (Catppuccin Latte) and night mode (Catppuccin Mocha). Both are defined entirely as CSS custom properties in `light-mode.css` and `night-mode.css`, with all structural styles in `structure.css`.

The active theme is saved to `localStorage` under the key `"theme"` and restored by an inline script in `base.html` that runs before the DOM is parsed, preventing a flash of the default theme. The theme toggle appears in the settings column of the footer and is only visible when the navigation menu is open.

---

## Licence

Nyaruhodo! is released under the GNU Affero General Public License v3.0. The full licence text is in the `LICENSE` file. Any modified version of this software made available over a network must also make its source code available to users of that service under the same licence terms.
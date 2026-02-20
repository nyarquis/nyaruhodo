# Nyaruhodo!

Nyaruhodo! is a file analysis web application that detects mismatches between a file's declared extension and its true binary format, as determined by inspecting the file's magic bytes (binary signature). It also extracts embedded metadata from supported file types and optionally cross-references suspicious files against the VirusTotal database.

The project is licensed under the GNU Affero General Public License v3.0. The source code is available at [github.com/nyarquis/nyaruhodo](https://github.com/nyarquis/nyaruhodo).

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

Files can be trivially renamed to carry misleading extensions. A PNG image saved as `document.pdf`, or a Windows executable disguised as `archive.zip`, will pass a naive extension check but reveal its true nature when its first bytes are read. Nyaruhodo! performs this inspection automatically by comparing the detected binary signature against a database of known magic byte sequences, then reports whether the claimed extension matches the actual file format.

The application is built on Flask and stores user accounts and scan logs in an SQLite database. The front end is served as plain HTML with vanilla JavaScript, using no front-end build toolchain.

---

## Features

- **Binary signature detection.** Reads the file header and matches it against a curated set of magic byte sequences covering over 60 file types.
- **Compound format resolution.** Disambiguates formats that share a common header (RIFF containers into WEBP, AVI, and WAV; ZIP containers into DOCX, XLSX, PPTX, and plain ZIP).
- **Metadata extraction.** Parses embedded metadata from JPEG (EXIF, GPS, JFIF), PNG (IHDR, pHYs, tEXt, iTXt, tIME, gAMA), MP3 (ID3v1, ID3v2.2, ID3v2.3, ID3v2.4), PDF (Info dictionary), HTML/XML (meta tags, XML declaration), ZIP-based Office formats (core.xml, app.xml), SQLite (page size, encoding, table and index counts), and ELF and PE executables (architecture, entry point, sections, compile timestamp).
- **VirusTotal integration.** Computes the SHA-256 hash of a file and queries the VirusTotal API for existing analysis results. Per-account API keys can be saved in the database.
- **User accounts.** Registration, login, and session management with bcrypt-hashed passwords via Werkzeug.
- **Scan history.** Authenticated users have each scan logged with a timestamp, filename, detected type, and match status. Individual log entries and full accounts can be deleted.
- **Light and night themes.** CSS custom properties drive two complete colour schemes (Catppuccin Latte and Catppuccin Mocha). The active theme is persisted in `localStorage`.
- **Unauthenticated scanning.** The file analysis endpoint does not require a login. Scan results are returned as JSON and rendered client-side. Only authenticated users have their scans logged.

---

## Project Structure

```
nyaruhodo/
├── main.py                          # Flask application, routes, and database initialisation
├── data/
│   ├── signatures.json              # Magic byte signature database
│   └── properties.json              # Lookup tables for EXIF, GPS, ID3, PE, ELF, and XML fields
├── nyaruhodo/
│   ├── __init__.py                  # Package exports
│   ├── nyaruhodo_core.py            # Signature matching and scan orchestration
│   ├── nyaruhodo_initialise.py      # Start-up banner and system information display
│   ├── nyaruhodo_services.py        # VirusTotal API client
│   ├── nyaruhodo_signatures.py      # Signature loading from signatures.json
│   └── nyaruhodo_properties/
│       ├── __init__.py              # Property reader dispatch table
│       ├── archive.py               # ZIP, DOCX, XLSX, PPTX, APK metadata
│       ├── audio.py                 # MP3 (ID3v1 and ID3v2) metadata
│       ├── common.py                # Shared file reading and byte decoding utilities
│       ├── database.py              # SQLite metadata
│       ├── document.py              # PDF metadata
│       ├── executable.py            # PE (EXE, DLL) and ELF metadata
│       ├── image.py                 # JPEG and PNG metadata
│       ├── markup.py                # HTML and XML metadata
│       └── tables.py                # Loads and exposes lookup tables from properties.json
├── static/
│   ├── script.js                    # Client-side upload, result rendering, and theme switching
│   ├── structure.css                # Layout, components, and theme-agnostic styles
│   ├── light-mode.css               # Catppuccin Latte colour scheme
│   └── night-mode.css               # Catppuccin Mocha colour scheme
└── templates/
    ├── base.html                    # Shared layout, navigation, and footer
    ├── index.html                   # File upload and result display page
    ├── dashboard.html               # Scan history, account management, and API key storage
    ├── login.html                   # Login form
    └── register.html                # Registration form
```

---

## Installation

Python 3.8 or later is required. Flask and Werkzeug are the only runtime dependencies.

```bash
git clone https://github.com/nyarquis/nyaruhodo.git
cd nyaruhodo
pip install flask werkzeug
```

No database migration step is needed. The application creates the SQLite database and its tables automatically on first run.

---

## Configuration

Configuration is handled through environment variables.

`SECRET_KEY` sets the Flask session secret. If not provided, a random 24-byte key is generated at startup, which means all sessions are invalidated whenever the process restarts. For persistent sessions across restarts, set this variable to a fixed value.

```bash
export SECRET_KEY="your-secret-key-here"
```

`VIRUS_TOTAL_API_KEY` provides a fallback VirusTotal API key used when an authenticated user has not saved a personal key in their account settings. This variable is optional. VirusTotal scanning is only triggered when the user opts in and a mismatch is detected.

```bash
export VIRUS_TOTAL_API_KEY="your-virustotal-api-key"
```

---

## Running the Application

```bash
python main.py
```

The server starts on `0.0.0.0:5000` in debug mode. The start-up sequence prints a banner, system information, and a progress log of all loaded binary signatures.

For production use, run behind a WSGI server such as Gunicorn and disable debug mode:

```bash
gunicorn -w 4 -b 0.0.0.0:8000 "main:server"
```

The application accepts uploaded files up to 100 MB. Uploaded files are written to the `uploads/` directory, which is excluded from version control via `.gitignore`.

---

## How It Works

### Signature Matching

When a file is uploaded, `nyaruhodo_core.scan` reads the first 32 bytes of the file and compares them against every entry in the loaded signature dictionary. Signatures are stored as raw bytes and the comparison uses `str.startswith`, so longer signatures take precedence when they appear earlier in the iteration order.

Two signatures receive additional treatment. Files beginning with `RIFF` are inspected at bytes 8 to 12 to distinguish WEBP, AVI, and WAV. Files beginning with `PK\x03\x04` (the ZIP local file header) are scanned for directory paths characteristic of DOCX (`word/`), XLSX (`xl/`), and PPTX (`ppt/`).

If no binary signature matches, the application attempts to read the first 1024 bytes as UTF-8 text. Success results in a classification of `TXT`; failure results in `UNKNOWN`.

The claimed extension is taken from the uploaded filename and compared against the detected type. A small set of equivalent pairs (JPG/JPEG, HTM/HTML, TIF/TIFF) is treated as valid matches.

### Metadata Extraction

After the file type is determined, `nyaruhodo_properties.read` dispatches to the appropriate reader module. Each reader is independent and returns a flat dictionary of string values. The dispatcher converts all values to strings and removes empty entries before the result is merged into the scan response.

### Response

The scan endpoint returns a JSON object containing the original filename, claimed extension, detected type, description, mismatch flag, analysis message, and (where available) a `metadata` object and a `virustotal` object. The client renders this entirely in JavaScript without a page reload.

---

## Supported File Types

The signature database covers the following formats, among others:

7Z, ACCDB, AIFF, APK, AR, BMP, BZ2, CHM, CRX, DEX, DOCX, ELF, EML, EXE/DLL, FLAC, GIF, GZ, HTML, ICO, JPEG, JXL, Mach-O (universal, 32-bit, 64-bit), MDB, MIDI, MKV, MP3, MP4, OGG, OLE (compound document), OTF, PCX, PDF, PNG, PostScript, RAR, RIFF (WAV, AVI, WEBP), RTF, scripts with shebangs, SQLite, SVG, TIFF, TTF, VDI, VHD, VHDX, VMDK, WOFF, WOFF2, XAR, XML, XZ, Z, ZIP (standard, empty, spanned).

Metadata extraction is available for a subset of these: JPEG, PNG, MP3, PDF, HTML, XML, SVG, ZIP, DOCX, XLSX, PPTX, APK, SQLite, EXE, DLL, and ELF.

---

## VirusTotal Integration

VirusTotal scanning is opt-in and only triggers automatically when a mismatch is detected and the user has checked the "Check with VirusTotal" option on the upload form.

The application computes the SHA-256 hash of the uploaded file and queries the VirusTotal `/files/{hash}` endpoint. It does not upload the file to VirusTotal; it only queries for pre-existing analysis results. If the hash is not found (HTTP 404), the response directs the user to VirusTotal's manual upload page.

API keys are resolved in the following order: the authenticated user's stored key, then the `VIRUS_TOTAL_API_KEY` environment variable. If neither is present, the scan returns an error.

Users can save and remove their personal API key from the dashboard. The key is stored in the `users` table and transmitted only over the connection between the browser and the application server.

---

## User Accounts and Scan History

Registration requires only a username and password. Passwords are hashed with PBKDF2-HMAC-SHA256 via `werkzeug.security.generate_password_hash`.

All scans performed while authenticated are recorded in the `logs` table with the filename, detected file type, match status (Match, Mismatch, or Unknown), and a UTC timestamp. Log entries are displayed in the dashboard in reverse chronological order. Timestamps are formatted in the browser's local timezone using the `Intl.DateTimeFormat` API.

Individual log entries can be deleted from the dashboard. Account deletion requires password confirmation, removes all associated log entries, and clears the session.

---

## Theming

The application ships with two themes. Light mode uses the Catppuccin Latte palette and night mode uses Catppuccin Mocha. Both are defined entirely as CSS custom properties in `light-mode.css` and `night-mode.css` respectively, with all structural styles in `structure.css`.

The active theme is saved to `localStorage` under the key `"theme"` and restored on page load by an inline script in `base.html` that runs before the DOM is parsed, preventing a flash of the default theme.

The theme toggle appears in the settings column of the footer and is only visible when the navigation menu is open.

---

## Licence

Nyaruhodo! is released under the GNU Affero General Public License v3.0. The full licence text is included in the `LICENSE` file. In summary, any modified version of this software that is made available over a network must also make its source code available to users of that service under the same licence terms.
# Neuro-Symphony — Context experiment (web data collection)

This folder contains the **web application used to collect behavioral data** for the *contextual information manipulation* study described in the dissertation *“Emotions in Music: How Naturalistic Music Listening Encodes Acoustic and Emotional Features in the Brain and Is Shaped by Extra-Musical Context”* (IMT School for Advanced Studies Lucca, 2025). 

In the study, participants complete an **online, multi-session listening paradigm** in which brief **program-note descriptions** (manipulated in valence and narrative authenticity) are shown before each symphonic movement; during listening, participants continuously report felt affect via a **six-button task**, followed by post-movement questionnaires. 

---

## What the web app does

### Participant flow (high level)
1. **Account creation & login** (to persist progress across multiple listening sessions).   
2. **Consent / Terms** (adult-only participation; GDPR-aligned data protection language in the study terms).   
3. **Preliminary questionnaires** (one-time):
   - Demographics + screening (e.g., language, psychiatric exclusion items).
   - **Gold-MSI** and **BFI-10**.
4. **Per-session questionnaire**:
   - **WHO-5** at the beginning of each listening session.   
5. **Listening session** (per symphony, split across movements):
   - Read a program note.
   - Listen to the movement and interact continuously with **6 emotion/sensation buttons**.
   - Provide post-movement ratings and feedback.
6. **Dashboard** to resume later (progress tracking and session timeouts).

### Core experimental design (implemented via condition assignment)
The study follows a **2×2 factorial design** crossing:
- **Affective coherence**: description valence *coherent* vs *opposite* to the music
- **Narrative authenticity**: *reference* vs *injected* narrative source  
and assigns all four conditions across the four movements within an experiment, with balanced/randomized pairings. 

---

## Tech stack

- **PHP** for server-side logic (sessions, routing, saving data)
- **JavaScript + jQuery** for the single-page interaction and AJAX saves
- **CSV / JSON** as storage (no SQL database)
- Designed for **Apache2 + PHP** deployment; `.htaccess`-style hardening is recommended for production. 

---

## Repository layout (relevant parts)

```
music_context/
  web/                          # deploy this as the web root (DocumentRoot)
    index.php                   # login entry
    dashboard.php               # user progress + experiment entry points
    build_experiment.php        # single-page experiment loader
    content/                    # page fragments (terms, questionnaires, experiment UI, etc.)
    php/                        # server endpoints (save/load/assign)
    js/                         # client logic (experiment, questionnaires)
    css/                        # styles
    data/                       # stimulus manifests + framework.json
    userdata/                   # per-user folders + experiment logs (writeable)
    security/                   # encryption helpers (AES, key derivation)
  code/                         # analysis / preprocessing scripts (not required to run the website)
  responses/                    # exported data/plots (not required to run the website)
```

---

## Local development setup (quickstart)

### 1) Requirements
- PHP **7.4+** (recommended) with:
  - `openssl` (encryption helpers)
  - `json` (already bundled in most PHP builds)
- A web server:
  - **Apache2** (closest to production), or
  - the PHP built-in dev server for quick testing.

### 2) Run with PHP’s built-in server (fastest)
From the repository root:

```bash
php -S localhost:8000 -t music_context/web
```

Then open `http://localhost:8000`.

> Note: the built-in server will not honor Apache `.htaccess` rules. Use Apache/Nginx for production-like testing.

### 3) File permissions
The app writes into:
- `music_context/web/userdata/`
- per-user subfolders created inside `userdata/`

Make sure the web server user can write there (typical Apache group is `www-data`):

```bash
sudo chgrp -R www-data music_context/web/userdata
sudo chmod -R 770 music_context/web/userdata
```

---

## Required configuration

### Global secret key (encryption)
The site encrypts sensitive values (e.g., email / user ID) using **AES-256-CBC**, with a **user-specific key derived from the username + a server-side global key**.   

In `web/security/endecrypt.php` there is a `key_path` pointing to a server-local file (e.g., `/var/secure/keys/neurosymphony_music_context.key`). Create that file and restrict permissions:

```bash
sudo mkdir -p /var/secure/keys
openssl rand -hex 32 | sudo tee /var/secure/keys/neurosymphony_music_context.key >/dev/null
sudo chmod 600 /var/secure/keys/neurosymphony_music_context.key
```

For local development you can either:
- edit `key_path` to a local path you control, or
- create the same path on your machine.

### Credential store (`users.csv`)
In production the app uses a CSV credential store (hashed usernames + password hashes, plus encrypted fields). For safety, **do not commit this file**.

Create an empty file to start:

```bash
touch music_context/web/users.csv
chmod 600 music_context/web/users.csv
```

### Stimuli configuration (`framework.json`)
`web/data/framework.json` defines each listening experiment:
- title
- audio-path CSV
- description CSV (Italian and optional English)
- condition assignment CSV (shuffled combinations)

To add/replace symphonies:
1. Add your audio files in `web/audio/` (or update the paths to where you host them).
2. Update the relevant `audio_path_*.csv`.
3. Add/update the `*_processed.csv` description files.
4. Edit `framework.json` to point to the new CSVs.

---

## Data written by the website

The website is intentionally database-free: it reads/writes **JSON + CSV files** on disk. 

### Per-user state (JSON)
`web/userdata/user_<USER_ID>/<USER_ID>.json` stores:
- consent acceptance
- preliminary questionnaire answers
- per-session progress markers (what is completed, what is next)

### Button task time series (CSV)
For each track/movement the client samples the 6 button states at **1 Hz** and saves a CSV:
- first column: timestamp (ms from start)
- next 6 columns: 0/1 button values

(Downstream preprocessing described in the dissertation discards timestamps, aligns participants, smooths, and downsamples.) 

### Experiment assignment log (CSV)
`web/userdata/experiments_log.csv` records start/finish timestamps and the assigned condition category for balancing.

---

## Security notes (production checklist)

The dissertation describes a hardened setup including:
- protecting sensitive CSV files via server rules
- disabling directory listing
- restricting direct access to `userdata/`
- sanitizing inputs and using POST/AJAX endpoints
- avoiding SQL entirely (no SQL injection surface) 

If you deploy this publicly, at minimum:
- serve over **HTTPS**
- block web access to `userdata/` and credential files
- ensure keys are **not** inside the repo
- review and test permission boundaries

---

## Citation

If you use this code in academic work, cite the dissertation chapter describing the platform and paradigm. 

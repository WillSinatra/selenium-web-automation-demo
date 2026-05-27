<div align="center">

# 🌐 Web Automation Toolkit

**Professional browser automation utility built with Playwright & Python**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Playwright](https://img.shields.io/badge/Playwright-1.40+-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)](https://playwright.dev/python)
[![License](https://img.shields.io/badge/License-Proprietary-red?style=for-the-badge)](./LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)]()

*Automate web forms, capture screenshots, and run multi-step browser workflows — all from a clean CLI interface.*

</div>

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **Browser Automation** | Drive Chromium headlessly or with a visible window using Playwright |
| 📋 **CSV Batch Form Filling** | Process multiple form submissions from a single structured CSV |
| 📸 **Auto Screenshot Capture** | Timestamped screenshots at every workflow stage |
| 🔍 **Input Validation** | Validate URLs, CSV schemas, and required fields before running |
| 📊 **Result Export** | Every run generates `output/results.csv` with full status details |
| 🎨 **Colored CLI Output** | Color-coded terminal messages for instant status recognition |
| 📝 **Structured Logging** | Dual file + console logging with configurable verbosity |
| 🔄 **Retry Logic** | Configurable automatic retries for failed navigation attempts |

---

## 📁 Project Structure

```
web_automation_toolkit/
├── main.py                       # ← CLI entry point
├── config.py                     # ← Global configuration
├── requirements.txt
├── sample_data/
│   └── sample_forms.csv          # ← Demo input data
├── modules/
│   ├── browser.py                # Browser session management
│   ├── workflow_handler.py       # End-to-end workflow orchestration
│   ├── form_filler.py            # Form detection & field filling
│   ├── screenshot_manager.py     # Screenshot capture & naming
│   ├── validators.py             # Input validation utilities
│   └── logger.py                 # Centralized colored logging
├── logs/                         # ← Auto-generated: app.log
├── output/                       # ← Auto-generated: results.csv
└── screenshots/                  # ← Auto-generated: PNG files
```

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/web_automation_toolkit.git
cd web_automation_toolkit
```

### 2. Create a Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

---

## 🚀 CLI Usage

### 📸 `screenshot` — Capture Any Web Page

```bash
python main.py screenshot --url https://example.com --label homepage
```

| Option | Description |
|--------|-------------|
| `--url` | Target URL *(required)* |
| `--label` | Label embedded in the filename *(default: capture)* |
| `--no-headless` | Show the browser window while capturing |

---

### ⚙️ `workflow` — Batch Form Processing

```bash
python main.py workflow \
  --input sample_data/sample_forms.csv \
  --url https://www.selenium.dev/selenium/web/web-form.html
```

| Option | Description |
|--------|-------------|
| `--input` | Path to the CSV input file *(required)* |
| `--url` | Override URL for every row *(optional)* |
| `--no-headless` | Show the browser window |

---

### 🔍 `validate` — Pre-flight CSV Check

```bash
python main.py validate --input sample_data/sample_forms.csv
```

Checks file existence, schema completeness, non-empty data, and URL format — before a single browser opens.

---

### 📝 `fill` — Single Form Fill

```bash
python main.py fill \
  --url https://www.selenium.dev/selenium/web/web-form.html \
  --field "input[name='my-text']:Jane Doe" \
  --field "input[name='my-email']:jane@example.com" \
  --submit
```

| Option | Description |
|--------|-------------|
| `--url` | Target URL *(required)* |
| `--field` | `selector:value` pair — repeat for each field |
| `--submit` | Click the submit button after filling |
| `--no-headless` | Show the browser window |

---

## 📊 Input / Output Examples

### Input CSV (`sample_data/sample_forms.csv`)

| url | first_name | last_name | email | phone | company | subscribe |
|-----|-----------|-----------|-------|-------|---------|-----------|
| https://... | John | Smith | john@acme.com | +1-555-0101 | Acme Corp | true |
| https://... | Maria | Garcia | maria@tech.io | +1-555-0102 | TechStart Inc | false |
| https://... | David | Johnson | *(empty)* | +44-20-7946 | Global Logic | true |

### Output CSV (`output/results.csv`)

| timestamp | url | status | success | error_message |
|-----------|-----|--------|---------|---------------|
| 2024-01-15T10:30:00 | https://... | success | True | Success indicator found: 'received' |
| 2024-01-15T10:30:08 | https://... | warning | False | Failure indicator found: 'required' |

---

## 🛡️ Error Handling

The toolkit handles errors gracefully at every stage:

| Scenario | Behaviour |
|----------|-----------|
| Invalid URL | Validation fails immediately with a clear message |
| Missing CSV columns | Schema check reports which columns are absent |
| Network timeout | Automatic retry up to `MAX_RETRIES` times |
| Element not found | Warning logged, workflow continues to next step |
| Browser crash | Graceful teardown, partial results saved |

---

## 🎬 Demo Workflow

Run the complete demo in three steps:

```bash
# Step 1 — Validate input data
python main.py validate --input sample_data/sample_forms.csv

# Step 2 — Quick screenshot sanity check
python main.py screenshot --url https://example.com --label demo

# Step 3 — Full batch workflow
python main.py workflow \
  --input sample_data/sample_forms.csv \
  --url https://www.selenium.dev/selenium/web/web-form.html
```

---

## 📸 Screenshots

Screenshots are automatically saved to `screenshots/` with timestamped names:

```
screenshots/
├── 20240115_103000_01_navigation.png
├── 20240115_103001_before_fill.png
├── 20240115_103002_02_filled_form.png
└── 20240115_103003_03_after_submit.png
```

---

## 🎥 GIF Demo

> *Record a GIF using [ScreenToGif](https://www.screentogif.com/) (Windows) or [Peek](https://github.com/phw/peek) (Linux) and drop it here.*

```
[Place your demo.gif in the screenshots/ folder and update this link]
![Demo](screenshots/demo.gif)
```

---

## 🔮 Future Improvements

- [ ] **Parallel execution** — Process multiple rows concurrently with asyncio
- [ ] **PDF report generation** — Export results as a formatted PDF
- [ ] **Login workflow support** — Handle authentication before automation
- [ ] **Proxy rotation** — Built-in proxy management for large-scale runs
- [ ] **Email notifications** — Send run summaries via SMTP
- [ ] **Scheduled runs** — Cron / Task Scheduler integration
- [ ] **Docker support** — One-command containerized deployment
- [ ] **Dashboard UI** — Web-based visual results viewer

---

## 📄 License

Copyright © 2025 Santiago Sánchez.

This project is intended for portfolio and demonstration purposes.
Unauthorized commercial redistribution, resale, or reproduction
of this software or source code is prohibited without explicit permission.

---

<div align="center">

**Built with ❤️ using Python + Playwright**

*⭐ Star this repo if you find it useful!*

</div>

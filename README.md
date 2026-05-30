# 🚀 Job Agent

A powerful CLI-based job scraping tool that aggregates job listings from multiple platforms like **Naukri, RemoteOK, and Wellfound** into a single structured CSV output.

---

## 📌 Features

* 🔍 Search jobs by role and location
* 🌐 Multi-source scraping:

  * Naukri (dynamic scraping with browser automation)
  * RemoteOK (API-based)
  * Wellfound (JS-rendered scraping via Firecrawl)
* ⚡ Fast and lightweight CLI tool
* 📄 Exports results to CSV
* 🧠 Supports headless browsing
* 📴 Offline fallback support (HTML input)

---

## 🛠️ Tech Stack

* **Python**
* **BeautifulSoup**
* **undetected-chromedriver**
* **Firecrawl API**
* **Requests**

---

## ⚙️ Setup

```bash
# Create virtual environment
python -m venv venv

# Activate environment
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
```

Add your API key:

```
FIRECRAWL_API_KEY=your_api_key_here
```

---

## 🚀 Usage

### 🔎 Search jobs

```bash
python -m src.main --role "Software Engineer" --location "Bangalore"
```

### 🌍 Without location

```bash
python -m src.main --role "Backend Developer"
```

### 🎯 Specific sources

```bash
python -m src.main --role "Data Analyst" --sources naukri,remoteok
```

### ⚡ Headless mode

```bash
python -m src.main --role "Python Developer" --headless
```

### 📴 Offline mode

```bash
python -m src.main --role "Backend Engineer" --naukri-html saved_file.html
```

---

## 📂 Output

All results are saved as:

```
output/jobs_<timestamp>.csv
```

---

## 🧱 Project Structure

```
src/
├── main.py
├── models.py
├── csv_writer.py
└── scrapers/
    ├── base.py
    ├── naukri.py
    ├── remoteok.py
    └── wellfound.py
```

---

## 📌 CLI Arguments

| Argument      | Required | Description    |
| ------------- | -------- | -------------- |
| --role        | ✅ Yes    | Job role       |
| --location    | ❌ No     | Job location   |
| --sources     | ❌ No     | Select sources |
| --headless    | ❌ No     | Run without UI |
| --naukri-html | ❌ No     | Use saved HTML |

---

## 🎯 Future Improvements

* Web dashboard (React + Spring Boot 👀)
* Database integration (PostgreSQL)
* Scheduled scraping (cron jobs)
* Docker support

---

## 👨‍💻 Author

**YS-Pundir**

---

## ⭐ Contribute / Support

If you like this project:

* ⭐ Star the repo
* 🍴 Fork it
* 🚀 Improve it

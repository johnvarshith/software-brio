# 🤖 AI Lead Enrichment Agent

An autonomous Python-based AI agent designed to crawl target company domains, extract clean and relevant DOM content, and use Large Language Models (LLMs) with strict structured outputs to generate actionable business intelligence.

The system combines **browser automation, web scraping, LLM-based information extraction, structured validation, agentic search, and API cost tracking** into a resilient multi-step pipeline.

---

## 🏗️ Architecture & Workflow

The agent operates through a modular and resilient pipeline:

```text
Target Company Domains
        │
        ▼
┌─────────────────────────┐
│  Playwright Browser     │
│  Automated Web Crawling │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Relevant Page Discovery │
│ /about /team /pricing   │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ DOM Content Processing  │
│ BeautifulSoup           │
│ Markdownify             │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Groq LLM + Instructor   │
│ Pydantic Validation     │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Structured Lead Data    │
│ Company / ICP / People  │
└────────────┬────────────┘
             │
             ▼
     Missing LinkedIn?
          /     \
        Yes      No
         │        │
         ▼        ▼
   Tavily Search  Complete
         │
         ▼
┌─────────────────────────┐
│ Final Enriched Output   │
│ output/output.json      │
└─────────────────────────┘
```

### Pipeline Steps

### 1. Automated Browsing — Playwright

- Uses **Playwright** for reliable browser automation.
- Supports JavaScript-rendered websites.
- Automatically navigates target company domains.
- Discovers relevant subpages such as:
  - `/about`
  - `/team`
  - `/pricing`
  - `/contact`
- Attempts to dismiss common cookie-consent banners.

### 2. Context Pre-Processing

Raw HTML is cleaned before being sent to the LLM.

The pipeline:

- Removes unnecessary CSS and JavaScript.
- Removes navigation and boilerplate content.
- Extracts meaningful DOM text.
- Converts cleaned HTML into Markdown using **Markdownify**.
- Reduces unnecessary LLM token consumption.

### 3. LLM-Based Information Extraction

The cleaned website content is processed using:

- **Groq**
- **Instructor**
- **Pydantic**

Instructor integrates the LLM with Pydantic schemas to enforce structured responses.

The agent extracts information such as:

- Company overview
- Ideal Customer Profile (ICP)
- Company/contact information
- Leadership information
- Leadership LinkedIn profiles

### 4. 🔎 Agentic Search Fallback — Bonus

If leadership names are discovered but their LinkedIn URLs are missing, the agent automatically triggers a **Tavily web search**.

```text
Leadership Name Found
        │
        ▼
LinkedIn URL Missing?
        │
       YES
        │
        ▼
Tavily Web Search
        │
        ▼
Relevant Profile Found
        │
        ▼
Enriched Leadership Data
```

This allows the system to dynamically decide when external search is required instead of performing unnecessary searches.

### 5. 🛡️ Resilience & Error Handling

The pipeline is designed to continue processing even when individual domains fail.

It gracefully handles:

- HTTP errors
- 404 pages
- Browser timeouts
- Website loading failures
- Missing pages
- LLM/API failures
- Search failures

Errors are isolated to individual domains so that one failed website does not terminate the entire pipeline.

### 6. 💰 Token & API Cost Tracking

The agent tracks estimated:

- LLM token usage
- API usage
- Estimated processing cost
- Usage per company/domain

This provides visibility into the operational cost of running the enrichment pipeline.

---

## ✨ Key Features

| Feature | Implementation |
|---|---|
| 🌐 Web Crawling | Playwright |
| 🧹 DOM Cleaning | BeautifulSoup |
| 📝 Content Conversion | Markdownify |
| 🧠 LLM Processing | Groq |
| 📦 Structured Output | Instructor + Pydantic |
| 🔎 Agentic Search | Tavily |
| 🛡️ Error Handling | Per-domain exception handling |
| 💰 Cost Tracking | Token/API usage estimation |
| 📄 Final Output | JSON |

---

## 🛠️ Tech Stack

### Core

- Python 3.9+
- Playwright
- BeautifulSoup4
- Markdownify

### AI / LLM

- Groq
- Instructor
- Pydantic

### Search

- Tavily API

### Configuration

- Python Dotenv

---

## ⚙️ Setup & Installation

### Prerequisites

Make sure you have:

- Python **3.9 or higher**
- A **Groq API Key**
- A **Tavily API Key**

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd ai-intern-agent
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it:

**Windows**

```bash
venv\Scripts\activate
```

**macOS / Linux**

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Install the Playwright Chromium browser:

```bash
playwright install chromium
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

> ⚠️ Never commit your `.env` file or API keys to GitHub.

---

## 🚀 Running the Agent

Run the main script:

```bash
python main.py
```

The agent will process the configured target domains:

```text
postman.com
supabase.com
vapi.ai
```

During execution, the terminal displays:

- Current domain being processed
- Pages discovered
- Extraction progress
- Token usage
- Search enrichment activity
- Errors and recovery information
- Estimated API costs

The final structured results are generated as:

```text
output/output.json
```

---

## 📁 Project Structure

```text
ai-intern-agent/
│
├── main.py
├── requirements.txt
├── README.md
├── .gitignore
├── .env
│
├── output/
│   └── output.json
│
└── venv/
```

> `.env`, `venv/`, and generated output files should not be committed to the repository.

---

## 📊 Sample Output

The agent produces structured JSON containing enriched company intelligence.

A simplified example:

```json
{
  "company_name": "Example Company",
  "company_overview": "AI-powered software company...",
  "ideal_customer_profile": "...",
  "contacts": [],
  "leadership": [
    {
      "name": "John Doe",
      "title": "CEO",
      "linkedin_url": "https://linkedin.com/in/example"
    }
  ]
}
```

The actual output schema is determined by the Pydantic models implemented in the project.

---

## 🎯 Evaluation Rubric Alignment

### Scraping Architecture

- Uses **Playwright** for JavaScript-rendered content.
- Automatically discovers relevant company pages.
- Uses **BeautifulSoup** and **Markdownify** for DOM cleaning.
- Avoids sending unnecessary raw HTML dumps directly to the LLM.

### Structured Outputs

- Uses **Instructor** for structured LLM extraction.
- Uses **Pydantic** models to validate generated data.
- Produces predictable JSON-compatible outputs.

### Error Handling

The orchestrator handles failures on a per-domain basis.

If a website is unavailable, returns a 404, times out, or blocks the scraper:

```text
Failed Domain
     │
     ▼
Log Error
     │
     ▼
Continue Pipeline
     │
     ▼
Process Next Domain
```

This prevents a single failed website from crashing the entire enrichment process.

---

## 🚀 Bonus Features

### 🔎 1. Agentic Search Integration

Implemented a **Tavily-powered search fallback** that activates when leadership information is discovered but corresponding LinkedIn URLs are unavailable.

This enables the agent to make a dynamic decision about when external search is necessary.

### 🤖 2. Agentic Workflow

The pipeline does not simply scrape pages sequentially.

It dynamically:

1. Discovers relevant pages.
2. Extracts available information.
3. Identifies missing information.
4. Decides when additional search is required.
5. Enriches the extracted data.
6. Produces the final structured result.

### 💰 3. Token & API Cost Tracking

The system tracks estimated LLM usage and API costs for each processed domain, providing visibility into the operational efficiency of the agent.

---

## 🔐 Security

The following files and directories are intentionally excluded from Git:

```text
.env
venv/
__pycache__/
output/
```

API credentials should always be stored through environment variables rather than hardcoded in source code.

---

## 📌 Target Domains

The assignment is configured to process:

- [Postman](https://www.postman.com/)
- [Supabase](https://supabase.com/)
- [Vapi](https://vapi.ai/)

---

## 👨‍💻 Author

**[Your Full Name]**

AI / ML Engineer | Python Developer

GitHub: [Your GitHub Profile]

LinkedIn: [Your LinkedIn Profile]

---

## 📄 License

This project was developed as part of an AI Engineer Intern practical assignment.

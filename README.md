# Databricks Data Engineer Certification Study Companion

A practice application to help you prepare for the Databricks Data Engineer Associate and Professional certification exams.

## Overview

This application provides two types of practice exercises to reinforce your understanding of Databricks and data engineering concepts:

1. **Multiple Choice Questions (MCQ)** — Practice with blueprint-aligned questions covering all Associate exam domains
2. **Code-Completion Exercises (Phase 2)** — Wordle-style syntax practice for SQL and PySpark code

The app helps you study efficiently by offering domain-based filtering, detailed explanations, and instant feedback on your answers.

## Quick Start

### Prerequisites

- Node.js 18+ (for frontend)
- Python 3.10+ (for backend)
- Git (recommended)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd DataBricks-DE-cert-study-companion
   ```

2. **Initialize the frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   The frontend will start on `http://localhost:3000`

3. **Initialize the backend** (in a new terminal)
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   python -m uvicorn app.main:app --reload
   ```
   The backend API will start on `http://localhost:8000`

## Project Structure

```
DataBricks-DE-cert-study-companion/
├── exercises/              # Content: YAML exercise files (MCQs, code-completion)
│   └── associate/         # Associate-level certification exercises
├── frontend/              # React 18+ application (Vite, Tailwind CSS)
│   ├── src/              # React components, pages, styles
│   └── package.json      # Frontend dependencies
├── backend/               # Python FastAPI application
│   ├── app/              # FastAPI routes, models, logic
│   └── requirements.txt   # Python dependencies
├── docs/                  # Documentation and guides
├── README.md             # This file
└── .gitignore            # Git ignore rules
```

## Content Bank

MCQ exercises are stored as YAML files in `exercises/associate/`. Each file contains:

- **Question metadata** — domain, difficulty, type (single/multi-choice)
- **Question text** — the question prompt and optional code snippets
- **Answer options** — text and correctness flag
- **Explanation** — why the correct answer is right, why distractors are wrong
- **References** — links to official Databricks documentation

### Schema Example

```yaml
- id: dbx-de-0001
  type: single_choice
  exam: associate
  domain: "Databricks Lakehouse Platform"
  difficulty: medium
  question: "What is the primary benefit of Delta Lake?"
  options:
    - id: a
      text: "ACID transactions and schema enforcement"
      correct: true
    - id: b
      text: "Unlimited storage capacity"
      correct: false
  answer: [a]
  explanation: "Delta Lake provides ACID transactions..."
  references:
    - "https://docs.databricks.com/delta/"
```

## Architecture & Design

For detailed information about the technical architecture, naming conventions, and implementation patterns, see:

- **[Architecture Documentation](docs/architecture.md)** — Tech stack, design decisions, project structure
- **[Epics and Stories](docs/epics.md)** — Feature breakdown and implementation roadmap

## Development

### Running Tests

**Frontend:**
```bash
cd frontend
npm test
```

**Backend:**
```bash
cd backend
pytest
```

### Coding Standards

- **Frontend:** PascalCase for components, camelCase for variables and functions
- **Backend:** snake_case for functions, camelCase for JSON APIs
- **API Responses:** All API responses wrap data in `{success, data, error}` structure

See [Architecture Documentation](docs/architecture.md) for complete conventions.

## Phases

### Phase 1 (MVP)
- ✅ MCQ practice interface with domain filtering
- ✅ Detailed answer explanations
- ✅ Session management
- ✅ Anki export for portable study

### Phase 2
- Code-Completion exercises (Wordle-style)
- Token-level feedback (green/yellow/grey)
- Syntax practice for SQL and PySpark

### Future Phases
- Timed mock exams
- Per-domain analytics and readiness metrics
- Spaced repetition system
- Question bank generation from official docs

## Study Tips

1. **Start with domain filtering** — Focus on weak areas first
2. **Read explanations carefully** — They teach the reasoning, not just the answer
3. **Mix difficulty levels** — Build fundamentals with easy questions, then challenge yourself
4. **Use Anki export** — Review on your mobile device or during commutes (via Anki app)
5. **Refer to official docs** — Follow the reference links to deepen your understanding

## Official Resources

- **Databricks Certification:** https://databricks.com/learn/certification
- **Databricks Documentation:** https://docs.databricks.com
- **Exam Guide:** Download the official PDF exam guide from Databricks for domain weights and scope

## Contributing

If you've authored additional exercises or found errors, please contribute by:

1. Creating a new YAML file in `exercises/associate/` following the schema
2. Ensuring all questions are original and properly explained
3. Adding references to official Databricks documentation
4. Submitting a pull request with your additions

## License

This project is for personal study and educational purposes. All content should align with Databricks' official exam blueprint and documentation.

## Support

For questions or issues:

1. Check the [Architecture Documentation](docs/architecture.md)
2. Review the [Epics and Stories](docs/epics.md) for implementation details
3. Consult Databricks official documentation at https://docs.databricks.com

---

**Last updated:** 2026-06-05  
**Current Phase:** 1 (MCQ Practice MVP)

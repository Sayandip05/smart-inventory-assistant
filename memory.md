# InvIQ Memory & Development Log

## April 2026 - Environment & Database Fixes
- **LangSmith Configuration**: Updated the LangChain environment variables to use the modern `LANGSMITH_*` prefix. Configured `.env` and `backend/app/core/config.py` to correctly initialize LangSmith tracing using the provided API key for the `InvIQ` project.
- **LLM Cleanup**: Removed the placeholder `OPENAI_API_KEY` from `.env` as the project relies exclusively on Groq for LLM capabilities.
- **Database Connectivity Fix**: 
  - Updated the `DATABASE_URL` to use the NeonDB connection-pooling endpoint (`ep-rough-shape-anpw5kgk-pooler.c-6.us-east-1.aws.neon.tech`).
  - Diagnosed a critical DNS resolution failure where the local ISP DNS was unable to resolve NeonDB subdomains, resulting in `No such host is known` errors in the backend and generic "Invalid username or password" errors on the frontend.
  - Resolved the connectivity issue by changing the active network interface's DNS servers to Google Public DNS (`8.8.8.8`, `8.8.4.4`) via an elevated PowerShell command.
- **Database Verification**: Successfully verified that the backend connects to the database via Python, and confirmed the `admin` user is seeded and available for authentication.



## Quick Start Commands

To run the project locally, open two separate terminal windows from the project root (`InvIQ`).

**Backend Terminal:**
```powershell
cd backend
..\venv\Scripts\activate
python -m uvicorn app.main:app --reload --port 8000
cd frontend
npm run dev

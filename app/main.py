import asyncio
import os
from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import razorpay
from google import genai
from dotenv import load_dotenv

# Import local modules - Ensure these files exist in your folder structure
from app.routers import internships
from app.services.repo_service import extract_code_from_repo
from app.supabase_client import supabase 

load_dotenv()

app = FastAPI(
    title="BluePeak Professional API",
    description="2026 Edition: Payments, AI Grading, and Simulations",
    version="1.1.1"
)

# --- 1. CONFIGURATION ---
rzp_client = razorpay.Client(
    auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET"))
)
ai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# CORS Update: Allows both local testing and your production Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://bluepeakfrontend-git-main-mys-projects-e11c9265.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AIReviewReport(BaseModel):
    score: int = Field(description="Score out of 100")
    feedback: str = Field(description="Bullet points of technical feedback")
    passed: bool = Field(description="True if the score is 60 or higher")

app.include_router(internships.router)

@app.get("/")
async def root():
    return {"status": "online", "message": "BluePeak API v1.1.1 operational."}

# --- 2. ENDPOINTS ---
@app.post("/internships/submit")
async def submit_internship(
    user_id: str = Body(...), 
    repo_url: str = Body(...), 
    week: int = Body(...)
):
    try:
        # 1. Extraction logic
        code_context = extract_code_from_repo(repo_url, user_id, week)
        if not code_context:
            raise HTTPException(status_code=400, detail="Repo unreadable or empty.")

        # 2. AI Generation with Retry Logic
        max_retries = 3
        report_data = None
        
        prompt = f"Act as Principal Engineer at BluePeak. Review Week {week} simulation code:\n{code_context}"

        for attempt in range(max_retries):
            try:
                response = ai_client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt,
                    config={
                        'response_mime_type': 'application/json',
                        'response_schema': AIReviewReport,
                    }
                )
                report_data = response.parsed
                break 
            except Exception as ai_err:
                if "503" in str(ai_err) and attempt < max_retries - 1:
                    await asyncio.sleep((attempt + 1) * 3)
                else:
                    raise ai_err

        if not report_data:
            raise HTTPException(status_code=503, detail="AI Service Overloaded.")

        # [cite_start]3. Save to Supabase [cite: 5, 17, 30, 43]
        supabase.table("submissions").insert({
            "user_id": user_id,
            "week_number": week,
            "repo_url": repo_url,
            "score": report_data.score,
            "feedback": report_data.feedback,
            "passed": report_data.passed
        }).execute()

        return {"status": "success", "report": report_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import asyncio
import time
from fastapi import FastAPI, Body, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.routers import internships
from app.services.repo_service import extract_code_from_repo
from app.supabase_client import supabase 
from google import genai
from pydantic import BaseModel, Field
import razorpay
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="BluePeak Professional API",
    description="2026 Edition: Payments, AI Grading, and Simulations",
    version="1.1.1"
)

# --- 1. CONFIGURATION & CLIENTS ---
rzp_client = razorpay.Client(
    auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET"))
)
ai_client = genai.Client()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. STRUCTURED AI MODELS ---
class AIReviewReport(BaseModel):
    score: int = Field(description="Score out of 100")
    feedback: str = Field(description="3-4 bullet points of technical feedback")
    passed: bool = Field(description="True if the score is 60 or higher")

# --- 3. ROUTES & ENDPOINTS ---
app.include_router(internships.router)

@app.get("/")
async def root():
    return {"status": "online", "message": "BluePeak API v1.1.1 operational."}

# --- 4. PAYMENT ENDPOINTS ---
@app.post("/payments/create-order")
async def create_order(amount: int = Body(..., embed=True)):
    try:
        data = {"amount": amount * 100, "currency": "INR", "receipt": "receipt_bluepeak_enroll"}
        return rzp_client.order.create(data=data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/payments/verify")
async def verify_payment(payload: dict = Body(...)):
    try:
        rzp_client.utility.verify_payment_signature(payload)
        return {"status": "success"}
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Signature")

# --- 5. AI AUTO-GRADER ENDPOINT (WITH RETRY LOGIC) ---

@app.post("/internships/submit")
async def submit_internship(
    user_id: str = Body(...), 
    repo_url: str = Body(...), 
    week: int = Body(...)
):
    try:
        # 1. Extraction
        code_context = extract_code_from_repo(repo_url, user_id, week)
        if not code_context:
            raise HTTPException(status_code=400, detail="Repo unreadable or empty.")

        # 2. AI Generation with Retry Logic for 503 Errors
        max_retries = 3
        report_data = None
        
        prompt = f"""
        Act as a Principal Engineer at BluePeak Labs. Review Week {week} simulation code.
        Focus on: structure, security (.env usage), and core logic implementation.
        STUDENT CODE:
        {code_context}
        """

        for attempt in range(max_retries):
            try:
                response = ai_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config={
                        'response_mime_type': 'application/json',
                        'response_schema': AIReviewReport,
                    }
                )
                report_data = response.parsed
                break # Success! Exit the loop.
            
            except Exception as ai_err:
                # If Gemini is overloaded (503), wait and retry
                if "503" in str(ai_err) and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 3  # 3s, 6s wait
                    print(f"Gemini Overloaded (503). Attempt {attempt + 1} failed. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    # If it's a different error or we're out of retries, raise it
                    print(f"Permanent AI Error: {ai_err}")
                    raise ai_err

        if not report_data:
            raise HTTPException(status_code=503, detail="AI Service is currently overloaded. Please try again in a few moments.")

        # 3. Save to Supabase
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
        print(f"Submission Error: {e}")
        error_msg = str(e)
        if "503" in error_msg:
            error_msg = "Google's AI servers are busy. We tried 3 times. Please wait a minute and click 'Run Review' again."
        raise HTTPException(status_code=500, detail=error_msg)
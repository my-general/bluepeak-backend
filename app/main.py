import asyncio
import os
import razorpay
from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from supabase import create_client, Client
from google import genai
from dotenv import load_dotenv

# Ensure this service exists in your local folder structure
from app.services.repo_service import extract_code_from_repo

# Load Local Environment Variables
load_dotenv()

app = FastAPI(
    title="BluePeak Professional API", 
    description="2026 Edition: Payment Gateway & AI Simulation Auditing",
    version="1.1.6"
)

# --- 1. CONFIGURATION & CLIENTS ---
# Using the keys provided (Ensure these are in your .env file)
RZP_ID = os.getenv("RAZORPAY_KEY_ID")
RZP_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

# Razorpay Client
rzp_client = razorpay.Client(auth=(RZP_ID, RZP_SECRET))

# Gemini AI Client (2.0 Flash)
ai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Supabase Client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"), 
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

# CORS Policy - Allowing local and potential production origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-bluepeak-app.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. DATA MODELS ---

class OrderRequest(BaseModel):
    course_id: str
    user_id: str

class VerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    user_id: str
    course_id: str

class AIReviewReport(BaseModel):
    score: int = Field(description="Score out of 100")
    feedback: str = Field(description="3-4 bullet points of technical feedback")
    passed: bool = Field(description="True if score is 60 or higher")

class SubmissionRequest(BaseModel):
    user_id: str
    repo_url: str
    course_id: str
    week: int

# --- 3. PAYMENT ENDPOINTS ---

@app.post("/payments/create-order")
async def create_order(request: OrderRequest):
    try:
        # Fetch the real price from Supabase 'courses' table
        res = supabase.table("courses").select("fee_amount").eq("id", request.course_id).single().execute()
        
        if not res.data:
            raise HTTPException(status_code=404, detail="Track fee not configured in DB.")
            
        amount_in_paise = int(res.data['fee_amount'] * 100)
        
        data = {
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": f"rcpt_{request.course_id[:3]}_{request.user_id[:5]}",
            "notes": {
                "user_id": request.user_id,
                "course_id": request.course_id
            }
        }
        order = rzp_client.order.create(data=data)
        return order
    except Exception as e:
        print(f"🔥 Order Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/payments/verify")
async def verify_payment(request: VerifyRequest):
    try:
        # 1. Razorpay Signature Verification
        params_dict = {
            'razorpay_order_id': request.razorpay_order_id,
            'razorpay_payment_id': request.razorpay_payment_id,
            'razorpay_signature': request.razorpay_signature
        }
        rzp_client.utility.verify_payment_signature(params_dict)

        # 2. Database Record Creation (Linking Payment to User)
        enrollment_data = {
            "user_id": request.user_id,
            "course_id": request.course_id,
            "status": "active"
        }
        
        # Upsert ensures that refreshing doesn't cause a duplicate error
        supabase.table("enrollments").upsert(enrollment_data, on_conflict="user_id,course_id").execute()
        
        return {"status": "success", "message": f"Successfully enrolled in {request.course_id}"}

    except Exception as e:
        print(f"❌ Verification Failed: {str(e)}") 
        raise HTTPException(status_code=400, detail="Invalid payment signature or verification error.")

# --- 4. AI SIMULATION GRADER ---

@app.post("/internships/submit")
async def submit_internship(request: SubmissionRequest):
    try:
        # 1. Code Extraction
        code_context = extract_code_from_repo(request.repo_url, request.user_id, request.week)
        
        if not code_context:
            raise HTTPException(status_code=400, detail="Repository unreadable, empty, or private.")

        # 2. AI Prompting
        # We define a strict persona for Gemini 2.0 Flash
        prompt = f"""
        Act as a Principal Software Engineer at BluePeak Labs. 
        Review the following code for Week {request.week} of the {request.course_id} simulation.
        
        CRITERIA:
        - Logic Correctness: Does the code solve the problem?
        - Architecture: Is the project structure professional?
        - Security: Are there any leaked secrets or poor practices?

        CODE TO REVIEW:
        {code_context}
        """

        # Gemini 2.0 Flash Call
        response = ai_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={
                'response_mime_type': 'application/json',
                'response_schema': AIReviewReport,
            }
        )
        
        report_data = response.parsed

        # 3. Persistent Storage of the Grade
        supabase.table("submissions").insert({
            "user_id": request.user_id,
            "course_id": request.course_id,
            "week_number": request.week,
            "repo_url": request.repo_url,
            "score": report_data.score,
            "feedback": report_data.feedback,
            "passed": report_data.passed
        }).execute()

        return {"status": "success", "report": report_data}

    except Exception as e:
        print(f"🤖 AI Audit Error: {e}")
        # If AI fails, we don't want to crash the frontend, just return an error message
        raise HTTPException(status_code=500, detail=str(e))
        #raise HTTPException(status_code=500, detail="The AI Grading Engine is currently processing a high volume. Please try again.")

@app.get("/")
async def health_check():
    return {"status": "operational", "engine": "BluePeak 2026 Core", "version": "1.1.6"}

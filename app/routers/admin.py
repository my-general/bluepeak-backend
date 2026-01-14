from fastapi import APIRouter, Depends, HTTPException
from app.supabase_client import supabase

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/stats")
async def get_admin_stats():
    # 1. Get Total Students
    students = supabase.table("profiles").select("id", count="exact").execute()
    
    # 2. Get Revenue (Sum of amounts from your payments table)
    # 3. Get Graduates (Count users who passed week 4)
    graduates = supabase.table("submissions") \
        .select("user_id") \
        .eq("week_number", 4) \
        .eq("passed", True) \
        .execute()

    return {
        "total_students": students.count,
        "total_graduates": len(graduates.data),
        "total_revenue": 49900 # Example: Fetch this from Razorpay/Supabase
    }
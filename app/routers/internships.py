from fastapi import APIRouter, HTTPException
from app.supabase_client import supabase
from app.schemas.internship import InternshipResponse
from typing import List

router = APIRouter(prefix="/internships", tags=["Internships"])

@router.get("/", response_model=List[InternshipResponse])
async def get_all_internships():
    # Fetch data from Supabase
    response = supabase.table("internships").select("*").execute()
    
    if not response.data:
        return []
        
    return response.data

@router.get("/{id}", response_model=InternshipResponse)
async def get_internship_details(id: str):
    response = supabase.table("internships").select("*").eq("id", id).single().execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Internship not found")
        
    return response.data
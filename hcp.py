from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.db import get_db
from models.models import HCP
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class HCPCreate(BaseModel):
    name: str
    specialty: Optional[str] = ""
    institution: Optional[str] = ""
    email: Optional[str] = ""
    phone: Optional[str] = ""
    territory: Optional[str] = ""

@router.get("/")
def get_hcps(db: Session = Depends(get_db)):
    hcps = db.query(HCP).all()
    if not hcps:
        # Seed with sample data
        seeds = [
            HCP(name="Dr. Ananya Sharma", specialty="Oncology", institution="Apollo Hospital", territory="Hyderabad"),
            HCP(name="Dr. Rajesh Patel", specialty="Cardiology", institution="AIIMS", territory="Delhi"),
            HCP(name="Dr. Priya Mehta", specialty="Neurology", institution="Manipal Hospital", territory="Bangalore"),
            HCP(name="Dr. Suresh Kumar", specialty="Endocrinology", institution="Fortis", territory="Mumbai"),
            HCP(name="Dr. Kavitha Reddy", specialty="Pulmonology", institution="KIMS", territory="Hyderabad"),
        ]
        for seed in seeds:
            db.add(seed)
        db.commit()
        hcps = db.query(HCP).all()
    
    return [{"id": h.id, "name": h.name, "specialty": h.specialty, 
             "institution": h.institution, "territory": h.territory} for h in hcps]

@router.post("/")
def create_hcp(hcp: HCPCreate, db: Session = Depends(get_db)):
    db_hcp = HCP(**hcp.dict())
    db.add(db_hcp)
    db.commit()
    db.refresh(db_hcp)
    return {"id": db_hcp.id, "message": "HCP created"}
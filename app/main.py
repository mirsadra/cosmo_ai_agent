"""
Cosmetic Formulation AI Agent - Main FastAPI Application
main.py
Labrugis Ltd. 2025
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
import uvicorn
from contextlib import asynccontextmanager
from models import (
    FormulationRequest, 
    FormulationResponse, 
    Ingredient, 
    IngredientAdd,
    ComplianceCheck,
    OptimizationRequest
)
from database import DatabaseManager
from logic import FormulationEngine


# Initialize database and engine
db_manager = DatabaseManager()
formulation_engine = FormulationEngine(db_manager)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize application on startup"""
    # Load initial data
    await db_manager.initialize()
    print("🧪 Cosmetic Formulation AI Agent initialized")
    print("📋 Database loaded with ingredients and templates")
    yield
    # Cleanup if needed
    print("🔄 Shutting down gracefully")

# Create FastAPI app
app = FastAPI(
    title="Cosmetic Formulation AI Agent",
    description="AI-powered cosmetic formulation system for UK market compliance",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Cosmetic Formulation AI Agent",
        "status": "active",
        "version": "1.0.0",
        "compliance": "UKES-ready"
    }

@app.get("/ingredients", response_model=List[Ingredient])
async def get_ingredients(
    category: Optional[str] = None,
    function: Optional[str] = None,
    limit: int = 100
):
    """Get available ingredients with optional filtering"""
    try:
        ingredients = await db_manager.get_ingredients(
            category=category,
            function=function,
            limit=limit
        )
        return ingredients
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingredients", response_model=Dict[str, str])
async def add_ingredient(ingredient: IngredientAdd):
    """Add new ingredient to database"""
    try:
        result = await db_manager.add_ingredient(ingredient)
        return {"message": "Ingredient added successfully", "id": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/formulate", response_model=FormulationResponse)
async def create_formulation(request: FormulationRequest):
    """Generate cosmetic formulation based on requirements"""
    try:
        formulation = await formulation_engine.generate_formulation(request)
        return formulation
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/compliance-check", response_model=ComplianceCheck)
async def check_compliance(formulation_data: Dict[str, Any]):
    """Check formulation compliance with UKES regulations"""
    try:
        compliance = await formulation_engine.check_compliance(formulation_data)
        return compliance
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/optimize", response_model=FormulationResponse)
async def optimize_formulation(request: OptimizationRequest):
    """Optimize existing formulation for cost, stability, or performance"""
    try:
        optimized = await formulation_engine.optimize_formulation(request)
        return optimized
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/templates")
async def get_templates(product_type: Optional[str] = None):
    """Get available formulation templates"""
    try:
        templates = await db_manager.get_templates(product_type)
        return templates
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/regulatory-info")
async def get_regulatory_info():
    """Get current UK/EU regulatory information"""
    return {
        "ukes_compliance": True,
        "cpnp_ready": True,
        "last_updated": "2025-01-01",
        "prohibited_substances": "Updated per EU Regulation 1223/2009",
        "concentration_limits": "Current as of 2025",
        "labeling_requirements": "UK specific requirements included"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
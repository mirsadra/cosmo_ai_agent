from fastapi import FastAPI
from app.models import FormulationRequest, FormulationResponse
from app.logic import generate_formulation

app = FastAPI(title="Cosmetic Formulation AI Agent")

@app.post("/formulate", response_model=FormulationResponse)
def formulate(request: FormulationRequest):
    return generate_formulation(request)

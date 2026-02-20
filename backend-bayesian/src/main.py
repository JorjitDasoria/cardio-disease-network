import os
from google import genai  # <--- NEW LIBRARY IMPORT
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional
from dotenv import load_dotenv
from src.model_logic import CardioBayesianModel

# 1. Load API Key
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# 2. Configure the New Google Client
# The new library uses a client instance rather than global configuration
client = genai.Client(api_key=API_KEY)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

bayesian_service = CardioBayesianModel()

@app.on_event("startup")
def startup_event():
    try:
        bayesian_service.load_and_train()
    except Exception as e:
        print(f"Failed to start model: {e}")

class PredictionRequest(BaseModel):
    evidence: Dict[str, str]
    treatments: Optional[Dict[str, str]] = None

@app.get("/")
def read_root():
    return {"status": "Bayesian Backend is running"}

@app.get("/network-structure")
def get_graph():
    return bayesian_service.get_structure()

@app.get("/verify")
def verify_model():
    """Returns statistical and clinical verification metrics."""
    if not bayesian_service.infer:
        raise HTTPException(status_code=503, detail="Model not trained")
    return bayesian_service.verify_model_performance()

@app.post("/predict")
def predict_heart_disease(request: PredictionRequest):
    if not bayesian_service.infer:
        raise HTTPException(status_code=503, detail="Model not trained")

    base_probability = bayesian_service.predict_risk(request.evidence)
    final_probability = float(base_probability)

    # Apply Treatment Reductions
    if request.treatments:
        t = request.treatments
        if t.get('statin') == 'High': final_probability *= 0.57
        elif t.get('statin') == 'Moderate': final_probability *= 0.70
        if t.get('bp_med') == 'Dual': final_probability *= 0.43
        elif t.get('bp_med') == 'Monotherapy': final_probability *= 0.65
        if t.get('pci') == 'Yes': final_probability *= 0.80

    return {
        "base_probability": float(base_probability),
        "disease_probability": round(final_probability, 4),
        "risk_level": "High" if final_probability > 0.5 else "Low"
    }

# --- NEW GENAI ENDPOINT ---
@app.post("/ask-ai")
def ask_ai_doctor(request: PredictionRequest):

    try:
        # 1. Construct prompt
        prompt = "Act as a Cardiologist. Evaluate the CVD risk for a patient with:\n"
        for key, value in request.evidence.items():
            prompt += f"- {key}: {value}\n"

        if request.treatments:
            prompt += "Treatments:\n"
            for key, value in request.treatments.items():
                prompt += f"- {key}: {value}\n"

        prompt += "\nTask: Provide a percentage estimate of heart disease risk and a 1-sentence explanation. Be concise."

        # 2. Call Gemini API (New Syntax)
        # Note: We switched to 'gemini-2.0-flash' as 1.5 is being phased out on some endpoints
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )

        # 3. Extract text
        return {"ai_response": response.text}

    except Exception as e:
        print(f"Gemini API Error: {e}")

        # Fallback Mock Response
        risk_level = "High" if bayesian_service.predict_risk(request.evidence) > 0.5 else "Low"
        return {
            "ai_response": f"**[AI UNAVAILABLE - Error: {str(e)}]**\nBased on clinical factors, risk appears {risk_level}."
        }
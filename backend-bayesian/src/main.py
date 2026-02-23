import os
from google import genai  # <--- NEW LIBRARY IMPORT
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional, Any
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

@app.get("/advanced-network")
def get_advanced_network_visual():
    """Returns structure and probabilities for the advanced graph visualization."""
    if not bayesian_service.model:
        raise HTTPException(status_code=503, detail="Model not trained")
    return bayesian_service.get_full_network_data()

@app.post("/verify")
def verify_model_dynamic(patient_data: Dict[str, Any]):
    """Returns dynamic statistical and clinical verification metrics based on user input."""
    if not bayesian_service.infer:
        raise HTTPException(status_code=503, detail="Model not trained")

    try:
        return bayesian_service.verify_model_performance(patient_data)
    except Exception as e:
        print(f"Verification Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
        # 1. Calculate the BN Risk FIRST to ground the AI
        bn_risk_float = bayesian_service.predict_risk(request.evidence)
        bn_percentage = bn_risk_float * 100
        risk_category = "High" if bn_risk_float > 0.5 else "Low"

        # 2. Construct the strict Prompt Grounding
        prompt = (
            "You are an AI medical assistant explaining a cardiovascular risk assessment. "
            "You MUST align your explanation with the provided mathematical model's result.\n\n"
            "Patient Profile:\n"
        )

        for key, value in request.evidence.items():
            prompt += f"- {key}: {value}\n"

        if request.treatments:
            prompt += "Treatments:\n"
            for key, value in request.treatments.items():
                prompt += f"- {key}: {value}\n"

        # 3. The Client Requirement: Force Trend Alignment
        prompt += f"\nCRITICAL INSTRUCTION:\n"
        prompt += f"Our deterministic Bayesian Network has already calculated this specific patient's risk to be exactly {bn_percentage:.1f}% ({risk_category} Risk) based on our custom clinical dataset.\n"
        prompt += "RULES:\n"
        prompt += "1. NO HALLUCINATING NUMBERS: Do not calculate or state your own risk percentages (e.g., do not reference ASCVD scores).\n"
        prompt += f"2. TREND ALIGNMENT: Your analysis MUST completely align with the {bn_percentage:.1f}% risk figure. If the math model calculates a surprisingly low risk despite traditional risk factors, explain that 'within the context of this specific dataset, these combined factors represent a lower relative probability.' Do not contradict the model.\n"
        prompt += "3. FORMAT: Keep it brief, professional, and under 3 sentences."

        # 4. Call Gemini API
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )

        # 5. Extract text
        return {"ai_response": response.text}

    except Exception as e:
        print(f"Gemini API Error: {e}")

        # Fallback Mock Response
        try:
            risk_level = "High" if bayesian_service.predict_risk(request.evidence) > 0.5 else "Low"
        except:
            risk_level = "Unknown"

        return {
            "ai_response": f"**[AI UNAVAILABLE - Error: {str(e)}]**\nBased on clinical factors, risk appears {risk_level}."
        }
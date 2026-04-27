import requests
import json
import time

# Ensure your FastAPI server is running on this URL
BASE_URL = "http://localhost:8000"

# Define a batch of hypothetical patient profiles to test
test_patients = [
    {
        "name": "1. Perfect Health (Baseline)",
        "evidence": {
            "Age_Bin": "Young", "Sex_Label": "Female", "BP_Bin": "Normal",
            "Chol_Bin": "Desirable", "HR_Bin": "High_Rate", "CP_Label": "Non_Anginal",
            "FBS_Label": "Normal_Sugar", "CA_Label": "0.0_Vessels", "Thal_Label": "Normal"
        },
        "treatments": {"statin": "None", "bp_med": "None", "pci": "None"}
    },
    {
        "name": "2. Classic High Risk (Untreated)",
        "evidence": {
            "Age_Bin": "Old", "Sex_Label": "Male", "BP_Bin": "High_BP",
            "Chol_Bin": "High_Chol", "HR_Bin": "Low_Rate", "CP_Label": "Typical_Angina",
            "FBS_Label": "High_Sugar", "CA_Label": "3.0_Vessels", "Thal_Label": "Reversible_Defect"
        },
        "treatments": {"statin": "None", "bp_med": "None", "pci": "None"}
    },
    {
        "name": "3. Classic High Risk (Aggressively Treated)",
        "evidence": {
            "Age_Bin": "Old", "Sex_Label": "Male", "BP_Bin": "High_BP",
            "Chol_Bin": "High_Chol", "HR_Bin": "Low_Rate", "CP_Label": "Typical_Angina",
            "FBS_Label": "High_Sugar", "CA_Label": "3.0_Vessels", "Thal_Label": "Reversible_Defect"
        },
        "treatments": {"statin": "High", "bp_med": "Dual", "pci": "Yes"}
    },
    {
        "name": "4. The Borderline Case",
        "evidence": {
            "Age_Bin": "Middle", "Sex_Label": "Male", "BP_Bin": "Elevated",
            "Chol_Bin": "Borderline", "HR_Bin": "Normal_Rate", "CP_Label": "Atypical_Angina",
            "FBS_Label": "Normal_Sugar", "CA_Label": "1.0_Vessels", "Thal_Label": "Normal"
        },
        "treatments": {"statin": "None", "bp_med": "None", "pci": "None"}
    },
    {
        "name": "5. The Dataset Paradox (Asymptomatic)",
        "evidence": {
            "Age_Bin": "Young", "Sex_Label": "Male", "BP_Bin": "Normal",
            "Chol_Bin": "Desirable", "HR_Bin": "Normal_Rate", "CP_Label": "Asymptomatic",
            "FBS_Label": "Normal_Sugar", "CA_Label": "0.0_Vessels", "Thal_Label": "Normal"
        },
        "treatments": {"statin": "None", "bp_med": "None", "pci": "None"}
    },
    {
        "name": "6. Hidden Danger (Normal Vitals, Bad Scan)",
        "evidence": {
            "Age_Bin": "Middle", "Sex_Label": "Female", "BP_Bin": "Normal",
            "Chol_Bin": "Desirable", "HR_Bin": "High_Rate", "CP_Label": "Non_Anginal",
            "FBS_Label": "Normal_Sugar", "CA_Label": "2.0_Vessels", "Thal_Label": "Fixed_Defect"
        },
        "treatments": {"statin": "Moderate", "bp_med": "None", "pci": "None"}
    },
    {
        "name": "7. The Paradox (Old, Bad Vitals, Clean Scan)",
        "evidence": {
            "Age_Bin": "Old", "Sex_Label": "Male", "BP_Bin": "High_BP",
            "Chol_Bin": "High_Chol", "HR_Bin": "Low_Rate", "CP_Label": "Asymptomatic",
            "FBS_Label": "High_Sugar", "CA_Label": "0.0_Vessels", "Thal_Label": "Normal"
        },
        "treatments": {"statin": "None", "bp_med": "None", "pci": "None"}
    },
    {
        "name": "8. Young Female (Genetically High Chol)",
        "evidence": {
            "Age_Bin": "Young", "Sex_Label": "Female", "BP_Bin": "Normal",
            "Chol_Bin": "High_Chol", "HR_Bin": "High_Rate", "CP_Label": "Non_Anginal",
            "FBS_Label": "Normal_Sugar", "CA_Label": "0.0_Vessels", "Thal_Label": "Normal"
        },
        "treatments": {"statin": "Moderate", "bp_med": "None", "pci": "None"}
    },
    {
        "name": "9. Middle-Aged Male (Previous Stent)",
        "evidence": {
            "Age_Bin": "Middle", "Sex_Label": "Male", "BP_Bin": "Normal",
            "Chol_Bin": "Desirable", "HR_Bin": "Normal_Rate", "CP_Label": "Atypical_Angina",
            "FBS_Label": "Normal_Sugar", "CA_Label": "1.0_Vessels", "Thal_Label": "Fixed_Defect"
        },
        "treatments": {"statin": "High", "bp_med": "Monotherapy", "pci": "Yes"}
    },
    {
        "name": "10. Silent Ischemia",
        "evidence": {
            "Age_Bin": "Old", "Sex_Label": "Female", "BP_Bin": "Elevated",
            "Chol_Bin": "Borderline", "HR_Bin": "Low_Rate", "CP_Label": "Asymptomatic",
            "FBS_Label": "Normal_Sugar", "CA_Label": "2.0_Vessels", "Thal_Label": "Reversible_Defect"
        },
        "treatments": {"statin": "None", "bp_med": "None", "pci": "None"}
    },
    {
        "name": "11. High Stress, Normal Vessels",
        "evidence": {
            "Age_Bin": "Middle", "Sex_Label": "Male", "BP_Bin": "High_BP",
            "Chol_Bin": "Borderline", "HR_Bin": "High_Rate", "CP_Label": "Typical_Angina",
            "FBS_Label": "Normal_Sugar", "CA_Label": "0.0_Vessels", "Thal_Label": "Normal"
        },
        "treatments": {"statin": "None", "bp_med": "Dual", "pci": "None"}
    }
]

print(f"{'Patient Profile':<40} | {'Math (BN) %':<15} | {'AI %':<10} | {'Difference'}")
print("-" * 85)

for patient in test_patients:
    payload = {
        "evidence": patient["evidence"],
        "treatments": patient["treatments"]
    }

    try:
        # 1. Get the Math Score
        bn_response = requests.post(f"{BASE_URL}/predict", json=payload)
        bn_data = bn_response.json()
        math_score = bn_data.get("disease_probability", 0) * 100

        # 2. Get the AI Score
        ai_response = requests.post(f"{BASE_URL}/ask-ai-general", json=payload)
        ai_data = ai_response.json()
        ai_score = ai_data.get("ai_percentage", 0)

        # Calculate the disparity
        diff = abs(math_score - ai_score)


        #save to database
        save_payload = {
            "patient_name": patient["name"],
            "bn_score": math_score,
            "ai_score": ai_score
        }
        requests.post(f"{BASE_URL}/save-record", json=save_payload)

        # Print the row
        print(f"{patient['name']:<40} | {math_score:>14.1f}% | {ai_score:>9}% | {diff:>8.1f}%")

        # Small delay to prevent hitting free-tier API rate limits
        time.sleep(2)

    except Exception as e:
        print(f"Failed to process {patient['name']}: {e}")

print("-" * 85)
print("Testing Complete. You can copy this data into Excel or a CSV for the client.")
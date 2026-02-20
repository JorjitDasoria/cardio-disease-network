import pandas as pd
import numpy as np
from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.estimators import BayesianEstimator
from pgmpy.inference import VariableElimination
import os

# Define the path to your dataset
DATASET_PATH = os.path.join(os.path.dirname(__file__), 'heart_disease_dataset.csv')

class CardioBayesianModel:
    def __init__(self):
        self.model = None
        self.infer = None

    def load_and_train(self):
        """Loads data, discretizes it, defines structure, and trains the model."""
        if not os.path.exists(DATASET_PATH):
            raise FileNotFoundError(f"Dataset not found at {DATASET_PATH}")

        print(f"Loading dataset from: {DATASET_PATH}")
        df = pd.read_csv(DATASET_PATH)

        # Process the data
        formatted_df = self._discretize_heart_data(df)

        self.training_data = formatted_df

        if formatted_df.empty:
            raise ValueError("CRITICAL ERROR: Dataset is empty after processing.")

        print(f"--- Processed Data Info ({len(formatted_df)} rows) ---")
        print(formatted_df.head())
        print(formatted_df.dtypes)  # DEBUG: Ensure all are 'object' (string)

        # Define the structure
        self.model = DiscreteBayesianNetwork([
            ('Sex_Label', 'BP_Bin'),
            ('Sex_Label', 'Chol_Bin'),
            ('Age_Bin', 'BP_Bin'),
            ('Age_Bin', 'Chol_Bin'),
            ('Age_Bin', 'HR_Bin'),
            ('Age_Bin', 'CA_Label'),
            ('Chol_Bin', 'CA_Label'),
            ('HR_Bin', 'CA_Label'),
            ('Sex_Label', 'Disease_Target'),
            ('BP_Bin', 'Disease_Target'),
            ('Chol_Bin', 'Disease_Target'),
            ('HR_Bin', 'Disease_Target'),
            ('Oldpeak_Bin', 'Disease_Target'),
            ('Slope_Label', 'Disease_Target'),
            ('CA_Label', 'Disease_Target'),
            ('Thal_Label', 'Disease_Target'),
            ('FBS_Label', 'Disease_Target'),
            ('ECG_Label', 'Disease_Target'),
            ('Disease_Target', 'Exang_Label'),
            ('Disease_Target', 'CP_Label')
        ])

        print("Fitting model...")
        self.model.fit(formatted_df, estimator=BayesianEstimator, prior_type='BDeu', equivalent_sample_size=10)
        self.infer = VariableElimination(self.model)
        print("Model trained successfully.")

    def predict_risk(self, evidence):
        try:
            result = self.infer.query(variables=['Disease_Target'], evidence=evidence)
            # Adjust index based on your specific target labels ('Positive' vs 'Negative')
            if 'Positive' in result.state_names['Disease_Target']:
                pos_idx = result.name_to_no['Disease_Target']['Positive']
                return result.values[pos_idx]
            else:
                return 0.0
        except Exception as e:
            print(f"Prediction Error: {e}")
            return None

    def get_structure(self):
        return {
            "nodes": list(self.model.nodes()),
            "edges": list(self.model.edges())
        }


    def verify_model_performance(self):
        """
        Runs statistical and clinical checks on the model.
        """
        if self.infer is None or self.training_data is None:
            return {"error": "Model not trained"}

        results = {}

        # 1. STATISTICAL VERIFICATION (Data vs. Model)
        # Calculate frequency of 'Positive' disease in the raw dataset
        actual_counts = self.training_data['Disease_Target'].value_counts(normalize=True)
        data_prob = actual_counts.get('Positive', 0.0)

        # Calculate marginal probability in the Bayesian Network
        model_prob_obj = self.infer.query(variables=['Disease_Target'])
        # Extract the probability for 'Positive'
        pos_index = model_prob_obj.name_to_no['Disease_Target']['Positive']
        model_prob = model_prob_obj.values[pos_index]

        results['statistical'] = {
            "dataset_prevalence": float(data_prob),
            "model_probability": float(model_prob),
            "difference": float(abs(data_prob - model_prob))
        }

        # 2. CLINICAL VERIFICATION (Scenario Testing)
        # Scenario: Old Age + High BP + High Chol (Should be VERY High Risk)
        clinical_q = self.infer.query(
            variables=['Disease_Target'],
            evidence={'Age_Bin': 'Old', 'BP_Bin': 'High_BP', 'Chol_Bin': 'High_Chol'}
        )
        results['clinical_scenario'] = float(clinical_q.values[pos_index])

        # 3. EXPLAINING AWAY (Inter-causal Reasoning)
        # Does knowing High BP "explain away" the need for High Chol to be the cause?
        # A. Baseline: P(High Chol | Disease)
        base_chol = self.infer.query(variables=['Chol_Bin'], evidence={'Disease_Target': 'Positive'})
        chol_idx = base_chol.name_to_no['Chol_Bin']['High_Chol']
        prob_chol_given_disease = base_chol.values[chol_idx]

        # B. Explained: P(High Chol | Disease, High BP)
        # If High BP is present, does the probability of High Chol go down?
        exp_chol = self.infer.query(variables=['Chol_Bin'], evidence={'Disease_Target': 'Positive', 'BP_Bin': 'High_BP'})
        prob_chol_given_disease_bp = exp_chol.values[chol_idx]

        results['explaining_away'] = {
            "p_high_chol_given_disease": float(prob_chol_given_disease),
            "p_high_chol_given_disease_and_high_bp": float(prob_chol_given_disease_bp),
            "effect": "Probability Dropped (Explained Away)" if prob_chol_given_disease_bp < prob_chol_given_disease else "Probability Increased/Same"
        }

        return results


    def _discretize_heart_data(self, df):
        df_bin = df.copy()

        # 1. Ensure numeric columns are actually numeric
        numeric_cols = ['age', 'trestbps', 'chol', 'thalach', 'oldpeak', 'ca', 'num']
        for col in numeric_cols:
            if col in df_bin.columns:
                df_bin[col] = pd.to_numeric(df_bin[col], errors='coerce')

        # 2. Continuous Binning
        df_bin['Age_Bin'] = pd.cut(df_bin['age'], bins=[0, 45, 60, 120], labels=['Young', 'Middle', 'Old'])
        df_bin['BP_Bin'] = pd.cut(df_bin['trestbps'], bins=[0, 120, 140, 300], labels=['Normal', 'Elevated', 'High_BP'], right=False)
        df_bin['Chol_Bin'] = pd.cut(df_bin['chol'], bins=[0, 200, 240, 600], labels=['Desirable', 'Borderline', 'High_Chol'], right=False)
        df_bin['HR_Bin'] = pd.cut(df_bin['thalach'], bins=[0, 110, 150, 250], labels=['Low_Rate', 'Normal_Rate', 'High_Rate'])
        df_bin['Oldpeak_Bin'] = pd.cut(df_bin['oldpeak'], bins=[-1, 0, 2.0, 10], labels=['No_Depression', 'Ischemia', 'Severe_Ischemia'])

        # 3. Mappings
        df_bin['Sex_Label'] = df_bin['sex'].map({1: 'Male', 0: 'Female'})
        df_bin['CA_Label'] = df_bin['ca'].apply(lambda x: f"{x}_Vessels" if pd.notnull(x) else None)
        df_bin['CP_Label'] = df_bin['cp'].map({1: 'Typical_Angina', 2: 'Atypical_Angina', 3: 'Non_Anginal', 4: 'Asymptomatic'})
        df_bin['FBS_Label'] = df_bin['fbs'].map({1: 'High_Sugar', 0: 'Normal_Sugar'})
        df_bin['ECG_Label'] = df_bin['restecg'].map({0: 'Normal', 1: 'ST_Abnorm', 2: 'LVH'})
        df_bin['Exang_Label'] = df_bin['exang'].map({1: 'Yes', 0: 'No'})
        df_bin['Slope_Label'] = df_bin['slope'].map({1: 'Upsloping', 2: 'Flat', 3: 'Downsloping'})
        df_bin['Thal_Label'] = df_bin['thal'].map({3: 'Normal', 6: 'Fixed_Defect', 7: 'Reversible_Defect'})
        df_bin['Disease_Target'] = df_bin['num'].apply(lambda x: 'Positive' if x > 0 else 'Negative')

        cols_to_keep = ['Age_Bin', 'Sex_Label', 'CP_Label', 'BP_Bin', 'Chol_Bin',
                        'FBS_Label', 'ECG_Label', 'HR_Bin', 'Exang_Label',
                        'Oldpeak_Bin', 'Slope_Label', 'Thal_Label', 'CA_Label', 'Disease_Target']

        # 4. Filter and Drop NaNs
        df_subset = df_bin[cols_to_keep].dropna()

        # 5. FINAL FIXES:
        # A. Reset Index: Ensures rows are numbered 0, 1, 2... nicely
        df_subset = df_subset.reset_index(drop=True)

        # B. Convert to Object: pgmpy prefers 'object' over 'string'
        df_final = df_subset.astype(object)

        return df_final
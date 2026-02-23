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


    def verify_model_performance(self, patient_data: dict = None):
        """
        Runs statistical and dynamic clinical checks on the model.
        Uses exact 'Positive'/'Negative' string mapping based on the dataset.
        """
        if self.infer is None or self.training_data is None:
            return {"error": "Model not trained"}

        if patient_data is None:
            patient_data = {}

        results = {}
        TARGET_COLUMN = 'Disease_Target'
        POSITIVE_VAL = 'Positive'  # We now know this is exactly what your CSV uses!

        # --- 1. STATISTICAL VERIFICATION (MSE) ---
        try:
            # Get actual dataset probability for 'Positive'
            actual_counts = self.training_data[TARGET_COLUMN].value_counts(normalize=True)
            data_prob = actual_counts.get(POSITIVE_VAL, 0.0)

            # Get model probability for 'Positive'
            model_prob_obj = self.infer.query(variables=[TARGET_COLUMN])
            states = list(model_prob_obj.state_names[TARGET_COLUMN])
            pos_idx = states.index(POSITIVE_VAL)
            model_prob = model_prob_obj.values[pos_idx]

            # Calculate true Mean Squared Error
            mse_value = (data_prob - model_prob) ** 2

            results['statistical'] = {
                "dataset_prevalence": float(data_prob),
                "model_probability": float(model_prob),
                "difference": float(mse_value)
            }
        except Exception as e:
            print(f"Error in Statistical: {e}")
            results['statistical'] = {"dataset_prevalence": 0, "model_probability": 0, "difference": 0}

        # --- 2. DYNAMIC CLINICAL SCENARIO ---
        try:
            clean_evidence = {k: v for k, v in patient_data.items() if v and v != "-- Select --"}
            valid_evidence = {k: v for k, v in clean_evidence.items() if k in self.model.nodes()}

            clinical_q = self.infer.query(variables=[TARGET_COLUMN], evidence=valid_evidence)
            clin_states = list(clinical_q.state_names[TARGET_COLUMN])
            clin_pos_idx = clin_states.index(POSITIVE_VAL)

            results['clinical_scenario'] = float(clinical_q.values[clin_pos_idx])
        except Exception as e:
            print(f"Error in Clinical: {e}")
            results['clinical_scenario'] = 0.0

        # --- 3. DYNAMIC EXPLAINING AWAY ---
        try:
            if 'Chol_Bin' in self.model.nodes():
                # A. Base P(High Chol | Disease = Positive)
                base_chol = self.infer.query(variables=['Chol_Bin'], evidence={TARGET_COLUMN: POSITIVE_VAL})
                chol_states = list(base_chol.state_names['Chol_Bin'])

                # Find the state containing "High" (e.g., 'High_Chol')
                high_chol_idx = next((i for i, s in enumerate(chol_states) if 'High' in str(s)), len(chol_states) - 1)
                prob_chol_given_disease = base_chol.values[high_chol_idx]

                # B. Explained P(High Chol | Disease = Positive, User's BP)
                patient_bp = patient_data.get('BP_Bin')

                if patient_bp and patient_bp != "-- Select --" and 'BP_Bin' in self.model.nodes():
                    # Ensure the BP they selected is valid in the model before querying
                    bp_check = self.infer.query(variables=['BP_Bin'])
                    bp_states = list(bp_check.state_names['BP_Bin'])

                    if patient_bp in bp_states:
                        exp_chol = self.infer.query(variables=['Chol_Bin'], evidence={TARGET_COLUMN: POSITIVE_VAL, 'BP_Bin': patient_bp})
                        prob_chol_given_disease_bp = exp_chol.values[high_chol_idx]
                    else:
                        prob_chol_given_disease_bp = prob_chol_given_disease
                else:
                    prob_chol_given_disease_bp = prob_chol_given_disease

                effect_text = "Probability Dropped (Explained Away)" if prob_chol_given_disease_bp < prob_chol_given_disease else "Probability Increased/Same"

                results['explaining_away'] = {
                    "p_high_chol_given_disease": float(prob_chol_given_disease),
                    "p_high_chol_given_disease_and_patient_bp": float(prob_chol_given_disease_bp),
                    "effect": effect_text
                }
            else:
                raise ValueError("Chol_Bin node missing")
        except Exception as e:
            print(f"Error in Explaining Away: {e}")
            results['explaining_away'] = {
                "p_high_chol_given_disease": 0.0,
                "p_high_chol_given_disease_and_patient_bp": 0.0,
                "effect": "Error calculating"
            }

        return results

    def get_full_network_data(self):
        """
        Returns the network structure (edges) AND the base probabilities for each node.
        This is for the advanced visualization.
        """
        if self.infer is None:
            return {"error": "Model not trained"}

        # 1. Get the edges (same as before)
        edges = [list(edge) for edge in self.model.edges()]

        # 2. Get the probabilities for every node
        node_data = {}
        for node in self.model.nodes():
            try:
                # Query the base probability of this node (no evidence)
                prob_obj = self.infer.query(variables=[node])

                states = prob_obj.state_names[node]
                values = prob_obj.values

                # Format into a list of {state: 'High', prob: 0.45}
                node_probs = []
                for i, state in enumerate(states):
                    node_probs.append({
                        "state": str(state),
                        "prob": float(values[i]),
                        # Format as a nice percentage string
                        "label": f"{float(values[i])*100:.1f}%"
                    })

                node_data[node] = node_probs
            except Exception as e:
                print(f"Could not get probabilities for node {node}: {e}")
                node_data[node] = []

        return {
            "edges": edges,
            "nodes": node_data
        }


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
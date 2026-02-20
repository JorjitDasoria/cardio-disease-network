import React, { useState } from 'react';
import axios from 'axios';

const RiskCalculator = () => {
    const [evidence, setEvidence] = useState({});
    const [treatments, setTreatments] = useState({ statin: 'None', bp_med: 'None', pci: 'None' });

    // Results
    const [bayesResult, setBayesResult] = useState(null);
    const [aiResult, setAiResult] = useState(null);

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleEvidenceChange = (e) => {
        const { name, value } = e.target;
        const newEvidence = { ...evidence };
        if (value === "") delete newEvidence[name];
        else newEvidence[name] = value;
        setEvidence(newEvidence);
    };

    const handleTreatmentChange = (e) => {
        const { name, value } = e.target;
        setTreatments(prev => ({ ...prev, [name]: value }));
    };

    const calculateRisk = async () => {
        setLoading(true);
        setError(null);
        setBayesResult(null);
        setAiResult(null);

        const payload = { evidence, treatments };

        try {
            // 1. Call Bayesian Model
            const bayesReq = axios.post(`${process.env.REACT_APP_API_URL}/predict`, payload);

            // 2. Call AI Wrapper (Run in parallel!)
            const aiReq = axios.post(`${process.env.REACT_APP_API_URL}/ask-ai`, payload);

            const [bayesRes, aiRes] = await Promise.all([bayesReq, aiReq]);

            setBayesResult(bayesRes.data);
            setAiResult(aiRes.data.ai_response);

        } catch (err) {
            console.error(err);
            setError("Calculation failed. Check backend/API Key.");
        }
        setLoading(false);
    };

    const handleReset = () => {
        setEvidence({});
        setTreatments({ statin: 'None', bp_med: 'None', pci: 'None' });
        setBayesResult(null);
        setAiResult(null);
    };

    return (
        <div style={styles.container}>

            {/* --- COLUMN 1: INPUT FORM --- */}
            <div style={styles.inputPanel}>
                <div style={styles.header}>
                    <h2>Patient Data</h2>
                    <button onClick={handleReset} style={styles.resetBtn}>Reset</button>
                </div>

                <div style={styles.scrollableForm}>
                    {/* 1. AGE: Based on bins [0, 45, 60, 120] */}
                    <FormSelect label="Age Group" name="Age_Bin" value={evidence.Age_Bin} onChange={handleEvidenceChange}>
                        <option value="Young">Young (&lt; 45 years)</option>
                        <option value="Middle">Middle (45 - 60 years)</option>
                        <option value="Old">Old (&gt; 60 years)</option>
                    </FormSelect>

                    <FormSelect label="Sex" name="Sex_Label" value={evidence.Sex_Label} onChange={handleEvidenceChange}>
                        <option value="Male">Male</option>
                        <option value="Female">Female</option>
                    </FormSelect>

                    {/* 2. BLOOD PRESSURE: Based on bins [0, 120, 140, 300] */}
                    <FormSelect label="Blood Pressure (Resting)" name="BP_Bin" value={evidence.BP_Bin} onChange={handleEvidenceChange}>
                        <option value="Normal">Normal (&lt; 120 mmHg)</option>
                        <option value="Elevated">Elevated (120 - 139 mmHg)</option>
                        <option value="High_BP">High (≥ 140 mmHg)</option>
                    </FormSelect>

                    {/* 3. CHOLESTEROL: Based on bins [0, 200, 240, 600] */}
                    <FormSelect label="Cholesterol" name="Chol_Bin" value={evidence.Chol_Bin} onChange={handleEvidenceChange}>
                        <option value="Desirable">Desirable (&lt; 200 mg/dL)</option>
                        <option value="Borderline">Borderline (200 - 239 mg/dL)</option>
                        <option value="High_Chol">High (≥ 240 mg/dL)</option>
                    </FormSelect>

                    {/* 4. HEART RATE: Based on bins [0, 110, 150, 250] */}
                    <FormSelect label="Max Heart Rate" name="HR_Bin" value={evidence.HR_Bin} onChange={handleEvidenceChange}>
                        <option value="Low_Rate">Low (&lt; 110 bpm)</option>
                        <option value="Normal_Rate">Normal (110 - 150 bpm)</option>
                        <option value="High_Rate">High (&gt; 150 bpm)</option>
                    </FormSelect>

                    <FormSelect label="Chest Pain Type" name="CP_Label" value={evidence.CP_Label} onChange={handleEvidenceChange}>
                        <option value="Typical_Angina">Typical Angina</option>
                        <option value="Atypical_Angina">Atypical Angina</option>
                        <option value="Non_Anginal">Non-Anginal Pain</option>
                        <option value="Asymptomatic">Asymptomatic</option>
                    </FormSelect>

                    {/* 5. FASTING BLOOD SUGAR: Based on > 120 threshold */}
                    <FormSelect label="Fasting Blood Sugar" name="FBS_Label" value={evidence.FBS_Label} onChange={handleEvidenceChange}>
                        <option value="Normal_Sugar">Normal (&lt; 120 mg/dL)</option>
                        <option value="High_Sugar">High (&gt; 120 mg/dL)</option>
                    </FormSelect>

                    <FormSelect label="Blocked Vessels (Fluoroscopy)" name="CA_Label" value={evidence.CA_Label} onChange={handleEvidenceChange}>
                        <option value="0.0_Vessels">0 Vessels</option>
                        <option value="1.0_Vessels">1 Vessel</option>
                        <option value="2.0_Vessels">2 Vessels</option>
                        <option value="3.0_Vessels">3 Vessels</option>
                    </FormSelect>

                    <FormSelect label="Thalassemia" name="Thal_Label" value={evidence.Thal_Label} onChange={handleEvidenceChange}>
                        <option value="Normal">Normal</option>
                        <option value="Fixed_Defect">Fixed Defect (Permanent)</option>
                        <option value="Reversible_Defect">Reversible Defect (Blood Flow Issue)</option>
                    </FormSelect>

                    <h4 style={{marginTop: '15px', borderTop: '1px solid #eee', paddingTop: '10px'}}>Interventions</h4>

                    <FormSelect label="Statin Therapy" name="statin" value={treatments.statin} onChange={handleTreatmentChange}>
                        <option value="None">None</option>
                        <option value="Moderate">Moderate Intensity (30% reduction)</option>
                        <option value="High">High Intensity (50% reduction)</option>
                    </FormSelect>

                    <FormSelect label="BP Medication" name="bp_med" value={treatments.bp_med} onChange={handleTreatmentChange}>
                        <option value="None">None</option>
                        <option value="Monotherapy">Monotherapy (Standard)</option>
                        <option value="Dual">Dual-Combination (Aggressive)</option>
                    </FormSelect>
                    <FormSelect label="History of PCI / Stents" name="pci" value={treatments.pci} onChange={handleTreatmentChange}>
                        <option value="None">No History</option>
                        <option value="Yes">Yes (Previous Procedure)</option>
                    </FormSelect>
                </div>

                <button onClick={calculateRisk} style={styles.calcBtn} disabled={loading}>
                    {loading ? "Analyzing..." : "Analyze Risk"}
                </button>
                {error && <p style={{ color: 'red', marginTop: '10px' }}>{error}</p>}
            </div>

            {/* --- COLUMN 2: BAYESIAN RESULT --- */}
            <div style={styles.resultPanel}>
                <h3 style={{color: '#2c3e50'}}>Bayesian Network</h3>
                <p style={{fontSize: '0.8rem', color: '#7f8c8d'}}>Deterministic Math Model</p>

                {bayesResult ? (
                    <div style={{ textAlign: 'center', marginTop: '20px' }}>
                        <h1 style={{ fontSize: '3.5rem', margin: '10px 0', color: bayesResult.disease_probability > 0.5 ? '#e74c3c' : '#2ecc71' }}>
                            {(bayesResult.disease_probability * 100).toFixed(1)}%
                        </h1>
                        <div style={{
                            padding: '8px 16px', borderRadius: '20px', display: 'inline-block',
                            backgroundColor: bayesResult.disease_probability > 0.5 ? '#e74c3c' : '#2ecc71',
                            color: 'white', fontWeight: 'bold'
                        }}>
                            {bayesResult.disease_probability > 0.5 ? "High Risk" : "Low Risk"}
                        </div>
                        <p style={{marginTop: '20px', fontSize: '0.9rem'}}>Calculated purely from dataset probabilities.</p>
                    </div>
                ) : (
                    <div style={styles.placeholder}>Waiting for data...</div>
                )}
            </div>

            {/* --- COLUMN 3: AI WRAPPER RESULT --- */}
            <div style={{...styles.resultPanel, borderLeft: '4px solid #8e44ad'}}>
                <h3 style={{color: '#8e44ad'}}>AI Doctor (LLM)</h3>
                <p style={{fontSize: '0.8rem', color: '#7f8c8d'}}>Generative "Opinion"</p>

                {aiResult ? (
                    <div style={{ marginTop: '20px', textAlign: 'left' }}>
                        <p style={{whiteSpace: 'pre-wrap', lineHeight: '1.5', fontSize: '0.95rem'}}>
                            {aiResult}
                        </p>
                        <div style={{marginTop: '20px', padding: '10px', backgroundColor: '#f0e6f5', borderRadius: '5px', fontSize: '0.8rem', color: '#8e44ad'}}>
                            <strong>Note:</strong> AI estimates may hallucinate or vary from the mathematical model.
                        </div>
                    </div>
                ) : (
                    <div style={styles.placeholder}>Waiting for data...</div>
                )}
            </div>

        </div>
    );
};

// ... Helper Components ...
const FormSelect = ({ label, name, value, onChange, children }) => (
    <div style={{ marginBottom: '10px' }}>
        <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 'bold' }}>{label}</label>
        <select name={name} value={value || ""} onChange={onChange} style={{ width: '100%', padding: '6px', borderRadius: '4px' }}>
            <option value="">-- Select --</option>
            {children}
        </select>
    </div>
);

const styles = {
    container: { display: 'flex', gap: '20px', marginTop: '30px', height: '600px', fontFamily: 'Arial, sans-serif' },
    inputPanel: { flex: '1', backgroundColor: '#fff', padding: '20px', borderRadius: '10px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)', display: 'flex', flexDirection: 'column' },
    scrollableForm: { flex: '1', overflowY: 'auto', paddingRight: '10px' },
    header: { display: 'flex', justifyContent: 'space-between', marginBottom: '15px' },
    resultPanel: { flex: '1', backgroundColor: '#f8f9fa', padding: '20px', borderRadius: '10px', textAlign: 'center', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' },
    calcBtn: { width: '100%', padding: '12px', backgroundColor: '#3498db', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer', marginTop: '10px' },
    resetBtn: { background: 'none', border: '1px solid #ccc', padding: '2px 8px', borderRadius: '4px', cursor: 'pointer' },
    placeholder: { marginTop: '100px', color: '#ccc', fontStyle: 'italic' }
};

export default RiskCalculator;
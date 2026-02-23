import React, { useEffect, useState } from 'react';
import axios from 'axios';

// We now pass 'evidence' and a trigger 'isAnalyzed' from the parent calculator
const VerificationPanel = ({ evidence, isAnalyzed }) => {
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        // Do not fetch until the user clicks the Analyze button
        if (!isAnalyzed) return;

        // Changed to POST to send the user's specific dropdown choices
        axios.post(`${process.env.REACT_APP_API_URL}/verify`, evidence)
            .then(res => {
                setData(res.data);
                setError(null);
            })
            .catch(err => {
                console.error("Verification failed:", err);
                setError("Backend Error: Check your Python logs. There is likely a column name mismatch in model_logic.py.");
            });
    }, [isAnalyzed, evidence]); // Re-runs whenever these change

    if (error) return <div style={{...styles.loading, color: 'red'}}>{error}</div>;
    if (!data) return <div style={styles.loading}>Fill out the patient data and click "Analyze Risk" to generate Verification Stats.</div>;

    return (
        <div style={styles.container}>
            <h3 style={styles.title}>✅ Dynamic Model Verification</h3>

            <div style={styles.grid}>
                {/* Card 1: Statistical Accuracy */}
                <div style={styles.card}>
                    <h4>1. Statistical Calibration</h4>
                    <p style={styles.desc}>Comparing Dataset Frequency vs. Model Probability</p>
                    <div style={styles.statRow}>
                        <span>Dataset Prevalence:</span>
                        <strong>{(data.statistical.dataset_prevalence * 100).toFixed(2)}%</strong>
                    </div>
                    <div style={styles.statRow}>
                        <span>Model Probability:</span>
                        <strong>{(data.statistical.model_probability * 100).toFixed(2)}%</strong>
                    </div>
                    <div style={{...styles.statRow, marginTop: '10px', color: data.statistical.difference < 0.05 ? 'green' : 'orange'}}>
                        <span>Mean Squared Error (MSE):</span>
                        <strong>{data.statistical.difference.toFixed(4)}</strong>
                    </div>
                </div>

                {/* Card 2: Dynamic Clinical Logic */}
                <div style={styles.card}>
                    <h4>2. Clinical Scenario Check</h4>
                    <p style={styles.desc}>Risk for: <i>Your Specific Patient</i></p>
                    <div style={styles.bigStat}>
                        {(data.clinical_scenario * 100).toFixed(1)}%
                    </div>
                    <p style={{fontSize: '0.8rem', color: '#666'}}>Matches your BN calculation above</p>
                </div>

                {/* Card 3: Dynamic Explaining Away */}
                <div style={styles.card}>
                    <h4>3. "Explaining Away" Effect</h4>
                    <p style={styles.desc}>Does their specific Blood Pressure explain the disease, reducing the likelihood of High Cholesterol?</p>
                    <div style={styles.statRow}>
                        <span>Base P(High Chol | Disease):</span>
                        <strong>{(data.explaining_away.p_high_chol_given_disease * 100).toFixed(1)}%</strong>
                    </div>
                    <div style={styles.statRow}>
                        <span>P(High Chol | Disease + Patient BP):</span>
                        <strong>{(data.explaining_away.p_high_chol_given_disease_and_patient_bp * 100).toFixed(1)}%</strong>
                    </div>
                    <div style={{marginTop: '10px', fontWeight: 'bold', color: '#2980b9'}}>
                        Result: {data.explaining_away.effect}
                    </div>
                </div>
            </div>
        </div>
    );
};

const styles = {
    container: { marginTop: '40px', padding: '20px', borderTop: '2px solid #eee' },
    title: { textAlign: 'center', marginBottom: '20px', color: '#2c3e50' },
    grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' },
    card: { padding: '20px', background: '#fff', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', border: '1px solid #ddd' },
    desc: { fontSize: '0.85rem', color: '#7f8c8d', marginBottom: '15px', fontStyle: 'italic' },
    statRow: { display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.9rem' },
    bigStat: { fontSize: '2.5rem', fontWeight: 'bold', color: '#e74c3c', textAlign: 'center', margin: '10px 0' },
    loading: { textAlign: 'center', padding: '20px', color: '#666', fontStyle: 'italic' }
};

export default VerificationPanel;
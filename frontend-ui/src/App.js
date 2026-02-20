import React from 'react';
import BayesianNetwork from './BayesianNetwork';
import RiskCalculator from './RiskCalculator'; // <--- Import it
import VerificationPanel from './VerificationPanel';

function App() {
    return (
        <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif', maxWidth: '1200px', margin: '0 auto' }}>
            <h1>Cardiovascular Disease Bayesian Network</h1>
            <p style={{ color: '#666' }}>
                This graph visualizes the probabilistic dependencies between risk factors.
            </p>

            {/* 1. The Graph Visualization */}
            <BayesianNetwork />

            <hr style={{ margin: '40px 0', border: '0', borderTop: '1px solid #eee' }} />

            {/* 2. The Interactive Calculator */}
            <h2 style={{ marginBottom: '10px' }}>Interactive Risk Calculator</h2>
            <p style={{ color: '#666' }}>
                Select known patient attributes below. The Bayesian Network will update the probability based on the evidence provided.
            </p>
            <RiskCalculator />
            <hr style={{ margin: '40px 0', border: '0', borderTop: '1px solid #eee' }} />
            <VerificationPanel />
        </div>
    );
}

export default App;
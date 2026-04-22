import React, { useEffect, useState } from 'react'; // <-- ADDED useState
import ReactFlow, {
    Background,
    Controls,
    useNodesState,
    useEdgesState,
    MarkerType
} from 'reactflow';
import 'reactflow/dist/style.css';
import axios from 'axios';
import dagre from 'dagre';

// 1. Import your custom node template
import ProbabilityNode from './ProbabilityNode';

// 2. Register the custom node type for React Flow
const nodeTypes = { probNode: ProbabilityNode };

// --- LAYOUT ENGINE (Auto-arranges nodes) ---
const getLayoutedElements = (nodes, edges) => {
    const dagreGraph = new dagre.graphlib.Graph();
    dagreGraph.setGraph({ rankdir: 'TB', ranksep: 80, nodesep: 50 });

    dagreGraph.setDefaultEdgeLabel(() => ({}));

    nodes.forEach((node) => {
        dagreGraph.setNode(node.id, { width: 250, height: 150 });
    });

    edges.forEach((edge) => {
        dagreGraph.setEdge(edge.source, edge.target);
    });

    dagre.layout(dagreGraph);

    const layoutedNodes = nodes.map((node) => {
        const nodeWithPosition = dagreGraph.node(node.id);
        return {
            ...node,
            targetPosition: 'top',
            sourcePosition: 'bottom',
            position: {
                x: nodeWithPosition.x - 125,
                y: nodeWithPosition.y - 75,
            },
        };
    });

    return { nodes: layoutedNodes, edges };
};

// --- NEW LOADING PLACEHOLDER COMPONENT ---
const NetworkLoadingPlaceholder = () => {
    const accentCol = '#2c3e50';
    const textCol = '#7f8c8d';

    return (
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column', padding: '40px', justifyContent: 'center' }}>

            {/* Header / Loader Row */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '20px', borderBottom: '1px solid #eee', paddingBottom: '20px', marginBottom: '30px' }}>
                <div style={{ width: '40px', height: '40px', border: '5px solid #e2e8f0', borderTop: `5px solid ${accentCol}`, borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
                <div>
                    <h3 style={{ margin: 0, color: accentCol, fontSize: '1.5rem' }}>
                        Clinical Model Initializing
                    </h3>
                    <p style={{ margin: '5px 0 0 0', color: textCol, fontSize: '1rem' }}>
                        Booting up Bayesian Network and retrieving Probability Tables...
                    </p>
                </div>
            </div>

            {/* Medical Expert Context Row (3 columns) */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '20px' }}>
                <div style={placeholderCardStyle}>
                    <div style={iconStyle}>DAG</div>
                    <h4 style={cardTitleStyle}>Structural Model</h4>
                    <p style={cardTextStyle}>Building the Directed Acyclic Graph defining causal dependencies between clinical variables.</p>
                </div>
                <div style={placeholderCardStyle}>
                    <div style={iconStyle}>Bayes</div>
                    <h4 style={cardTitleStyle}>Probabilistic Fitting</h4>
                    <p style={cardTextStyle}>Calculating Conditional Probabilities for all symptom nodes against the final Disease Target.</p>
                </div>
                <div style={placeholderCardStyle}>
                    <div style={iconStyle}>RF</div>
                    <h4 style={cardTitleStyle}>Interactive Rendering</h4>
                    <p style={cardTextStyle}>Computing node positioning and rendering the interactive visualization engine.</p>
                </div>
            </div>

            <style>{`
                @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            `}</style>
        </div>
    );
};

// Reusable styling helpers for the placeholder
const placeholderCardStyle = { backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '20px', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', boxShadow: '0 2px 4px rgba(0,0,0,0.02)' };
const iconStyle = { fontSize: '1.2rem', fontWeight: 'bold', backgroundColor: '#f8f9fa', color: '#2c3e50', padding: '10px 15px', borderRadius: '8px', marginBottom: '15px', border: '1px solid #eee' };
const cardTitleStyle = { margin: '0 0 8px 0', color: '#2c3e50', fontSize: '1.1rem' };
const cardTextStyle = { margin: 0, fontSize: '0.9rem', color: '#7f8c8d', lineHeight: '1.5' };


// --- MAIN COMPONENT ---
const BayesianNetwork = () => {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);

    // 3. NEW STATE: Track whether the API is still loading
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        setIsLoading(true); // Ensure it's true when starting the fetch

        axios.get(`${process.env.REACT_APP_API_URL}/advanced-network`)
            .then((response) => {
                const rawData = response.data;

                const initialNodes = Object.keys(rawData.nodes).map((nodeId) => ({
                    id: nodeId,
                    type: 'probNode',
                    data: {
                        label: nodeId.replace('_', ' '),
                        probs: rawData.nodes[nodeId]
                    },
                    position: { x: 0, y: 0 },
                }));

                const initialEdges = rawData.edges.map((edge, index) => ({
                    id: `e${index}`,
                    source: edge[0],
                    target: edge[1],
                    type: 'smoothstep',
                    markerEnd: { type: MarkerType.ArrowClosed },
                    style: { stroke: '#b1b1b7', strokeWidth: 1.5 }
                }));

                const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
                    initialNodes,
                    initialEdges
                );

                setNodes(layoutedNodes);
                setEdges(layoutedEdges);
            })
            .catch((error) => console.error("Error fetching network:", error))
            .finally(() => {
                // 4. CRITICAL: Turn off the loading screen regardless of success or failure
                setIsLoading(false);
            });
    }, [setNodes, setEdges]);

    return (
        <div style={{ height: '800px', border: '1px solid #ddd', borderRadius: '12px', background: '#f8f9fa', overflow: 'hidden' }}>
            {/* 5. CONDITIONAL RENDERING: Show placeholder OR the actual graph */}
            {isLoading ? (
                <NetworkLoadingPlaceholder />
            ) : (
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    nodeTypes={nodeTypes}
                    fitView
                    attributionPosition="bottom-right"
                >
                    <Background color="#ccc" gap={16} />
                    <Controls />
                </ReactFlow>
            )}
        </div>
    );
};

export default BayesianNetwork;
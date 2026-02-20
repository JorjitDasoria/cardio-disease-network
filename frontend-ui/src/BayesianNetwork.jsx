import React, { useEffect } from 'react';
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

// --- LAYOUT ENGINE (Auto-arranges nodes) ---
// --- LAYOUT ENGINE (Auto-arranges nodes) ---
const getLayoutedElements = (nodes, edges) => {
    const dagreGraph = new dagre.graphlib.Graph();
    dagreGraph.setGraph({ rankdir: 'TB' }); // TB = Top to Bottom layout

    // --- CRITICAL FIX: Create empty objects for edges so dagre doesn't crash ---
    dagreGraph.setDefaultEdgeLabel(() => ({}));
    // --------------------------------------------------------------------------

    nodes.forEach((node) => {
        // We give the node a width/height so dagre knows how much space it needs
        dagreGraph.setNode(node.id, { width: 150, height: 50 });
    });

    edges.forEach((edge) => {
        dagreGraph.setEdge(edge.source, edge.target);
    });

    // Calculate the layout
    dagre.layout(dagreGraph);

    // Apply the calculated positions to the React Flow nodes
    const layoutedNodes = nodes.map((node) => {
        const nodeWithPosition = dagreGraph.node(node.id);
        return {
            ...node,
            targetPosition: 'top',
            sourcePosition: 'bottom',
            position: {
                x: nodeWithPosition.x - 75, // Shift by half width to center
                y: nodeWithPosition.y - 25, // Shift by half height to center
            },
        };
    });

    return { nodes: layoutedNodes, edges };
};
// -------------------------------------------
// -------------------------------------------

const BayesianNetwork = () => {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);

    useEffect(() => {
        // 1. Fetch data from Python Backend
        axios.get(`${process.env.REACT_APP_API_URL}/network-structure`)
            .then((response) => {
                const rawData = response.data;

                // 2. Convert Python data to React Flow format
                const initialNodes = rawData.nodes.map((nodeId) => ({
                    id: nodeId,
                    data: { label: nodeId },
                    position: { x: 0, y: 0 }, // Position will be fixed by dagre
                    style: { background: '#fff', border: '1px solid #777', padding: 10, borderRadius: 5 }
                }));

                const initialEdges = rawData.edges.map((edge, index) => ({
                    id: `e${index}`,
                    source: edge[0],
                    target: edge[1],
                    type: 'smoothstep',
                    markerEnd: { type: MarkerType.ArrowClosed }, // Add arrowheads
                }));

                // 3. Apply Auto-Layout
                const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
                    initialNodes,
                    initialEdges
                );

                setNodes(layoutedNodes);
                setEdges(layoutedEdges);
            })
            .catch((error) => console.error("Error fetching network:", error));
    }, [setNodes, setEdges]);

    return (
        <div style={{ height: '500px', border: '1px solid #ddd', borderRadius: '8px' }}>
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                fitView
            >
                <Background />
                <Controls />
            </ReactFlow>
        </div>
    );
};

export default BayesianNetwork;
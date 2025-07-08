// src/services/api.types.ts

export interface SessionData {
    disease?: string;
    innovationLevel?: number;
    logs?: any[];
    decisionTarget?: any;
    decisionPocket?: any;
    decisionCompound?: any;
    moleculeImage?: string;
    workflowState?: any;
    allTargets?: any[];
    triedTargets?: string[];
    targetExplanation?: string;
    selectionReason?: string;
    optimizationExplanation?: string;
    currentStructurePath?: string;
    currentPocketCenter?: [number, number, number];
    currentProteinName?: string;
    currentLigandSmiles?: string[];
    currentOptimizedSmiles?: string;
    isUsingAlphaFold?: boolean;
    step?: number;
}

export interface Session {
    id: string;
    title: string;
    created_at: number;
    updated_at: number;
    session_data: SessionData;
}

export interface SessionMetadata {
    id: string;
    title: string;
    created_at: string;
    last_modified: string;
}

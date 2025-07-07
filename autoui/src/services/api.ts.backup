// src/services/api.ts
export interface ApiResponse<T> {
    success: boolean;
    error?: string;
    [key: string]: any;
}

export interface TargetWithScore {
  symbol: string;
  innovation_score: number;
}

export interface AiGeneratedLigand {
  smiles: string;
  reason: string;
  is_ai_generated: boolean;
}

const API_BASE = 'http://192.168.1.100:5001/api';
// const API_BASE = 'http://192.168.1.100:5001/api';


async function postJson<T>(path: string, body: any): Promise<ApiResponse<T>> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return res.json();
}

export async function getDiseaseTargets(disease: string, innovationLevel: number = 5) {
  return postJson<{
    targets: string[];
    targets_with_scores: TargetWithScore[];
  }>('/disease-targets', { disease, innovation_level: innovationLevel });
}

export async function getUniprotEntries(gene_symbol: string) {
  return postJson<{ acc: string; name: string }[]>('/uniprot-entries', { gene_symbol });
}

export async function getVerifiedTarget(disease: string) {
  return postJson<{ 
    symbol: string;
    uniprot_acc: string;
    name: string;
    innovation_score: number;
    entries: { acc: string; name: string }[];
  }>('/verified-target', { disease });
}

export async function getStructureSources(uniprot_acc: string) {
  return postJson<{ 
    alphafold_available: boolean; 
    pdb_ids: string[];
    structure_path?: string;
    structure_source?: string;
  }>('/structure-sources', { uniprot_acc });
}

export async function predictPockets(structure_path: string) {
  return postJson<{ pockets: { center: [number, number, number]; score: number }[] }>('/predict-pockets', { structure_path });
}

export async function getLigands(uniprot_acc?: string, custom_smiles?: string[], disease?: string) {
  return postJson<{ 
    chembl_smiles?: string[]; 
    custom_smiles?: string[];
    ai_generated_smiles?: string[];
    ai_generated_full?: AiGeneratedLigand[];
  }>('/get-ligands', { uniprot_acc, custom_smiles, disease });
}

export async function aiDecision(params: { options: string[]; context?: string; question: string }) {
  return postJson<{ selected_option: string; explanation: string }>('/ai-decision', params);
}

export async function selectCompound(params: {
  smiles_list: string[];
  disease: string;
  protein: string;
  pocket_center?: [number, number, number];
}) {
  return postJson<{ selected_smiles: string; optimized_smiles: string; explanation: string }>('/select-compound', params);
}

export async function generateMoleculeImage(smiles: string) {
  return postJson<{ image_data: string }>('/molecule-image', { smiles });
}

//  export async function generateDockingImage(
//    protein_path: string,
//    ligand_smiles: string,
//    pocket_center: [number, number, number]
//  ) {
//    return postJson<{ image_data: string }>('/docking-image', { protein_path, ligand_smiles, pocket_center });
//  }

export async function completeWorkflow(disease: string, selected_targets?: string[]) {
  return postJson<any>('/complete-workflow', { disease, selected_targets });
}

export async function getDecisionExplanations() {
  const res = await fetch(`${API_BASE}/decision-explanations`);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return res.json();
}

export async function getTargetExplanation(gene_symbol: string, disease: string) {
  return postJson<{ explanation: string }>('/target-explanation', { gene_symbol, disease });
}

export async function generateProteinVisualization(structure_path: string, pocket_center?: [number, number, number]) {
  return postJson<{ html: string }>('/protein-visualization', { structure_path, pocket_center });
}

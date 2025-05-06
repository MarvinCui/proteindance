// src/services/api.ts
export interface ApiResponse<T> {
    success: boolean;
    error?: string;
    [key: string]: any;
  }
  
  const API_BASE = 'http://localhost:5001/api';
  
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
    return postJson<string[]>('/disease-targets', { disease, innovation_level: innovationLevel });
  }
  
  export async function getUniprotEntries(gene_symbol: string) {
    return postJson<{ acc: string; name: string }[]>('/uniprot-entries', { gene_symbol });
  }
  
  export async function getStructureSources(uniprot_acc: string) {
    return postJson<{ alphafold_available: boolean; pdb_ids: string[] }>('/structure-sources', { uniprot_acc });
  }
  
  export async function predictPockets(structure_path: string) {
    return postJson<{ pockets: { center: [number, number, number]; score: number }[] }>('/predict-pockets', { structure_path });
  }
  
  export async function getLigands(uniprot_acc?: string, custom_smiles?: string[]) {
    return postJson<{ chembl_smiles?: string[]; custom_smiles?: string[] }>('/get-ligands', { uniprot_acc, custom_smiles });
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

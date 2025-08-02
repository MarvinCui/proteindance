// src/services/api.ts
import { Session, SessionData, SessionMetadata } from './api.types';
import { apiConfigManager, getApiBaseUrl } from '../config/api-config';
import authService from './authService';

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

// 动态获取API基础URL
const getApiBase = () => getApiBaseUrl();

// 获取认证headers (用于POST请求)
const getAuthHeaders = (): Record<string, string> => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json'
  };
  
  const token = authService.getToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  return headers;
};

// 获取基础认证headers (用于GET/DELETE请求)
const getBasicAuthHeaders = (): Record<string, string> => {
  const headers: Record<string, string> = {};
  
  const token = authService.getToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  return headers;
};


async function postJson<T>(path: string, body: any): Promise<ApiResponse<T>> {
  try {
    const apiBase = getApiBase();
    console.log(`🌐 postJson 开始: ${path}`);
    console.log(`📍 完整URL: ${apiBase}${path}`);
    console.log(`📋 请求体:`, body);
    
    const res = await fetch(`${apiBase}${path}`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(body),
    });
    
    console.log(`📡 fetch 响应状态: ${res.status}`);
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`HTTP ${res.status}: ${text}`);
    }
    return res.json();
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error(`网络连接失败：无法连接到后端服务 (${getApiBase()})。请检查：\n1. 后端服务是否运行在 http://localhost:5001\n2. 网络连接是否正常\n3. 防火墙是否阻止连接`);
    }
    throw error;
  }
}

async function getJson<T>(path: string): Promise<T> {
  try {
    const apiBase = getApiBase();
    const res = await fetch(`${apiBase}${path}`, {
      method: 'GET',
      headers: getBasicAuthHeaders(),
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`HTTP ${res.status}: ${text}`);
    }
    return res.json();
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error(`网络连接失败：无法连接到后端服务 (${getApiBase()})。请检查：\n1. 后端服务是否运行在 http://localhost:5001\n2. 网络连接是否正常\n3. 防火墙是否阻止连接`);
    }
    throw error;
  }
}

async function deleteJson(path: string): Promise<void> {
    try {
        const apiBase = getApiBase();
        const res = await fetch(`${apiBase}${path}`, { 
            method: 'DELETE',
            headers: getBasicAuthHeaders(),
        });
        if (!res.ok && res.status !== 204) {
            const text = await res.text();
            throw new Error(`HTTP ${res.status}: ${text}`);
        }
    } catch (error) {
        if (error instanceof TypeError && error.message.includes('fetch')) {
            throw new Error(`网络连接失败：无法连接到后端服务 (${getApiBase()})。请检查：\n1. 后端服务是否运行在 http://localhost:5001\n2. 网络连接是否正常\n3. 防火墙是否阻止连接`);
        }
        throw error;
    }
}

// 健康检查函数 - 使用配置管理器
export const checkBackendHealth = async (): Promise<{healthy: boolean, message: string, config?: any}> => {
  return await apiConfigManager.getHealthStatus();
};

export const api = {
  // 健康检查和配置管理
  healthCheck: checkBackendHealth,
  getConfig: () => apiConfigManager.getConfig(),
  updateConfig: (config: any) => apiConfigManager.updateConfig(config),
  autoDetect: () => apiConfigManager.autoDetectBackend(),
  
  getDiseaseTargets: (disease: string, innovationLevel: number = 5) => {
    return postJson<{
      targets: string[];
      targets_with_scores: TargetWithScore[];
    }>('/disease-targets', { disease, innovation_level: innovationLevel });
  },

  getUniprotEntries: (gene_symbol: string) => {
    return postJson<{ acc: string; name: string }[]>('/uniprot-entries', { gene_symbol });
  },

  getVerifiedTarget: (disease: string) => {
    return postJson<{ 
      symbol: string;
      uniprot_acc: string;
      name: string;
      innovation_score: number;
      entries: { acc: string; name: string }[];
    }>('/verified-target', { disease });
  },

  getStructureSources: (uniprot_acc: string) => {
    return postJson<{ 
      alphafold_available: boolean; 
      pdb_ids: string[];
      structure_path?: string;
      structure_source?: string;
    }>('/structure-sources', { uniprot_acc });
  },

  predictPockets: (structure_path: string) => {
    return postJson<{ pockets: { center: [number, number, number]; score: number }[] }>('/predict-pockets', { structure_path });
  },

  getLigands: (uniprot_acc?: string, custom_smiles?: string[], disease?: string) => {
    return postJson<{ 
      chembl_smiles?: string[]; 
      custom_smiles?: string[];
      ai_generated_smiles?: string[];
      ai_generated_full?: AiGeneratedLigand[];
    }>('/get-ligands', { uniprot_acc, custom_smiles, disease });
  },

  aiDecision: (params: { options: string[]; context?: string; question: string }) => {
    return postJson<{ selected_option: string; explanation: string }>('/ai-decision', params);
  },

  selectCompound: (params: {
    smiles_list: string[];
    disease: string;
    protein: string;
    pocket_center?: [number, number, number];
  }) => {
    return postJson<{ selected_smiles: string; optimized_smiles: string; explanation: string }>('/select-compound', params);
  },

  generateMoleculeImage: (smiles: string) => {
    return postJson<{ image_data: string }>('/molecule-image', { smiles });
  },

  completeWorkflow: (disease: string, selected_targets?: string[]) => {
    return postJson<any>('/complete-workflow', { disease, selected_targets });
  },

  getDecisionExplanations: async () => {
    const apiBase = getApiBase();
    const res = await fetch(`${getApiBase()}/decision-explanations`);
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`HTTP ${res.status}: ${text}`);
    }
    return res.json();
  },

  getTargetExplanation: (gene_symbol: string, disease: string) => {
    return postJson<{ explanation: string }>('/target-explanation', { gene_symbol, disease });
  },

  generateScientificAnalysis: (params: {
    disease: string;
    gene_symbol: string;
    uniprot_acc?: string;
    structure_path?: string;
    pocket_center?: [number, number, number];
    smiles_list?: string[];
    optimized_smiles?: string;
    docking_result?: any;
    docking_score?: number;
  }) => {
    return postJson<{ explanation: string }>('/scientific-analysis', params);
  },

  generateProteinVisualization: (structure_path: string, pocket_center?: [number, number, number]) => {
    return postJson<{ html: string }>('/protein-visualization', { structure_path, pocket_center });
  },

  // Molecular Docking API
  performMolecularDocking: (params: {
    protein_path: string;
    ligand_smiles: string;
    pocket_center: [number, number, number];
    box_size?: [number, number, number];
  }) => {
    return postJson<{
      success: boolean;
      protein_path: string;
      ligand_smiles: string;
      pocket_center: [number, number, number];
      box_size: [number, number, number];
      best_score: number;
      poses: Array<{
        pose_id: number;
        binding_affinity: number;
        rmsd_lower: number;
        rmsd_upper: number;
      }>;
      output_path: string;
    }>('/molecular-docking', params);
  },

  generateDockingVisualization: (params: {
    protein_path: string;
    ligand_smiles: string;
    pocket_center: [number, number, number];
    box_size?: [number, number, number];
  }) => {
    console.log('🔥 API.generateDockingVisualization 调用开始');
    console.log('📋 参数:', params);
    console.log('🌐 getApiBase():', getApiBase());
    console.log('📡 即将发送POST请求到:', `${getApiBase()}/docking-visualization`);
    
    const result = postJson<{
      success: boolean;
      docking_result: {
        protein_path: string;
        ligand_smiles: string;
        pocket_center: [number, number, number];
        box_size: [number, number, number];
        best_score: number;
        poses: Array<{
          pose_id: number;
          binding_affinity: number;
          rmsd_lower: number;
          rmsd_upper: number;
        }>;
        output_path: string;
      };
      visualization: {
        success: boolean;
        html_content: string;
        images: string[];
        docking_summary: {
          ligand_smiles: string;
          best_score: number;
          num_poses: number;
          pocket_center: [number, number, number];
        };
        pymol_analysis?: {
          ki_estimate?: string;
          ic50_prediction?: string;
          binding_analysis?: string;
        };
      };
    }>('/docking-visualization', params)
      .then(response => {
        console.log('✅ API.generateDockingVisualization 响应接收:', response);
        return response;
      })
      .catch(error => {
        console.error('❌ API.generateDockingVisualization 请求失败:', error);
        throw error;
      });
    
    console.log('📤 API.generateDockingVisualization 请求Promise已创建');
    return result;
  },

  generateDockingImage: (params: {
    protein_path: string;
    ligand_smiles: string;
    pocket_center: [number, number, number];
    box_size?: [number, number, number];
  }) => {
    return postJson<{
      success: boolean;
      image_data?: string;
      error?: string;
    }>('/docking-image', params);
  },

  // Session Management
  listSessions: () => {
    return getJson<SessionMetadata[]>('/sessions');
  },

  getSession: (sessionId: string) => {
    return getJson<Session>(`/sessions/${sessionId}`);
  },

  saveSession: (sessionData: SessionData, sessionId?: string) => {
    const path = sessionId ? `/sessions?session_id=${sessionId}` : '/sessions';
    return postJson<Session>(path, sessionData);
  },

  deleteSession: (sessionId: string) => {
    return deleteJson(`/sessions/${sessionId}`);
  },
};

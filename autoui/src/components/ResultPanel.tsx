import React, { useState } from 'react'
import styled from '@emotion/styled'
import { getApiBaseUrl } from '../config/api-config'

const Panel = styled.div`
  background: white;
  border-radius: 12px;
  padding: 0;
  margin-top: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  overflow: hidden;
`

const TabContainer = styled.div`
  display: flex;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
`

const Tab = styled.button<{ active: boolean }>`
  flex: 1;
  padding: 16px 24px;
  background: ${props => props.active ? 'white' : 'transparent'};
  border: none;
  border-bottom: 3px solid ${props => props.active ? '#4f46e5' : 'transparent'};
  color: ${props => props.active ? '#4f46e5' : '#64748b'};
  font-size: 16px;
  font-weight: ${props => props.active ? '600' : '500'};
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: ${props => props.active ? 'white' : '#f1f5f9'};
    color: #4f46e5;
  }
`

const TabContent = styled.div`
  padding: 24px;
`

const Section = styled.div`
  margin-bottom: 24px;
  &:last-child { margin-bottom: 0; }
`

const SectionTitle = styled.h3`
  font-size: 18px;
  color: #4f46e5;
  margin: 0 0 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid rgba(79,70,229,0.2);
`

const FileLink = styled.a`
  display: inline-flex;
  align-items: center;
  padding: 8px 16px;
  margin: 0 8px 8px 0;
  background: #f3f4f6;
  border-radius: 6px;
  color: #4f46e5;
  text-decoration: none;
  transition: all 0.2s;
  
  &:hover {
    background: #e5e7eb;
    transform: translateY(-1px);
  }
  
  svg {
    margin-right: 8px;
  }
`

const InfoGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
  margin: 16px 0;
`

const InfoCard = styled.div`
  background: #f8fafc;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  
  h4 {
    margin: 0 0 8px;
    color: #64748b;
    font-size: 14px;
  }
  
  p {
    margin: 0;
    color: #334155;
    font-size: 16px;
  }
`

const ExplanationSection = styled.div`
  background: #f8fafc;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  border-left: 3px solid #4f46e5;
  
  h4 {
    margin: 0 0 8px;
    color: #4f46e5;
    font-size: 16px;
    font-weight: 600;
  }
  
  p {
    margin: 0;
    color: #334155;
    font-size: 15px;
    line-height: 1.6;
  }
`

const MoleculeComparisonContainer = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin: 20px 0;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
    gap: 16px;
  }
`

const MoleculeCard = styled.div`
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  transition: all 0.3s ease;
  
  &:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,0.12);
    transform: translateY(-2px);
  }
  
  h4 {
    margin: 0 0 16px;
    color: #4f46e5;
    font-size: 16px;
    font-weight: 600;
  }
  
  img {
    max-width: 100%;
    height: auto;
    min-height: 200px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    background: white;
    padding: 10px;
  }
  
  .molecule-info {
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid #e2e8f0;
    
    .smiles-text {
      font-family: 'Courier New', monospace;
      font-size: 12px;
      color: #64748b;
      word-break: break-all;
      background: rgba(255,255,255,0.8);
      padding: 8px;
      border-radius: 4px;
      margin-top: 8px;
    }
  }
`

const SingleMoleculeContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 20px 0;
  
  img {
    max-width: 400px;
    height: auto;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  }
`

const DockingResultContainer = styled.div`
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 24px;
  margin: 24px 0;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
`

const DockingScoreCard = styled.div`
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  color: white;
  padding: 20px;
  border-radius: 12px;
  text-align: center;
  margin-bottom: 20px;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
  
  h3 {
    margin: 0 0 8px 0;
    font-size: 24px;
    font-weight: 700;
  }
  
  p {
    margin: 0;
    font-size: 14px;
    opacity: 0.9;
  }
`

const DockingMetricsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
  
  .metric-card {
    background: white;
    padding: 16px;
    border-radius: 8px;
    text-align: center;
    border: 1px solid #e2e8f0;
    
    .metric-value {
      font-size: 20px;
      font-weight: 600;
      color: #4f46e5;
      margin-bottom: 4px;
    }
    
    .metric-label {
      font-size: 12px;
      color: #64748b;
      text-transform: uppercase;
      font-weight: 500;
    }
  }
`

const PyMOLImagesGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 20px;
  margin: 24px 0;
`

const PyMOLImageCard = styled.div`
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  transition: all 0.3s ease;
  
  &:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,0.12);
    transform: translateY(-2px);
  }
  
  h4 {
    margin: 0 0 12px 0;
    color: #4f46e5;
    font-size: 16px;
    font-weight: 600;
    text-align: center;
  }
  
  img {
    width: 100%;
    height: auto;
    min-height: 200px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    background: #f8fafc;
    object-fit: contain;
  }
  
  .image-description {
    margin-top: 8px;
    font-size: 13px;
    color: #64748b;
    text-align: center;
    line-height: 1.4;
  }
`

const DockingImageSection = styled.div`
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px;
  margin: 24px 0;
  
  h4 {
    margin: 0 0 16px 0;
    color: #4f46e5;
    font-size: 18px;
    font-weight: 600;
    text-align: center;
    
    .icon {
      margin-right: 8px;
    }
  }
  
  .section-description {
    text-align: center;
    color: #64748b;
    margin-bottom: 20px;
    font-size: 14px;
  }
`

const PoseTableContainer = styled.div`
  overflow-x: auto;
  margin-top: 20px;
  
  table {
    width: 100%;
    border-collapse: collapse;
    background: white;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    
    th, td {
      padding: 12px;
      text-align: left;
      border-bottom: 1px solid #e2e8f0;
    }
    
    th {
      background: #f8fafc;
      font-weight: 600;
      color: #475569;
      font-size: 14px;
    }
    
    td {
      font-size: 14px;
      color: #334155;
    }
    
    tr:hover {
      background: #f8fafc;
    }
  }
`

interface Props {
  disease: string
  geneSymbol: string
  uniprotAcc?: string | null
  pocketCenter: [number, number, number] | null
  optimizedSmiles: string | null
  explanation: string | null
  selectionReason?: string | null
  optimizationExplanation?: string | null
  moleculeImage?: string | null
  dockingImage?: string | null
  structurePath?: string | null
  targetExplanation?: string | null
  originalSmiles?: string | null
  originalMoleculeImage?: string | null
  ligandSmiles?: string[] | null
  sessionId?: string | null
  dockingResult?: {
    success: boolean
    best_score: number
    num_poses: number
    poses: Array<{
      pose_id: number
      binding_affinity: number
      rmsd_lower: number
      rmsd_upper: number
    }>
  } | null
  dockingVisualization?: {
    success: boolean
    html_content: string
    docking_summary: {
      ligand_smiles: string
      best_score: number
      num_poses: number
      pocket_center: [number, number, number]
    }
    images?: string[]
    pymol_analysis?: {
      ki_estimate?: string
      ic50_prediction?: string
      binding_analysis?: string
    }
  } | null
}

const ResultPanel: React.FC<Props> = ({
  disease,
  geneSymbol,
  uniprotAcc,
  pocketCenter,
  optimizedSmiles,
  explanation,
  selectionReason,
  optimizationExplanation,
  moleculeImage,
  dockingImage,
  structurePath,
  targetExplanation,
  originalSmiles,
  originalMoleculeImage,
  ligandSmiles,
  sessionId,
  dockingResult,
  dockingVisualization
}) => {
  
  const [activeTab, setActiveTab] = useState('molecules')

  const tabs = [
    { id: 'molecules', label: '🧪 分子结构对比', icon: '🧪' },
    { id: 'docking', label: '🎯 分子对接结果', icon: '🎯' },
    { id: 'analysis', label: '📊 科学分析', icon: '📊' },
    { id: 'files', label: '📁 重要文件', icon: '📁' }
  ]

  // 下载配体文件的函数
  const downloadLigandFile = async (ligandType: 'original' | 'optimized', format: 'pdb' | 'pdbqt', index: number = 0) => {
    if (!sessionId) {
      console.error('会话ID不存在，无法下载配体文件');
      return;
    }

    try {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        console.error('用户未登录，无法下载配体文件');
        return;
      }

      const apiBase = getApiBaseUrl().replace('/api', '');
      const url = new URL(`${apiBase}/api/download/ligand/${sessionId}`);
      url.searchParams.append('ligand_type', ligandType);
      url.searchParams.append('file_format', format);
      if (ligandType === 'original') {
        url.searchParams.append('ligand_index', index.toString());
      }

      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(`下载失败: ${response.status}`);
      }

      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `${ligandType}_ligand.${format}`;
      if (contentDisposition) {
        const matches = contentDisposition.match(/filename="([^"]*)"/) || contentDisposition.match(/filename=([^;]*)/);
        if (matches && matches[1]) {
          filename = matches[1];
        }
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);

    } catch (error) {
      console.error('下载配体文件失败:', error);
    }
  };

  // 下载蛋白质结构文件的函数
  const downloadStructureFile = async (format: 'pdb' | 'pdbqt') => {
    if (!sessionId) {
      console.error('会话ID不存在，无法下载结构文件');
      return;
    }

    try {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        console.error('用户未登录，无法下载结构文件');
        return;
      }

      const apiBase = getApiBaseUrl().replace('/api', '');
      const url = new URL(`${apiBase}/api/download/structure/${sessionId}`);
      url.searchParams.append('file_format', format);

      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(`下载失败: ${response.status}`);
      }

      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `protein_structure.${format}`;
      if (contentDisposition) {
        const matches = contentDisposition.match(/filename="([^"]*)"/) || contentDisposition.match(/filename=([^;]*)/);
        if (matches && matches[1]) {
          filename = matches[1];
        }
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);

    } catch (error) {
      console.error('下载结构文件失败:', error);
    }
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'molecules':
        return renderMoleculeComparison()
      case 'docking':
        return renderDockingResults()
      case 'analysis':
        return renderScientificAnalysis()
      case 'files':
        return renderImportantFiles()
      default:
        return renderMoleculeComparison()
    }
  }

  const renderMoleculeComparison = () => (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h3 style={{ color: '#4f46e5', marginBottom: '16px', fontSize: '20px' }}>研究成果总结</h3>
        <InfoGrid>
          <InfoCard>
            <h4>目标疾病</h4>
            <p>{disease}</p>
          </InfoCard>
          <InfoCard>
            <h4>选定靶点</h4>
            <p>{geneSymbol}</p>
          </InfoCard>
          <InfoCard>
            <h4>UniProt ID</h4>
            <p>{uniprotAcc || '未知'}</p>
          </InfoCard>
          <InfoCard>
            <h4>结合口袋坐标</h4>
            <p>{pocketCenter ? `(${pocketCenter.map(n => n.toFixed(2)).join(', ')})` : '未确定'}</p>
          </InfoCard>
        </InfoGrid>
      </div>

      {(moleculeImage || originalMoleculeImage) ? (
        <div>
          <h3 style={{ color: '#4f46e5', marginBottom: '16px', fontSize: '20px' }}>分子结构对比</h3>
          
          {/* 双分子对比显示 */}
          {originalMoleculeImage && moleculeImage ? (
            <MoleculeComparisonContainer>
              <MoleculeCard>
                <h4>📋 原始ChEMBL化合物</h4>
                <img 
                  src={`data:image/png;base64,${originalMoleculeImage}`} 
                  alt="原始ChEMBL化合物结构" 
                />
                <div className="molecule-info">
                  <div style={{ fontSize: '14px', color: '#64748b', fontWeight: 500 }}>
                    来源：ChEMBL数据库
                  </div>
                  {originalSmiles && (
                    <div className="smiles-text">
                      SMILES: {originalSmiles}
                    </div>
                  )}
                </div>
              </MoleculeCard>
              
              <MoleculeCard>
                <h4>⚡ AI优化后化合物</h4>
                <img 
                  src={`data:image/png;base64,${moleculeImage}`} 
                  alt="AI优化后的分子结构" 
                />
                <div className="molecule-info">
                  <div style={{ fontSize: '14px', color: '#64748b', fontWeight: 500 }}>
                    来源：AI模型优化
                  </div>
                  {optimizedSmiles && (
                    <div className="smiles-text">
                      SMILES: {optimizedSmiles}
                    </div>
                  )}
                </div>
              </MoleculeCard>
            </MoleculeComparisonContainer>
          ) : (
            /* 单分子显示（向后兼容） */
            <SingleMoleculeContainer>
              {moleculeImage && (
                <img 
                  src={`data:image/png;base64,${moleculeImage}`} 
                  alt="分子结构" 
                />
              )}
              {originalMoleculeImage && !moleculeImage && (
                <img 
                  src={`data:image/png;base64,${originalMoleculeImage}`} 
                  alt="原始化合物结构" 
                />
              )}
            </SingleMoleculeContainer>
          )}
        </div>
      ) : (
        <div style={{ 
          textAlign: 'center', 
          padding: '60px 20px',
          background: '#f8fafc',
          borderRadius: '12px',
          border: '2px dashed #e2e8f0'
        }}>
          <div style={{ fontSize: '64px', marginBottom: '16px' }}>🧪</div>
          <h3 style={{ color: '#64748b', marginBottom: '8px' }}>暂无分子结构数据</h3>
          <p style={{ color: '#94a3b8', margin: 0 }}>
            完成化合物优化后将显示分子结构对比
          </p>
        </div>
      )}
    </div>
  )

  const renderDockingResults = () => (
    <div>
      {(dockingResult || dockingVisualization) ? (
        <div>
          {dockingResult && dockingResult.success && (
            <DockingResultContainer>
              <DockingScoreCard>
                <h3>{dockingResult.best_score.toFixed(2)} kcal/mol</h3>
                <p>最佳结合亲和力</p>
              </DockingScoreCard>
              
              <DockingMetricsGrid>
                <div className="metric-card">
                  <div className="metric-value">{dockingResult.num_poses}</div>
                  <div className="metric-label">构象数量</div>
                </div>
                <div className="metric-card">
                  <div className="metric-value">
                    {dockingResult.best_score < -8 ? "强" : dockingResult.best_score < -6 ? "中等" : "弱"}
                  </div>
                  <div className="metric-label">结合强度</div>
                </div>
                <div className="metric-card">
                  <div className="metric-value">
                    {dockingResult.poses.length > 0 ? dockingResult.poses[0].rmsd_lower.toFixed(2) : "N/A"}
                  </div>
                  <div className="metric-label">RMSD 下限</div>
                </div>
              </DockingMetricsGrid>
              
              {dockingResult.poses.length > 0 && (
                <PoseTableContainer>
                  <table>
                    <thead>
                      <tr>
                        <th>构象ID</th>
                        <th>结合亲和力 (kcal/mol)</th>
                        <th>RMSD下限</th>
                        <th>RMSD上限</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dockingResult.poses.slice(0, 5).map(pose => (
                        <tr key={pose.pose_id}>
                          <td>{pose.pose_id}</td>
                          <td>{pose.binding_affinity.toFixed(2)}</td>
                          <td>{pose.rmsd_lower.toFixed(2)}</td>
                          <td>{pose.rmsd_upper.toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </PoseTableContainer>
              )}
            </DockingResultContainer>
          )}
          
          {/* PyMOL专业可视化图像 */}
          {dockingVisualization && dockingVisualization.success && dockingVisualization.images && dockingVisualization.images.length > 0 && (
            <DockingImageSection>
              <h4>
                <span className="icon">🎨</span>
                PyMOL 专业分子可视化
              </h4>
              <div className="section-description">
                高质量的分子对接可视化图像，适用于科学发表和深度分析
              </div>
              
              <PyMOLImagesGrid>
                {dockingVisualization.images.map((imagePath, index) => {
                  // 解析图像类型和描述
                  const getImageInfo = (path: string) => {
                    if (path.includes('overview')) {
                      return { 
                        title: '🔬 全景视图',
                        description: '蛋白质-配体复合物的整体结构视图，显示完整的分子间相互作用'
                      }
                    } else if (path.includes('binding_site')) {
                      return { 
                        title: '🎯 结合位点',
                        description: '结合口袋的详细视图，突出显示关键氨基酸残基和氢键相互作用'
                      }
                    } else if (path.includes('surface_view')) {
                      return { 
                        title: '🌊 表面视图',
                        description: '分子表面表示，展示结合口袋的形状互补性和疏水相互作用'
                      }
                    } else if (path.includes('close_up')) {
                      return { 
                        title: '🔍 特写视图',
                        description: '结合位点的放大视图，显示原子级别的相互作用细节'
                      }
                    } else if (path.includes('electrostatic')) {
                      return { 
                        title: '⚡ 静电视图',
                        description: '静电势表面，显示电荷分布和静电相互作用'
                      }
                    } else if (path.includes('hydrophobic')) {
                      return { 
                        title: '💧 疏水视图',
                        description: '疏水性相互作用图，展示非极性残基与配体的相互作用'
                      }
                    } else {
                      return { 
                        title: `📊 视图 ${index + 1}`,
                        description: '专业分子对接可视化图像'
                      }
                    }
                  }
                  
                  const imageInfo = getImageInfo(imagePath)
                  const apiBase = getApiBaseUrl().replace('/api', '')
                  
                  return (
                    <PyMOLImageCard key={index}>
                      <h4>{imageInfo.title}</h4>
                      <img 
                        src={`${apiBase}/api/images/${imagePath}`}
                        alt={imageInfo.title}
                        onError={(e) => {
                          console.warn(`PyMOL图像加载失败: ${imagePath}`)
                          e.currentTarget.style.display = 'none'
                        }}
                      />
                      <div className="image-description">
                        {imageInfo.description}
                      </div>
                    </PyMOLImageCard>
                  )
                })}
              </PyMOLImagesGrid>
              
              {/* PyMOL分析结果 */}
              {dockingVisualization.pymol_analysis && (
                <div style={{
                  background: 'white',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                  padding: '16px',
                  marginTop: '20px'
                }}>
                  <h5 style={{
                    margin: '0 0 12px 0',
                    color: '#4f46e5',
                    fontSize: '16px',
                    fontWeight: '600'
                  }}>
                    🧮 PyMOL科学分析
                  </h5>
                  
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                    gap: '12px'
                  }}>
                    {dockingVisualization.pymol_analysis.ki_estimate && (
                      <div style={{
                        background: '#f8fafc',
                        padding: '12px',
                        borderRadius: '6px',
                        border: '1px solid #e2e8f0'
                      }}>
                        <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>
                          Ki 估值
                        </div>
                        <div style={{ fontSize: '16px', fontWeight: '600', color: '#334155' }}>
                          {dockingVisualization.pymol_analysis.ki_estimate}
                        </div>
                      </div>
                    )}
                    
                    {dockingVisualization.pymol_analysis.ic50_prediction && (
                      <div style={{
                        background: '#f8fafc',
                        padding: '12px',
                        borderRadius: '6px',
                        border: '1px solid #e2e8f0'
                      }}>
                        <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>
                          IC50 预测
                        </div>
                        <div style={{ fontSize: '16px', fontWeight: '600', color: '#334155' }}>
                          {dockingVisualization.pymol_analysis.ic50_prediction}
                        </div>
                      </div>
                    )}
                    
                    {dockingVisualization.pymol_analysis.binding_analysis && (
                      <div style={{
                        background: '#f8fafc',
                        padding: '12px',
                        borderRadius: '6px',
                        border: '1px solid #e2e8f0',
                        gridColumn: '1 / -1'
                      }}>
                        <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>
                          结合分析
                        </div>
                        <div style={{ fontSize: '14px', color: '#334155', lineHeight: '1.5' }}>
                          {dockingVisualization.pymol_analysis.binding_analysis}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </DockingImageSection>
          )}
          
          {dockingResult && !dockingResult.success && (
            <div style={{ 
              textAlign: 'center', 
              padding: '40px',
              background: '#fef7f0',
              borderRadius: '12px',
              border: '1px solid #fed7aa'
            }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>⚠️</div>
              <h4 style={{ color: '#ea580c', marginBottom: '8px' }}>分子对接失败</h4>
              <p style={{ color: '#9a3412', margin: 0 }}>
                无法完成分子对接，可能是由于蛋白质结构或化合物结构的问题
              </p>
            </div>
          )}
        </div>
      ) : (
        <div style={{ 
          textAlign: 'center', 
          padding: '60px 20px',
          background: '#f8fafc',
          borderRadius: '12px',
          border: '2px dashed #e2e8f0'
        }}>
          <div style={{ fontSize: '64px', marginBottom: '16px' }}>🎯</div>
          <h3 style={{ color: '#64748b', marginBottom: '8px' }}>暂无对接结果</h3>
          <p style={{ color: '#94a3b8', margin: 0 }}>
            完成分子对接后将显示详细的对接结果和可视化
          </p>
        </div>
      )}
    </div>
  )

  const renderScientificAnalysis = () => (
    <div>
      {/* 靶点分析部分 */}
      {targetExplanation && (
        <ExplanationSection>
          <h4>靶点分析</h4>
          <p>{targetExplanation}</p>
        </ExplanationSection>
      )}
      
      {/* AI生成的综合科学分析 */}
      {explanation && (
        <ExplanationSection>
          <h4>药物发现科学解释</h4>
          <p style={{ lineHeight: '1.8', whiteSpace: 'pre-line' }}>{explanation}</p>
        </ExplanationSection>
      )}
      
      {/* 化合物选择和优化的详细解释 */}
      {(selectionReason || optimizationExplanation) && (
        <>
          {selectionReason && (
            <ExplanationSection>
              <h4>化合物选择理由</h4>
              <p>{selectionReason}</p>
            </ExplanationSection>
          )}
          
          {optimizationExplanation && (
            <ExplanationSection>
              <h4>分子优化解释</h4>
              <p>{optimizationExplanation}</p>
            </ExplanationSection>
          )}
        </>
      )}
      
      {/* 如果没有任何分析内容 */}
      {!targetExplanation && !explanation && !selectionReason && !optimizationExplanation && (
        <div style={{ 
          textAlign: 'center', 
          padding: '60px 20px',
          background: '#f8fafc',
          borderRadius: '12px',
          border: '2px dashed #e2e8f0'
        }}>
          <div style={{ fontSize: '64px', marginBottom: '16px' }}>📊</div>
          <h3 style={{ color: '#64748b', marginBottom: '8px' }}>暂无科学分析</h3>
          <p style={{ color: '#94a3b8', margin: 0 }}>
            完成工作流程后将生成详细的科学分析报告
          </p>
        </div>
      )}
    </div>
  )

  const renderImportantFiles = () => (
    <div>
      {(structurePath && sessionId) || optimizedSmiles || (sessionId && ligandSmiles && ligandSmiles.length > 0) ? (
        <div>
          {structurePath && sessionId && (
            <div style={{ marginBottom: '24px' }}>
              <h4 style={{ fontSize: '16px', color: '#4f46e5', marginBottom: '12px' }}>🧬 蛋白质结构文件</h4>
              <div style={{ 
                background: '#f8fafc',
                padding: '16px',
                borderRadius: '8px',
                border: '1px solid #e2e8f0'
              }}>
                <FileLink 
                  href="#" 
                  onClick={(e) => { e.preventDefault(); downloadStructureFile('pdb'); }}
                  style={{ marginRight: '12px' }}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M13 9h5.5L13 3.5V9M6 2h8l6 6v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4c0-1.11.89-2 2-2m9 16v-2H6v2h9m3-4v-2H6v2h12z"/>
                  </svg>
                  蛋白质PDB
                </FileLink>
                <FileLink 
                  href="#" 
                  onClick={(e) => { e.preventDefault(); downloadStructureFile('pdbqt'); }}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M13 9h5.5L13 3.5V9M6 2h8l6 6v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4c0-1.11.89-2 2-2m9 16v-2H6v2h9m3-4v-2H6v2h12z"/>
                  </svg>
                  蛋白质PDBQT
                </FileLink>
              </div>
            </div>
          )}
          
          {optimizedSmiles && (
            <div style={{ marginBottom: '24px' }}>
              <h4 style={{ fontSize: '16px', color: '#4f46e5', marginBottom: '12px' }}>⚡ SMILES分子数据</h4>
              <div style={{ 
                background: '#f8fafc',
                padding: '16px',
                borderRadius: '8px',
                border: '1px solid #e2e8f0'
              }}>
                <FileLink href={`data:text/plain;charset=utf-8,${encodeURIComponent(optimizedSmiles)}`} download="optimized_molecule.smi">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2m14 8V5H5v6h14m0 2H5v6h14v-6z"/>
                  </svg>
                  优化后分子SMILES
                </FileLink>
              </div>
            </div>
          )}
          
          {/* 配体文件下载 */}
          {sessionId && (
            <>
              {/* 原始配体文件下载 */}
              {ligandSmiles && ligandSmiles.length > 0 && (
                <div style={{ marginBottom: '24px' }}>
                  <h4 style={{ fontSize: '16px', color: '#4f46e5', marginBottom: '12px' }}>📋 原始配体文件</h4>
                  {ligandSmiles.map((_, index) => (
                    <div key={index} style={{ 
                      marginBottom: '12px',
                      background: '#f8fafc',
                      padding: '12px',
                      borderRadius: '8px',
                      border: '1px solid #e2e8f0'
                    }}>
                      <div style={{ fontSize: '14px', color: '#64748b', marginBottom: '8px', fontWeight: '500' }}>
                        配体 {index + 1}
                      </div>
                      <FileLink 
                        href="#" 
                        onClick={(e) => { e.preventDefault(); downloadLigandFile('original', 'pdb', index); }}
                        style={{ marginRight: '12px' }}
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
                        </svg>
                        PDB格式
                      </FileLink>
                      <FileLink 
                        href="#" 
                        onClick={(e) => { e.preventDefault(); downloadLigandFile('original', 'pdbqt', index); }}
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
                        </svg>
                        PDBQT格式
                      </FileLink>
                    </div>
                  ))}
                </div>
              )}
              
              {/* 优化后配体文件下载 */}
              {optimizedSmiles && (
                <div style={{ marginBottom: '24px' }}>
                  <h4 style={{ fontSize: '16px', color: '#4f46e5', marginBottom: '12px' }}>⚡ 优化后配体文件</h4>
                  <div style={{ 
                    background: '#f8fafc',
                    padding: '16px',
                    borderRadius: '8px',
                    border: '1px solid #e2e8f0'
                  }}>
                    <FileLink 
                      href="#" 
                      onClick={(e) => { e.preventDefault(); downloadLigandFile('optimized', 'pdb'); }}
                      style={{ marginRight: '12px' }}
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
                      </svg>
                      优化配体PDB
                    </FileLink>
                    <FileLink 
                      href="#" 
                      onClick={(e) => { e.preventDefault(); downloadLigandFile('optimized', 'pdbqt'); }}
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
                      </svg>
                      优化配体PDBQT
                    </FileLink>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      ) : (
        <div style={{ 
          textAlign: 'center', 
          padding: '60px 20px',
          background: '#f8fafc',
          borderRadius: '12px',
          border: '2px dashed #e2e8f0'
        }}>
          <div style={{ fontSize: '64px', marginBottom: '16px' }}>📁</div>
          <h3 style={{ color: '#64748b', marginBottom: '8px' }}>暂无可下载文件</h3>
          <p style={{ color: '#94a3b8', margin: 0 }}>
            完成工作流程后将生成蛋白质结构、配体文件等可下载资源
          </p>
        </div>
      )}
    </div>
  )

  return (
    <Panel>
      <TabContainer>
        {tabs.map((tab) => (
          <Tab
            key={tab.id}
            active={activeTab === tab.id}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </Tab>
        ))}
      </TabContainer>
      
      <TabContent>
        {renderTabContent()}
      </TabContent>
    </Panel>
  )
}

export default ResultPanel
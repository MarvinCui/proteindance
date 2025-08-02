import React, { useEffect, useRef, useState } from 'react'
import styled from '@emotion/styled'

const ViewerContainer = styled.div`
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  margin: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
`

const ViewerTitle = styled.h3`
  font-size: 18px;
  color: #4f46e5;
  margin: 0 0 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid rgba(79,70,229,0.2);
`

const ViewerFrame = styled.div`
  width: 100%;
  height: 350px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
  background: #f8fafc;
  position: relative;
  flex-shrink: 0;
`

const LoadingOverlay = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: #6b7280;
`

const ErrorMessage = styled.div`
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
  padding: 12px;
  color: #dc2626;
  margin: 12px 0;
`

const InfoPanel = styled.div`
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 6px;
  padding: 12px;
  margin: 12px 0;
  
  p {
    margin: 0;
    font-size: 14px;
    color: #0369a1;
  }
`

interface Props {
  structurePath?: string
  pocketCenter?: [number, number, number] | null
  ligandSmiles?: string[] | null
  optimizedSmiles?: string | null
}

const ProteinViewerSimple: React.FC<Props> = ({ 
  structurePath, 
  pocketCenter,
  ligandSmiles = null,
  optimizedSmiles = null
}) => {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [structureInfo, setStructureInfo] = useState<any>(null)

  useEffect(() => {
    if (!structurePath) return

    const loadStructureInfo = async () => {
      try {
        setLoading(true)
        setError(null)

        // 获取蛋白质结构数据 - 使用动态配置
        const { getApiBaseUrl } = await import('../config/api-config')
        const API_BASE = getApiBaseUrl().replace('/api', '') // 移除/api后缀
        // 确保路径正确编码，避免双斜杠问题
        const encodedPath = encodeURIComponent(structurePath)
        const response = await fetch(`${API_BASE}/api/structure/${encodedPath}`)
        if (!response.ok) {
          throw new Error(`Failed to load structure: ${response.statusText}`)
        }
        
        const structureData = await response.text()
        
        // 解析PDB文件的基本信息
        const lines = structureData.split('\n')
        const headerLine = lines.find(line => line.startsWith('HEADER'))
        const titleLines = lines.filter(line => line.startsWith('TITLE'))
        const atomLines = lines.filter(line => line.startsWith('ATOM'))
        
        const info = {
          filename: structurePath.split('/').pop(),
          header: headerLine ? headerLine.substring(10, 50).trim() : '未知',
          title: titleLines.map(line => line.substring(10).trim()).join(' '),
          atomCount: atomLines.length,
          chains: [...new Set(atomLines.map(line => line.substring(21, 22)))].filter(c => c.trim()),
          residueCount: [...new Set(atomLines.map(line => line.substring(17, 20) + line.substring(22, 26)))].length
        }
        
        setStructureInfo(info)
        setLoading(false)

      } catch (err) {
        console.error('Error loading protein structure:', err)
        setError(err instanceof Error ? err.message : 'Failed to load protein structure')
        setLoading(false)
      }
    }

    loadStructureInfo()
  }, [structurePath])

  if (!structurePath) {
    return null
  }

  return (
    <ViewerContainer className="protein-viewer-simple">
      <ViewerTitle>蛋白质结构信息</ViewerTitle>
      
      {error && (
        <ErrorMessage>
          {error}
        </ErrorMessage>
      )}

      {loading && (
        <LoadingOverlay>
          加载蛋白质结构中...
        </LoadingOverlay>
      )}

      {structureInfo && (
        <InfoPanel>
          <p><strong>文件名：</strong> {structureInfo.filename}</p>
          <p><strong>标题：</strong> {structureInfo.title || structureInfo.header}</p>
          <p><strong>原子数量：</strong> {structureInfo.atomCount}</p>
          <p><strong>氨基酸残基：</strong> {structureInfo.residueCount}</p>
          <p><strong>蛋白链：</strong> {structureInfo.chains.join(', ')}</p>
          {pocketCenter && (
            <p><strong>结合口袋中心：</strong> ({pocketCenter.map(n => n.toFixed(2)).join(', ')})</p>
          )}
          {ligandSmiles && (
            <p><strong>配体分子：</strong> {ligandSmiles.length} 个 SMILES 结构</p>
          )}
          {optimizedSmiles && (
            <p><strong>优化化合物：</strong> {optimizedSmiles.substring(0, 30)}...</p>
          )}
        </InfoPanel>
      )}

      <ViewerFrame className="viewer-frame">
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          height: '100%',
          flexDirection: 'column',
          color: '#6b7280'
        }}>
          <div style={{ fontSize: '24px', marginBottom: '16px' }}>🧬</div>
          <p>蛋白质结构文件已加载</p>
          <p style={{ fontSize: '14px', textAlign: 'center', marginTop: '8px' }}>
            3D可视化功能正在开发中<br/>
            当前显示结构基本信息
          </p>
          {structureInfo && (
            <div style={{ marginTop: '16px', fontSize: '12px', textAlign: 'center' }}>
              <p>文件路径: {structurePath}</p>
            </div>
          )}
        </div>
      </ViewerFrame>
    </ViewerContainer>
  )
}

export default ProteinViewerSimple
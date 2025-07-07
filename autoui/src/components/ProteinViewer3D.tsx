import React, { useEffect, useRef, useState } from 'react'
import styled from '@emotion/styled'

const ViewerContainer = styled.div`
  background: white;
  border-radius: 8px;
  padding: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  margin: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
`

const ViewerTitle = styled.h3`
  font-size: 14px;
  color: #4f46e5;
  margin: 0 0 8px;
  padding-bottom: 4px;
  border-bottom: 1px solid rgba(79,70,229,0.2);
`

const ViewerFrame = styled.div`
  width: 100%;
  height: 320px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  overflow: hidden;
  background: #000;
  position: relative;
  flex-shrink: 0;
`

const LoadingOverlay = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: white;
  z-index: 10;
`

const ControlPanel = styled.div`
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
  flex-wrap: wrap;
`

const ControlButton = styled.button`
  padding: 4px 8px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  background: white;
  color: #374151;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 12px;
  
  &:hover {
    background: #f9fafb;
    border-color: #4f46e5;
  }
  
  &.active {
    background: #4f46e5;
    color: white;
    border-color: #4f46e5;
  }
`

const ErrorMessage = styled.div`
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
  padding: 12px;
  color: #dc2626;
  margin: 12px 0;
`

interface Props {
  structurePath?: string
  pocketCenter?: [number, number, number] | null
  ligandSmiles?: string[] | null  // 配体SMILES列表
  optimizedSmiles?: string | null  // 优化后的化合物
}

declare global {
  interface Window {
    $3Dmol: any;
  }
}

const ProteinViewer3D: React.FC<Props> = ({ 
  structurePath, 
  pocketCenter,
  ligandSmiles = null,
  optimizedSmiles = null
}) => {
  const viewerRef = useRef<HTMLDivElement>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [viewer, setViewer] = useState<any>(null)
  const [viewStyle, setViewStyle] = useState('cartoon')
  const [showLigands, setShowLigands] = useState(true)
  const [ligandModels, setLigandModels] = useState<any[]>([])

  useEffect(() => {
    if (!structurePath) return

    const initViewer = async () => {
      try {
        setLoading(true)
        setError(null)

        // 检查是否已经有3dmol包
        if (typeof window !== 'undefined' && window.$3Dmol) {
          await loadStructure()
          return
        }

        // 动态加载3dmol
        const script = document.createElement('script')
        script.src = 'https://3dmol.org/build/3Dmol-min.js'
        
        script.onload = async () => {
          // 等待一段时间确保库完全初始化
          setTimeout(async () => {
            try {
              await loadStructure()
            } catch (err) {
              setError(`初始化3D查看器失败: ${err}`)
              setLoading(false)
            }
          }, 200)
        }
        
        script.onerror = () => {
          setError('无法加载3D可视化库，请检查网络连接')
          setLoading(false)
        }
        
        document.head.appendChild(script)

      } catch (err) {
        console.error('Error initializing viewer:', err)
        setError(`初始化失败: ${err}`)
        setLoading(false)
      }
    }

    const loadStructure = async () => {
      try {
        const $3Dmol = window.$3Dmol
        if (!$3Dmol) {
          throw new Error('3DMol 库未加载')
        }

        // 获取结构数据
        const API_BASE = 'http://192.168.1.100:5001'
        // 确保路径正确编码，避免双斜杠问题
        const encodedPath = encodeURIComponent(structurePath)
        const response = await fetch(`${API_BASE}/api/structure/${encodedPath}`)
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }
        
        const pdbData = await response.text()
        
        if (!pdbData || pdbData.trim().length === 0) {
          throw new Error('接收到空的结构数据')
        }

        // 检查容器
        if (!viewerRef.current) {
          throw new Error('查看器容器未准备好')
        }

        // 创建查看器
        const viewerConfig = {
          backgroundColor: 'black'
        }
        
        const viewerInstance = $3Dmol.createViewer(viewerRef.current, viewerConfig)
        
        // 添加模型
        viewerInstance.addModel(pdbData, 'pdb')
        
        // 设置样式
        viewerInstance.setStyle({}, { cartoon: { color: 'spectrum' } })
        
        // 添加口袋标记
        if (pocketCenter && Array.isArray(pocketCenter) && pocketCenter.length === 3) {
          viewerInstance.addSphere({
            center: { x: pocketCenter[0], y: pocketCenter[1], z: pocketCenter[2] },
            radius: 3.0,
            color: 'red',
            alpha: 0.6
          })
        }
        
        // 添加配体分子
        await addLigandMolecules(viewerInstance)
        
        // 添加优化后的化合物
        await addOptimizedCompound(viewerInstance)
        
        // 调整视角和渲染
        viewerInstance.zoomTo()
        viewerInstance.render()
        
        setViewer(viewerInstance)
        setLoading(false)

      } catch (err) {
        console.error('Error loading structure:', err)
        setError(`加载结构失败: ${err}`)
        setLoading(false)
      }
    }

    initViewer()
  }, [structurePath, pocketCenter, ligandSmiles, optimizedSmiles])
  
  // SMILES转3D结构的函数
  const smilesTo3D = async (smiles: string): Promise<string | null> => {
    try {
      const API_BASE = 'http://192.168.1.100:5001'
      const response = await fetch(`${API_BASE}/api/smiles-to-3d`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ smiles })
      })
      
      if (!response.ok) {
        console.warn(`SMILES转换失败: ${smiles}`)
        return null
      }
      
      const data = await response.json()
      return data.success ? data.mol_data : null
    } catch (err) {
      console.warn(`SMILES转换错误: ${err}`)
      return null
    }
  }
  
  // 添加配体分子到口袋中
  const addLigandMolecules = async (viewerInstance: any) => {
    if (!ligandSmiles || !pocketCenter || !showLigands) return
    
    const models: any[] = []
    
    // 只显示前3个配体，避免过于拥挤
    const smilesSubset = ligandSmiles.slice(0, 3)
    
    for (let i = 0; i < smilesSubset.length; i++) {
      const smiles = smilesSubset[i]
      const molData = await smilesTo3D(smiles)
      
      if (molData) {
        try {
          const model = viewerInstance.addModel(molData, 'sdf')
          
          // 随机位置在口袋附近
          const offsetX = (Math.random() - 0.5) * 6  // 随机偏移 -3 到 3
          const offsetY = (Math.random() - 0.5) * 6
          const offsetZ = (Math.random() - 0.5) * 6
          
          model.translate({
            x: pocketCenter[0] + offsetX,
            y: pocketCenter[1] + offsetY,
            z: pocketCenter[2] + offsetZ
          })
          
          // 配体样式 - 用不同颜色区分
          const colors = ['cyan', 'yellow', 'magenta']
          model.setStyle({}, {
            stick: {
              colorscheme: colors[i] || 'cyan',
              radius: 0.2
            },
            sphere: {
              colorscheme: colors[i] || 'cyan',
              radius: 0.3,
              alpha: 0.8
            }
          })
          
          models.push(model)
        } catch (err) {
          console.warn(`添加配体${i+1}失败:`, err)
        }
      }
    }
    
    setLigandModels(models)
  }
  
  // 添加优化后的化合物
  const addOptimizedCompound = async (viewerInstance: any) => {
    if (!optimizedSmiles || !pocketCenter) return
    
    const molData = await smilesTo3D(optimizedSmiles)
    
    if (molData) {
      try {
        const model = viewerInstance.addModel(molData, 'sdf')
        
        // 优化化合物放在口袋中心
        model.translate({
          x: pocketCenter[0],
          y: pocketCenter[1],
          z: pocketCenter[2]
        })
        
        // 特殊样式 - 绿色高亮
        model.setStyle({}, {
          stick: {
            colorscheme: 'greenCarbon',
            radius: 0.3
          },
          sphere: {
            colorscheme: 'greenCarbon',
            radius: 0.4,
            alpha: 0.9
          }
        })
        
        // 添加标签
        viewerInstance.addLabel('优化化合物', {
          position: {
            x: pocketCenter[0],
            y: pocketCenter[1] + 3,
            z: pocketCenter[2]
          },
          backgroundColor: 'green',
          fontColor: 'white',
          fontSize: 12
        })
        
      } catch (err) {
        console.warn('添加优化化合物失败:', err)
      }
    }
  }

  const changeStyle = (style: string) => {
    if (!viewer) return
    
    try {
      setViewStyle(style)
      
      // 清除样式
      viewer.setStyle({}, {})
      
      // 应用新样式
      switch (style) {
        case 'cartoon':
          viewer.setStyle({}, { cartoon: { color: 'spectrum' } })
          break
        case 'stick':
          viewer.setStyle({}, { stick: {} })
          break
        case 'sphere':
          viewer.setStyle({}, { sphere: {} })
          break
        case 'line':
          viewer.setStyle({}, { line: {} })
          break
      }
      
      // 重新添加口袋标记（样式切换后保持可见）
      if (pocketCenter && Array.isArray(pocketCenter) && pocketCenter.length === 3) {
        viewer.addSphere({
          center: { x: pocketCenter[0], y: pocketCenter[1], z: pocketCenter[2] },
          radius: 3.0,
          color: 'red',
          alpha: 0.6
        })
      }
      
      // 重新添加配体和优化化合物
      if (showLigands) {
        addLigandMolecules(viewer)
        addOptimizedCompound(viewer)
      }
      
      viewer.render()
    } catch (err) {
      console.error('Error changing style:', err)
    }
  }
  
  const toggleLigands = () => {
    setShowLigands(!showLigands)
    if (viewer) {
      if (!showLigands) {
        // 显示配体
        addLigandMolecules(viewer)
        addOptimizedCompound(viewer)
      } else {
        // 隐藏配体 - 重新初始化查看器
        viewer.clear()
        // 重新加载蛋白质结构
        if (structurePath) {
          // 这里可以重新调用加载逻辑
          window.location.reload() // 简单的做法，重新加载页面
        }
      }
      viewer.render()
    }
  }

  if (!structurePath) {
    return null
  }

  return (
    <ViewerContainer className="protein-viewer-3d">
      <ViewerTitle>蛋白质3D结构</ViewerTitle>
      
      {error && (
        <ErrorMessage>
          {error}
        </ErrorMessage>
      )}
      
      {!error && (
        <>
          <ControlPanel>
            <ControlButton 
              className={viewStyle === 'cartoon' ? 'active' : ''}
              onClick={() => changeStyle('cartoon')}
            >
              卡通
            </ControlButton>
            <ControlButton 
              className={viewStyle === 'stick' ? 'active' : ''}
              onClick={() => changeStyle('stick')}
            >
              棒状
            </ControlButton>
            <ControlButton 
              className={viewStyle === 'sphere' ? 'active' : ''}
              onClick={() => changeStyle('sphere')}
            >
              球状
            </ControlButton>
            <ControlButton 
              className={viewStyle === 'line' ? 'active' : ''}
              onClick={() => changeStyle('line')}
            >
              线条
            </ControlButton>
            
            {/* 配体显示控制 */}
            <ControlButton 
              className={showLigands ? 'active' : ''}
              onClick={toggleLigands}
              style={{ 
                marginLeft: '10px',
                backgroundColor: showLigands ? '#10b981' : '#6b7280',
                border: 'none'
              }}
            >
              {showLigands ? '🧪 隐藏配体' : '🧪 显示配体'}
            </ControlButton>
          </ControlPanel>
          
          {/* 配体信息显示 */}
          {(ligandSmiles || optimizedSmiles) && (
            <div style={{
              fontSize: '12px',
              color: '#6b7280',
              marginBottom: '8px',
              padding: '8px',
              backgroundColor: '#f9fafb',
              borderRadius: '6px',
              border: '1px solid #e5e7eb'
            }}>
              {ligandSmiles && (
                <div>📊 配体数量: {ligandSmiles.length} (显示前3个)</div>
              )}
              {optimizedSmiles && (
                <div>✨ 优化化合物: 已加载</div>
              )}
              <div style={{ fontSize: '11px', marginTop: '4px', color: '#9ca3af' }}>
                配体以不同颜色显示：蓝绿、黄、紫红 | 优化化合物：绿色
              </div>
            </div>
          )}

          <ViewerFrame className="viewer-frame">
            <div 
              ref={viewerRef} 
              style={{ 
                width: '100%', 
                height: '100%',
                position: 'relative'
              }} 
            />
            {loading && (
              <LoadingOverlay>
                正在加载3D结构...
              </LoadingOverlay>
            )}
          </ViewerFrame>
        </>
      )}
    </ViewerContainer>
  )
}

export default ProteinViewer3D
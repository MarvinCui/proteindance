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
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
`

const ControlButton = styled.button`
  padding: 8px 16px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
  color: #374151;
  cursor: pointer;
  transition: all 0.2s;
  
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
}

declare global {
  interface Window {
    $3Dmol: any;
  }
}

const ProteinViewer3D: React.FC<Props> = ({ 
  structurePath, 
  pocketCenter 
}) => {
  const viewerRef = useRef<HTMLDivElement>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [viewer, setViewer] = useState<any>(null)
  const [viewStyle, setViewStyle] = useState('cartoon')

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
  }, [structurePath, pocketCenter])

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
      
      viewer.render()
    } catch (err) {
      console.error('Error changing style:', err)
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
          </ControlPanel>

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
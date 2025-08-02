import React, { useEffect, useRef, useState } from 'react'
import styled from '@emotion/styled'

const ViewerContainer = styled.div`
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  margin: 16px 0;
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
  height: 500px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
  background: #f8fafc;
  position: relative;
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
  receptorPath?: string
  ligandPath?: string
  pocketCenter?: [number, number, number] | null
  onVisualizationReady?: (viewerHtml: string) => void
}

const ProteinViewer: React.FC<Props> = ({
  receptorPath,
  ligandPath,
  pocketCenter,
  onVisualizationReady,
}) => {
  const viewerRef = useRef<HTMLDivElement>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [viewer, setViewer] = useState<any>(null)
  const [viewStyle, setViewStyle] = useState('cartoon')

  useEffect(() => {
    if (!receptorPath) return

    // 动态加载3dmol
    const load3DMol = async () => {
      try {
        setLoading(true)
        setError(null)

        // 检查是否已加载3dmol
        if (!(window as any).$3Dmol) {
          await new Promise<void>((resolve, reject) => {
            const script = document.createElement('script')
            script.src = 'https://3dmol.org/build/3Dmol-min.js'
            script.onload = () => {
              // 等待一小段时间确保库完全加载
              setTimeout(resolve, 100)
            }
            script.onerror = () => reject(new Error('Failed to load 3DMol'))
            document.head.appendChild(script)
          })
        }

        // 再次确认$3Dmol已加载
        const $3Dmol = (window as any).$3Dmol
        if (!$3Dmol) {
          throw new Error('3DMol library not available')
        }

        // 获取蛋白质结构数据 - 使用动态配置
        const { getApiBaseUrl } = await import('../config/api-config')
        const API_BASE = getApiBaseUrl().replace('/api', '') // 移除/api后缀

        // 确保容器存在且有尺寸
        if (!viewerRef.current) {
          throw new Error('Viewer container not available')
        }

        // 创建3DMol viewer
        const viewerInstance = $3Dmol.createViewer(viewerRef.current, {
          backgroundColor: 'white',
        })

        // 加载受体
        const encodedReceptorPath = encodeURIComponent(receptorPath)
        const receptorResponse = await fetch(
          `${API_BASE}/api/structure/${encodedReceptorPath}`,
        )
        if (!receptorResponse.ok) {
          throw new Error(
            `Failed to load receptor structure: ${receptorResponse.statusText}`,
          )
        }
        const receptorData = await receptorResponse.text()
        if (!receptorData || receptorData.trim().length === 0) {
          throw new Error('Empty receptor structure data received')
        }
        viewerInstance.addModel(receptorData, 'pdbqt')

        // 加载配体
        if (ligandPath) {
          const encodedLigandPath = encodeURIComponent(ligandPath)
          const ligandResponse = await fetch(
            `${API_BASE}/api/structure/${encodedLigandPath}`,
          )
          if (ligandResponse.ok) {
            const ligandData = await ligandResponse.text()
            if (ligandData && ligandData.trim().length > 0) {
              viewerInstance.addModels(ligandData, 'pdbqt')
            }
          } else {
            console.warn(
              `Could not load ligand file: ${ligandResponse.statusText}`,
            )
          }
        }

        // 设置样式
        viewerInstance.setStyle({}, { cartoon: { color: 'spectrum' } })
        viewerInstance.setStyle({ hetflag: true }, { stick: {} })

        // 如果有口袋中心，添加标记
        if (
          pocketCenter &&
          Array.isArray(pocketCenter) &&
          pocketCenter.length === 3
        ) {
          viewerInstance.addSphere({
            center: {
              x: pocketCenter[0],
              y: pocketCenter[1],
              z: pocketCenter[2],
            },
            radius: 3.0,
            color: 'red',
            alpha: 0.5,
          })
        }

        // 渲染并居中
        viewerInstance.zoomTo()
        viewerInstance.render()

        setViewer(viewerInstance)
        setLoading(false)

        // 回调函数传递HTML
        if (onVisualizationReady) {
          const html = `
              <div id="protein-viewer" style="width: 100%; height: 500px;"></div>
              <script>
                console.log('Protein viewer initialized');
              </script>
            `
          onVisualizationReady(html)
        }
      } catch (err) {
        console.error('Error loading protein structure:', err)
        setError(
          err instanceof Error
            ? err.message
            : 'Failed to load protein structure',
        )
        setLoading(false)
      }
    }

    load3DMol()
  }, [receptorPath, ligandPath, pocketCenter, onVisualizationReady])

  const changeViewStyle = (style: string) => {
    if (!viewer) return

    try {
      setViewStyle(style)

      const proteinSelector = { hetflag: false }

      // Remove previous surface if any
      viewer.removeSurface()

      // Apply new style to protein
      switch (style) {
        case 'cartoon':
          viewer.setStyle(proteinSelector, { cartoon: { color: 'spectrum' } })
          break
        case 'stick':
          viewer.setStyle(proteinSelector, {
            stick: { colorscheme: 'default' },
          })
          break
        case 'sphere':
          viewer.setStyle(proteinSelector, {
            sphere: { colorscheme: 'default' },
          })
          break
        case 'surface':
          // Keep cartoon and add surface
          viewer.setStyle(proteinSelector, { cartoon: { color: 'spectrum' } })
          viewer.addSurface('VDW', {
            opacity: 0.7,
            color: 'white',
            selector: proteinSelector,
          })
          break
        default:
          viewer.setStyle(proteinSelector, { cartoon: { color: 'spectrum' } })
      }

      // Ensure ligand is always stick
      viewer.setStyle({ hetflag: true }, { stick: {} })

      viewer.render()
    } catch (err) {
      console.error('Error changing view style:', err)
      setError('Failed to change visualization style')
    }
  }

  if (!receptorPath) {
    return null
  }

  return (
    <ViewerContainer>
      <ViewerTitle>蛋白质结构可视化</ViewerTitle>
      
      <ControlPanel>
        <ControlButton 
          className={viewStyle === 'cartoon' ? 'active' : ''}
          onClick={() => changeViewStyle('cartoon')}
        >
          卡通模式
        </ControlButton>
        <ControlButton 
          className={viewStyle === 'stick' ? 'active' : ''}
          onClick={() => changeViewStyle('stick')}
        >
          棒状模式
        </ControlButton>
        <ControlButton 
          className={viewStyle === 'sphere' ? 'active' : ''}
          onClick={() => changeViewStyle('sphere')}
        >
          球状模式
        </ControlButton>
        <ControlButton 
          className={viewStyle === 'surface' ? 'active' : ''}
          onClick={() => changeViewStyle('surface')}
        >
          表面模式
        </ControlButton>
      </ControlPanel>

      {error && (
        <ErrorMessage>
          {error}
        </ErrorMessage>
      )}

      <ViewerFrame>
        <div ref={viewerRef} style={{ width: '100%', height: '100%' }} />
        {loading && (
          <LoadingOverlay>
            加载蛋白质结构中...
          </LoadingOverlay>
        )}
      </ViewerFrame>
    </ViewerContainer>
  )
}

export default ProteinViewer
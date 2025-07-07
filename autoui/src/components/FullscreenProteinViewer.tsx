import React from 'react'
import styled from '@emotion/styled'
import ProteinViewerCombined from './ProteinViewerCombined'

const Overlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 0;
  overflow: hidden;
`

const ModalContainer = styled.div`
  background: white;
  border-radius: 12px;
  width: 90vw;
  height: 90vh;
  max-width: 1400px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  position: relative;
`

const ModalHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
`

const ModalTitle = styled.h2`
  margin: 0;
  font-size: 20px;
  color: #1e293b;
  font-weight: 600;
`

const CloseButton = styled.button`
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #64748b;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  
  &:hover {
    background: #e2e8f0;
    color: #1e293b;
  }
`

const ModalContent = styled.div`
  flex: 1;
  padding: 24px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
`

const FullscreenViewerContainer = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  
  /* 全屏时调整3D查看器尺寸 */
  .protein-viewer-3d .viewer-frame {
    height: 100% !important;
    min-height: 400px;
  }
  
  .protein-viewer-simple .viewer-frame {
    height: 100% !important;
    min-height: 300px;
  }
  
  /* 确保内容完全可见 */
  .protein-viewer-combined {
    height: 100% !important;
    max-height: 100% !important;
    overflow: hidden !important;
  }
`

const InfoText = styled.p`
  margin: 0 0 16px;
  color: #64748b;
  font-size: 14px;
  text-align: center;
`

interface Props {
  isOpen: boolean
  onClose: () => void
  structurePath?: string | null
  pocketCenter?: [number, number, number] | null
  proteinName?: string
}

const FullscreenProteinViewer: React.FC<Props> = ({
  isOpen,
  onClose,
  structurePath,
  pocketCenter,
  proteinName = '蛋白质结构'
}) => {
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown)
      // 阻止背景滚动
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = 'auto'
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }

  return (
    <Overlay onClick={handleOverlayClick} tabIndex={-1}>
      <ModalContainer>
        <ModalHeader>
          <ModalTitle>
            {proteinName} - 全屏视图
            {pocketCenter && (
              <span style={{ 
                fontSize: '14px', 
                color: '#64748b', 
                fontWeight: 'normal',
                marginLeft: '12px'
              }}>
                口袋中心: ({pocketCenter.map(n => n.toFixed(2)).join(', ')})
              </span>
            )}
          </ModalTitle>
          <CloseButton onClick={onClose} title="关闭 (ESC)">
            ×
          </CloseButton>
        </ModalHeader>
        
        <ModalContent>
          {structurePath ? (
            <>
              <InfoText>
                您可以使用鼠标拖拽旋转、滚轮缩放、右键平移来查看结构详情
              </InfoText>
              <FullscreenViewerContainer>
                <ProteinViewerCombined 
                  structurePath={structurePath}
                  pocketCenter={pocketCenter}
                />
              </FullscreenViewerContainer>
            </>
          ) : (
            <div style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexDirection: 'column',
              color: '#64748b'
            }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>🧬</div>
              <p>暂无蛋白质结构数据</p>
            </div>
          )}
        </ModalContent>
      </ModalContainer>
    </Overlay>
  )
}

export default FullscreenProteinViewer
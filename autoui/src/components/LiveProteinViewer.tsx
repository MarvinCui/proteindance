import React, { useState } from 'react'
import styled from '@emotion/styled'
import ProteinViewerCombined from './ProteinViewerCombined'
import FullscreenProteinViewer from './FullscreenProteinViewer'

const ViewerContainer = styled.div`
  background: white;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  width: 100%;
  box-sizing: border-box;
`

const TitleRow = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 6px;
  border-bottom: 2px solid rgba(79,70,229,0.2);
`

const ViewerTitle = styled.h3`
  font-size: 16px;
  color: #4f46e5;
  margin: 0;
  flex: 1;
  text-align: center;
`

const ExpandButton = styled.button`
  background: none;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 6px 8px;
  cursor: pointer;
  color: #64748b;
  font-size: 12px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 4px;
  
  &:hover {
    background: #f1f5f9;
    border-color: #4f46e5;
    color: #4f46e5;
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`

const ContentContainer = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
`

const PlaceholderContainer = styled.div`
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8fafc;
  border-radius: 8px;
  border: 2px dashed #d1d5db;
  flex-direction: column;
  color: #6b7280;
  text-align: center;
  padding: 20px;
`

const PlaceholderIcon = styled.div`
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
`

const PlaceholderText = styled.p`
  margin: 0;
  font-size: 14px;
  line-height: 1.5;
`

interface Props {
  structurePath?: string | null
  pocketCenter?: [number, number, number] | null
  currentStep?: number
  proteinName?: string
}

const LiveProteinViewer: React.FC<Props> = ({ 
  structurePath, 
  pocketCenter,
  currentStep = 0,
  proteinName = '蛋白质结构'
}) => {
  const [isFullscreenOpen, setIsFullscreenOpen] = useState(false)
  const renderContent = () => {
    if (!structurePath) {
      return (
        <PlaceholderContainer>
          <PlaceholderIcon>🧬</PlaceholderIcon>
          <PlaceholderText>
            {currentStep < 3 ? (
              <>
                等待蛋白质结构获取...<br/>
                <small>完成结构获取后将在此处显示3D结构</small>
              </>
            ) : (
              <>
                未获取到蛋白质结构<br/>
                <small>请重试或检查网络连接</small>
              </>
            )}
          </PlaceholderText>
        </PlaceholderContainer>
      )
    }

    return (
      <ContentContainer>
        <ProteinViewerCombined 
          structurePath={structurePath}
          pocketCenter={pocketCenter}
        />
      </ContentContainer>
    )
  }

  return (
    <>
      <ViewerContainer>
        <TitleRow>
          <div style={{ width: '60px' }}></div> {/* 左侧空间平衡 */}
          <ViewerTitle>
            实时蛋白质结构
            {pocketCenter && (
              <small style={{ 
                display: 'block', 
                fontSize: '12px', 
                color: '#6b7280', 
                fontWeight: 'normal',
                marginTop: '4px'
              }}>
                口袋中心: ({pocketCenter.map(n => n.toFixed(1)).join(', ')})
              </small>
            )}
          </ViewerTitle>
          <ExpandButton 
            onClick={() => setIsFullscreenOpen(true)}
            disabled={!structurePath}
            title="全屏查看"
          >
            🔍 放大
          </ExpandButton>
        </TitleRow>
        {renderContent()}
      </ViewerContainer>

      <FullscreenProteinViewer
        isOpen={isFullscreenOpen}
        onClose={() => setIsFullscreenOpen(false)}
        structurePath={structurePath}
        pocketCenter={pocketCenter}
        proteinName={proteinName}
      />
    </>
  )
}

export default LiveProteinViewer
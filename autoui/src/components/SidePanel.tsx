import React from 'react'
import styled from '@emotion/styled'
import HistoryPanel from './HistoryPanel'
import LiveProteinViewer from './LiveProteinViewer'

const Container = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100vh;
  max-height: 100vh;
  overflow: hidden;
  padding: 0;
  margin: 0;
`

const HistorySection = styled.div`
  flex: 0 0 auto;
  min-height: 0;
  background: transparent;
`

const StructureSection = styled.div`
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: transparent;
`

interface LogEntry {
  step: number
  category: '状态' | '决策' | '日志'
  message: string
}

interface Props {
  logs: LogEntry[]
  structurePath?: string | null
  pocketCenter?: [number, number, number] | null
  currentStep?: number
  proteinName?: string
}

const SidePanel: React.FC<Props> = ({ 
  logs, 
  structurePath, 
  pocketCenter, 
  currentStep,
  proteinName 
}) => {
  return (
    <Container>
      <HistorySection>
        <HistoryPanel logs={logs} />
      </HistorySection>
      
      <StructureSection>
        <LiveProteinViewer 
          structurePath={structurePath}
          pocketCenter={pocketCenter}
          currentStep={currentStep}
          proteinName={proteinName}
        />
      </StructureSection>
    </Container>
  )
}

export default SidePanel
import React from 'react'
import styled from '@emotion/styled'
import LiveProteinViewer from './LiveProteinViewer'
import HistoryPanel from './HistoryPanel'

const Container = styled.div`
  display: flex;
  flex-direction: column;
  height: 100%;
  max-height: 100vh;
  background-color: #f8f9fc;
`

const HistorySection = styled.div`
  flex: 0 0 30%; /* Fixed 30% height */
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 8px;
  border-bottom: 1px solid #e5e7eb;
`

const ViewerSection = styled.div`
  flex: 0 0 70%; /* Fixed 70% height */
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 8px;
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
  ligandSmiles?: string[] | null
  optimizedSmiles?: string | null
}

const SidePanel: React.FC<Props> = ({
  logs,
  structurePath,
  pocketCenter,
  currentStep,
  proteinName,
  ligandSmiles = null,
  optimizedSmiles = null,
}) => {
  return (
    <Container>
      <HistorySection>
        <HistoryPanel logs={logs} />
      </HistorySection>
      <ViewerSection>
        <LiveProteinViewer
          structurePath={structurePath}
          pocketCenter={pocketCenter}
          currentStep={currentStep}
          proteinName={proteinName}
          ligandSmiles={ligandSmiles}
          optimizedSmiles={optimizedSmiles}
        />
      </ViewerSection>
    </Container>
  )
}

export default SidePanel
import React from 'react'
import styled from '@emotion/styled'

const Panel = styled.div`
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-top: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
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

const ImageContainer = styled.div`
  display: flex;
  gap: 20px;
  margin: 16px 0;
  
  img {
    max-width: 45%;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }
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

interface Props {
  disease: string
  geneSymbol: string
  uniprotAcc?: string
  pocketCenter: [number, number, number]
  optimizedSmiles: string
  explanation: string
  moleculeImage?: string
  dockingImage?: string
  structurePath?: string
}

const ResultPanel: React.FC<Props> = ({
  disease,
  geneSymbol,
  uniprotAcc,
  pocketCenter,
  optimizedSmiles,
  explanation,
  moleculeImage,
  dockingImage,
  structurePath
}) => {
  return (
    <Panel>
      <Section>
        <SectionTitle>研究成果总结</SectionTitle>
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
            <p>({pocketCenter.map(n => n.toFixed(2)).join(', ')})</p>
          </InfoCard>
        </InfoGrid>
      </Section>

      {(moleculeImage || dockingImage) && (
        <Section>
          <SectionTitle>结构可视化</SectionTitle>
          <ImageContainer>
            {moleculeImage && (
              <img src={`data:image/png;base64,${moleculeImage}`} alt="优化后的分子结构" />
            )}
            {dockingImage && (
              <img src={`data:image/png;base64,${dockingImage}`} alt="蛋白质-配体对接" />
            )}
          </ImageContainer>
        </Section>
      )}

      <Section>
        <SectionTitle>科学分析</SectionTitle>
        <p style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>{explanation}</p>
      </Section>

      <Section>
        <SectionTitle>重要文件</SectionTitle>
        <div>
          {structurePath && (
            <FileLink href={`file://${structurePath}`} target="_blank">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M13 9h5.5L13 3.5V9M6 2h8l6 6v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4c0-1.11.89-2 2-2m9 16v-2H6v2h9m3-4v-2H6v2h12z"/>
              </svg>
              蛋白质结构文件
            </FileLink>
          )}
          <FileLink href={`data:text/plain;charset=utf-8,${encodeURIComponent(optimizedSmiles)}`} download="optimized_molecule.smi">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2m14 8V5H5v6h14m0 2H5v6h14v-6z"/>
            </svg>
            优化后分子SMILES
          </FileLink>
        </div>
      </Section>
    </Panel>
  )
}

export default ResultPanel

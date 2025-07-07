import React, { useState } from 'react'
import ProteinViewer3D from './ProteinViewer3D'
import ProteinViewerSimple from './ProteinViewerSimple'

interface Props {
  structurePath?: string
  pocketCenter?: [number, number, number] | null
}

const ProteinViewerCombined: React.FC<Props> = ({ 
  structurePath, 
  pocketCenter 
}) => {
  const [use3D, setUse3D] = useState(true)

  if (!structurePath) {
    return null
  }

  // 如果选择使用3D，显示3D查看器
  if (use3D) {
    return (
      <div className="protein-viewer-combined" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <div style={{ flex: 1, overflow: 'hidden' }}>
          <ProteinViewer3D 
            structurePath={structurePath}
            pocketCenter={pocketCenter}
          />
        </div>
        <div style={{ 
          textAlign: 'center', 
          marginTop: '8px',
          fontSize: '12px',
          color: '#6b7280',
          flexShrink: 0
        }}>
          <button 
            onClick={() => setUse3D(false)}
            style={{
              background: 'none',
              border: '1px solid #d1d5db',
              borderRadius: '4px',
              padding: '3px 6px',
              cursor: 'pointer',
              fontSize: '11px'
            }}
          >
            信息视图
          </button>
        </div>
      </div>
    )
  }

  // 否则显示简单信息视图
  return (
    <div className="protein-viewer-combined" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ flex: 1, overflow: 'hidden' }}>
        <ProteinViewerSimple 
          structurePath={structurePath}
          pocketCenter={pocketCenter}
        />
      </div>
      <div style={{ 
        textAlign: 'center', 
        marginTop: '8px',
        fontSize: '12px',
        color: '#6b7280',
        flexShrink: 0
      }}>
        <button 
          onClick={() => setUse3D(true)}
          style={{
            background: 'none',
            border: '1px solid #d1d5db',
            borderRadius: '4px',
            padding: '3px 6px',
            cursor: 'pointer',
            fontSize: '11px'
          }}
        >
          3D视图
        </button>
      </div>
    </div>
  )
}

export default ProteinViewerCombined
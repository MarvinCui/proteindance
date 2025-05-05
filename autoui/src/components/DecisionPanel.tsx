import React from 'react'

interface Entry {
  step: number
  category: string
  message: string
}
interface Props {
  logs: Entry[]
}

export default function DecisionPanel({ logs }: Props) {
  return (
    <>
      <style>{`
        .panel { background:#fff7ed; border-radius:10px;
                 box-shadow:0 2px 8px rgba(0,0,0,0.05);
                 padding:16px; margin-bottom:16px; border-left:4px solid #f59e0b; }
        .title { font-weight:600; color:#b45309; margin-bottom:8px; }
        .item  { font-size:14px; color:#92400e; margin-bottom:4px; }
      `}</style>
      <div className="panel">
        <div className="title">AI 决策（步骤 {logs[0]?.step || '-'}）</div>
        {logs.length === 0
          ? <div className="item">— 暂无决策</div>
          : logs.map((l, i) => (
              <div key={i} className="item">{l.message}</div>
            ))
        }
      </div>
    </>
  )
}

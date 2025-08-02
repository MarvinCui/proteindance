import React from 'react'

interface Entry {
  step: number
  category: string
  message: string
}
interface Props {
  logs: Entry[]
}

export default function LogPanel({ logs }: Props) {
  return (
    <>
      <style>{`
        .panel { background:#f1f5f9; border-radius:10px;
                 box-shadow:0 2px 8px rgba(0,0,0,0.05);
                 padding:16px; margin-bottom:16px;
                 max-height:200px; overflow-y:auto; }
        .title { font-weight:600; color:#1e293b; margin-bottom:8px; }
        .entry { font-family:monospace; font-size:12px;
                 color:#475569; margin-bottom:4px; white-space:pre-wrap; }
      `}</style>
      <div className="panel">
        <div className="title">原始日志（步骤 {logs[0]?.step || '-'}）</div>
        {logs.length === 0
          ? <div className="entry">— 暂无日志</div>
          : logs.map((l, i) => (
              <div key={i} className="entry">{l.message}</div>
            ))
        }
      </div>
    </>
  )
}

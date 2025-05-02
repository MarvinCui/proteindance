import React, { useState } from 'react'

interface Entry {
  step: number
  category: string
  message: string
}
interface Props {
  logs: Entry[]
}

export default function HistoryPanel({ logs }: Props) {
  const [open, setOpen] = useState(false)
  return (
    <>
      <style>{`
        .history { width:260px; font-size:13px; }
        .header  { font-weight:600; background:#e2e8f0;
                   padding:8px 12px; border-radius:8px; cursor:pointer;
                   user-select:none; }
        .body    { max-height:600px; overflow-y:auto; margin-top:8px;
                   background:#fff; border-radius:8px;
                   box-shadow:0 2px 8px rgba(0,0,0,0.05); }
        .item    { padding:6px 12px; border-bottom:1px solid #f0f0f0;
                   color:#475569; }
      `}</style>
      <div className="history">
        <div className="header" onClick={() => setOpen(!open)}>
          {open ? '▼' : '▶'} 历史记录（{logs.length} 条）
        </div>
        {open && (
          <div className="body">
            {logs.map((l, i) => (
              <div key={i} className="item">
                步骤{l.step} [{l.category}]<br/>
                {l.message}
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  )
}

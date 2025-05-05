import React from 'react'

interface Entry {
  step: number
  category: string
  message: string
}
interface Props {
  logs: Entry[]
}

export default function StatusPanel({ logs }: Props) {
  return (
    <>
      <style>{`
        .panel { background:#f8fafc; border-radius:10px;
                 box-shadow:0 2px 8px rgba(0,0,0,0.05);
                 padding:16px; margin-bottom:16px; }
        .title { font-weight:600; color:#4f46e5; margin-bottom:8px; }
        .item  { font-size:14px; color:#334155; margin-bottom:4px; }
      `}</style>
      <div className="panel">
        <div className="title">状态信息（步骤 {logs[0]?.step || '-'}）</div>
        {logs.length === 0
          ? <div className="item">— 暂无当前步骤状态</div>
          : logs.map((l, i) => (
              <div key={i} className="item">— {l.message}</div>
            ))
        }
      </div>
    </>
  )
}

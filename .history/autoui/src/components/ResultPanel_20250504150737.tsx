import React from 'react'
import { saveAs } from 'file-saver'          // npm i file-saver
import Viewer3D from './Viewer3D'            // 👈 在线 3D 预览（下方新文件）

interface Props {
  disease: string
  decisionTarget:   any
  decisionPocket:   any
  decisionCompound: any
  moleculeImage: string | null
  dockingImage:  string | null
  modelPath:     string | null
  logs: any[]
}

export default function ResultPanel (p:Props) {
  /* 下载当前日志为 txt */
  const downloadLogs = () => {
    const blob = new Blob(
      p.logs.map(l=>`${l.step}.${l.category}: ${l.message}\n`),
      { type:'text/plain;charset=utf-8'}
    )
    saveAs(blob, `ProteinDance_${Date.now()}.log`)
  }

  return (
    <div style={{textAlign:'center'}}>
      <h2 style={{margin:'4px 0 16px'}}>🎉 流程完成</h2>

      {/* 关键信息卡片 */}
      <div style={{
        display:'grid',gap:16,gridTemplateColumns:'1fr 1fr',
        marginBottom:24
      }}>
        <InfoCard label="疾病"   value={p.disease} />
        <InfoCard label="靶点"   value={p.decisionTarget?.selected_option} />
        <InfoCard label="最佳口袋"
                  value={p.decisionPocket?.selected_option} />
        <InfoCard label="优化 SMILES"
                  value={p.decisionCompound?.optimized_smiles?.slice(0,60)+'…'} />
      </div>

      {/* 图片展示 */}
      {p.moleculeImage && (
        <img
          src={`data:image/png;base64,${p.moleculeImage}`}
          style={{width:'100%',borderRadius:8,marginBottom:16}}
        />
      )}
      {p.dockingImage && (
        <img
          src={`data:image/png;base64,${p.dockingImage}`}
          style={{width:'100%',borderRadius:8,marginBottom:16}}
        />
      )}

      {/* 在线 3D 预览 */}
      {p.modelPath && (
        <>
          <h3 style={{margin:'24px 0 8px'}}>🧩 在线查看蛋白质模型</h3>
          <Viewer3D pdbUrl={p.modelPath} />
        </>
      )}

      {/* 下载按钮区 */}
      <div style={{marginTop:32,display:'flex',gap:16,justifyContent:'center'}}>
        <button onClick={downloadLogs}>下载运行日志</button>
        {p.moleculeImage && (
          <a
            href={`data:image/png;base64,${p.moleculeImage}`}
            download="Molecule.png"
          >
            <button>下载分子图片</button>
          </a>
        )}
        {p.dockingImage && (
          <a
            href={`data:image/png;base64,${p.dockingImage}`}
            download="Docking.png"
          >
            <button>下载对接图片</button>
          </a>
        )}
      </div>
    </div>
  )
}

/* 简单信息卡片组件 */
function InfoCard({label,value}:{label:string,value:any}) {
  return (
    <div style={{
      padding:12,border:'1px solid #eee',borderRadius:8,background:'#fafafa'
    }}>
      <div style={{fontSize:12,color:'#999'}}>{label}</div>
      <div style={{fontWeight:600,wordBreak:'break-all'}}>{value||'—'}</div>
    </div>
  )
}

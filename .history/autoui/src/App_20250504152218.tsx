// src/App.tsx
import React, { useState } from 'react'
import WorkflowStepper from './components/WorkflowStepper'
import StatusPanel from './components/StatusPanel'
import DecisionPanel from './components/DecisionPanel'
import LogPanel from './components/LogPanel'
import HistoryPanel from './components/HistoryPanel'
import * as api from './services/api'
import ResultPanel from './components/ResultPanel.tsx'         // <-- 新增

// src/App.tsx


// 新增完成视图
interface CompletedData {
  disease: string
  target: string
  pocketImage?: string | null
  moleculeImage?: string | null
  dockingImage?: string | null
  resultFiles: { name: string; url: string }[]
  pdbUrl?: string | null
}

const CompletedView: React.FC<{ data: CompletedData }> = ({ data }) => {
  const viewerRef = useRef<HTMLDivElement>(null)
  const [viewerReady, setViewerReady] = useState(false)

  useEffect(() => {
    if (!data.pdbUrl || viewerReady) return
    // 动态加载 molstar
    const script = document.createElement('script')
    script.src = 'https://unpkg.com/molstar/build/viewer/molstar.js'
    script.onload = () => {
      // @ts-ignore
      const viewer = new window.MolStar.Plugin.Viewer(viewerRef.current, {
        layoutIsExpanded: false,
        layoutShowControls: false,
        layoutShowSequence: true,
        layoutShowLog: false
      })
      viewer.loadStructureFromUrl(data.pdbUrl)
      setViewerReady(true)
    }
    document.body.appendChild(script)
  }, [data.pdbUrl, viewerReady])

  return (
    <div style={{ maxWidth: 700, margin: '0 auto', padding: 32 }}>
      <h2 style={{ textAlign: 'center' }}>🎉 研发流程已完成</h2>
      <p style={{ marginTop: 16 }}>疾病: <strong>{data.disease}</strong></p>
      <p>最终选择靶点: <strong>{data.target}</strong></p>

      {data.pocketImage && (
        <>
          <h3>口袋预测</h3>
          <img src={`data:image/png;base64,${data.pocketImage}`} style={{ width: '100%', borderRadius: 8 }} />
        </>
      )}

      {data.moleculeImage && (
        <>
          <h3>优化化合物</h3>
          <img src={`data:image/png;base64,${data.moleculeImage}`} style={{ width: '100%', borderRadius: 8 }} />
        </>
      )}

      {data.dockingImage && (
        <>
          <h3>对接结果</h3>
          <img src={`data:image/png;base64,${data.dockingImage}`} style={{ width: '100%', borderRadius: 8 }} />
        </>
      )}

      {data.resultFiles.length > 0 && (
        <>
          <h3>下载结果文件</h3>
          <ul>
            {data.resultFiles.map(f => (
              <li key={f.url}><a href={f.url} download>{f.name}</a></li>
            ))}
          </ul>
        </>
      )}

      {data.pdbUrl && (
        <>
          <h3>在线查看蛋白质模型</h3>
          <div ref={viewerRef} style={{ height: 400, borderRadius: 8, overflow: 'hidden', background: '#f4f5f8' }} />
        </>
      )}
    </div>
  )}


interface LogEntry {
  step: number
  category: '状态' | '决策' | '日志'
  message: string
}

export default function App() {
  const [disease, setDisease] = useState('')
  const [step, setStep] = useState(0)
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [decisionTarget, setDecisionTarget] = useState<any>(null)
  const [decisionPocket, setDecisionPocket] = useState<any>(null)
  const [decisionCompound, setDecisionCompound] = useState<any>(null)
  const [moleculeImage, setMoleculeImage] = useState<string | null>(null)
  const [dockingImage, setDockingImage] = useState<string | null>(null)

  const addLog = (
    logStep: number,
    category: LogEntry['category'],
    message: string
  ) => {
    setLogs(prev => [...prev, { step: logStep, category, message }])
  }

  const handleStart = async () => {
    setStep(0)
    setLogs([])
    setDecisionTarget(null)
    setDecisionPocket(null)
    setDecisionCompound(null)
    setMoleculeImage(null)
    setDockingImage(null)

    try {
      // STEP 1: 靶点识别
      setStep(1)
      addLog(1, '状态', `调用 DeepSeek 获取潜在蛋白靶点：${disease}`)
      const tRes = await api.getDiseaseTargets(disease)
      addLog(1, '日志', JSON.stringify(tRes))
      if (!tRes.success) throw new Error(tRes.error)
      addLog(1, '状态', `DeepSeek 返回：${tRes.targets.join('、')}`)

      // STEP 2: AI 决策 选靶点
      addLog(2, '状态', 'AI 正在选择最佳靶点…')
      const td = await api.aiDecision({
        options: tRes.targets,
        context: `为疾病「${disease}」选择最合适的药物靶点。`,
        question: '哪个蛋白靶点最适合作为药物开发目标？'
      })
      addLog(2, '日志', JSON.stringify(td))
      if (!td.success) throw new Error(td.error)
      setDecisionTarget(td)
      addLog(2, '决策', `选择: ${td.selected_option} 理由: ${td.explanation}`)

      // STEP 3: UniProt 检索
      setStep(2)
      addLog(2, '状态', `查询 UniProt 条目：${td.selected_option}`)
      const uRes = await api.getUniprotEntries(td.selected_option)
      addLog(2, '日志', JSON.stringify(uRes))
      if (!uRes.success) throw new Error(uRes.error)
      addLog(2, '状态', `UniProt 返回：${uRes.entries.map(e => e.acc).join('、')}`)

      // STEP 4: 结构获取
      setStep(3)
      if (!uRes.entries || uRes.entries.length === 0) {
        addLog(3, '状态', '错误：未找到任何 UniProt 条目，请确认基因符号是否正确')
        return
      }
      const acc = uRes.entries[0].acc
      addLog(3, '状态', `获取 UniProt Accession：${acc}`)
      const sRes = await api.getStructureSources(acc)
      addLog(3, '日志', JSON.stringify(sRes))
      if (!sRes.success) throw new Error(sRes.error)
      const modelPath = (sRes as any).structure_path ?? (sRes as any).pdb_ids[0]
      addLog(3, '状态', `结构文件路径：${modelPath}`)

      // STEP 5: 口袋预测
      setStep(4)
      addLog(4, '状态', `预测结合口袋：${modelPath}`)
      const pRes = await api.predictPockets(modelPath)
      addLog(4, '日志', JSON.stringify(pRes))
      if (!pRes.success) throw new Error(pRes.error)
      addLog(4, '状态', `检测到 ${pRes.pockets.length} 个候选口袋`)

      // AI 决策 选口袋
      addLog(5, '状态', 'AI 正在选择最佳口袋…')
      const pocketOpts = pRes.pockets.map((p, i) => `#${i + 1} score=${p.score.toFixed(2)}`)
      const pd = await api.aiDecision({
        options: pocketOpts,
        context: `为蛋白 ${td.selected_option} 选择最佳结合口袋。`,
        question: '哪个口袋最优？'
      })
      addLog(5, '日志', JSON.stringify(pd))
      if (!pd.success) throw new Error(pd.error)
      setDecisionPocket(pd)
      addLog(5, '决策', `选择: ${pd.selected_option} 理由: ${pd.explanation}`)

      // STEP 6: 配体获取
      setStep(5)
      addLog(5, '状态', `获取候选配体：${acc}`)
      const lRes = await api.getLigands(acc)
      addLog(5, '日志', JSON.stringify(lRes))
      if (!lRes.success) throw new Error(lRes.error)
      const allSmiles = [...(lRes.custom_smiles || []), ...(lRes.chembl_smiles || [])]
      addLog(5, '状态', `共获取 ${allSmiles.length} 条 SMILES`)

      // STEP 7: 化合物优化
      setStep(6)
      addLog(6, '状态', 'AI 正在优化化合物…')
      const cd = await api.selectCompound({
        smiles_list: allSmiles,
        disease,
        protein: td.selected_option,
        pocket_center: pRes.pockets[pocketOpts.indexOf(pd.selected_option)].center
      })
      addLog(6, '日志', JSON.stringify(cd))
      if (!cd.success) throw new Error(cd.error)
      setDecisionCompound(cd)
      addLog(6, '决策', `优化后: ${cd.optimized_smiles} 理由: ${cd.explanation}`)

      // STEP 8: 分子图像
      setStep(7)
      addLog(7, '状态', '生成分子结构图…')
      const mi = await api.generateMoleculeImage(cd.optimized_smiles)
      addLog(7, '日志', JSON.stringify(mi))
      if (mi.success) setMoleculeImage(mi.image_data)

      // STEP 9: 对接可视化
      setStep(8)
      addLog(8, '状态', '生成蛋白-配体对接图…')
      const di = await api.generateDockingImage(
        modelPath,
        cd.optimized_smiles,
        pRes.pockets[pocketOpts.indexOf(pd.selected_option)].center
      )
      addLog(8, '日志', JSON.stringify(di))
      if (di.success) setDockingImage(di.image_data)

      // STEP 10: 完成
      setStep(10)
      addLog(10, '状态', '流程全部完成！')
    } catch (err: any) {
      addLog(step || 1, '状态', `🚨 出错：${err.message}`)
    }
  }

  const active = step > 0 && step < 10

  return (
    <>
      <style>{`
        body {
          margin: 0; padding: 0;
          background: #f0f2f7;
        }
        .wrapper {
          display: flex; justify-content: center;
          align-items: flex-start; padding: 40px; gap: 24px;
        }
        .app {
          position: relative;
          width: 100%; max-width: 800px;
          background: #fff; border-radius: 12px;
          box-shadow: 0 8px 24px rgba(0,0,0,0.1);
          padding: 32px; font-family: 'Segoe UI', sans-serif;
          border: 2px solid transparent;
          overflow: hidden; z-index: 1;
        }
        .app.active {
          animation: borderBreathe 2.5s ease-in-out infinite;
        }
        @keyframes borderBreathe {
          0%,100% {
            border-color: rgba(79,70,229,0.4);
            box-shadow: 0 0 0 0 rgba(79,70,229,0.4);
          }
          50% {
            border-color: rgba(79,70,229,1);
            box-shadow: 0 0 20px 6px rgba(79,70,229,0.3);
          }
        }

        /* 标题区域＋logo */
        .title-row {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-bottom: 24px;
        }

        .title-row h3 {
          margin: 4px 0 0;
          font-size: 16px;
          color: #666;
        }

        .logo-placeholder {
          width: 40px; height: 40px;
          background: #ccc; border-radius: 8px;
          margin-right: 12px;
          animation: pulseLogo 2s ease-in-out infinite;
        }
        @keyframes pulseLogo {
          0%,100% { opacity: 0.6; }
          50% { opacity: 1; }
        }
        h1 {
          margin: 0; font-size: 28px; color: #333;
          transition: color 0.3s;
        }

        /* 输入框 / 按钮 动画 */
        .input {
          display: flex; gap: 16px;
          justify-content: center; margin-bottom: 32px;
        }
        .input input {
          flex: 1; padding: 12px; font-size: 16px;
          border: 1px solid #ccc; border-radius: 8px;
          transition: border-color 0.3s, box-shadow 0.3s;
        }
        .input input:focus {
          border-color: #4f46e5;
          box-shadow: 0 0 0 3px rgba(79,70,229,0.2);
          outline: none;
        }
        .input button {
          background: #4f46e5; color: #fff; border: none;
          padding: 0 24px; border-radius: 8px; font-size: 16px;
          cursor: pointer;
          transition: transform 0.2s, box-shadow 0.2s;
        }
        .input button:hover {
          transform: translateY(-2px);
          box-shadow: 0 6px 12px rgba(0,0,0,0.1);
        }
        .input button:active {
          transform: translateY(0) scale(0.97);
        }
      `}</style>

      <div className="wrapper">
        <div className={`app${active ? ' active' : ''}`}>
          <div className="title-row">
            {/* <div className="logo-placeholder" /> */}
            <h1>Protein Dance</h1>
            <h3>基于DeepSeek的全自动制药智能体</h3>
          </div>

          {step === 0 ? (
            <div className="input">
              <input
                value={disease}
                placeholder="输入疾病名称"
                onChange={e => setDisease(e.target.value)}
              />
              <button onClick={handleStart}>开始</button>
            </div>
          ) : (
            <>
              <WorkflowStepper
                currentStep={step}
                stepLabels={[
                  '靶点识别','UniProt检索','结构获取','口袋预测',
                  '配体获取','化合物优化','分子图像','对接可视化','结果保存','完成'
                ]}
              />

              <StatusPanel logs={logs.filter(l => l.category === '状态' && l.step === step)} />
              <DecisionPanel logs={logs.filter(l => l.category === '决策')} />
              <LogPanel logs={logs.filter(l => l.category === '日志' && l.step === step)} />

              {moleculeImage && (
                <img
                  src={`data:image/png;base64,${moleculeImage}`}
                  style={{ width:'100%', borderRadius:8, margin:'24px 0' }}
                />
              )}
              {dockingImage && (
                <img
                  src={`data:image/png;base64,${dockingImage}`}
                  style={{ width:'100%', borderRadius:8, margin:'24px 0' }}
                />
              )}
            </>
          )}
        </div>

        <HistoryPanel logs={logs} />
      </div>
    </>
  )
}

import React, { useState } from 'react'
import WorkflowStepper   from './components/WorkflowStepper'
import StatusPanel       from './components/StatusPanel'
import DecisionPanel     from './components/DecisionPanel'
import LogPanel          from './components/LogPanel'
import HistoryPanel      from './components/HistoryPanel'
import ResultPanel       from './components/ResultPanel'   // 👈 新增
import * as api          from './services/api'

interface LogEntry {
  step: number
  category: '状态' | '决策' | '日志'
  message: string
}

export default function App() {
  const [disease,          setDisease]          = useState('')
  const [step,             setStep]             = useState(0)
  const [logs,             setLogs]             = useState<LogEntry[]>([])
  const [decisionTarget,   setDecisionTarget]   = useState<any>(null)
  const [decisionPocket,   setDecisionPocket]   = useState<any>(null)
  const [decisionCompound, setDecisionCompound] = useState<any>(null)
  const [moleculeImage,    setMoleculeImage]    = useState<string | null>(null)
  const [dockingImage,     setDockingImage]     = useState<string | null>(null)
  const [modelPath,        setModelPath]        = useState<string | null>(null) // 👈 for 3D viewer

  /* ---------- 日志工具 ---------- */
  const addLog = (
    logStep: number,
    category: LogEntry['category'],
    message: string
  ) => setLogs(prev => [...prev, { step: logStep, category, message }])

  /* ---------- 主流程 ---------- */
  const handleStart = async () => {
    // 重置
    setStep(0); setLogs([])
    setDecisionTarget(null); setDecisionPocket(null); setDecisionCompound(null)
    setMoleculeImage(null);  setDockingImage(null);    setModelPath(null)

    try {
      /* STEP‑1 ─ 靶点识别 */
      setStep(1)
      addLog(1,'状态',`调用 DeepSeek 获取潜在蛋白靶点：${disease}`)
      const tRes = await api.getDiseaseTargets(disease)
      addLog(1,'日志',JSON.stringify(tRes))
      if (!tRes.success) throw new Error(tRes.error)
      addLog(1,'状态',`DeepSeek 返回：${tRes.targets.join('、')}`)

      /* STEP‑2 ─ AI 决策选靶点 */
      setStep(2)
      addLog(2,'状态','AI 正在选择最佳靶点…')
      const td = await api.aiDecision({
        options:tRes.targets,
        context:`为疾病「${disease}」选择最合适的药物靶点。`,
        question:'哪个蛋白靶点最适合作为药物开发目标？'
      })
      addLog(2,'日志',JSON.stringify(td))
      if(!td.success) throw new Error(td.error)
      setDecisionTarget(td)
      addLog(2,'决策',`选择: ${td.selected_option} 理由: ${td.explanation}`)

      /* STEP‑3 ─ UniProt 检索 */
      setStep(3)
      addLog(3,'状态',`查询 UniProt 条目：${td.selected_option}`)
      const uRes = await api.getUniprotEntries(td.selected_option)
      addLog(3,'日志',JSON.stringify(uRes))
      if(!uRes.success) throw new Error(uRes.error)
      if(!uRes.entries.length) throw new Error('未找到 UniProt 条目')
      addLog(3,'状态',`UniProt 返回：${uRes.entries.map(e=>e.acc).join('、')}`)

      /* STEP‑4 ─ 结构获取 */
      setStep(4)
      const acc = uRes.entries[0].acc
      addLog(4,'状态',`获取结构来源：${acc}`)
      const sRes:any = await api.getStructureSources(acc)
      addLog(4,'日志',JSON.stringify(sRes))
      if(!sRes.success) throw new Error(sRes.error)
      const pdbFile = sRes.structure_path ?? sRes.pdb_ids[0]
      setModelPath(pdbFile)                          // 👈 保存以供 3D 预览
      addLog(4,'状态',`结构文件路径：${pdbFile}`)

      /* STEP‑5 ─ 口袋预测 */
      setStep(5)
      addLog(5,'状态',`预测结合口袋：${pdbFile}`)
      const pRes = await api.predictPockets(pdbFile)
      addLog(5,'日志',JSON.stringify(pRes))
      if(!pRes.success) throw new Error(pRes.error)
      addLog(5,'状态',`检测到 ${pRes.pockets.length} 个候选口袋`)

      /* STEP‑6 ─ AI 选口袋 */
      addLog(6,'状态','AI 正在选择最佳口袋…')
      const pocketOpts = pRes.pockets.map((p,i)=>`#${i+1} score=${p.score.toFixed(2)}`)
      const pd = await api.aiDecision({
        options:pocketOpts,
        context:`为蛋白 ${td.selected_option} 选择最佳结合口袋。`,
        question:'哪个口袋最优？'
      })
      addLog(6,'日志',JSON.stringify(pd))
      if(!pd.success) throw new Error(pd.error)
      setDecisionPocket(pd)
      addLog(6,'决策',`选择: ${pd.selected_option} 理由: ${pd.explanation}`)

      /* STEP‑7 ─ 配体获取 */
      setStep(7)
      addLog(7,'状态',`获取候选配体：${acc}`)
      const lRes = await api.getLigands(acc)
      addLog(7,'日志',JSON.stringify(lRes))
      if(!lRes.success) throw new Error(lRes.error)
      
      const allSmiles = [
  ...(lRes.custom_smiles || []),
  ...(lRes.chembl_smiles || [])
]
      addLog(7,'状态',`共获取 ${allSmiles.length} 条 SMILES`)

      /* STEP‑8 ─ 化合物优化 */
      setStep(8)
      addLog(8,'状态','AI 正在优化化合物…')
      const cd = await api.selectCompound({
        smiles_list:allSmiles,
        disease,
        protein:td.selected_option,
        pocket_center:pRes.pockets[pocketOpts.indexOf(pd.selected_option)].center
      })
      addLog(8,'日志',JSON.stringify(cd))
      if(!cd.success) throw new Error(cd.error)
      setDecisionCompound(cd)
      addLog(8,'决策',`优化后: ${cd.optimized_smiles} 理由: ${cd.explanation}`)

      /* STEP‑9 ─ 分子/对接图像 */
      setStep(9)
      addLog(9,'状态','生成分子结构图…')
      const mi = await api.generateMoleculeImage(cd.optimized_smiles)
      if(mi.success) setMoleculeImage(mi.image_data)
      addLog(9,'日志',JSON.stringify(mi))

      addLog(9,'状态','生成蛋白-配体对接图…')
      const di = await api.generateDockingImage(
        pdbFile, cd.optimized_smiles,
        pRes.pockets[pocketOpts.indexOf(pd.selected_option)].center
      )
      if(di.success) setDockingImage(di.image_data)
      addLog(9,'日志',JSON.stringify(di))

      /* STEP‑10 ─ 完成 */
      setStep(10)
      addLog(10,'状态','流程全部完成！')
    } catch(err:any){
      addLog(step||1,'状态',`🚨 出错：${err.message}`)
      setStep(10)   // 直接进入完成页，方便查看日志
    }
  }

  const active = step>0 && step<10

  /* ---------- UI 渲染 ---------- */
  return (
    <>
      {/* —— 样式同之前 —— */}
      {/* …（为节省篇幅，样式块保留不变） … */}

      <div className="wrapper">
        <div className={`app${active ? ' active' : ''}`}>
          <div className="title-row">
            <h1>Protein Dance</h1>
            <h3>基于DeepSeek的全自动制药智能体</h3>
          </div>

          {step === 0 ? (
            /* —— 初始输入 —— */
            <div className="input">
              <input
                value={disease}
                placeholder="输入疾病名称"
                onChange={e=>setDisease(e.target.value)}
              />
              <button onClick={handleStart}>开始</button>
            </div>
          ) : step < 10 ? (
            /* —— 流程进行中 —— */
            <>
              <WorkflowStepper
                currentStep={step}
                stepLabels={[
                  '靶点识别','AI选靶点','UniProt检索','结构获取',
                  '口袋预测','AI选口袋','配体获取','化合物优化',
                  '结果渲染','完成'
                ]}
              />

              <StatusPanel   logs={logs.filter(l=>l.category==='状态' && l.step===step)} />
              <DecisionPanel logs={logs.filter(l=>l.category==='决策')} />
              <LogPanel      logs={logs.filter(l=>l.category==='日志'  && l.step===step)} />
            </>
          ) : (
            /* —— 完成界面 —— */
            <ResultPanel
              disease          ={disease}
              decisionTarget   ={decisionTarget}
              decisionPocket   ={decisionPocket}
              decisionCompound ={decisionCompound}
              moleculeImage    ={moleculeImage}
              dockingImage     ={dockingImage}
              modelPath        ={modelPath}  // 👈 for 3D 预览
              logs             ={logs}
            />
          )}
        </div>

        <HistoryPanel logs={logs} />
      </div>
    </>
  )
}

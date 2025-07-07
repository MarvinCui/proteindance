import React, { useState } from 'react'
import WorkflowStepper from './components/WorkflowStepper'
import StatusPanel from './components/StatusPanel'
import DecisionPanel from './components/DecisionPanel'
import LogPanel from './components/LogPanel'
import SidePanel from './components/SidePanel'
import InnovationSlider from './components/InnovationSlider'
import * as api from './services/api'
import ResultPanel from './components/ResultPanel'
import { TargetWithScore } from './services/api'

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
  // 已移除 dockingImage 状态
  const [workflowState, setWorkflowState] = useState<any>(null)
  const [innovationLevel, setInnovationLevel] = useState(5)
  // 更新状态存储包含创新度的靶点列表
  const [allTargets, setAllTargets] = useState<TargetWithScore[]>([])
  // 新增状态记录已尝试的靶点
  const [triedTargets, setTriedTargets] = useState<string[]>([])
  // 记录靶点解释
  const [targetExplanation, setTargetExplanation] = useState<string | null>(null)
  // 分离记录选择理由和优化解释
  const [selectionReason, setSelectionReason] = useState<string | null>(null)
  const [optimizationExplanation, setOptimizationExplanation] = useState<string | null>(null)
  // 新增状态用于实时结构显示
  const [currentStructurePath, setCurrentStructurePath] = useState<string | null>(null)
  const [currentPocketCenter, setCurrentPocketCenter] = useState<[number, number, number] | null>(null)
  const [currentProteinName, setCurrentProteinName] = useState<string>('蛋白质结构')
  // 新增配体状态
  const [currentLigandSmiles, setCurrentLigandSmiles] = useState<string[] | null>(null)
  const [currentOptimizedSmiles, setCurrentOptimizedSmiles] = useState<string | null>(null)

  const addLog = (
    logStep: number,
    category: LogEntry['category'],
    message: string
  ) => {
    setLogs(prev => [...prev, { step: logStep, category, message }])
  }

  // 新增函数：尝试获取UniProt条目
  const tryGetUniprotEntry = async (target: string) => {
    addLog(2, '状态', `查询 UniProt 条目：${target}`)
    const uRes = await api.getUniprotEntries(target)
    addLog(2, '日志', JSON.stringify(uRes))
    
    // 记录已尝试的靶点
    setTriedTargets(prev => [...prev, target])
    
    return uRes
  }

  // 更新函数：获取下一个未尝试的靶点，优先选择创新度相近的
  const getNextTarget = () => {
    // 过滤出未尝试的靶点
    const remaining = allTargets.filter(t => !triedTargets.includes(t.symbol))
    if (remaining.length === 0) return null
    
    // 按创新度与用户请求的创新度接近程度排序
    const sorted = [...remaining].sort((a, b) => {
      const diffA = Math.abs(a.innovation_score - innovationLevel)
      const diffB = Math.abs(b.innovation_score - innovationLevel)
      return diffA - diffB
    })
    
    // 返回创新度最接近的靶点
    return sorted[0]
  }

  const handleStart = async () => {
    setStep(0)
    setLogs([])
    setDecisionTarget(null)
    setDecisionPocket(null)
    setDecisionCompound(null)
    setMoleculeImage(null)
    setWorkflowState(null)
    // 重置靶点状态
    setAllTargets([])
    setTriedTargets([])
    // 重置结构显示状态
    setCurrentStructurePath(null)
    setCurrentPocketCenter(null)
    setCurrentProteinName('蛋白质结构')
    // 重置配体状态
    setCurrentLigandSmiles(null)
    setCurrentOptimizedSmiles(null)

    try {
      // STEP 1: 靶点识别
      setStep(1)
      addLog(1, '状态', `调用 DeepSeek 获取潜在蛋白靶点：${disease}（创新度：${innovationLevel}）`)
      const tRes = await api.getDiseaseTargets(disease, innovationLevel)
      addLog(1, '日志', JSON.stringify(tRes))
      if (!tRes.success) throw new Error(tRes.error)
      
      // 存储靶点列表（包含创新度）
      setAllTargets(tRes.targets_with_scores || [])
      
      // 展示靶点及其创新度
      const targetDisplay = tRes.targets_with_scores 
        ? tRes.targets_with_scores.map((t: TargetWithScore) => `${t.symbol}[创新度:${t.innovation_score}]`).join('、')
        : tRes.targets.join('、')
      
      addLog(1, '状态', `DeepSeek 返回：${targetDisplay}`)

      // STEP 2: AI 决策 选靶点
      addLog(2, '状态', 'AI 正在选择最佳靶点…')
      
      // 使用包含创新度的选项
      const targetOptions = tRes.targets_with_scores
        ? tRes.targets_with_scores.map((t: TargetWithScore) => `${t.symbol} [创新度:${t.innovation_score}]`)
        : tRes.targets
      
      const td = await api.aiDecision({
        options: targetOptions,
        context: `为疾病「${disease}」选择最合适的药物靶点，考虑用户指定的创新度(${innovationLevel}/10)。`,
        question: '哪个蛋白靶点最适合作为药物开发目标？'
      })
      
      addLog(2, '日志', JSON.stringify(td))
      if (!td.success) throw new Error(td.error)
      
      // 从选择的选项中提取基因符号
      const selectedSymbol = td.selected_option.split(' ')[0]
      
      // 更新决策目标，只保存基因符号部分
      const updatedDecision = {
        ...td,
        selected_option: selectedSymbol,
        raw_selected_option: td.selected_option  // 保存原始选择
      }
      
      setDecisionTarget(updatedDecision)
      addLog(2, '决策', `选择: ${td.selected_option} 理由: ${td.explanation}`)

      // 获取靶点解释
      try {
        const prompt = `请简要介绍${selectedSymbol}蛋白在${disease}疾病中的作用机制，包括它的功能和为什么是有价值的药物靶点（80-120字）`
        const targetInfoRes = await api.getTargetExplanation(selectedSymbol, disease)
        if (targetInfoRes.success && targetInfoRes.explanation) {
          setTargetExplanation(targetInfoRes.explanation)
          addLog(2, '决策', `靶点分析: ${targetInfoRes.explanation}`)
        }
      } catch (error) {
        console.log("获取靶点解释失败:", error)
      }

      // STEP 3: UniProt 检索 - 尝试首选靶点
      setStep(2)
      let currentTarget = selectedSymbol
      let uRes = await tryGetUniprotEntry(currentTarget)
      
      // 如果未找到UniProt条目，尝试其他靶点
      while (!uRes.success || !uRes.entries || uRes.entries.length === 0) {
        // 获取下一个未尝试的靶点
        const nextTargetObj = getNextTarget()
        if (!nextTargetObj) {
          addLog(2, '状态', '普通靶点查询失败，尝试获取已验证的UniProt靶点...')
          
          // 所有靶点都尝试失败，使用我们的新API获取已验证靶点
          try {
            const verifiedRes = await api.getVerifiedTarget(disease)
            if (verifiedRes.success) {
              addLog(2, '状态', `已获取已验证的替代靶点: ${verifiedRes.symbol}[创新度:${verifiedRes.innovation_score}]`)
              
              // 更新靶点列表
              setAllTargets(prev => [...prev, {
                symbol: verifiedRes.symbol,
                innovation_score: verifiedRes.innovation_score
              }])
              
              // 更新决策靶点
              setDecisionTarget({
                ...updatedDecision,
                selected_option: verifiedRes.symbol,
                innovation_score: verifiedRes.innovation_score,
                fallback: true
              })
              
              addLog(2, '决策', `更换为已验证靶点: ${verifiedRes.symbol}[创新度:${verifiedRes.innovation_score}] (UniProt: ${verifiedRes.uniprot_acc})`)
              
              // 使用验证过的UniProt条目
              uRes = {
                success: true,
                entries: verifiedRes.entries
              }
              
              // 记录这个靶点已尝试
              setTriedTargets(prev => [...prev, verifiedRes.symbol])
              
              break // 跳出循环，使用这个已验证的靶点
            } else {
              addLog(2, '状态', `错误：无法获取已验证靶点 - ${verifiedRes.error}`)
              addLog(2, '状态', '错误：所有靶点都无法在UniProt中找到匹配项')
              return
            }
          } catch (error) {
            addLog(2, '状态', `错误：获取已验证靶点时发生异常 - ${error}`)
            addLog(2, '状态', '错误：所有靶点都无法在UniProt中找到匹配项')
            return
          }
        }
        
        const nextTarget = nextTargetObj.symbol
        const nextScore = nextTargetObj.innovation_score
        
        addLog(2, '状态', `未找到${currentTarget}的UniProt条目，尝试下一个靶点：${nextTarget}[创新度:${nextScore}]`)
        currentTarget = nextTarget
        
        // 更新决策靶点
        setDecisionTarget({
          ...updatedDecision, 
          selected_option: currentTarget,
          innovation_score: nextScore
        })
        
        addLog(2, '决策', `更换靶点为: ${currentTarget}[创新度:${nextScore}]`)
        
        // 尝试新靶点
        uRes = await tryGetUniprotEntry(currentTarget)
      }
      
      addLog(2, '状态', `UniProt 返回：${uRes.entries.map((e: { acc: string; name: string }) => e.acc).join('、')}`)

      // STEP 4: 结构获取
      setStep(3)
      const acc = uRes.entries[0].acc
      addLog(3, '状态', `获取 UniProt Accession：${acc}`)
      const sRes = await api.getStructureSources(acc)
      addLog(3, '日志', JSON.stringify(sRes))
      if (!sRes.success) throw new Error(sRes.error)
      const modelPath = (sRes as any).structure_path ?? (sRes as any).pdb_ids[0]
      addLog(3, '状态', `结构文件路径：${modelPath}`)
      setWorkflowState({ uniprot_acc: acc, structure_path: modelPath })
      
      // 立即显示结构
      setCurrentStructurePath(modelPath)
      setCurrentProteinName(`${currentTarget} 蛋白质`)

      // STEP 5: 口袋预测
      setStep(4)
      addLog(4, '状态', `预测结合口袋：${modelPath}`)
      const pRes = await api.predictPockets(modelPath)
      addLog(4, '日志', JSON.stringify(pRes))
      if (!pRes.success) throw new Error(pRes.error)
      
      // 检查是否找到了口袋
      if (!pRes.pockets || pRes.pockets.length === 0) {
        throw new Error('未检测到合适的结合口袋，请尝试使用其他蛋白结构')
      }
      
      addLog(4, '状态', `检测到 ${pRes.pockets.length} 个候选口袋`)

      // AI 决策 选口袋
      addLog(5, '状态', 'AI 正在选择最佳口袋…')
      const pocketOpts = pRes.pockets.map((p: { center: [number, number, number]; score: number }, i: number) => `#${i + 1} score=${p.score.toFixed(2)}`)
      const pd = await api.aiDecision({
        options: pocketOpts,
        context: `为蛋白 ${currentTarget} 选择最佳结合口袋。`,
        question: '哪个口袋最优？'
      })
      addLog(5, '日志', JSON.stringify(pd))
      if (!pd.success) throw new Error(pd.error)
      
      // 安全地查找选择的口袋
      const selectedIndex = pocketOpts.indexOf(pd.selected_option)
      if (selectedIndex === -1 || selectedIndex >= pRes.pockets.length) {
        throw new Error(`选择的口袋索引无效: ${pd.selected_option}`)
      }
      const selectedPocket = pRes.pockets[selectedIndex]
      
      setDecisionPocket({ ...pd, pocket_center: selectedPocket.center })
      addLog(5, '决策', `选择: ${pd.selected_option} 理由: ${pd.explanation}`)
      
      // 更新结构显示，包含口袋中心
      setCurrentPocketCenter(selectedPocket.center)

      // STEP 6: 配体获取
      setStep(5)
      addLog(5, '状态', `获取候选配体：${acc}`)
      const lRes = await api.getLigands(acc, undefined, disease)
      addLog(5, '日志', JSON.stringify(lRes))
      if (!lRes.success) throw new Error(lRes.error)
      
      // 收集所有来源的SMILES
      let allSmiles: string[] = []
      let hasAiGenerated = false
      
      // 常规数据库配体
      if (lRes.custom_smiles) {
        allSmiles = [...allSmiles, ...lRes.custom_smiles]
      }
      if (lRes.chembl_smiles) {
        allSmiles = [...allSmiles, ...lRes.chembl_smiles]
        addLog(5, '状态', `从ChEMBL数据库获取了${lRes.chembl_smiles.length}个配体`)
      }
      
      // AI生成的配体
      if (lRes.ai_generated_smiles) {
        hasAiGenerated = true
        allSmiles = [...allSmiles, ...lRes.ai_generated_smiles]
        
        // 显示这些是AI生成的配体
        addLog(5, '状态', `🤖 AI生成了${lRes.ai_generated_smiles.length}个配体（未在数据库中找到现有配体）`)
        
        // 显示生成理由
        if (lRes.ai_generated_full && lRes.ai_generated_full.length > 0) {
          lRes.ai_generated_full.forEach((item: any, index: number) => {
            addLog(5, '决策', `🤖 AI生成配体 #${index+1}: ${item.smiles.substring(0, 30)}... 设计理由: ${item.reason}`)
          })
        }
      }
      
      if (allSmiles.length === 0) {
        throw new Error("无法获取或生成任何配体")
      }
      
      addLog(5, '状态', `共获取 ${allSmiles.length} 条 SMILES${hasAiGenerated ? ' (包含AI生成)' : ''}`)
      
      // 更新配体状态，触发实时显示
      setCurrentLigandSmiles(allSmiles)

      // STEP 7: 化合物优化
      setStep(6)
      addLog(6, '状态', 'AI 正在优化化合物…')
      const cd = await api.selectCompound({
        smiles_list: allSmiles,
        disease,
        protein: currentTarget,
        pocket_center: selectedPocket.center
      })
      addLog(6, '日志', JSON.stringify(cd))
      if (!cd.success) throw new Error(cd.error)
      setDecisionCompound(cd)
      
      // 更新优化化合物状态，触发实时显示
      setCurrentOptimizedSmiles(cd.optimized_smiles)

      // 改进解释显示 - 分别显示选择理由和优化解释
      if (cd.explanation) {
        // 尝试从返回的解释中解析出选择理由和优化解释
        const selectReasonMatch = cd.explanation.match(/选择理由:\s*(.*?)(?=\n\n优化解释:|$)/s);
        const optimizeExplainMatch = cd.explanation.match(/优化解释:\s*(.*?)$/s);
        
        const selectReason = selectReasonMatch ? selectReasonMatch[1].trim() : "未提供选择理由";
        const optimizeExplain = optimizeExplainMatch ? optimizeExplainMatch[1].trim() : "未提供优化解释";
        
        // 保存到状态中供结果面板使用
        setSelectionReason(selectReason);
        setOptimizationExplanation(optimizeExplain);
        
        // 添加两条单独的日志，更清晰地展示
        addLog(6, '决策', `选择理由: ${selectReason}`);
        addLog(6, '决策', `优化解释: ${optimizeExplain}`);
        
        // 仅添加优化后的SMILES信息日志
        addLog(6, '状态', `优化后的SMILES: ${cd.optimized_smiles}`);
      } else {
        // 兼容旧格式
        addLog(6, '决策', `优化后: ${cd.optimized_smiles} 理由: ${cd.explanation || "未提供"}`);
      }

      // STEP 8: 分子图像
      setStep(7)
      addLog(7, '状态', '生成分子结构图…')
      const mi = await api.generateMoleculeImage(cd.optimized_smiles)
      addLog(7, '日志', JSON.stringify(mi))
      if (mi.success) setMoleculeImage(mi.image_data)

      // 最后一步：结果保存
      setStep(8)
      addLog(8, '状态', '结果保存中...')
      // 在这里可以添加保存数据逻辑
      addLog(8, '状态', '流程全部完成！')
    } catch (err: any) {
      addLog(step || 1, '状态', `🚨 出错：${err.message}`)
    }
  }

  const active = step > 0 && step < 8

  return (
    <>
      <style>{`
        body {
          margin: 0; padding: 0;
          background: #f0f2f7;
        }
        .wrapper {
          display: flex; justify-content: center;
          align-items: stretch; padding: 20px; gap: 24px;
          min-height: 100vh;
          max-width: 1400px;
          margin: 0 auto;
        }
        .app {
          position: relative;
          flex: 1;
          background: #fff; border-radius: 12px;
          box-shadow: 0 8px 24px rgba(0,0,0,0.1);
          padding: 32px; font-family: 'Segoe UI', sans-serif;
          border: 2px solid transparent;
          overflow: hidden; z-index: 1;
          height: fit-content;
          align-self: flex-start;
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
        
        .designer-credit {
          margin-top: 6px;
          font-size: 12px;
          color: #9CA3AF;
          font-weight: 500;
          letter-spacing: 0.05em;
          text-transform: uppercase;
          background: linear-gradient(90deg, #6366F1 0%, #8B5CF6 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          opacity: 0.85;
          text-align: center;
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
          height: 44px; /* Explicitly set height */
        }
        .input button:hover {
          transform: translateY(-2px);
          box-shadow: 0 6px 12px rgba(0,0,0,0.1);
        }
        .input button:active {
          transform: translateY(0) scale(0.97);
        }

        /* 侧边栏样式 */
        .side-panel {
          width: 380px;
          flex-shrink: 0;
          height: 100vh;
          max-height: 100vh;
          overflow: hidden;
          display: flex;
          flex-direction: column;
          align-self: stretch;
        }

        /* Responsive adjustments */
        @media (max-width: 1200px) { /* Large tablet */
          .wrapper {
            flex-direction: column;
            gap: 20px;
          }
          .side-panel {
            width: 100%;
            order: 2;
          }
        }

        @media (max-width: 768px) { /* Tablet and smaller */
          .wrapper {
            padding: 15px;
            gap: 16px;
          }
          .app {
            padding: 20px;
          }
          .input {
            flex-direction: row; /* Keep horizontal layout for all screens */
            gap: 12px;
            align-items: center;
          }
          .input input {
            flex: 1;
            font-size: 15px; /* Slightly smaller font */
            min-width: 0; /* Allow input to shrink if needed */
          }
          .input button {
            width: auto; /* Auto width based on content */
            font-size: 15px; /* Slightly smaller font */
          }
          .title-row h1 {
            font-size: 24px; /* Slightly smaller h1 */
          }
          .title-row h3 {
            font-size: 14px; /* Slightly smaller h3 */
          }
        }

        @media (max-width: 480px) { /* Mobile phones */
          .wrapper {
            padding: 10px;
            flex-direction: column;
            gap: 15px;
          }
          .app {
            padding: 15px;
          }
          .side-panel {
            width: 100%;
            order: 2;
          }
          .title-row h1 {
            font-size: 20px; 
          }
          .title-row h3 {
            font-size: 13px;
          }
          .input {
            width: 100%;
            flex-direction: row; /* Keep horizontal layout */
            align-items: center;
            gap: 8px; /* Smaller gap on mobile */
          }
          .input input {
            flex: 1; /* Input takes available space */
            min-width: 0; /* Allow input to shrink if needed */
          }
          .input button {
            width: auto; /* Auto width based on content */
            padding: 0 12px; /* Less horizontal padding */
            height: 40px; /* Slightly shorter than desktop */
            font-size: 14px;
            white-space: nowrap; /* Prevent button text from wrapping */
          }
          /* Further adjustments for panels if needed */
        }
      `}</style>

      <div className="wrapper">
        <div className={`app${active ? ' active' : ''}`}>
          <div className="title-row">
            <h1>Protein Dance</h1>
            <h3>基于DeepSeek的全自动制药智能体</h3>
            <div className="designer-credit">Designed by Zhenxiong W. & Boran C. Guided by Dr Lingfang T. in Biochemphysics</div>
          </div>

          {step === 0 ? (
            <>
              <div className="input">
                <input
                  value={disease}
                  placeholder="输入疾病名称"
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setDisease(e.target.value)}
                />
                <button onClick={handleStart}>开始</button>
              </div>
              <InnovationSlider 
                value={innovationLevel}
                onChange={setInnovationLevel}
              />
            </>
          ) : step === 8 ? (
            <>
              <WorkflowStepper
                currentStep={step}
              />
              <ResultPanel
                disease={disease}
                geneSymbol={decisionTarget?.selected_option || ''}
                uniprotAcc={workflowState?.uniprot_acc}
                pocketCenter={decisionPocket?.pocket_center || null}
                optimizedSmiles={decisionCompound?.optimized_smiles || null}
                explanation={decisionCompound?.explanation || null}
                selectionReason={selectionReason}
                optimizationExplanation={optimizationExplanation}
                moleculeImage={moleculeImage}
                structurePath={workflowState?.structure_path}
                targetExplanation={targetExplanation}
              />
            </>
          ) : (
            <>
              <WorkflowStepper
                currentStep={step}
              />
              <StatusPanel logs={logs.filter(l => l.category === '状态' && l.step === step)} />
              <DecisionPanel logs={logs.filter(l => l.category === '决策')} />
              <LogPanel logs={logs.filter(l => l.category === '日志' && l.step === step)} />
            </>
          )}
        </div>

        <div className="side-panel">
          <SidePanel 
            logs={logs} 
            structurePath={currentStructurePath}
            pocketCenter={currentPocketCenter}
            currentStep={step}
            proteinName={currentProteinName}
            ligandSmiles={currentLigandSmiles}
            optimizedSmiles={currentOptimizedSmiles}
          />
        </div>
      </div>
    </>
  )
}
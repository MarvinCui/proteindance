import React, { useState, useEffect, useCallback, useRef } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import WorkflowStepper from './components/WorkflowStepper'
import StatusPanel from './components/StatusPanel'
import DecisionPanel from './components/DecisionPanel'
import LogPanel from './components/LogPanel'
import SidePanel from './components/SidePanel'
import InnovationSlider from './components/InnovationSlider'
import { api } from './services/api'
import ResultPanel from './components/ResultPanel'
import { TargetWithScore } from './services/api'
import { SessionHistory } from './components/SessionHistory'
import { Session, SessionData } from './services/api.types'
import { ApiConfigPanel } from './components/ApiConfigPanel'
import authService, { User } from './services/authService'
import VerifyEmail from './pages/VerifyEmail'
import ResetPassword from './pages/ResetPassword'
import DockingConfirmationModal from './components/DockingConfirmationModal'
import DockingProgressTracker from './components/DockingProgressTracker'

interface LogEntry {
  step: number
  category: '状态' | '决策' | '日志' | '错误' | '警告' | '调试'
  message: string
}

function MainApp() {
  const [disease, setDisease] = useState('')
  const [step, setStep] = useState(0)
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [decisionTarget, setDecisionTarget] = useState<any>(null)
  const [decisionPocket, setDecisionPocket] = useState<any>(null)
  const [decisionCompound, setDecisionCompound] = useState<any>(null)
  const [moleculeImage, setMoleculeImage] = useState<string | null>(null)
  const [originalMoleculeImage, setOriginalMoleculeImage] = useState<string | null>(null)
  const [dockingImage, setDockingImage] = useState<string | null>(null)
  const [workflowState, setWorkflowState] = useState<any>(null)
  // 添加同步状态跟踪ref，解决React异步更新问题
  const workflowStateRef = useRef<any>(null)
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
  // 科学分析解释
  const [scientificAnalysis, setScientificAnalysis] = useState<string | null>(null)
  // 新增状态用于实时结构显示
  const [currentStructurePath, setCurrentStructurePath] = useState<string | null>(null)
  const [currentPocketCenter, setCurrentPocketCenter] = useState<[number, number, number] | null>(null)
  const [currentProteinName, setCurrentProteinName] = useState<string>('蛋白质结构')
  // 新增配体状态
  const [currentLigandSmiles, setCurrentLigandSmiles] = useState<string[] | null>(null)
  // API配置面板状态
  const [showConfigPanel, setShowConfigPanel] = useState(false)
  const [currentOptimizedSmiles, setCurrentOptimizedSmiles] = useState<string | null>(null)
  // 新增AlphaFold指示灯状态
  const [isUsingAlphaFold, setIsUsingAlphaFold] = useState<boolean>(false)
  // Session Management State
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)
  // 认证状态
  const [user, setUser] = useState<User | null>(null)
  // 分子对接状态
  const [dockingResult, setDockingResult] = useState<any>(null)
  const [dockingVisualization, setDockingVisualization] = useState<any>(null)
  // 分子对接确认和进度状态
  const [showDockingModal, setShowDockingModal] = useState(false)
  const [showDockingProgress, setShowDockingProgress] = useState(false)
  const [dockingParams, setDockingParams] = useState<any>(null)
  const [shouldSkipDocking, setShouldSkipDocking] = useState(false)

  // 认证初始化
  useEffect(() => {
    const initAuth = async () => {
      if (authService.isAuthenticated()) {
        try {
          const result = await authService.getCurrentUserInfo()
          if (result.success) {
            setUser(result.user!)
          } else {
            // 令牌可能已过期，清除认证信息
            authService.logout()
          }
        } catch (error) {
          console.error('获取用户信息失败:', error)
          authService.logout()
        }
      }
    }
    
    initAuth()
  }, [])

  // 注销处理
  const handleLogout = () => {
    authService.logout()
    setUser(null)
    // 可选：清除当前会话状态
    handleNewSession()
  }

  // Function to save the current state - 使用useCallback确保稳定性
  const saveCurrentSession = useCallback(async () => {
    const sessionData: SessionData = {
      disease,
      step,
      logs,
      decisionTarget,
      decisionPocket,
      decisionCompound,
      moleculeImage: moleculeImage || undefined,
      originalMoleculeImage: originalMoleculeImage || undefined,
      workflowState: workflowStateRef.current, // 使用ref获取最新状态
      innovationLevel,
      allTargets,
      triedTargets,
      targetExplanation: targetExplanation || undefined,
      selectionReason: selectionReason || undefined,
      optimizationExplanation: optimizationExplanation || undefined,
      scientificAnalysis: scientificAnalysis || undefined,
      currentStructurePath: currentStructurePath || undefined,
      currentPocketCenter: currentPocketCenter || undefined,
      currentProteinName,
      currentLigandSmiles: currentLigandSmiles || undefined,
      currentOptimizedSmiles: currentOptimizedSmiles || undefined,
      isUsingAlphaFold,
      dockingResult: dockingResult || undefined,
      dockingVisualization: dockingVisualization || undefined,
      dockingImage: dockingImage || undefined,
    };
    try {
      const savedSession = await api.saveSession(sessionData, currentSessionId || undefined);
      if (!currentSessionId) {
        setCurrentSessionId(savedSession.id);
      }
      addLog(step, '日志', `Session state saved with ID: ${savedSession.id}`)
    } catch (error) {
      console.error("Failed to save session:", error);
      addLog(step, '状态', '🚨 Error saving session state.')
    }
  }, [step, disease, logs, decisionTarget, decisionPocket, decisionCompound, moleculeImage, originalMoleculeImage, innovationLevel, allTargets, triedTargets, targetExplanation, selectionReason, optimizationExplanation, scientificAnalysis, currentStructurePath, currentPocketCenter, currentProteinName, currentLigandSmiles, currentOptimizedSmiles, isUsingAlphaFold, dockingResult, dockingVisualization, dockingImage, currentSessionId]);

  // 使用ref跟踪workflowState更新
  // workflowStateRef已在上面声明，这里同步更新
  workflowStateRef.current = workflowState;

  // Effect to save state whenever a major step changes - 移除workflowState依赖避免循环触发
  useEffect(() => {
    if (step > 0) { // Only save after the process has started
      // 延迟保存确保状态更新完成
      const saveTimer = setTimeout(() => {
        saveCurrentSession();
      }, 200);
      return () => clearTimeout(saveTimer);
    }
  }, [step, decisionTarget, decisionPocket, decisionCompound]); // 移除 workflowState 依赖

  const handleSessionSelect = (session: Session) => {
    setCurrentSessionId(session.id);
    const data = session.session_data;
    setDisease(data.disease || '');
    setStep(data.step || 0);
    setLogs(data.logs || []);
    setDecisionTarget(data.decisionTarget || null);
    setDecisionPocket(data.decisionPocket || null);
    setDecisionCompound(data.decisionCompound || null);
    setMoleculeImage(data.moleculeImage || null);
    setOriginalMoleculeImage(data.originalMoleculeImage || null);
    setWorkflowState(data.workflowState || null);
    setInnovationLevel(data.innovationLevel || 5);
    setAllTargets(data.allTargets || []);
    setTriedTargets(data.triedTargets || []);
    setTargetExplanation(data.targetExplanation || null);
    setSelectionReason(data.selectionReason || null);
    setOptimizationExplanation(data.optimizationExplanation || null);
    setScientificAnalysis(data.scientificAnalysis || null);
    setCurrentStructurePath(data.currentStructurePath || null);
    setCurrentPocketCenter(data.currentPocketCenter || null);
    setCurrentProteinName(data.currentProteinName || '蛋白质结构');
    setCurrentLigandSmiles(data.currentLigandSmiles || null);
    setCurrentOptimizedSmiles(data.currentOptimizedSmiles || null);
    setIsUsingAlphaFold(data.isUsingAlphaFold || false);
    setDockingResult(data.dockingResult || null);
    setDockingVisualization(data.dockingVisualization || null);
    setDockingImage(data.dockingImage || null);
  };

  const handleNewSession = () => {
    setCurrentSessionId(null);
    setDisease('');
    setStep(0);
    setLogs([]);
    setDecisionTarget(null);
    setDecisionPocket(null);
    setDecisionCompound(null);
    setMoleculeImage(null);
    setOriginalMoleculeImage(null);
    setWorkflowState(null);
    workflowStateRef.current = null; // 同时清理ref
    setInnovationLevel(5);
    setAllTargets([]);
    setTriedTargets([]);
    setTargetExplanation(null);
    setSelectionReason(null);
    setOptimizationExplanation(null);
    setScientificAnalysis(null);
    setCurrentStructurePath(null);
    setCurrentPocketCenter(null);
    setCurrentProteinName('蛋白质结构');
    setCurrentLigandSmiles(null);
    setCurrentOptimizedSmiles(null);
    setIsUsingAlphaFold(false);
    setDockingResult(null);
    setDockingVisualization(null);
    setDockingImage(null);
    // 重置对接模态框状态
    setShowDockingModal(false);
    setShowDockingProgress(false);
    setDockingParams(null);
    setShouldSkipDocking(false);
  };

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

  // 异步延迟函数，允许UI更新
  const asyncDelay = (ms: number = 100) => new Promise(resolve => setTimeout(resolve, ms))

  const handleStart = async () => {
    // 防止重复执行
    if (step > 0) {
      addLog(0, '警告', '工作流正在执行中，请勿重复点击开始')
      return
    }
    
    setStep(0)
    setLogs([])
    setDecisionTarget(null)
    setDecisionPocket(null)
    setDecisionCompound(null)
    setMoleculeImage(null)
    setOriginalMoleculeImage(null)
    
    // 改进的状态管理: 更加谨慎的清理逻辑
    const existingWorkflowState = workflowStateRef.current || workflowState
    
    if (existingWorkflowState?.structure_path && existingWorkflowState?.uniprot_acc) {
      // 验证保留的状态是否与当前疾病匹配
      if (disease && existingWorkflowState.disease && existingWorkflowState.disease !== disease) {
        addLog(0, '状态', `检测到疾病变化 (${existingWorkflowState.disease} → ${disease})，清理旧状态`)
        setWorkflowState(null)
        workflowStateRef.current = null
        setCurrentStructurePath(null)
        setCurrentPocketCenter(null)
      } else {
        addLog(0, '状态', `保留现有蛋白质结构: ${existingWorkflowState.structure_path} (UniProt: ${existingWorkflowState.uniprot_acc})`)
        addLog(0, '调试', `完整工作流状态: ${JSON.stringify(existingWorkflowState)}`)
        // 确保状态同步
        if (existingWorkflowState !== workflowState) {
          setWorkflowState(existingWorkflowState)
        }
        if (existingWorkflowState !== workflowStateRef.current) {
          workflowStateRef.current = existingWorkflowState
        }
        // 确保UI状态与workflowState同步
        if (existingWorkflowState.structure_path) {
          setCurrentStructurePath(existingWorkflowState.structure_path)
        }
      }
    } else {
      if (existingWorkflowState) {
        addLog(0, '调试', `重置不完整的工作流状态: ${JSON.stringify(existingWorkflowState)}`)
      }
      setWorkflowState(null)
      workflowStateRef.current = null
      setCurrentStructurePath(null)
      setCurrentPocketCenter(null)
    }
    // 仅在必要时重置其他状态（避免过度清理）
    if (!existingWorkflowState || !existingWorkflowState.structure_path) {
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
      // 重置AlphaFold指示灯状态
      setIsUsingAlphaFold(false)
      // 重置科学分析
      setScientificAnalysis(null)
    }

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

      // 允许UI更新
      await asyncDelay(50)

      // STEP 2: AI 决策 选靶点
      setStep(2)
      addLog(2, '状态', 'AI 正在选择最佳靶点…')
      
      // 允许UI更新
      await asyncDelay(50)
      
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
        const targetInfoRes = await api.getTargetExplanation(selectedSymbol, disease)
        if (targetInfoRes.success && targetInfoRes.explanation) {
          setTargetExplanation(targetInfoRes.explanation)
          addLog(2, '决策', `靶点分析: ${targetInfoRes.explanation}`)
        }
      } catch (error) {
        console.log("获取靶点解释失败:", error)
      }

      // 允许UI更新
      await asyncDelay(50)

      // STEP 3: UniProt 检索 - 尝试首选靶点
      setStep(3)
      
      // 允许UI更新
      await asyncDelay(50)
      
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

      // 允许UI更新
      await asyncDelay(50)

      // STEP 4: 结构获取
      setStep(4)
      
      // 允许UI更新
      await asyncDelay(50)
      
      const acc = uRes.entries[0].acc
      addLog(3, '状态', `获取 UniProt Accession：${acc}`)
      const sRes = await api.getStructureSources(acc)
      addLog(3, '日志', JSON.stringify(sRes))
      if (!sRes.success) throw new Error(sRes.error)
      
      const modelPath = (sRes as any).structure_path
      const structureSource = (sRes as any).structure_source
      
      // 检查必要的结构数据
      if (!modelPath) {
        throw new Error('未获取到蛋白质结构文件路径')
      }
      
      // 根据结构来源设置指示灯状态和日志信息
      if (structureSource === 'alphafold') {
        setIsUsingAlphaFold(true)
        addLog(3, '状态', `使用 AlphaFold 预测结构：${modelPath}`)
        addLog(3, '状态', '🧬 当前使用AI预测结构（AlphaFold）')
      } else if (structureSource === 'pdb') {
        setIsUsingAlphaFold(false)
        addLog(3, '状态', `使用 PDB 实验结构：${modelPath}`)
        addLog(3, '状态', '🔬 当前使用实验解析结构（PDB）')
      } else {
        setIsUsingAlphaFold(false)
        addLog(3, '状态', `结构文件路径：${modelPath}`)
      }
      
      const newWorkflowState = { 
        uniprot_acc: acc, 
        structure_path: modelPath, 
        structure_source: structureSource,
        disease: disease,  // 保存当前疾病信息
        target_symbol: currentTarget  // 保存当前靶点信息
      }
      addLog(4, '调试', `设置工作流状态: ${JSON.stringify(newWorkflowState)}`)
      
      // 原子性更新workflowState和相关状态
      setWorkflowState(newWorkflowState)
      workflowStateRef.current = newWorkflowState // 立即更新ref
      
      // 立即保存会话状态
      setTimeout(async () => {
        try {
          await saveCurrentSession()
          addLog(4, '调试', '工作流状态保存完成')
        } catch (error) {
          addLog(4, '错误', `工作流状态保存失败: ${error}`)
        }
      }, 50)
      
      // 立即显示结构
      setCurrentStructurePath(modelPath)
      setCurrentProteinName(`${currentTarget} 蛋白质`)
      
      addLog(4, '状态', `✅ 结构获取完成：${modelPath}`)
      addLog(4, '调试', `WorkflowState设置状态: ${JSON.stringify(newWorkflowState)}`)

      // 允许UI更新
      await asyncDelay(50)

      // STEP 5: 口袋预测
      setStep(5)
      
      // 允许UI更新
      await asyncDelay(50)
      
      // 验证workflowState存在
      if (!workflowStateRef.current || !workflowStateRef.current.structure_path) {
        addLog(5, '错误', '工作流状态在步骤5中丢失，重新设置')
        setWorkflowState(newWorkflowState)
        workflowStateRef.current = newWorkflowState
      }
      
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

      // 允许UI更新
      await asyncDelay(50)

      // STEP 6: 配体获取
      setStep(6)
      
      // 允许UI更新
      await asyncDelay(50)
      
      // 验证workflowState在步骤6中的存在
      if (!workflowStateRef.current || !workflowStateRef.current.structure_path) {
        addLog(6, '错误', '工作流状态在步骤6中丢失，重新设置')
        setWorkflowState(newWorkflowState)
        workflowStateRef.current = newWorkflowState
      }
      
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

      // 允许UI更新
      await asyncDelay(50)

      // STEP 7: 化合物优化
      setStep(7)
      
      // 允许UI更新
      await asyncDelay(50)
      
      // 验证workflowState在步骤7中的存在
      if (!workflowStateRef.current || !workflowStateRef.current.structure_path) {
        addLog(7, '错误', '工作流状态在步骤7中丢失，需要从其他状态恢复')
        addLog(7, '调试', `当前workflowState: ${JSON.stringify(workflowState)}`)
        addLog(7, '调试', `workflowStateRef.current: ${JSON.stringify(workflowStateRef.current)}`)
        
        // 尝试从可用状态重建workflowState
        if (currentStructurePath && acc) {
          const recoveredState = {
            uniprot_acc: acc,
            structure_path: currentStructurePath,
            structure_source: isUsingAlphaFold ? 'alphafold' : 'pdb',
            disease: disease,
            target_symbol: currentTarget
          }
          addLog(7, '状态', `从当前状态恢复workflowState: ${JSON.stringify(recoveredState)}`)
          setWorkflowState(recoveredState)
          workflowStateRef.current = recoveredState
        } else {
          throw new Error('无法恢复工作流状态。请从步骤4重新开始结构获取。')
        }
      }
      
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

      // 允许UI更新
      await asyncDelay(50)

      // STEP 8: 分子对接 - 改进前置验证
      setStep(8)
      
      // 允许UI更新  
      await asyncDelay(50)
      
      addLog(7, '状态', '🔬 准备分子对接分析...')
      
      // 更强的前置验证：同时检查React状态和ref
      const currentWorkflowState = workflowStateRef.current || workflowState
      
      if (!currentWorkflowState) {
        addLog(7, '错误', '工作流状态丢失，尝试恢复')
        // 尝试使用可用的状态数据重新构建
        if (currentStructurePath && acc) {
          const recoveredState = {
            uniprot_acc: acc,
            structure_path: currentStructurePath,
            structure_source: isUsingAlphaFold ? 'alphafold' : 'pdb',
            disease: disease,
            target_symbol: currentTarget
          }
          setWorkflowState(recoveredState)
          workflowStateRef.current = recoveredState
          addLog(7, '状态', '工作流状态已恢复')
        } else {
          throw new Error('工作流状态丢失且无法恢复。请从步骤4重新开始结构获取。')
        }
      }
      
      if (!currentWorkflowState.structure_path) {
        addLog(7, '错误', '蛋白质结构路径丢失')
        addLog(7, '错误', `当前workflowState: ${JSON.stringify(currentWorkflowState)}`)
        throw new Error('蛋白质结构路径丢失。请从步骤4重新开始结构获取。')
      }
      
      if (!selectedPocket || !selectedPocket.center) {
        addLog(7, '错误', '结合口袋信息丢失')
        throw new Error('结合口袋信息丢失。请从步骤5重新开始口袋预测。')
      }
      
      if (!cd.optimized_smiles) {
        addLog(7, '错误', '优化化合物信息丢失')
        throw new Error('优化化合物信息丢失。请从步骤7重新开始化合物优化。')
      }
      
      // 验证workflowState与当前上下文的一致性
      if (currentWorkflowState.disease && currentWorkflowState.disease !== disease) {
        addLog(7, '警告', `检测到疾病不匹配: 工作流中的疾病(${currentWorkflowState.disease}) vs 当前疾病(${disease})`)
      }
      
      if (currentWorkflowState.target_symbol && currentWorkflowState.target_symbol !== currentTarget) {
        addLog(7, '警告', `检测到靶点不匹配: 工作流中的靶点(${currentWorkflowState.target_symbol}) vs 当前靶点(${currentTarget})`)
      }
      
      // 准备对接参数
      const dockingParameters = {
        protein_path: currentWorkflowState.structure_path,
        ligand_smiles: cd.optimized_smiles,
        pocket_center: selectedPocket.center as [number, number, number]
      };
      
      addLog(7, '调试', `对接参数验证通过: ${JSON.stringify(dockingParameters)}`)
      
      // 生成实际的 vina 命令用于历史记录
      const vinaCommand = `vina --receptor ${currentWorkflowState.structure_path} --ligand ligand.pdbqt --center_x ${selectedPocket.center[0]} --center_y ${selectedPocket.center[1]} --center_z ${selectedPocket.center[2]} --size_x 20 --size_y 20 --size_z 20 --out result.pdbqt --log docking.log --exhaustiveness 8`
      addLog(7, '日志', `执行分子对接命令: ${vinaCommand}`)
      
      // 设置对接参数并显示确认模态框
      setDockingParams(dockingParameters);
      console.log('🎯 设置对接参数并显示模态框:', dockingParameters);
      
      // 允许UI更新
      await asyncDelay(100)
      
      setShowDockingModal(true);
      console.log('✅ 对接模态框状态设置为 true');
      
      // 等待用户选择（通过Promise实现异步等待）
      console.log('⏳ 开始等待用户选择...');
      const userChoice = await new Promise<'proceed' | 'skip'>((resolve) => {
        const handleDockingChoice = (choice: 'proceed' | 'skip') => {
          console.log(`🎯 用户选择: ${choice}`);
          // 不要立即关闭模态框，让API调用决定何时关闭
          resolve(choice);
        };
        
        // 临时存储选择处理函数到window对象（用于模态框回调）
        (window as any).__dockingChoiceHandler = handleDockingChoice;
        console.log('📋 对接选择处理函数已设置到 window 对象');
      });
      
      console.log(`✅ 用户选择结果: ${userChoice}`);
      
      if (userChoice === 'skip') {
        addLog(6, '状态', '⏭️ 用户选择跳过分子对接，直接进入结果分析');
        setShouldSkipDocking(true);
        
        // 关闭模态框，因为跳过了对接
        setShowDockingModal(false);
        
        // 创建模拟对接结果用于显示
        const mockDockingResult = {
          success: false,
          skipped: true,
          ligand_smiles: cd.optimized_smiles,
          protein_path: currentWorkflowState?.structure_path || 'unknown',
          pocket_center: selectedPocket.center,
          message: "用户选择跳过分子对接步骤"
        };
        setDockingResult(mockDockingResult);
      } else {
        // 用户选择继续对接
        addLog(6, '状态', '🚀 开始分子对接分析...');
        addLog(6, '调试', `📋 对接参数: ${JSON.stringify(dockingParameters)}`);
        console.log('🔥 前端准备发送对接请求:', dockingParameters);
        
        // 关闭选择模态框，显示进度追踪器
        setShowDockingModal(false);
        setShowDockingProgress(true);
        
        // 立即开始后台API调用，不等待进度弹窗完成
        const performDockingApi = async () => {
          try {
            console.log('🚀 发送API请求: generateDockingVisualization');
            addLog(6, '调试', '📤 正在向后端发送对接请求...');
            const dockingRes = await api.generateDockingVisualization(dockingParameters);
            console.log('✅ API响应接收:', dockingRes);
            addLog(6, '日志', `分子对接响应: ${JSON.stringify(dockingRes)}`);
            
            if (dockingRes.success) {
              setDockingResult(dockingRes.docking_result);
              setDockingVisualization(dockingRes.visualization);
              
              const bestScore = dockingRes.docking_result.best_score;
              const numPoses = dockingRes.docking_result.poses.length;
              
              addLog(6, '状态', `✅ 分子对接完成：最佳分数 ${bestScore.toFixed(2)}`);
              addLog(6, '决策', `分子对接结果: 获得 ${numPoses} 个构象，最佳结合分数为 ${bestScore.toFixed(2)} kcal/mol`);
              
              // 评价对接结果
              if (bestScore < -7.0) {
                addLog(6, '决策', `🎯 优秀的分子对接结果！分数 ${bestScore.toFixed(2)} 表明化合物与靶点有很强的结合亲和力`);
              } else if (bestScore < -5.0) {
                addLog(6, '决策', `👍 良好的分子对接结果，分数 ${bestScore.toFixed(2)} 表明有中等结合亲和力`);
              } else {
                addLog(6, '决策', `⚠️ 分子对接分数 ${bestScore.toFixed(2)} 偏高，可能需要进一步优化化合物结构`);
              }
              
              // 检查分子对接结果中是否已包含可视化数据
              if (dockingRes.docking_result?.visualization?.images) {
                addLog(6, '状态', '✅ 分子对接可视化已生成');
                console.log('对接可视化数据:', dockingRes.docking_result.visualization);
              } else {
                addLog(6, '状态', '⚠️ 分子对接可视化数据不可用，但对接成功完成');
              }
              
              addLog(6, '状态', '✅ 分子对接阶段完成');
            } else {
              addLog(6, '状态', `❌ 分子对接失败: ${dockingRes.visualization?.error || '未知错误'}`);
            }
          } catch (dockingError: any) {
            console.error('❌ 分子对接过程中发生错误:', dockingError);
            addLog(6, '状态', `分子对接API调用失败: ${dockingError?.message || String(dockingError)}`);
            addLog(6, '错误', `详细错误信息: ${JSON.stringify(dockingError, null, 2)}`);
          }
        };
        
        // 后台启动API调用，不阻塞进度显示
        performDockingApi();
      }

      // 只有在用户选择完成后才继续后续步骤
      console.log(`🎯 用户选择处理完成，继续后续流程 (选择: ${userChoice})`);

      // 允许UI更新
      await asyncDelay(50)

      // STEP 9: 分子图像
      setStep(9)
      
      // 允许UI更新
      await asyncDelay(50)
      
      addLog(8, '状态', '生成分子结构图…')
      
      // 生成优化后的分子图像
      const mi = await api.generateMoleculeImage(cd.optimized_smiles)
      addLog(8, '日志', JSON.stringify(mi))
      if (mi.success) setMoleculeImage(mi.image_data)
      
      // 生成原始化合物图像（如果有选中的SMILES）
      if (cd.selected_smiles) {
        addLog(8, '状态', '生成原始化合物结构图…')
        const originalMi = await api.generateMoleculeImage(cd.selected_smiles)
        addLog(8, '日志', `原始分子图像: ${JSON.stringify(originalMi)}`)
        if (originalMi.success) setOriginalMoleculeImage(originalMi.image_data)
      }

      // 允许UI更新
      await asyncDelay(50)

      // STEP 9: 生成科学分析
      addLog(8, '状态', 'AI 正在生成科学分析报告…')
      
      // 构建完整的工作流数据用于科学分析，包含分子对接结果
      const analysisData = {
        disease,
        gene_symbol: currentTarget,
        uniprot_acc: currentWorkflowState?.uniprot_acc,
        structure_path: currentWorkflowState?.structure_path,
        pocket_center: selectedPocket.center,
        smiles_list: allSmiles,
        optimized_smiles: cd.optimized_smiles,
        docking_result: dockingResult,
        docking_score: dockingResult?.best_score
      }
      
      addLog(8, '日志', `科学分析数据: ${JSON.stringify(analysisData)}`)
      
      try {
        const scientificAnalysisData = await api.generateScientificAnalysis(analysisData)
        addLog(8, '日志', `科学分析响应: ${JSON.stringify(scientificAnalysisData)}`)
        
        if (scientificAnalysisData.success) {
          setScientificAnalysis(scientificAnalysisData.explanation)
          addLog(8, '状态', '✅ 科学分析报告生成完成')
          addLog(8, '决策', `科学分析内容（前100字符）: ${scientificAnalysisData.explanation.substring(0, 100)}...`)
          console.log('科学分析已设置:', scientificAnalysisData.explanation.substring(0, 200))
        } else {
          addLog(8, '状态', `❌ 科学分析报告生成失败: ${scientificAnalysisData.error || '未知错误'}`)
        }
      } catch (analysisError: any) {
        addLog(8, '状态', `科学分析API调用失败: ${analysisError.message}`)
        console.error('科学分析生成错误:', analysisError)
      }

      // 允许UI更新
      await asyncDelay(50)

      // 最后一步：结果保存
      setStep(10)
      
      // 允许UI更新
      await asyncDelay(50)
      
      addLog(9, '状态', '结果保存中...')
      // 在这里可以添加保存数据逻辑
      addLog(9, '状态', '流程全部完成！')
    } catch (err: any) {
      addLog(step || 1, '状态', `🚨 出错：${err.message}`)
      
      // 如果是结构相关错误，清理可能的无效状态
      if (err.message.includes('缺少蛋白质结构文件路径') || err.message.includes('结构')) {
        addLog(step || 1, '状态', '检测到结构相关错误，清理状态以便重新获取')
        if (!workflowState?.structure_path) {
          setWorkflowState(null)
        }
      }
    }
  }

  const active = step > 0 && step < 10

  return (
    <>
      <style>{`
        body {
          margin: 0; padding: 0;
          background: #f0f2f7;
          overflow: hidden; /* Prevent body from scrolling */
        }
        .super-wrapper {
          display: flex;
          height: 100vh;
          width: 100vw;
          overflow: hidden; /* Prevent overall wrapper from scrolling */
          transition: padding-left 0.3s ease-in-out;
        }
        .session-history-container {
          position: fixed; /* Fixed position to overlay or slide in/out */
          top: 0;
          left: 0;
          height: 100%;
          width: 280px;
          flex-shrink: 0;
          background: #f8f9fc;
          border-right: 1px solid #e5e7eb;
          transition: transform 0.3s ease-in-out;
          z-index: 200; /* Ensure it's above other content */
          display: flex;
          flex-direction: column;
        }
        .session-history-container.collapsed {
          transform: translateX(-100%);
        }
        .collapse-btn {
          position: fixed; /* Fixed position relative to viewport */
          top: 50%;
          left: 280px; /* Start at the edge of the expanded sidebar */
          transform: translateY(-50%);
          width: 24px;
          height: 80px;
          background: #4f46e5;
          border: 1px solid #4338ca;
          border-left: none;
          border-radius: 0 8px 8px 0;
          cursor: pointer;
          z-index: 201; /* Above the sidebar */
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 16px;
          color: #fff;
          box-shadow: 2px 0 5px rgba(0,0,0,0.1);
          transition: left 0.3s ease-in-out, background-color 0.2s;
        }
        .session-history-container.collapsed + .collapse-btn {
          left: 0; /* Move to the edge of the screen when collapsed */
        }
        .collapse-btn:hover {
          background: #4338ca;
        }

        .content-and-right-panel-wrapper {
            display: flex;
            flex-grow: 1;
            width: calc(100% - 280px); /* Account for left sidebar */
            margin-left: 280px;
            transition: all 0.3s ease-in-out;
            position: relative;
            overflow: hidden; /* Prevent horizontal scroll */
        }

        .session-history-container.collapsed ~ .content-and-right-panel-wrapper {
            margin-left: 0;
            width: 100%;
        }

        .main-content-wrapper {
          flex: 1;
          overflow-y: auto;
          overflow-x: hidden; /* Prevent horizontal scroll */
          padding: 12px;
          display: flex;
          flex-direction: column;
          min-height: 0;
          min-width: 0; /* Allow content to shrink */
        }

        .app {
          position: relative;
          width: 100%;
          max-width: 810px; /* Reduced by 10% from 900px */
          margin: 0 auto;
          background: #fff;
          border-radius: 8px;
          box-shadow: 0 4px 16px rgba(0,0,0,0.1);
          padding: 16px;
          font-family: 'Segoe UI', sans-serif;
          border: 2px solid transparent;
          z-index: 1;
          flex-shrink: 0; /* Prevent shrinking */
          min-height: fit-content;
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
            margin-bottom: 12px;
        }

        .title-row h3 {
          margin: 2px 0 0;
          font-size: 14px;
          color: #666;
        }
        
        .designer-credit {
          margin-top: 4px;
          font-size: 10px;
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

        /* 认证区域样式 */
        .auth-section {
          margin-top: 12px;
          display: flex;
          justify-content: center;
          align-items: center;
        }

        .user-info {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 8px 16px;
          background: rgba(79, 70, 229, 0.1);
          border: 1px solid rgba(79, 70, 229, 0.2);
          border-radius: 20px;
        }

        .welcome-text {
          font-size: 14px;
          color: #4f46e5;
          font-weight: 500;
        }

        .logout-btn {
          padding: 4px 12px;
          background: #dc2626;
          color: white;
          border: none;
          border-radius: 12px;
          font-size: 12px;
          cursor: pointer;
          transition: background-color 0.2s;
        }

        .logout-btn:hover {
          background: #b91c1c;
        }

        .auth-buttons {
          display: flex;
          gap: 8px;
        }

        .auth-btn {
          padding: 6px 16px;
          border: 1px solid #d1d5db;
          border-radius: 16px;
          background: white;
          cursor: pointer;
          transition: all 0.2s;
          font-size: 13px;
          font-weight: 500;
        }

        .login-btn {
          color: #4f46e5;
          border-color: #4f46e5;
        }

        .login-btn:hover {
          background: #4f46e5;
          color: white;
        }

        .register-btn {
          color: #059669;
          border-color: #059669;
        }

        .register-btn:hover {
          background: #059669;
          color: white;
        }

        /* AlphaFold指示灯样式 */
        .alphafold-indicator {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          margin-top: 8px;
          padding: 4px 8px;
          background: rgba(34, 197, 94, 0.1);
          border: 1px solid rgba(34, 197, 94, 0.2);
          border-radius: 12px;
          font-size: 11px;
          color: #059669;
          animation: alphafoldPulse 2s ease-in-out infinite;
        }

        .indicator-dot {
          width: 6px;
          height: 6px;
          background: #10b981;
          border-radius: 50%;
          animation: dotPulse 1.5s ease-in-out infinite;
        }

        .indicator-text {
          font-weight: 500;
          letter-spacing: 0.02em;
        }

        @keyframes alphafoldPulse {
          0%, 100% {
            background: rgba(34, 197, 94, 0.1);
            border-color: rgba(34, 197, 94, 0.2);
          }
          50% {
            background: rgba(34, 197, 94, 0.15);
            border-color: rgba(34, 197, 94, 0.3);
          }
        }

        @keyframes dotPulse {
          0%, 100% {
            opacity: 1;
            transform: scale(1);
          }
          50% {
            opacity: 0.7;
            transform: scale(1.2);
          }
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
          margin: 0; font-size: 24px; color: #333;
          transition: color 0.3s;
        }

        /* 输入框 / 按钮 动画 */
        .input {
          display: flex; gap: 12px;
          justify-content: center; margin-bottom: 16px;
        }
        .input input {
          flex: 1; padding: 10px; font-size: 14px;
          border: 1px solid #ccc; border-radius: 6px;
          transition: border-color 0.3s, box-shadow 0.3s;
        }
        .input input:focus {
          border-color: #4f46e5;
          box-shadow: 0 0 0 2px rgba(79,70,229,0.2);
          outline: none;
        }
        .input button {
          background: #4f46e5; color: #fff; border: none;
          padding: 0 16px; border-radius: 6px; font-size: 14px;
          cursor: pointer;
          transition: transform 0.2s, box-shadow 0.2s;
          height: 38px; /* Explicitly set height */
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
          width: 340px;
          min-width: 280px; /* Minimum width to maintain functionality */
          max-width: 400px; /* Maximum width to prevent overflow */
          flex-shrink: 1; /* Allow shrinking if needed */
          height: 100vh;
          max-height: 100vh;
          overflow: hidden;
          display: flex;
          flex-direction: column;
          padding: 8px;
          background-color: #f0f2f7;
          transition: width 0.3s ease-in-out;
        }

        .session-history-container.collapsed ~ .content-and-right-panel-wrapper .side-panel {
            width: 450px; /* Expand right sidebar when left is collapsed */
        }

        /* Responsive adjustments */
        @media (max-width: 1200px) { /* Large tablet */
          .super-wrapper {
            flex-direction: column;
          }
          .main-content-wrapper {
            order: 1;
          }
          .side-panel {
            width: 100%;
            height: 500px; /* Fixed height on smaller screens */
            max-height: 500px;
            order: 2;
          }
          .session-history-container {
            position: relative; /* Revert fixed positioning */
            transform: none !important; /* Disable transform */
            width: 100%;
            height: auto;
            max-height: 300px;
            border-right: none;
            border-top: 1px solid #e5e7eb;
            order: 3;
            z-index: 1;
          }
          .session-history-container.collapsed {
             height: 0;
             min-height: 0;
             overflow: hidden;
          }
          .collapse-btn {
            display: none; /* Hide collapse button on mobile layouts */
          }
          .content-and-right-panel-wrapper {
            margin-left: 0; /* No margin on mobile */
            flex-direction: column;
            width: 100%;
          }
        }

        @media (max-width: 768px) { /* Tablet and smaller */
          .main-content-wrapper {
            padding: 8px;
            gap: 10px;
          }
          .app {
            padding: 12px;
          }
          .input {
            flex-direction: row; /* Keep horizontal layout for all screens */
            gap: 8px;
            align-items: center;
          }
          .input input {
            flex: 1;
            font-size: 14px; /* Slightly smaller font */
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
          .main-content-wrapper {
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

      <div className="super-wrapper">
        <div className={`session-history-container ${isSidebarCollapsed ? 'collapsed' : ''}`}>
            <SessionHistory 
                onSessionSelect={handleSessionSelect} 
                currentSessionId={currentSessionId}
                onNewSession={handleNewSession}
            />
        </div>
        <button onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)} className="collapse-btn" title={isSidebarCollapsed ? "Show Sidebar" : "Collapse Sidebar"}>
          {isSidebarCollapsed ? '▶' : '◀'}
        </button>
        <div className="content-and-right-panel-wrapper">
            <div className="main-content-wrapper">
              <div className={`app${active ? ' active' : ''}`}>
                <div className="title-row">
                  <h1>Protein Dance</h1>
                  <h3>基于DeepSeek的全自动制药智能体</h3>
                  <div className="designer-credit">Designed by Zhenxiong W. & Boran C. Guided by Dr Lingfang T. in Biochemphysics</div>
                  
                  {/* 用户认证区域 */}
                  {/* <div className="auth-section">
                    {user ? (
                      <div className="user-info">
                        <span className="welcome-text">欢迎, {user.username}</span>
                        <button className="logout-btn" onClick={handleLogout}>
                          注销
                        </button>
                      </div>
                    ) : (
                      <div className="auth-note">
                        <span>请在左侧历史面板中登录以保存会话</span>
                      </div>
                    )}
                  </div> */}
                  
                  {/* AlphaFold指示灯 */}
                  {isUsingAlphaFold && (
                    <div className="alphafold-indicator">
                      <span className="indicator-dot"></span>
                      <span className="indicator-text">AlphaFold AI预测结构</span>
                    </div>
                  )}
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
                ) : step === 9 || step === 10 ? (
                  <>
                    <WorkflowStepper
                      currentStep={step}
                    />
                    {/* 调试输出 */}
                    {console.log('Step 8 - ResultPanel数据:', {
                      disease,
                      geneSymbol: decisionTarget?.selected_option,
                      targetExplanation: targetExplanation ? `${targetExplanation.substring(0, 50)}...` : null,
                      scientificAnalysis: scientificAnalysis ? `${scientificAnalysis.substring(0, 50)}...` : null,
                      explanation: (scientificAnalysis || decisionCompound?.explanation) ? 
                        `${(scientificAnalysis || decisionCompound?.explanation).substring(0, 50)}...` : null
                    })}
                    <ResultPanel
                      disease={disease}
                      geneSymbol={decisionTarget?.selected_option || ''}
                      uniprotAcc={workflowState?.uniprot_acc}
                      pocketCenter={decisionPocket?.pocket_center || null}
                      optimizedSmiles={decisionCompound?.optimized_smiles || null}
                      explanation={scientificAnalysis || decisionCompound?.explanation || null}
                      // selectionReason={selectionReason}
                      // optimizationExplanation={optimizationExplanation}
                      moleculeImage={moleculeImage}
                      dockingImage={dockingImage}
                      originalMoleculeImage={originalMoleculeImage}
                      originalSmiles={decisionCompound?.selected_smiles || null}
                      structurePath={workflowState?.structure_path}
                      targetExplanation={targetExplanation}
                      dockingResult={dockingResult}
                      dockingVisualization={dockingVisualization}
                      ligandSmiles={currentLigandSmiles}
                      sessionId={currentSessionId}
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
      </div>

      {/* API配置按钮 */}
      <button
        onClick={() => setShowConfigPanel(!showConfigPanel)}
        style={{
          position: 'fixed',
          top: '20px',
          right: showConfigPanel ? '380px' : '20px',
          zIndex: 1001,
          backgroundColor: '#3b82f6',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          padding: '10px 12px',
          cursor: 'pointer',
          fontSize: '16px',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
          transition: 'right 0.3s ease'
        }}
        title="API配置"
      >
        ⚙️
      </button>

      {/* API配置面板 */}
      {showConfigPanel && (
        <ApiConfigPanel onClose={() => setShowConfigPanel(false)} />
      )}

      {/* 分子对接确认模态框 */}
      <DockingConfirmationModal
        isOpen={showDockingModal}
        onSkip={() => {
          console.log('🚫 用户点击跳过对接');
          const handler = (window as any).__dockingChoiceHandler;
          if (handler) {
            console.log('✅ 调用跳过处理函数');
            handler('skip');
          } else {
            console.error('❌ 对接选择处理函数未找到');
          }
        }}
        onProceed={() => {
          console.log('🚀 用户点击继续对接');
          const handler = (window as any).__dockingChoiceHandler;
          if (handler) {
            console.log('✅ 调用继续处理函数');
            handler('proceed');
          } else {
            console.error('❌ 对接选择处理函数未找到');
          }
        }}
        onClose={() => {
          console.log('❌ 用户关闭模态框（默认跳过）');
          const handler = (window as any).__dockingChoiceHandler;
          if (handler) {
            console.log('✅ 调用默认跳过处理函数');
            handler('skip');
          } else {
            console.error('❌ 对接选择处理函数未找到');
          } // 默认跳过
        }}
        estimatedTime="5-10 分钟"
        resourceRequirements="高 CPU 使用率，PyMOL 环境，约 200MB 内存"
      />

      {/* 分子对接进度追踪器 */}
      <DockingProgressTracker
        isVisible={showDockingProgress}
        dockingParams={dockingParams}
        onComplete={() => {
          setShowDockingProgress(false);
          addLog(6, '状态', '🎉 分子对接进度显示完成！请查看历史记录中的实际结果...');
          // 真实API结果在后台处理，进度弹窗只是显示用途
        }}
        onError={(error) => {
          setShowDockingProgress(false);
          addLog(6, '状态', `❌ 分子对接进度显示错误: ${error}`);
        }}
      />
    </>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainApp />} />
        <Route path="/verify-email" element={<VerifyEmail />} />
        <Route path="/reset-password" element={<ResetPassword />} />
      </Routes>
    </BrowserRouter>
  )
}
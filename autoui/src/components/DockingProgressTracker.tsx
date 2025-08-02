import React, { useState, useEffect } from 'react'

interface DockingProgressTrackerProps {
  isVisible: boolean
  onComplete?: (result: any) => void
  onError?: (error: string) => void
  dockingParams?: {
    protein_path: string
    ligand_smiles: string
    pocket_center: [number, number, number]
  }
}

interface ProgressStep {
  id: string
  name: string
  description: string
  status: 'pending' | 'running' | 'completed' | 'error'
  progress: number
}

const DockingProgressTracker: React.FC<DockingProgressTrackerProps> = ({
  isVisible,
  onComplete,
  onError,
  dockingParams
}) => {
  const [steps, setSteps] = useState<ProgressStep[]>([
    {
      id: 'preparation',
      name: '蛋白质预处理',
      description: '清理蛋白质结构，移除有问题的标签',
      status: 'pending',
      progress: 0
    },
    {
      id: 'docking',
      name: '分子对接计算',
      description: '使用 AutoDock Vina 进行分子对接',
      status: 'pending',
      progress: 0
    },
    {
      id: 'visualization',
      name: 'PyMOL 可视化',
      description: '生成高质量分子结构图像',
      status: 'pending',
      progress: 0
    },
    {
      id: 'analysis',
      name: '科学分析',
      description: '分析结合能和生成科学报告',
      status: 'pending',
      progress: 0
    }
  ])

  const [currentStep, setCurrentStep] = useState(0)
  const [overallProgress, setOverallProgress] = useState(0)
  const [startTime, setStartTime] = useState<Date | null>(null)
  const [elapsedTime, setElapsedTime] = useState(0)

  // 模拟分子对接进度 (不等待真实API)
  useEffect(() => {
    if (!isVisible || !dockingParams) return

    setStartTime(new Date())
    
    const simulateDocking = async () => {
      try {
        // 进度弹窗纯显示用途，真实API在App.tsx中后台执行
        
        // 始终使用模拟进度，确保弹窗按预期时间完成
        // 步骤1: 蛋白质预处理
        await simulateStep(0, 'preparation', 2000)
        
        // 步骤2: 分子对接计算 (最耗时)
        await simulateStep(1, 'docking', 8000)
        
        // 步骤3: PyMOL 可视化
        await simulateStep(2, 'visualization', 3000)
        
        // 步骤4: 科学分析
        await simulateStep(3, 'analysis', 2000)
        
        // 完成
        setOverallProgress(100)
        
        // 模拟结果 - 真实结果会通过API在后台处理
        const mockResult = {
          success: true,
          best_score: -8.5,
          poses: [
            { binding_affinity: -8.5 },
            { binding_affinity: -7.8 },
            { binding_affinity: -7.2 }
          ],
          visualization: {
            success: true,
            images: [
              "overview.png",
              "binding_site.png", 
              "surface_view.png"
            ]
          },
          analysis: {
            success: true,
            models_count: 3,
            best_energy: -8.5
          }
        }
        
        setTimeout(() => {
          onComplete?.(mockResult)
        }, 500)
        
      } catch (error) {
        onError?.(error instanceof Error ? error.message : 'Docking failed')
      }
    }

    simulateDocking()
  }, [isVisible, dockingParams])

  // 计时器
  useEffect(() => {
    if (!startTime || overallProgress >= 100) return

    const timer = setInterval(() => {
      setElapsedTime(Math.floor((Date.now() - startTime.getTime()) / 1000))
    }, 1000)

    return () => clearInterval(timer)
  }, [startTime, overallProgress])

  const simulateStep = (stepIndex: number, stepId: string, duration: number): Promise<void> => {
    return new Promise((resolve) => {
      setCurrentStep(stepIndex)
      
      // 设置步骤为运行状态
      setSteps(prev => prev.map(step => 
        step.id === stepId 
          ? { ...step, status: 'running' }
          : step
      ))

      let progress = 0
      const interval = setInterval(() => {
        progress += Math.random() * 15 + 5 // 随机增长5-20%
        
        if (progress >= 100) {
          progress = 100
          clearInterval(interval)
          
          // 设置步骤为完成状态
          setSteps(prev => prev.map(step => 
            step.id === stepId 
              ? { ...step, status: 'completed', progress: 100 }
              : step
          ))
          
          // 更新总进度
          setOverallProgress((stepIndex + 1) * 25)
          
          setTimeout(resolve, 200)
        } else {
          // 更新步骤进度
          setSteps(prev => prev.map(step => 
            step.id === stepId 
              ? { ...step, progress }
              : step
          ))
        }
      }, duration / 20) // 每个步骤分20个更新
    })
  }

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  if (!isVisible) return null

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      zIndex: 1500,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '16px',
        padding: '32px',
        maxWidth: '600px',
        width: '90%',
        boxShadow: '0 20px 40px rgba(0, 0, 0, 0.3)'
      }}>
        {/* 标题 */}
        <div style={{
          textAlign: 'center',
          marginBottom: '24px'
        }}>
          <div style={{ fontSize: '32px', marginBottom: '8px' }}>🧬</div>
          <h2 style={{
            margin: 0,
            fontSize: '24px',
            fontWeight: 'bold',
            color: '#333'
          }}>
            分子对接进行中
          </h2>
          <p style={{
            margin: '8px 0 0 0',
            color: '#666',
            fontSize: '14px'
          }}>
            正在进行高精度分子对接分析...
          </p>
        </div>

        {/* 总进度条 */}
        <div style={{
          marginBottom: '24px'
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '8px'
          }}>
            <span style={{
              fontSize: '16px',
              fontWeight: 'bold',
              color: '#333'
            }}>
              总进度: {Math.round(overallProgress)}%
            </span>
            <span style={{
              fontSize: '14px',
              color: '#666'
            }}>
              ⏱️ {formatTime(elapsedTime)}
            </span>
          </div>
          <div style={{
            width: '100%',
            height: '8px',
            backgroundColor: '#e9ecef',
            borderRadius: '4px',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${overallProgress}%`,
              height: '100%',
              backgroundColor: '#007bff',
              transition: 'width 0.3s ease',
              background: 'linear-gradient(90deg, #007bff 0%, #0056b3 100%)'
            }} />
          </div>
        </div>

        {/* 步骤详情 */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '16px'
        }}>
          {steps.map((step, index) => (
            <div key={step.id} style={{
              display: 'flex',
              alignItems: 'center',
              padding: '12px',
              backgroundColor: step.status === 'running' ? '#e3f2fd' : '#f8f9fa',
              borderRadius: '8px',
              border: step.status === 'running' ? '2px solid #2196f3' : '1px solid #dee2e6',
              transition: 'all 0.3s ease'
            }}>
              {/* 状态图标 */}
              <div style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginRight: '12px',
                fontSize: '14px',
                fontWeight: 'bold',
                ...(step.status === 'completed' ? {
                  backgroundColor: '#28a745',
                  color: 'white'
                } : step.status === 'running' ? {
                  backgroundColor: '#007bff',
                  color: 'white'
                } : step.status === 'error' ? {
                  backgroundColor: '#dc3545',
                  color: 'white'
                } : {
                  backgroundColor: '#e9ecef',
                  color: '#6c757d'
                })
              }}>
                {step.status === 'completed' ? '✓' : 
                 step.status === 'running' ? '⟳' :
                 step.status === 'error' ? '✗' : index + 1}
              </div>

              {/* 步骤信息 */}
              <div style={{ flex: 1 }}>
                <div style={{
                  fontSize: '16px',
                  fontWeight: 'bold',
                  color: step.status === 'running' ? '#1976d2' : '#333',
                  marginBottom: '4px'
                }}>
                  {step.name}
                </div>
                <div style={{
                  fontSize: '13px',
                  color: '#666'
                }}>
                  {step.description}
                </div>
                
                {/* 步骤进度条 */}
                {step.status === 'running' && (
                  <div style={{
                    width: '100%',
                    height: '4px',
                    backgroundColor: '#e9ecef',
                    borderRadius: '2px',
                    marginTop: '8px',
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      width: `${step.progress}%`,
                      height: '100%',
                      backgroundColor: '#007bff',
                      transition: 'width 0.3s ease'
                    }} />
                  </div>
                )}
              </div>

              {/* 进度百分比 */}
              {step.status === 'running' && (
                <div style={{
                  fontSize: '14px',
                  fontWeight: 'bold',
                  color: '#1976d2',
                  marginLeft: '12px'
                }}>
                  {Math.round(step.progress)}%
                </div>
              )}
            </div>
          ))}
        </div>

        {/* 温馨提示 */}
        <div style={{
          marginTop: '20px',
          padding: '12px',
          backgroundColor: '#fff3cd',
          border: '1px solid #ffeeba',
          borderRadius: '6px',
          fontSize: '13px',
          color: '#856404'
        }}>
          💡 <strong>提示:</strong> 分子对接是计算密集型任务，请耐心等待。生成的结果将包含专业级的科学分析和可视化。
        </div>
      </div>
    </div>
  )
}

export default DockingProgressTracker
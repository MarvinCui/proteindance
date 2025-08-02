import React from 'react'

interface DockingConfirmationModalProps {
  isOpen: boolean
  onSkip: () => void
  onProceed: () => void
  onClose: () => void
  estimatedTime?: string
  resourceRequirements?: string
}

const DockingConfirmationModal: React.FC<DockingConfirmationModalProps> = ({
  isOpen,
  onSkip,
  onProceed,
  onClose,
  estimatedTime = "5-10 分钟",
  resourceRequirements = "高 CPU 使用率，需要 PyMOL 环境"
}) => {
  if (!isOpen) return null

  return (
    <>
      {/* 背景遮罩 */}
      <div 
        className="modal-overlay"
        onClick={onClose}
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
      >
        {/* 模态框内容 */}
        <div 
          className="modal-content"
          onClick={(e) => e.stopPropagation()}
          style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            padding: '24px',
            maxWidth: '500px',
            width: '90%',
            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.3)',
            animation: 'modalFadeIn 0.3s ease-out'
          }}
        >
          {/* 标题 */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            marginBottom: '20px'
          }}>
            <div style={{
              fontSize: '24px',
              marginRight: '12px'
            }}>🧬</div>
            <h2 style={{
              margin: 0,
              fontSize: '20px',
              fontWeight: 'bold',
              color: '#333'
            }}>
              分子对接确认
            </h2>
          </div>

          {/* 描述 */}
          <div style={{
            marginBottom: '24px',
            color: '#666',
            lineHeight: '1.6'
          }}>
            <p style={{ margin: '0 0 16px 0' }}>
              分子对接是一个计算密集型过程，将验证优化后的化合物与靶点蛋白的结合亲和力。
            </p>
            <p style={{ margin: '0' }}>
              您可以选择跳过此步骤直接查看结果，或继续进行完整的分子对接分析。
            </p>
          </div>

          {/* 资源信息 */}
          <div style={{
            backgroundColor: '#f8f9fa',
            border: '1px solid #e9ecef',
            borderRadius: '8px',
            padding: '16px',
            marginBottom: '24px'
          }}>
            <div style={{
              fontSize: '14px',
              fontWeight: 'bold',
              color: '#495057',
              marginBottom: '8px'
            }}>
              🔧 资源需求
            </div>
            <div style={{
              fontSize: '13px',
              color: '#6c757d',
              marginBottom: '8px'
            }}>
              <strong>预计时间:</strong> {estimatedTime}
            </div>
            <div style={{
              fontSize: '13px',
              color: '#6c757d'
            }}>
              <strong>系统要求:</strong> {resourceRequirements}
            </div>
          </div>

          {/* 对接功能列表 */}
          <div style={{
            backgroundColor: '#e3f2fd',
            border: '1px solid #bbdefb',
            borderRadius: '8px',
            padding: '16px',
            marginBottom: '24px'
          }}>
            <div style={{
              fontSize: '14px',
              fontWeight: 'bold',
              color: '#1976d2',
              marginBottom: '12px'
            }}>
              🎯 分子对接将提供
            </div>
            <ul style={{
              margin: 0,
              paddingLeft: '20px',
              fontSize: '13px',
              color: '#1565c0'
            }}>
              <li>高质量 PyMOL 分子可视化（6个专业视角）</li>
              <li>精确的结合能分析和统计报告</li>
              <li>多个结合构象的比较分析</li>
              <li>Ki 估值和 IC50 预测</li>
              <li>适合发表的科学图表</li>
            </ul>
          </div>

          {/* 按钮区域 */}
          <div style={{
            display: 'flex',
            gap: '12px',
            justifyContent: 'flex-end'
          }}>
            <button
              onClick={onSkip}
              style={{
                padding: '10px 20px',
                border: '1px solid #dee2e6',
                borderRadius: '6px',
                backgroundColor: '#f8f9fa',
                color: '#6c757d',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#e9ecef'
                e.currentTarget.style.color = '#495057'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#f8f9fa'
                e.currentTarget.style.color = '#6c757d'
              }}
            >
              ⏭️ 跳过对接，查看结果
            </button>
            
            <button
              onClick={onProceed}
              style={{
                padding: '10px 20px',
                border: 'none',
                borderRadius: '6px',
                backgroundColor: '#007bff',
                color: 'white',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#0056b3'
                e.currentTarget.style.transform = 'translateY(-1px)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#007bff'
                e.currentTarget.style.transform = 'translateY(0)'
              }}
            >
              🚀 继续分子对接
            </button>
          </div>
        </div>
      </div>

      {/* CSS 动画 */}
      <style>{`
        @keyframes modalFadeIn {
          from {
            opacity: 0;
            transform: scale(0.9) translateY(-20px);
          }
          to {
            opacity: 1;
            transform: scale(1) translateY(0);
          }
        }
        
        .modal-overlay {
          backdrop-filter: blur(4px);
        }
        
        @media (max-width: 768px) {
          .modal-content {
            margin: 20px;
            width: calc(100% - 40px) !important;
            max-width: none !important;
          }
        }
      `}</style>
    </>
  )
}

export default DockingConfirmationModal
import React from 'react'
import { motion } from 'framer-motion'

interface Props {
  currentStep: number
}

const stepLabels = [
  '靶点识别','UniProt检索','结构获取','口袋预测',
  '配体获取','化合物优化','分子图像','完成','用户下载','人工分析'
]

const containerVariants = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: 0.05
    }
  }
}

const circleVariants = {
  inactive: { scale: 0.8, backgroundColor: '#dde1e7' },
  active: { scale: 1.2, backgroundColor: '#4f46e5' }
}

const labelVariants = {
  inactive: { opacity: 0.4 },
  active: { opacity: 1 }
}

export default function WorkflowStepper({ currentStep }: Props) {
  return (
    <motion.ul
      className="stepper"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      style={{
        display:'flex', justifyContent:'space-between',
        listStyle:'none', padding:0, marginBottom:32
      }}
    >
      {stepLabels.map((label, idx) => {
        const stepNum = idx + 1
        const isActive = stepNum === currentStep
        const isDone = stepNum < currentStep

        return (
          <motion.li
            key={label}
            style={{ textAlign:'center', flex:1 }}
          >
            <motion.div
              variants={circleVariants}
              animate={isActive || isDone ? 'active' : 'inactive'}
              transition={{ type:'spring', stiffness:300 }}
              style={{
                width:32, height:32, borderRadius:16,
                margin:'0 auto', marginBottom:8
              }}
            />
            <motion.div
              variants={labelVariants}
              animate={isActive || isDone ? 'active' : 'inactive'}
              transition={{ duration:0.3 }}
              style={{ fontSize:12, color:'#333' }}
            >
              {label}
            </motion.div>
            {/* 步骤连线 */}
            {idx < stepLabels.length - 1 && (
              <motion.div
                style={{
                  position:'absolute', top:16, right:`calc(100% - 16px)`,
                  width:'100%', height:2,
                  background: stepNum < currentStep ? '#4f46e5' : '#dde1e7',
                  zIndex:-1
                }}
                initial={false}
                animate={{
                  background: stepNum < currentStep ? '#4f46e5' : '#dde1e7'
                }}
              />
            )}
          </motion.li>
        )
      })}
    </motion.ul>
  )
}

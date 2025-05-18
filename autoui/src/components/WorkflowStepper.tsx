import React from 'react'
import { motion } from 'framer-motion'

interface Props {
  currentStep: number
  stepLabels?: string[]
}

const defaultStepLabels = [
  '靶点识别','UniProt检索','结构获取','口袋预测',
  '配体获取','化合物优化','分子图像','结果保存'
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
  inactive: { 
    scale: 0.8, 
    backgroundColor: '#dde1e7',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)'
  },
  active: { 
    scale: 1.2, 
    backgroundColor: '#4f46e5',
    boxShadow: '0 0 12px rgba(79, 70, 229, 0.6)'
  }
}

const labelVariants = {
  inactive: { opacity: 0.4, fontWeight: 'normal' },
  active: { opacity: 1, fontWeight: 'bold' }
}

// CSS for responsive behavior
const stepperStyles = `
  .stepper {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-evenly;
    list-style: none;
    padding: 0;
    margin-bottom: 32px;
    position: relative;
  }
  
  .stepper-item {
    text-align: center;
    flex: 0 0 auto;
    position: relative;
    padding: 0 8px;
    margin: 0 4px;
  }
  
  .stepper-circle {
    width: 32px;
    height: 32px;
    border-radius: 16px;
    margin: 0 auto;
    margin-bottom: 10px;
    position: relative;
    z-index: 2;
  }
  
  .stepper-label {
    font-size: 12px;
    color: #333;
    position: relative;
    z-index: 2;
    white-space: nowrap;
    transition: all 0.3s;
  }
  
  /* Responsive styles for smaller screens */
  @media (max-width: 480px) {
    .stepper {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 20px 8px;
      padding: 0 4px;
    }
    
    .stepper-item {
      margin: 0;
      padding: 0;
    }
    
    .stepper-circle {
      width: 24px;
      height: 24px;
      border-radius: 12px;
      margin-bottom: 8px;
    }
    
    .stepper-label {
      font-size: 10px;
    }
  }
`

export default function WorkflowStepper({ currentStep, stepLabels = defaultStepLabels }: Props) {
  // Filter out any empty items (needed when App.tsx keeps passing all labels)
  const displayedLabels = stepLabels.filter(label => label.trim() !== '');
  
  return (
    <>
      <style>{stepperStyles}</style>
    <motion.ul
      className="stepper"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      >
        {displayedLabels.map((label, idx) => {
          const stepNum = idx + 1;
          const isActive = stepNum === currentStep;
          const isDone = stepNum < currentStep;

        return (
          <motion.li
            key={label}
              className="stepper-item"
          >
            <motion.div
                className="stepper-circle"
              variants={circleVariants}
              animate={isActive || isDone ? 'active' : 'inactive'}
                transition={{ type: 'spring', stiffness: 300 }}
            />
            <motion.div
                className="stepper-label"
              variants={labelVariants}
              animate={isActive || isDone ? 'active' : 'inactive'}
                transition={{ duration: 0.3 }}
            >
              {label}
            </motion.div>
          </motion.li>
          );
      })}
    </motion.ul>
    </>
  );
}

import React from 'react'

interface Props {
  value: number
  onChange: (value: number) => void
}

export default function InnovationSlider({ value, onChange }: Props) {
  return (
    <div className="innovation-slider">
      <label>靶点创新度</label>
      <div className="slider-row">
        <input
          type="range"
          min="1"
          max="10"
          value={value}
          onChange={e => onChange(Number(e.target.value))}
        />
        <span className="value">{value}</span>
      </div>
      <div className="description">
        {value <= 3 ? '选择经典、验证充分的靶点' :
         value <= 7 ? '平衡创新性与可靠性' :
                     '优先考虑新颖、未被充分研究的靶点'}
      </div>

      <style>{`
        .innovation-slider {
          margin: 16px 0;
          padding: 12px;
          background: #f8fafc;
          border-radius: 8px;
          border: 1px solid #e2e8f0;
        }
        
        label {
          display: block;
          font-size: 14px;
          color: #64748b;
          margin-bottom: 8px;
        }
        
        .slider-row {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        
        input[type="range"] {
          flex: 1;
          height: 4px;
          background: #e2e8f0;
          border-radius: 2px;
          -webkit-appearance: none;
        }
        
        input[type="range"]::-webkit-slider-thumb {
          -webkit-appearance: none;
          width: 16px;
          height: 16px;
          border-radius: 50%;
          background: #4f46e5;
          cursor: pointer;
          transition: all 0.2s;
        }
        
        input[type="range"]::-webkit-slider-thumb:hover {
          transform: scale(1.2);
        }
        
        .value {
          font-size: 16px;
          font-weight: 500;
          color: #4f46e5;
          min-width: 24px;
          text-align: center;
        }
        
        .description {
          margin-top: 8px;
          font-size: 13px;
          color: #94a3b8;
          font-style: italic;
        }
      `}</style>
    </div>
  )
}

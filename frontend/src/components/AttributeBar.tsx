import React, { useEffect, useRef, useState } from 'react';
import type { Attributes, Vitals } from '../types';

interface AttributeBarProps {
  attributes: Attributes;
  vitals: Vitals;
}

const ATTRIBUTE_NAMES: Record<string, string> = {
  STR: '力量',
  DEX: '敏捷',
  CON: '体质',
  INT: '智力',
  WIS: '感知',
  CHA: '魅力'
};

interface AnimationState {
    id: number;
    diff: number;
    type: 'positive' | 'negative';
}

const VitalDisplay: React.FC<{ 
    label: string; 
    value: number; 
    max?: number; 
    isSanity?: boolean; 
}> = ({ label, value, max, isSanity }) => {
    const prevValueRef = useRef(value);
    const [animations, setAnimations] = useState<AnimationState[]>([]);
    const [isShaking, setIsShaking] = useState(false);

    useEffect(() => {
        if (value !== prevValueRef.current) {
            const diff = value - prevValueRef.current;
            
            // Only animate significant updates (skip initial mount effectively if diff is huge? No, all updates valid)
            const type = diff > 0 ? 'positive' : 'negative';
            
            const newAnim: AnimationState = {
                id: Date.now(),
                diff,
                type
            };

            setAnimations(prev => [...prev, newAnim]);
            
            // Trigger Shake on damage
            if (diff < 0) {
                setIsShaking(true);
                setTimeout(() => setIsShaking(false), 400); // Match CSS animation duration
            }

            // Cleanup animation element after it finishes
            setTimeout(() => {
                setAnimations(prev => prev.filter(a => a.id !== newAnim.id));
            }, 1500); // Match CSS duration

            prevValueRef.current = value;
        }
    }, [value]);

    return (
        <div className={`vital-bar vital-container ${isShaking ? 'shaking' : ''}`}>
            <span className="vital-label">{label}</span>
            <span className={`vital-value ${isSanity ? 'sanity' : ''}`}>
                {value} {max !== undefined ? `/ ${max}` : ''}
            </span>
            {animations.map(anim => (
                 <span 
                    key={anim.id}
                    className={`vital-popup ${isSanity ? `sanity-${anim.type}` : anim.type}`}
                >
                    {anim.diff > 0 ? '+' : ''}{anim.diff}
                </span>
            ))}
        </div>
    );
};

export const AttributeBar: React.FC<AttributeBarProps> = ({ attributes, vitals }) => {
  return (
    <div className="panel attributes-panel">
      <h3 className="panel-header">角色状态</h3>
      
      <div className="vitals">
        <VitalDisplay label="生命值" value={vitals.hp} max={vitals.maxHp} />
        <VitalDisplay label="理智值" value={vitals.sanity} isSanity />
      </div>

      <div className="stats-grid">
        {Object.entries(attributes).map(([key, value]) => (
          <div key={key} className="stat-item">
            <span className="stat-label">{ATTRIBUTE_NAMES[key] || key}</span>
            <span className="stat-value">{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

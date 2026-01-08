import React from 'react';
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

export const AttributeBar: React.FC<AttributeBarProps> = ({ attributes, vitals }) => {
  return (
    <div className="panel attributes-panel">
      <h3 className="panel-header">角色状态</h3>
      
      <div className="vitals">
        <div className="vital-bar">
          <span className="vital-label">生命值</span>
          <span className="vital-value">{vitals.hp} / {vitals.maxHp}</span>
        </div>
        <div className="vital-bar">
          <span className="vital-label">理智值</span>
          <span className="vital-value sanity">{vitals.sanity} / {vitals.maxSanity}</span>
        </div>
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

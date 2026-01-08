import React from 'react';
import type { Attributes, Vitals } from '../types';

interface AttributeBarProps {
  attributes: Attributes;
  vitals: Vitals;
}

export const AttributeBar: React.FC<AttributeBarProps> = ({ attributes, vitals }) => {
  return (
    <div className="panel attributes-panel">
      <h3 className="panel-header">Character Status</h3>
      
      <div className="vitals">
        <div className="vital-bar">
          <span className="vital-label">HP</span>
          <span className="vital-value">{vitals.hp} / {vitals.maxHp}</span>
        </div>
        <div className="vital-bar">
          <span className="vital-label">SANITY</span>
          <span className="vital-value sanity">{vitals.sanity} / {vitals.maxSanity}</span>
        </div>
      </div>

      <div className="stats-grid">
        {Object.entries(attributes).map(([key, value]) => (
          <div key={key} className="stat-item">
            <span className="stat-label">{key}</span>
            <span className="stat-value">{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

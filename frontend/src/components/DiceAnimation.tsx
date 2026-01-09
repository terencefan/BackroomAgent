import React, { useEffect, useState } from 'react';

interface DiceAnimationProps {
  type: 'd6' | 'd20' | 'd100';
  result: number;
  reason?: string;
  onComplete: () => void;
}

export const DiceAnimation: React.FC<DiceAnimationProps> = ({ type, result, reason, onComplete }) => {
  const [currentValue, setCurrentValue] = useState(1);
  const [scale, setScale] = useState(0.5);
  const [opacity, setOpacity] = useState(0);

  useEffect(() => {
    // Fade in
    setTimeout(() => {
        setScale(1);
        setOpacity(1);
    }, 50);

    const maxVal = type === 'd20' ? 20 : (type === 'd6' ? 6 : 100);
    let steps = 20;
    let speed = 50;

    const interval = setInterval(() => {
        setCurrentValue(Math.floor(Math.random() * maxVal) + 1);
        steps--;
        if (steps <= 0) {
            clearInterval(interval);
            setCurrentValue(result);
            
            // Hold result then exit
            setTimeout(() => {
                setOpacity(0);
                setScale(1.5); // Zoom out effect
                setTimeout(onComplete, 500);
            }, 1000);
        } else {
            // Slow down as we get closer
            if (steps < 5) speed += 100;
        }
    }, speed);

    return () => clearInterval(interval);
  }, [type, result, onComplete]);

  return (
    <div style={{
        position: 'fixed',
        top: 0, left: 0, right: 0, bottom: 0,
        backgroundColor: 'rgba(0,0,0,0.7)',
        zIndex: 2000,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        transition: 'opacity 0.5s ease',
        opacity: opacity,
        backdropFilter: 'blur(5px)'
    }}>
        <div style={{
            color: '#eab308',
            fontSize: '1.5rem',
            marginBottom: '40px',
            textShadow: '0 0 10px rgba(234, 179, 8, 0.5)',
            transform: `scale(${scale})`,
            transition: 'transform 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275)'
        }}>
            {reason || 'DICE ROLL'}
        </div>
        
        <div style={{
            position: 'relative',
            width: '150px',
            height: '150px',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            transform: `scale(${scale})`,
            transition: 'transform 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275)'
        }}>
            {/* Hexagon shape for D20 / Circle for D100 / Square for D6 */}
            <div style={{
                position: 'absolute',
                width: '100%',
                height: '100%',
                backgroundColor: '#1a1a1a',
                border: '4px solid #eab308',
                borderRadius: type === 'd100' ? '50%' : (type === 'd6' ? '10%' : '20%'),
                boxShadow: '0 0 30px rgba(234, 179, 8, 0.3), inset 0 0 20px rgba(0,0,0,0.8)',
                transform: 'rotate(45deg)'
            }} />
            
            <span style={{
                position: 'relative',
                fontSize: '4rem',
                fontWeight: 'bold',
                color: '#fff',
                fontFamily: 'monospace',
                textShadow: '0 0 10px #000'
            }}>
                {currentValue}
            </span>
        </div>
        
        <div style={{
            marginTop: '40px',
            color: '#888',
            fontSize: '1rem'
        }}>
            {type.toUpperCase()}
        </div>
    </div>
  );
};

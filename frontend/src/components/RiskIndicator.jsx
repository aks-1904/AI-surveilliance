
import React from 'react';

const RiskIndicator = ({ alerts = [] }) => {
  const calculateCurrentRisk = () => {
    if (alerts.length === 0) return 'LOW';
    
    const recent = alerts.slice(0, 5);
    const highRisk = recent.filter(a => a.event?.risk_level === 'HIGH' || a.event?.risk_level === 'CRITICAL').length;
    
    if (highRisk >= 2) return 'HIGH';
    if (highRisk >= 1) return 'MEDIUM';
    return 'LOW';
  };

  const risk = calculateCurrentRisk();

  const getRiskConfig = () => {
    switch (risk) {
      case 'HIGH':
        return {
          color: 'bg-red-600',
          text: 'High Risk',
          icon: '🚨',
          bgColor: 'bg-red-50',
          textColor: 'text-red-900',
          borderColor: 'border-red-200'
        };
      case 'MEDIUM':
        return {
          color: 'bg-orange-500',
          text: 'Medium Risk',
          icon: '⚠️',
          bgColor: 'bg-orange-50',
          textColor: 'text-orange-900',
          borderColor: 'border-orange-200'
        };
      default:
        return {
          color: 'bg-green-500',
          text: 'Low Risk',
          icon: '✅',
          bgColor: 'bg-green-50',
          textColor: 'text-green-900',
          borderColor: 'border-green-200'
        };
    }
  };

  const config = getRiskConfig();

  return (
    <div className={`rounded-lg shadow-md p-4 border ${config.bgColor} ${config.borderColor}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-600 text-sm font-medium">Current Risk Level</p>
          <p className={`text-2xl font-bold mt-1 ${config.textColor}`}>{config.text}</p>
        </div>
        <div className="text-5xl">{config.icon}</div>
      </div>
      <div className="mt-3">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className={`h-2 rounded-full ${config.color} transition-all duration-500`}
            style={{ width: risk === 'HIGH' ? '100%' : risk === 'MEDIUM' ? '60%' : '30%' }}
          ></div>
        </div>
      </div>
    </div>
  );
};

export default RiskIndicator;
import React from 'react';
import { ShieldAlert, TrendingUp } from 'lucide-react';

interface ProbabilityGaugeProps {
  probability: number; // 0.0 to 1.0
  baselineProbability?: number;
  riskLevel: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL' | string;
  horizonHours?: number;
  modelVersion?: string;
  generatedAt?: string;
}

export const ProbabilityGauge: React.FC<ProbabilityGaugeProps> = ({
  probability,
  baselineProbability = 0.3628,
  riskLevel,
  horizonHours = 24,
  modelVersion = '1.0.0',
  generatedAt,
}) => {
  const pct = Math.round(probability * 100);
  const basePct = Math.round(baselineProbability * 100);

  // Stroke circumference calculation for SVG circle
  const radius = 78;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (pct / 100) * circumference;

  const riskConfig: Record<string, { color: string; bg: string; text: string; badge: string; desc: string }> = {
    LOW: {
      color: '#10b981',
      bg: 'bg-emerald-500/10',
      text: 'text-emerald-400',
      badge: 'border-emerald-500/30 text-emerald-400 bg-emerald-950/40',
      desc: 'Quiet solar state. Nominal background X-ray flux with low flare likelihood.',
    },
    MODERATE: {
      color: '#f59e0b',
      bg: 'bg-amber-500/10',
      text: 'text-amber-400',
      badge: 'border-amber-500/30 text-amber-400 bg-amber-950/40',
      desc: 'Moderate solar magnetic activity. Pre-flare micro-surges detected.',
    },
    HIGH: {
      color: '#f97316',
      bg: 'bg-orange-500/10',
      text: 'text-orange-400',
      badge: 'border-orange-500/30 text-orange-400 bg-orange-950/40',
      desc: 'Elevated flare probability. Strong magnetic complexity and flux gradients observed.',
    },
    CRITICAL: {
      color: '#ef4444',
      bg: 'bg-red-500/10',
      text: 'text-red-400',
      badge: 'border-red-500/30 text-red-400 bg-red-950/40',
      desc: 'High risk of strong flare event. Extreme active region activity or recent M+ precursor sequence.',
    },
  };

  const currentCfg = riskConfig[riskLevel] || riskConfig.HIGH;

  return (
    <div className="bg-[#0b1021]/80 backdrop-blur-md rounded-2xl border border-slate-800/80 p-6 flex flex-col justify-between relative overflow-hidden shadow-xl">
      {/* Subtle background glow */}
      <div
        className="absolute -right-16 -top-16 w-48 h-48 rounded-full blur-3xl pointer-events-none opacity-20"
        style={{ backgroundColor: currentCfg.color }}
      />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <ShieldAlert className="w-4 h-4 text-amber-400" />
          <h3 className="text-xs font-mono uppercase tracking-widest text-slate-300 font-bold">
            24-Hour Flare Forecast
          </h3>
        </div>
        <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold border ${currentCfg.badge}`}>
          {riskLevel} RISK
        </span>
      </div>

      {/* Radial Gauge & Numbers */}
      <div className="my-6 flex flex-col sm:flex-row items-center justify-center gap-8">
        <div className="relative w-44 h-44 flex items-center justify-center">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 180 180">
            {/* Background track */}
            <circle
              cx="90"
              cy="90"
              r={radius}
              className="stroke-slate-800/80"
              strokeWidth="12"
              fill="transparent"
            />
            {/* Calibrated Probability stroke */}
            <circle
              cx="90"
              cy="90"
              r={radius}
              stroke={currentCfg.color}
              strokeWidth="12"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              fill="transparent"
              className="transition-all duration-1000 ease-out"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
            <span className="text-4xl font-black tracking-tight text-white font-mono">{pct}%</span>
            <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider -mt-0.5">
              M-Class+ Prob.
            </span>
          </div>
        </div>

        {/* Forecast Metadata Breakdown */}
        <div className="space-y-3 max-w-xs text-left">
          <div>
            <span className="text-[11px] text-slate-400 font-mono">FORECAST TARGET:</span>
            <p className="text-sm font-semibold text-slate-100">
              ≥ M1.0 Solar Flare in next {horizonHours} hours
            </p>
          </div>

          <div className="flex items-center gap-3 text-xs font-mono bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
            <TrendingUp className="w-4 h-4 text-sky-400" />
            <div>
              <span className="text-slate-400 block text-[10px]">PERSISTENCE BASELINE:</span>
              <span className="text-slate-200 font-bold">{basePct}% probability</span>
            </div>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed font-sans">{currentCfg.desc}</p>
        </div>
      </div>

      {/* Footer Info */}
      <div className="pt-3 border-t border-slate-800/60 flex items-center justify-between text-[11px] font-mono text-slate-400">
        <span>Model: v{modelVersion} (Calibrated)</span>
        {generatedAt && (
          <span>Updated: {new Date(generatedAt).toLocaleTimeString()} UTC</span>
        )}
      </div>
    </div>
  );
};

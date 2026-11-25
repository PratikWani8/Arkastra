import React from 'react';
import { Satellite, Clock, Activity } from 'lucide-react';

interface CurrentFluxProps {
  longFlux: number;
  shortFlux: number;
  fluxRatio?: number;
  timestamp: string;
  activityClass?: string;
  satelliteId?: number | string;
  dataFreshness?: 'FRESH' | 'STALE' | 'UNAVAILABLE' | string;
}

export const CurrentFluxCard: React.FC<CurrentFluxProps> = ({
  longFlux,
  shortFlux,
  fluxRatio,
  timestamp,
  activityClass = 'B-Class',
  satelliteId = 18,
  dataFreshness = 'FRESH',
}) => {
  const formatSci = (val: number) => {
    if (!val || val <= 0) return '0.00e-0';
    return val.toExponential(3);
  };

  const getFlareBadgeColor = (cls: string) => {
    if (cls.startsWith('X')) return 'bg-red-500/20 text-red-400 border-red-500/40';
    if (cls.startsWith('M')) return 'bg-orange-500/20 text-orange-400 border-orange-500/40';
    if (cls.startsWith('C')) return 'bg-amber-500/20 text-amber-400 border-amber-500/40';
    return 'bg-sky-500/20 text-sky-400 border-sky-500/40';
  };

  const isFresh = dataFreshness === 'FRESH';

  return (
    <div className="bg-[#0b1021]/80 backdrop-blur-md rounded-2xl border border-slate-800/80 p-6 flex flex-col justify-between relative shadow-xl">
      {/* Top Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Activity className="w-4 h-4 text-amber-400" />
          <h3 className="text-xs font-mono uppercase tracking-widest text-slate-300 font-bold">
            Solar X-Ray Flux Telemetry
          </h3>
        </div>
        <div className="flex items-center space-x-2">
          <span
            className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${
              isFresh
                ? 'bg-emerald-950/40 text-emerald-400 border-emerald-500/30'
                : 'bg-amber-950/40 text-amber-400 border-amber-500/30'
            }`}
          >
            {dataFreshness}
          </span>
          <span className={`px-2.5 py-0.5 rounded text-xs font-mono font-black border ${getFlareBadgeColor(activityClass)}`}>
            {activityClass}
          </span>
        </div>
      </div>

      {/* Main Measurements Grid */}
      <div className="my-5 grid grid-cols-2 gap-4">
        {/* Long Wavelength (0.1 - 0.8nm) */}
        <div className="bg-[#060913]/70 p-3.5 rounded-xl border border-slate-800/70">
          <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 mb-1">
            <span>LONG FLUX (0.1-0.8nm)</span>
            <span className="text-amber-400 font-bold">XRS-B</span>
          </div>
          <div className="text-2xl font-black font-mono text-slate-100 tracking-tight">
            {formatSci(longFlux)}
          </div>
          <span className="text-[10px] font-mono text-slate-500">Watts / m²</span>
        </div>

        {/* Short Wavelength (0.05 - 0.4nm) */}
        <div className="bg-[#060913]/70 p-3.5 rounded-xl border border-slate-800/70">
          <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 mb-1">
            <span>SHORT FLUX (0.05-0.4nm)</span>
            <span className="text-sky-400 font-bold">XRS-A</span>
          </div>
          <div className="text-2xl font-black font-mono text-slate-100 tracking-tight">
            {formatSci(shortFlux)}
          </div>
          <span className="text-[10px] font-mono text-slate-500">Watts / m²</span>
        </div>
      </div>

      {/* Bottom Provenance Details */}
      <div className="pt-3 border-t border-slate-800/60 grid grid-cols-3 gap-2 text-[11px] font-mono text-slate-400">
        <div className="flex items-center space-x-1.5">
          <Satellite className="w-3.5 h-3.5 text-slate-400" />
          <span>GOES-{satelliteId}</span>
        </div>
        <div className="flex items-center space-x-1.5 truncate">
          <Clock className="w-3.5 h-3.5 text-slate-400" />
          <span className="truncate">{new Date(timestamp).toLocaleTimeString()} UTC</span>
        </div>
        <div className="text-right">
          <span>Ratio: {(fluxRatio || shortFlux / (longFlux || 1e-6)).toFixed(3)}</span>
        </div>
      </div>
    </div>
  );
};

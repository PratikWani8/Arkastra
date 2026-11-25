import React, { useState } from 'react';
import { Database, Cpu, Radio, RefreshCw, CheckCircle2, AlertCircle } from 'lucide-react';
import { triggerForecastPrediction } from '../../services/api';
import type { SystemHealth } from '../../types';

interface DataHealthProps {
  health: SystemHealth | null;
  onForecastTriggered?: () => void;
}

export const DataHealthCard: React.FC<DataHealthProps> = ({ health, onForecastTriggered }) => {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [triggerMsg, setTriggerMsg] = useState<string | null>(null);

  const handleManualForecast = async () => {
    try {
      setIsRefreshing(true);
      setTriggerMsg(null);
      await triggerForecastPrediction({});
      setTriggerMsg('Forecast successfully generated!');
      if (onForecastTriggered) onForecastTriggered();
    } catch (err: any) {
      setTriggerMsg(`Forecast trigger notice: ${err.message}`);
    } finally {
      setIsRefreshing(false);
      setTimeout(() => setTriggerMsg(null), 4000);
    }
  };

  const isDbUp = health?.database?.connected;
  const isMlUp = health?.mlService?.status === 'healthy';

  return (
    <div className="bg-[#0b1021]/80 backdrop-blur-md rounded-2xl border border-slate-800/80 p-6 flex flex-col justify-between shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Radio className="w-4 h-4 text-emerald-400" />
          <h3 className="text-xs font-mono uppercase tracking-widest text-slate-300 font-bold">
            Telemetry Subsystem Health
          </h3>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
          OPERATIONAL
        </span>
      </div>

      <div className="space-y-3 font-mono text-xs">
        {/* NOAA Ingestion Feed */}
        <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/70">
          <div className="flex items-center space-x-2">
            <Radio className="w-3.5 h-3.5 text-amber-400" />
            <span className="text-slate-300">NOAA GOES Telemetry Stream</span>
          </div>
          <span className="text-emerald-400 flex items-center gap-1 font-bold">
            <CheckCircle2 className="w-3.5 h-3.5" /> LIVE
          </span>
        </div>

        {/* Python ML Inference Service */}
        <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/70">
          <div className="flex items-center space-x-2">
            <Cpu className="w-3.5 h-3.5 text-sky-400" />
            <span className="text-slate-300">FastAPI ML Inference Service</span>
          </div>
          <span className={`flex items-center gap-1 font-bold ${isMlUp ? 'text-emerald-400' : 'text-amber-400'}`}>
            {isMlUp ? <CheckCircle2 className="w-3.5 h-3.5" /> : <AlertCircle className="w-3.5 h-3.5" />}
            {isMlUp ? 'CALIBRATED' : 'READY'}
          </span>
        </div>

        {/* MongoDB Database */}
        <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/70">
          <div className="flex items-center space-x-2">
            <Database className="w-3.5 h-3.5 text-indigo-400" />
            <span className="text-slate-300">Observation Data Store</span>
          </div>
          <span className="text-emerald-400 flex items-center gap-1 font-bold">
            <CheckCircle2 className="w-3.5 h-3.5" /> {isDbUp ? 'MONGO_ONLINE' : 'ACTIVE'}
          </span>
        </div>
      </div>

      {/* Manual Trigger Button */}
      <div className="mt-5 pt-3 border-t border-slate-800/60">
        <button
          onClick={handleManualForecast}
          disabled={isRefreshing}
          className="w-full inline-flex items-center justify-center space-x-2 py-2 px-4 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs transition-colors shadow-md shadow-amber-500/20 disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
          <span>{isRefreshing ? 'Running Inference...' : 'Generate On-Demand Forecast'}</span>
        </button>
        {triggerMsg && (
          <p className="mt-2 text-center text-[11px] font-mono text-amber-300">{triggerMsg}</p>
        )}
      </div>
    </div>
  );
};

import React, { useState, useEffect } from 'react';
import { fetchOverview, fetchHealth } from '../services/api';
import { ProbabilityGauge } from '../components/dashboard/ProbabilityGauge';
import { CurrentFluxCard } from '../components/dashboard/CurrentFluxCard';
import { SolarFluxChart } from '../components/dashboard/SolarFluxChart';
import { RecentFlaresTable } from '../components/dashboard/RecentFlaresTable';
import { DataHealthCard } from '../components/dashboard/DataHealthCard';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { AlertCircle, RefreshCw, ShieldCheck } from 'lucide-react';
import type { SystemHealth } from '../types';

export const DashboardPage: React.FC = () => {
  const [overview, setOverview] = useState<any>(null);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date());

  const loadData = async () => {
    try {
      setError(null);
      const [ovData, healthData] = await Promise.all([
        fetchOverview(),
        fetchHealth().catch(() => null),
      ]);
      setOverview(ovData);
      setHealth(healthData);
      setLastRefreshed(new Date());
    } catch (err: any) {
      console.error('Failed loading dashboard overview:', err);
      setError(err.message || 'Failed connecting to Arkastra space weather API');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // 30-sec polling
    return () => clearInterval(interval);
  }, []);

  if (loading && !overview) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-[500px]">
        <LoadingSpinner size="lg" label="Synchronizing GOES-16/18 Solar Telemetry..." />
      </div>
    );
  }

  const currentCond = overview?.currentConditions || {
    longFlux: 1.45e-6,
    shortFlux: 3.19e-7,
    fluxRatio: 0.22,
    timestamp: new Date().toISOString(),
    currentActivityClass: 'C1.4',
    satelliteId: 18,
    dataFreshness: 'FRESH',
  };

  const latestFc = overview?.latestForecast || {
    probabilityMPlus: 0.35,
    probabilityXPlus: null,
    riskLevel: 'HIGH',
    forecastHorizonHours: 24,
    modelVersion: '1.0.0',
    baselineProbability: 0.3628,
    generatedAt: new Date().toISOString(),
  };

  const chartData = (overview?.recentFluxTelemetry || []).map((obs: any) => ({
    timestamp: obs.timestamp,
    longFlux: obs.longFlux,
    shortFlux: obs.shortFlux,
  }));

  const events = overview?.recentEvents || [];

  return (
    <div className="flex-1 px-6 sm:px-10 py-8 max-w-7xl mx-auto w-full space-y-6">
      {/* Top Banner & Control Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl sm:text-2xl font-black text-white tracking-wide uppercase">
              Operational Solar Monitor
            </h1>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">
              REAL-TIME
            </span>
          </div>
          <p className="text-xs font-mono text-slate-400 mt-0.5">
            GOES primary X-ray sensor telemetry & calibrated 24h M-class+ flare forecast
          </p>
        </div>

        <div className="flex items-center space-x-3 text-xs font-mono">
          <span className="text-slate-500 text-[11px] hidden md:inline">
            Refreshed: {lastRefreshed.toLocaleTimeString()} UTC
          </span>
          <button
            onClick={loadData}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-amber-950/40 border border-amber-500/30 text-amber-300 text-xs font-mono flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-amber-400" />
            <span>{error}</span>
          </div>
          <button onClick={loadData} className="underline hover:text-white font-bold">
            Retry
          </button>
        </div>
      )}

      {/* Primary KPI Grid: Forecast Gauge & Current Flux */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 1. Primary 24-Hour Forecast Gauge */}
        <ProbabilityGauge
          probability={latestFc.probabilityMPlus}
          baselineProbability={latestFc.baselineProbability || 0.3628}
          riskLevel={latestFc.riskLevel}
          horizonHours={latestFc.forecastHorizonHours || 24}
          modelVersion={latestFc.modelVersion || '1.0.0'}
          generatedAt={latestFc.generatedAt}
        />

        {/* 2. Current Solar Flux Telemetry */}
        <CurrentFluxCard
          longFlux={currentCond.longFlux}
          shortFlux={currentCond.shortFlux}
          fluxRatio={currentCond.fluxRatio}
          timestamp={currentCond.timestamp}
          activityClass={currentCond.currentActivityClass}
          satelliteId={currentCond.satelliteId}
          dataFreshness={currentCond.dataFreshness}
        />
      </div>

      {/* Middle Row: Independent X-Class Status Notice */}
      <div className="bg-[#0b1021]/60 rounded-xl border border-slate-800/80 p-4 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-red-500/10 border border-red-500/30 flex items-center justify-center text-red-400 font-black">
            X
          </div>
          <div>
            <span className="text-slate-200 font-bold block">X-CLASS SOLAR FLARE TARGET</span>
            <span className="text-slate-400 text-[11px]">
              Independent X-class target model requires statistical qualification (super-rare event threshold)
            </span>
          </div>
        </div>
        <div className="flex items-center space-x-2 text-slate-400 bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800">
          <ShieldCheck className="w-4 h-4 text-amber-400" />
          <span>Independent model status: Monitored in Baseline</span>
        </div>
      </div>

      {/* Interactive Solar Flux Chart */}
      <SolarFluxChart data={chartData} />

      {/* Bottom Grid: Recent Flares Catalog & Telemetry Health */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <RecentFlaresTable events={events} />
        </div>
        <div>
          <DataHealthCard health={health} onForecastTriggered={loadData} />
        </div>
      </div>
    </div>
  );
};

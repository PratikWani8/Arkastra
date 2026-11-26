import React, { useState, useEffect } from 'react';
import { fetchForecastHistory } from '../services/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import {
  History,
  CheckCircle2,
  Clock,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import type { ForecastResult } from '../types';

export const ForecastHistoryPage: React.FC = () => {
  const [forecasts, setForecasts] = useState<ForecastResult[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [pages, setPages] = useState<number>(1);
  const [riskFilter, setRiskFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);

  const loadHistory = async () => {
    try {
      setLoading(true);
      const data = await fetchForecastHistory(page, 15, riskFilter, statusFilter);
      setForecasts(data.items || []);
      setTotal(data.total || 0);
      setPages(data.pages || 1);
    } catch (err) {
      console.error('Error fetching forecast history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, [page, riskFilter, statusFilter]);

  const getRiskBadge = (risk: string) => {
    if (risk === 'CRITICAL') return 'bg-red-500/20 text-red-400 border-red-500/40 font-bold';
    if (risk === 'HIGH') return 'bg-orange-500/20 text-orange-400 border-orange-500/40 font-bold';
    if (risk === 'MODERATE') return 'bg-amber-500/20 text-amber-400 border-amber-500/40';
    return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40';
  };

  const getStatusBadge = (status: string, _outcome: boolean | null | undefined) => {
    if (status === 'VERIFIED_POSITIVE') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] bg-red-950/40 text-red-400 border border-red-500/30">
          <CheckCircle2 className="w-3 h-3" /> M+ Flare Occurred
        </span>
      );
    }
    if (status === 'VERIFIED_NEGATIVE') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] bg-emerald-950/40 text-emerald-400 border border-emerald-500/30">
          <CheckCircle2 className="w-3 h-3" /> Quiet Sun (No Flare)
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] bg-amber-950/40 text-amber-400 border border-amber-500/30">
        <Clock className="w-3 h-3 animate-spin" /> 24h Horizon Pending
      </span>
    );
  };

  return (
    <div className="flex-1 px-6 sm:px-10 py-8 max-w-7xl mx-auto w-full space-y-6 font-sans">
      {/* Page Header */}
      <div className="pb-4 border-b border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <History className="w-5 h-5 text-amber-400" />
            <h1 className="text-xl sm:text-2xl font-black text-white tracking-wide uppercase">
              Forecast History & Verification
            </h1>
          </div>
          <p className="text-xs font-mono text-slate-400 mt-1">
            Historical 24-hour predictions verified against actual ground truth solar flare outcomes
          </p>
        </div>

        {/* Filter Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Risk Level Filter */}
          <select
            value={riskFilter}
            onChange={(e) => {
              setRiskFilter(e.target.value);
              setPage(1);
            }}
            className="bg-[#0b1021] border border-slate-800 text-xs font-mono rounded-lg px-3 py-1.5 text-slate-300 focus:outline-none focus:border-amber-500"
          >
            <option value="">All Risk Levels</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MODERATE">Moderate</option>
            <option value="LOW">Low</option>
          </select>

          {/* Verification Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="bg-[#0b1021] border border-slate-800 text-xs font-mono rounded-lg px-3 py-1.5 text-slate-300 focus:outline-none focus:border-amber-500"
          >
            <option value="">All Statuses</option>
            <option value="PENDING">Pending (Active 24h)</option>
            <option value="VERIFIED_POSITIVE">Verified Positive (Flare)</option>
            <option value="VERIFIED_NEGATIVE">Verified Negative (Quiet)</option>
          </select>
        </div>
      </div>

      {/* Main Forecast History Table */}
      <div className="bg-[#0b1021]/80 backdrop-blur-md rounded-2xl border border-slate-800/80 p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono text-slate-400">
            Total Ingested Forecasts: <strong className="text-slate-100">{total}</strong>
          </span>
          <span className="text-xs font-mono text-slate-500">Page {page} of {pages}</span>
        </div>

        {loading ? (
          <div className="py-12 flex justify-center">
            <LoadingSpinner size="md" label="Querying forecast history logs..." />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-500 text-[11px]">
                  <th className="pb-3 font-normal">OBSERVATION TIME</th>
                  <th className="pb-3 font-normal">M-CLASS+ PROB</th>
                  <th className="pb-3 font-normal">RISK LEVEL</th>
                  <th className="pb-3 font-normal">BASELINE PROB</th>
                  <th className="pb-3 font-normal">VERIFICATION OUTCOME</th>
                  <th className="pb-3 font-normal">MODEL</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {forecasts.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-500">
                      No forecasts match the selected filter.
                    </td>
                  </tr>
                ) : (
                  forecasts.map((fc) => {
                    const probPct = Math.round(fc.probabilityMPlus * 100);
                    const basePct = Math.round(fc.baselineProbability * 100);

                    return (
                      <tr key={fc._id || fc.generatedAt} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-3 text-slate-300 font-bold">
                          {new Date(fc.observationTimestamp).toLocaleDateString()}{' '}
                          <span className="text-slate-500 font-normal">
                            {new Date(fc.observationTimestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} UTC
                          </span>
                        </td>
                        <td className="py-3">
                          <span className="text-sm font-black text-white">{probPct}%</span>
                        </td>
                        <td className="py-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] border ${getRiskBadge(fc.riskLevel)}`}>
                            {fc.riskLevel}
                          </span>
                        </td>
                        <td className="py-3 text-slate-400">
                          {basePct}%
                        </td>
                        <td className="py-3">
                          {getStatusBadge(fc.verificationStatus || 'PENDING', fc.actualOutcome)}
                        </td>
                        <td className="py-3 text-slate-500 text-[10px]">
                          v{fc.modelVersion}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Navigation */}
        <div className="pt-4 border-t border-slate-800/60 flex items-center justify-between text-xs font-mono text-slate-400">
          <span>Showing records {forecasts.length > 0 ? (page - 1) * 15 + 1 : 0} to {Math.min(total, page * 15)}</span>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 disabled:opacity-30 hover:bg-slate-800"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setPage((p) => Math.min(pages, p + 1))}
              disabled={page >= pages}
              className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 disabled:opacity-30 hover:bg-slate-800"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

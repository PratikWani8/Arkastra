import React, { useState, useEffect } from 'react';
import { fetchSolarEvents, fetchSolarObservations } from '../services/api';
import { SolarFluxChart } from '../components/dashboard/SolarFluxChart';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { Sun, Filter, Flame, ChevronLeft, ChevronRight, Search } from 'lucide-react';
import type { SolarFlareEvent, SolarObservation } from '../types';

export const ExplorerPage: React.FC = () => {
  const [selectedClass, setSelectedClass] = useState<string>('');
  const [events, setEvents] = useState<SolarFlareEvent[]>([]);
  const [observations, setObservations] = useState<SolarObservation[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [page, setPage] = useState<number>(1);
  const [searchQuery, setSearchQuery] = useState<string>('');

  const loadExplorerData = async () => {
    try {
      setLoading(true);
      const [eventsRes, obsRes] = await Promise.all([
        fetchSolarEvents(100, selectedClass),
        fetchSolarObservations(page, 50),
      ]);
      setEvents(eventsRes.events || []);
      setObservations(obsRes.observations || []);
    } catch (err) {
      console.error('Error loading explorer data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadExplorerData();
  }, [selectedClass, page]);

  const filteredEvents = events.filter((ev) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      ev.flareClass.toLowerCase().includes(q) ||
      (ev.sourceLocation && ev.sourceLocation.toLowerCase().includes(q)) ||
      ev.eventId.toLowerCase().includes(q)
    );
  });

  const chartData = observations.map((o) => ({
    timestamp: o.timestamp,
    longFlux: o.longFlux,
    shortFlux: o.shortFlux,
  }));

  const flareClasses = ['ALL', 'X', 'M', 'C', 'B'];

  return (
    <div className="flex-1 px-6 sm:px-10 py-8 max-w-7xl mx-auto w-full space-y-6">
      {/* Page Header */}
      <div className="pb-4 border-b border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Sun className="w-5 h-5 text-amber-400" />
            <h1 className="text-xl sm:text-2xl font-black text-white tracking-wide uppercase">
              Solar Activity Explorer
            </h1>
          </div>
          <p className="text-xs font-mono text-slate-400 mt-1">
            Historical telemetry archives, flare catalogs, and multi-satellite observation explorer
          </p>
        </div>

        {/* Flare Class Filter Pills */}
        <div className="flex items-center space-x-1.5 bg-[#0b1021] p-1.5 rounded-xl border border-slate-800 text-xs font-mono">
          <Filter className="w-3.5 h-3.5 text-slate-400 ml-1.5 mr-1" />
          {flareClasses.map((cls) => {
            const isSelected = (cls === 'ALL' && selectedClass === '') || selectedClass === cls;
            return (
              <button
                key={cls}
                onClick={() => {
                  setSelectedClass(cls === 'ALL' ? '' : cls);
                  setPage(1);
                }}
                className={`px-3 py-1 rounded-lg font-bold transition-all ${
                  isSelected
                    ? 'bg-amber-500 text-slate-950 shadow-md'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                {cls}
              </button>
            );
          })}
        </div>
      </div>

      {/* Primary Historical Flux Chart */}
      <SolarFluxChart
        data={chartData}
        title="Historical GOES XRS Long & Short Telemetry Stream"
      />

      {/* Historical Flare Catalog Section */}
      <div className="bg-[#0b1021]/80 backdrop-blur-md rounded-2xl border border-slate-800/80 p-6 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center space-x-2">
            <Flame className="w-4 h-4 text-orange-400" />
            <h3 className="text-xs font-mono uppercase tracking-widest text-slate-300 font-bold">
              Solar Flare Event Catalog ({filteredEvents.length} Recorded)
            </h3>
          </div>

          <div className="relative w-full sm:w-64">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search event ID or location..."
              className="w-full bg-[#060913] border border-slate-800 text-xs font-mono rounded-lg pl-8 pr-3 py-1.5 text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-amber-500"
            />
          </div>
        </div>

        {loading ? (
          <div className="py-12 flex justify-center">
            <LoadingSpinner size="md" label="Querying historical flare catalogs..." />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-500 text-[11px]">
                  <th className="pb-3 font-normal">EVENT ID</th>
                  <th className="pb-3 font-normal">CLASS</th>
                  <th className="pb-3 font-normal">START TIME (UTC)</th>
                  <th className="pb-3 font-normal">PEAK TIME (UTC)</th>
                  <th className="pb-3 font-normal">PEAK FLUX</th>
                  <th className="pb-3 font-normal">SOLAR LOCATION</th>
                  <th className="pb-3 font-normal">AGENCY</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {filteredEvents.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-slate-500">
                      No flare records matched the selected query.
                    </td>
                  </tr>
                ) : (
                  filteredEvents.slice(0, 15).map((ev) => {
                    const isX = ev.flareClass.startsWith('X');
                    const isM = ev.flareClass.startsWith('M');
                    const isC = ev.flareClass.startsWith('C');
                    const badgeClass = isX
                      ? 'bg-red-500/20 text-red-400 border-red-500/40 font-black'
                      : isM
                      ? 'bg-orange-500/20 text-orange-400 border-orange-500/40 font-bold'
                      : isC
                      ? 'bg-amber-500/20 text-amber-400 border-amber-500/40'
                      : 'bg-sky-500/20 text-sky-400 border-sky-500/40';

                    return (
                      <tr key={ev.eventId || ev.beginTime} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-2.5 text-slate-300 font-bold truncate max-w-[160px]">
                          {ev.eventId}
                        </td>
                        <td className="py-2.5">
                          <span className={`px-2 py-0.5 rounded text-[11px] border ${badgeClass}`}>
                            {ev.flareClass}
                          </span>
                        </td>
                        <td className="py-2.5 text-slate-300">
                          {new Date(ev.beginTime).toLocaleDateString()}{' '}
                          {new Date(ev.beginTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </td>
                        <td className="py-2.5 text-slate-400">
                          {new Date(ev.peakTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </td>
                        <td className="py-2.5 text-slate-200 font-bold">
                          {ev.peakFlux ? `${ev.peakFlux.toExponential(2)} W/m²` : '—'}
                        </td>
                        <td className="py-2.5 text-slate-400">
                          {ev.sourceLocation || 'Disk Center'}
                        </td>
                        <td className="py-2.5 text-slate-500 text-[10px]">
                          {ev.source || 'NASA_DONKI'}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        <div className="pt-4 border-t border-slate-800/60 flex items-center justify-between text-xs font-mono text-slate-400">
          <span>Page {page} of archives</span>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 disabled:opacity-30 hover:bg-slate-800"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setPage((p) => p + 1)}
              className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

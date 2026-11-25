import React from 'react';
import { Flame } from 'lucide-react';
import type { SolarFlareEvent } from '../../types';

interface RecentFlaresTableProps {
  events: SolarFlareEvent[];
}

export const RecentFlaresTable: React.FC<RecentFlaresTableProps> = ({ events }) => {
  const getBadgeStyle = (cls: string) => {
    const c = cls.toUpperCase();
    if (c.startsWith('X')) return 'bg-red-500/20 text-red-400 border-red-500/40 font-black';
    if (c.startsWith('M')) return 'bg-orange-500/20 text-orange-400 border-orange-500/40 font-bold';
    if (c.startsWith('C')) return 'bg-amber-500/20 text-amber-400 border-amber-500/40';
    return 'bg-sky-500/20 text-sky-400 border-sky-500/40';
  };

  return (
    <div className="bg-[#0b1021]/80 backdrop-blur-md rounded-2xl border border-slate-800/80 p-6 flex flex-col justify-between shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Flame className="w-4 h-4 text-orange-400" />
          <h3 className="text-xs font-mono uppercase tracking-widest text-slate-300 font-bold">
            Recent Solar Flare Events
          </h3>
        </div>
        <span className="text-xs font-mono text-slate-500">{events.length} Events Cataloged</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left font-mono text-xs">
          <thead>
            <tr className="border-b border-slate-800 text-slate-500 text-[11px]">
              <th className="pb-2.5 font-normal">CLASS</th>
              <th className="pb-2.5 font-normal">BEGIN (UTC)</th>
              <th className="pb-2.5 font-normal">PEAK (UTC)</th>
              <th className="pb-2.5 font-normal">PEAK FLUX</th>
              <th className="pb-2.5 font-normal">SOURCE</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50">
            {events.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-6 text-center text-slate-500">
                  No recent flare events recorded in current observation buffer.
                </td>
              </tr>
            ) : (
              events.slice(0, 7).map((ev) => (
                <tr key={ev.eventId || ev.beginTime} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-2.5">
                    <span className={`px-2 py-0.5 rounded text-[11px] border ${getBadgeStyle(ev.flareClass)}`}>
                      {ev.flareClass}
                    </span>
                  </td>
                  <td className="py-2.5 text-slate-300">
                    {new Date(ev.beginTime).toLocaleDateString([], { month: 'short', day: '2-digit' })}{' '}
                    {new Date(ev.beginTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </td>
                  <td className="py-2.5 text-slate-400">
                    {new Date(ev.peakTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </td>
                  <td className="py-2.5 text-slate-300 font-bold">
                    {ev.peakFlux ? `${ev.peakFlux.toExponential(2)} W/m²` : '—'}
                  </td>
                  <td className="py-2.5 text-slate-500 text-[10px]">
                    {ev.source || 'NASA_DONKI'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="pt-3 mt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px] font-mono text-slate-500">
        <span>Verified flare events ingested from NASA CCMC DONKI & NOAA SWPC</span>
      </div>
    </div>
  );
};

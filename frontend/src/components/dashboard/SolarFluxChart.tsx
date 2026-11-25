import React, { useState } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  CartesianGrid,
} from 'recharts';
import { BarChart2 } from 'lucide-react';

interface FluxDataPoint {
  timestamp: string;
  longFlux: number;
  shortFlux: number;
}

interface SolarFluxChartProps {
  data: FluxDataPoint[];
  title?: string;
}

export const SolarFluxChart: React.FC<SolarFluxChartProps> = ({
  data,
  title = 'Solar X-Ray Flux Dynamics (GOES-16/18)',
}) => {
  const [windowLimit, setWindowLimit] = useState<number>(48);

  const formattedData = data.slice(-windowLimit).map((d) => ({
    time: new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    longFlux: d.longFlux,
    shortFlux: d.shortFlux,
  }));

  const formatYAxis = (val: number) => {
    if (val >= 1e-4) return 'X';
    if (val >= 1e-5) return 'M';
    if (val >= 1e-6) return 'C';
    if (val >= 1e-7) return 'B';
    return val.toExponential(1);
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-[#090e1f] border border-slate-700 p-3 rounded-lg shadow-xl font-mono text-xs space-y-1">
          <p className="text-slate-400 font-semibold mb-1">{label} UTC</p>
          <div className="flex items-center space-x-2 text-amber-400">
            <span className="w-2 h-2 rounded-full bg-amber-400" />
            <span>Long (0.1-0.8nm):</span>
            <span className="font-bold">{payload[0]?.value?.toExponential(3)} W/m²</span>
          </div>
          <div className="flex items-center space-x-2 text-sky-400">
            <span className="w-2 h-2 rounded-full bg-sky-400" />
            <span>Short (0.05-0.4nm):</span>
            <span className="font-bold">{payload[1]?.value?.toExponential(3)} W/m²</span>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-[#0b1021]/80 backdrop-blur-md rounded-2xl border border-slate-800/80 p-6 flex flex-col justify-between shadow-xl">
      {/* Chart Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div className="flex items-center space-x-2">
          <BarChart2 className="w-4 h-4 text-amber-400" />
          <h3 className="text-xs font-mono uppercase tracking-widest text-slate-300 font-bold">
            {title}
          </h3>
        </div>

        <div className="flex items-center space-x-1.5 text-xs font-mono">
          <button
            onClick={() => setWindowLimit(12)}
            className={`px-2.5 py-1 rounded transition-colors ${
              windowLimit === 12 ? 'bg-amber-500 text-slate-950 font-bold' : 'bg-slate-900 text-slate-400 hover:text-white'
            }`}
          >
            6H
          </button>
          <button
            onClick={() => setWindowLimit(48)}
            className={`px-2.5 py-1 rounded transition-colors ${
              windowLimit === 48 ? 'bg-amber-500 text-slate-950 font-bold' : 'bg-slate-900 text-slate-400 hover:text-white'
            }`}
          >
            24H
          </button>
          <button
            onClick={() => setWindowLimit(200)}
            className={`px-2.5 py-1 rounded transition-colors ${
              windowLimit === 200 ? 'bg-amber-500 text-slate-950 font-bold' : 'bg-slate-900 text-slate-400 hover:text-white'
            }`}
          >
            7D
          </button>
        </div>
      </div>

      {/* Chart Canvas */}
      <div className="h-64 sm:h-72 w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={formattedData} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" opacity={0.6} />
            <XAxis
              dataKey="time"
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              fontFamily="monospace"
            />
            <YAxis
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              fontFamily="monospace"
              tickFormatter={formatYAxis}
              domain={['auto', 'auto']}
            />
            <Tooltip content={<CustomTooltip />} />
            
            {/* Standard Solar Flare Classification Thresholds */}
            <ReferenceLine y={1e-4} stroke="#ef4444" strokeDasharray="3 3" label={{ value: 'X-Class (1e-4)', fill: '#ef4444', fontSize: 10, position: 'insideTopRight' }} />
            <ReferenceLine y={1e-5} stroke="#f97316" strokeDasharray="3 3" label={{ value: 'M-Class (1e-5)', fill: '#f97316', fontSize: 10, position: 'insideTopRight' }} />
            <ReferenceLine y={1e-6} stroke="#eab308" strokeDasharray="3 3" label={{ value: 'C-Class (1e-6)', fill: '#eab308', fontSize: 10, position: 'insideTopRight' }} />

            <Line
              type="monotone"
              dataKey="longFlux"
              name="Long Flux (0.1-0.8nm)"
              stroke="#f59e0b"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: '#f59e0b' }}
            />
            <Line
              type="monotone"
              dataKey="shortFlux"
              name="Short Flux (0.05-0.4nm)"
              stroke="#38bdf8"
              strokeWidth={1.5}
              dot={false}
              activeDot={{ r: 4, fill: '#38bdf8' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Legend Footer */}
      <div className="pt-3 border-t border-slate-800/60 flex flex-wrap items-center justify-between text-[11px] font-mono text-slate-400 gap-2">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-1 bg-amber-500 rounded" />
            <span>Long Flux 0.1-0.8nm (Primary)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-1 bg-sky-400 rounded" />
            <span>Short Flux 0.05-0.4nm</span>
          </div>
        </div>
        <div className="flex items-center space-x-3 text-[10px]">
          <span className="text-red-400 font-bold">X: ≥1e-4</span>
          <span className="text-orange-400 font-bold">M: ≥1e-5</span>
          <span className="text-amber-400 font-bold">C: ≥1e-6</span>
        </div>
      </div>
    </div>
  );
};

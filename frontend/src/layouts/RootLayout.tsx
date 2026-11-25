import React, { useState, useEffect } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { Sun, Activity, BarChart3, History, Cpu } from 'lucide-react';
import { fetchHealth } from '../services/api';
import type { SystemHealth } from '../types';

export const RootLayout: React.FC = () => {
  const [health, setHealth] = useState<SystemHealth | null>(null);

  useEffect(() => {
    let isMounted = true;
    const check = async () => {
      try {
        const data = await fetchHealth();
        if (isMounted) setHealth(data);
      } catch {
        if (isMounted) setHealth(null);
      }
    };
    check();
    const timer = setInterval(check, 30000);
    return () => {
      isMounted = false;
      clearInterval(timer);
    };
  }, []);

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: Activity },
    { name: 'Activity Explorer', path: '/explorer', icon: Sun },
    { name: 'Model Evaluation', path: '/model-performance', icon: BarChart3 },
    { name: 'Forecast History', path: '/history', icon: History },
  ];

  return (
    <div className="min-h-screen bg-[#050811] text-slate-100 flex flex-col font-sans selection:bg-amber-500/30 selection:text-amber-200">
      {/* Top Header */}
      <header className="sticky top-0 z-50 border-b border-slate-800/80 bg-[#070b18]/90 backdrop-blur-md px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <NavLink to="/" className="flex items-center space-x-3 group">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-amber-500 to-red-600 flex items-center justify-center shadow-lg shadow-amber-500/20 group-hover:scale-105 transition-transform">
              <Sun className="w-5 h-5 text-slate-950 font-bold" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-lg font-black tracking-wider text-white">ARKASTRA</span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30 font-semibold">
                  GOES-16/18
                </span>
              </div>
              <p className="text-[11px] font-mono text-slate-400 -mt-0.5">Solar Flare Probability Forecaster</p>
            </div>
          </NavLink>
        </div>

        {/* Global Nav */}
        <nav className="hidden md:flex items-center space-x-1 bg-slate-900/60 p-1 rounded-xl border border-slate-800">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-amber-500 text-slate-950 shadow font-semibold'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }`
                }
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* System Telemetry Badges */}
        <div className="flex items-center space-x-3 text-xs font-mono">
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-slate-900/80 border border-slate-800">
            <span
              className={`w-2 h-2 rounded-full ${
                health?.status === 'healthy' ? 'bg-emerald-400 animate-pulse' : 'bg-red-500'
              }`}
            />
            <span className="text-slate-400 text-[11px]">API:</span>
            <span className="text-slate-200 font-semibold text-[11px]">
              {health?.status === 'healthy' ? 'ONLINE' : 'CONNECTING'}
            </span>
          </div>

          <div className="hidden lg:flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-slate-900/80 border border-slate-800">
            <Cpu className="w-3 h-3 text-amber-400" />
            <span className="text-slate-400 text-[11px]">ML:</span>
            <span className="text-slate-200 font-semibold text-[11px]">
              {health?.mlService?.status === 'healthy' ? 'READY' : 'OFFLINE'}
            </span>
          </div>
        </div>
      </header>

      {/* Main App Content */}
      <main className="flex-1 flex flex-col">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/70 bg-[#060914] px-6 py-4 text-xs font-mono text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-2">
        <div className="flex items-center space-x-2">
          <span>ARKASTRA Space Weather Intelligence</span>
          <span>•</span>
          <span>Data: NOAA SWPC & NASA DONKI</span>
        </div>
        <div>
          <span>Forecast Horizon: 24h M-Class+ Probability</span>
        </div>
      </footer>
    </div>
  );
};

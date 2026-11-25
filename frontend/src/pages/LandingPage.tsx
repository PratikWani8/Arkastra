import React from 'react';
import { Link } from 'react-router-dom';
import {
  Sun,
  ShieldAlert,
  Cpu,
  Radio,
  ArrowRight,
  Satellite,
  CheckCircle,
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  return (
    <div className="flex-1 flex flex-col bg-[#050811] text-slate-100 font-sans">
      {/* 1. Hero Section */}
      <section className="relative overflow-hidden py-20 px-6 sm:px-12 flex flex-col items-center text-center">
        {/* Background Radial Solar Glow */}
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] bg-gradient-to-b from-amber-500/15 via-red-600/10 to-transparent blur-3xl rounded-full pointer-events-none" />

        <div className="relative z-10 max-w-4xl mx-auto space-y-6">
          <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-mono font-medium">
            <Sun className="w-4 h-4 animate-spin" />
            <span>Operational Space Weather Intelligence Platform</span>
          </div>

          <h1 className="text-4xl sm:text-6xl font-black tracking-tight text-white uppercase font-sans leading-tight">
            Predicting Solar Activity
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 via-orange-500 to-red-500">
              Before It Happens.
            </span>
          </h1>

          <p className="text-slate-300 text-base sm:text-xl max-w-3xl mx-auto font-normal leading-relaxed">
            An intelligent solar monitoring and forecasting platform that transforms real-time GOES X-ray observations into calibrated 24-hour solar flare risk probabilities.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
            <Link
              to="/dashboard"
              className="inline-flex items-center space-x-2 px-7 py-3.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-sm transition-all shadow-xl shadow-amber-500/25 group"
            >
              <span>Explore Live Dashboard</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              to="/model-performance"
              className="inline-flex items-center space-x-2 px-7 py-3.5 rounded-xl bg-slate-900/90 hover:bg-slate-800 text-slate-200 border border-slate-700/80 font-semibold text-sm transition-all shadow-lg"
            >
              <Cpu className="w-4 h-4 text-amber-400" />
              <span>Understand the Science</span>
            </Link>
          </div>
        </div>
      </section>

      {/* 2. Space Weather Threat Briefing */}
      <section className="py-14 px-6 sm:px-12 bg-[#070c1a] border-y border-slate-800/80">
        <div className="max-w-6xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-10 space-y-2">
            <span className="text-xs font-mono text-amber-400 uppercase tracking-widest font-bold">
              Mission Critical Impact
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white">
              Why Solar Flare Forecasting Matters
            </h2>
            <p className="text-sm text-slate-400">
              Solar flares release bursts of electromagnetic radiation, driving geomagnetic storms and ionospheric disturbances that impact global critical infrastructure.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-[#0b1021] p-6 rounded-2xl border border-slate-800/80 space-y-3">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center text-amber-400">
                <Radio className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-slate-100">Satellite & GPS Navigation</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                M and X-class flares disrupt GNSS/GPS positioning signals and cause high-frequency radio blackouts across equatorial and sub-polar aviation corridors.
              </p>
            </div>

            <div className="bg-[#0b1021] p-6 rounded-2xl border border-slate-800/80 space-y-3">
              <div className="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center text-red-400">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-slate-100">Power Grids & Telemetry</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Geomagnetically induced currents (GICs) from coronal mass ejections following flares cause transformer saturation, relay tripping, and grid instability.
              </p>
            </div>

            <div className="bg-[#0b1021] p-6 rounded-2xl border border-slate-800/80 space-y-3">
              <div className="w-10 h-10 rounded-xl bg-sky-500/10 flex items-center justify-center text-sky-400">
                <Satellite className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-slate-100">Orbital Assets & Astronauts</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Enhanced X-ray and proton flux heats the upper thermosphere, increasing orbital drag on low-Earth orbit satellites and posing radiation hazards to EVA crews.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 3. Core Capabilities */}
      <section className="py-16 px-6 sm:px-12 max-w-6xl mx-auto w-full">
        <div className="text-center max-w-2xl mx-auto mb-12 space-y-2">
          <span className="text-xs font-mono text-amber-400 uppercase tracking-widest font-bold">
            Scientific Rigor
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white">
            Engineered For Probabilistic Accuracy
          </h2>
          <p className="text-sm text-slate-400">
            Arkastra does not output naive binary guesses; it produces calibrated probabilities tested against strict persistence benchmarks.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="flex items-start space-x-4 p-5 rounded-xl bg-slate-900/40 border border-slate-800">
            <CheckCircle className="w-6 h-6 text-emerald-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h4 className="text-sm font-bold text-slate-100">Continuous GOES Telemetry</h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                Ingests 1-minute cadence XRS measurements from primary NOAA GOES satellites (GOES-16 and GOES-18), monitoring both 0.05-0.4nm and 0.1-0.8nm wavelength bands.
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-4 p-5 rounded-xl bg-slate-900/40 border border-slate-800">
            <CheckCircle className="w-6 h-6 text-emerald-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h4 className="text-sm font-bold text-slate-100">Brier Skill Score Superiority</h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                Achieves a positive Brier Skill Score (BSS = +0.2096) on an untouched chronological test set, outperforming the standard space weather persistence baseline.
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-4 p-5 rounded-xl bg-slate-900/40 border border-slate-800">
            <CheckCircle className="w-6 h-6 text-emerald-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h4 className="text-sm font-bold text-slate-100">Strict Temporal Embargo</h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                Zero lookahead or target leakage. Evaluated with 24-hour chronological embargoes separating training, validation, and test datasets.
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-4 p-5 rounded-xl bg-slate-900/40 border border-slate-800">
            <CheckCircle className="w-6 h-6 text-emerald-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h4 className="text-sm font-bold text-slate-100">Platt Probability Calibration</h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                Raw classifier scores undergo sigmoid probability calibration on independent validation sets, aligning forecast percentages with observed physical event frequencies.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 4. Technology Stack & Data Sources */}
      <section className="py-14 px-6 sm:px-12 bg-[#070b18] border-t border-slate-800/80">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-8">
          <div className="space-y-3 max-w-md">
            <span className="text-xs font-mono text-amber-400 uppercase tracking-widest font-bold">
              Provenance & Infrastructure
            </span>
            <h3 className="text-2xl font-black text-white">Authentic Solar Observations</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Powered by real-time streams and historical catalogs from the NOAA Space Weather Prediction Center (SWPC), NOAA NCEI, and NASA CCMC DONKI.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <span className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-mono text-slate-300">
              FastAPI ML Engine
            </span>
            <span className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-mono text-slate-300">
              Node.js / Express
            </span>
            <span className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-mono text-slate-300">
              MongoDB
            </span>
            <span className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-mono text-slate-300">
              React + Vite + Tailwind
            </span>
            <span className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-mono text-slate-300">
              Scikit-Learn & XGBoost
            </span>
          </div>
        </div>
      </section>
    </div>
  );
};

import React from 'react';
import { Sun } from 'lucide-react';

interface LoadingSpinnerProps {
  label?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  label = 'Acquiring solar telemetry...',
  size = 'md',
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  return (
    <div className="flex flex-col items-center justify-center p-8 space-y-3">
      <Sun className={`${sizeClasses[size]} text-amber-500 animate-spin`} />
      {label && <p className="text-xs uppercase tracking-widest text-slate-400 font-mono">{label}</p>}
    </div>
  );
};

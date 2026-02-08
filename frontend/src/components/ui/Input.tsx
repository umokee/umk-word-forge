import React from 'react';
import { cn } from '@/lib/utils';

interface InputProps {
  label?: string;
  placeholder?: string;
  value?: string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  type?: string;
  className?: string;
  error?: string;
  hint?: string;
}

export function Input({
  label,
  placeholder,
  value,
  onChange,
  type = 'text',
  className,
  error,
  hint,
}: InputProps) {
  return (
    <div className={cn('flex flex-col gap-1.5', className)}>
      {label && (
        <label className="text-sm font-medium text-[#e0e0e0]">{label}</label>
      )}
      <input
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        className={cn(
          'bg-[#1e1e1e] border border-[#2a2a2a] focus:border-[#00ff88] text-[#e0e0e0] rounded-sm px-3 py-2 text-sm placeholder:text-[#666666] outline-none transition-colors',
          error && 'border-red-500 focus:border-red-500'
        )}
      />
      {error && <p className="text-xs text-red-500">{error}</p>}
      {hint && !error && <p className="text-xs text-[#666666]">{hint}</p>}
    </div>
  );
}

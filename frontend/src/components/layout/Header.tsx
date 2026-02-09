import React from 'react';
import { cn } from '@/lib/utils';

interface HeaderProps {
  title: string;
  subtitle?: string;
  className?: string;
}

export function Header({ title, subtitle, className }: HeaderProps) {
  return (
    <div className={cn('mb-6', className)}>
      <h1 className="text-lg font-bold uppercase tracking-wider text-[#00ff88]">
        [{title.toUpperCase()}]
      </h1>
      {subtitle && (
        <p className="mt-1 text-xs text-[#666666]">{subtitle}</p>
      )}
    </div>
  );
}

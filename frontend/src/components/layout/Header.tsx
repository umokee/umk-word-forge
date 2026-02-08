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
      <h1 className="text-2xl font-bold text-[#e0e0e0]">{title}</h1>
      {subtitle && (
        <p className="mt-1 text-sm text-[#888888]">{subtitle}</p>
      )}
    </div>
  );
}

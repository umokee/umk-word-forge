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
      <h1 className="text-2xl font-bold text-[#E8E8EC]">{title}</h1>
      {subtitle && (
        <p className="mt-1 text-sm text-[#8B8B96]">{subtitle}</p>
      )}
    </div>
  );
}

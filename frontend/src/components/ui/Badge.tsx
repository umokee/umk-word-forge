import React from 'react';
import { cn } from '@/lib/utils';

type BadgeVariant = 'default' | 'success' | 'error' | 'warning' | 'accent';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

const variantStyles: Record<BadgeVariant, string> = {
  default: 'bg-[#1C1C20] text-[#8B8B96]',
  success: 'bg-emerald-500/10 text-emerald-400',
  error: 'bg-red-500/10 text-red-400',
  warning: 'bg-amber-500/10 text-amber-400',
  accent: 'bg-indigo-500/10 text-indigo-400',
};

export function Badge({
  children,
  variant = 'default',
  className,
}: BadgeProps) {
  return (
    <span
      className={cn(
        'rounded-sm px-2 py-0.5 text-xs font-mono inline-flex items-center',
        variantStyles[variant],
        className
      )}
    >
      {children}
    </span>
  );
}

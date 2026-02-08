import React from 'react';
import { cn } from '@/lib/utils';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

export function Card({ children, className, onClick }: CardProps) {
  return (
    <div
      onClick={onClick}
      className={cn(
        'bg-[#141416] border border-[#2A2A30] rounded-sm p-4',
        onClick && 'cursor-pointer hover:border-[#3A3A42] transition-colors',
        className
      )}
    >
      {children}
    </div>
  );
}

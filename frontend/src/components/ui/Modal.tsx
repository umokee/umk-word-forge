import React, { useEffect, useCallback } from 'react';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export function Modal({ isOpen, onClose, title, children }: ModalProps) {
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    },
    [onClose]
  );

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [isOpen, handleKeyDown]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      onClick={onClose}
    >
      {/* Overlay */}
      <div className="absolute inset-0 bg-black/60" />

      {/* Modal content */}
      <div
        onClick={(e) => e.stopPropagation()}
        className={cn(
          'relative z-10 w-full max-w-lg bg-[#141416] border border-[#2A2A30] rounded-sm shadow-xl'
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#2A2A30] px-6 py-4">
          <h2 className="text-lg font-semibold text-[#E8E8EC]">{title}</h2>
          <button
            onClick={onClose}
            className="text-[#5C5C66] hover:text-[#E8E8EC] transition-colors rounded-sm p-1 hover:bg-[#1C1C20]"
          >
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-4">{children}</div>
      </div>
    </div>
  );
}

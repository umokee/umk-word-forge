import React from 'react';
import { cn } from '@/lib/utils';
import { Table, TableRow, TableCell } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import type { WordListItem } from '@/types';

interface WordTableProps {
  words: WordListItem[];
  onRowClick: (id: number) => void;
}

const levelBadgeColors: Record<number, string> = {
  0: 'bg-[#2a2a2a] text-[#666666]',
  1: 'bg-[#0a3d2a]/50 text-[#0d5c3d]',
  2: 'bg-[#0d5c3d]/50 text-[#108050]',
  3: 'bg-[#108050]/50 text-[#15a060]',
  4: 'bg-[#15a060]/50 text-[#00aa55]',
  5: 'bg-[#00aa55]/50 text-[#00cc6a]',
  6: 'bg-[#00cc6a]/30 text-[#00ff88]',
  7: 'bg-[#00ff88]/20 text-[#00ff88]',
};

const levelNames: Record<number, string> = {
  0: 'New',
  1: 'Seen',
  2: 'Familiar',
  3: 'Recognized',
  4: 'Learned',
  5: 'Practiced',
  6: 'Mastered',
  7: 'Perfected',
};

const cefrBadgeColors: Record<string, string> = {
  A1: 'bg-[#00ff88]/20 text-[#00ff88]',
  A2: 'bg-[#00cc6a]/20 text-[#00cc6a]',
  B1: 'bg-[#ffaa00]/20 text-[#ffaa00]',
  B2: 'bg-[#ff8800]/20 text-[#ff8800]',
  C1: 'bg-[#ff4444]/20 text-[#ff4444]',
  C2: 'bg-[#ff4444]/30 text-[#ff6666]',
};

export function WordTable({ words, onRowClick }: WordTableProps) {
  return (
    <Table headers={['Word', 'Translation', 'Level', 'CEFR', 'Freq Rank']}>
      {words.map((word) => (
        <TableRow key={word.id} onClick={() => onRowClick(word.id)}>
          <TableCell className="font-mono font-medium text-[#e0e0e0]">
            {word.english}
          </TableCell>
          <TableCell className="text-[#888888]">
            {word.translations.join(', ')}
          </TableCell>
          <TableCell>
            <span
              className={cn(
                'rounded-sm px-2 py-0.5 text-xs font-mono inline-flex items-center',
                levelBadgeColors[0]
              )}
            >
              {levelNames[0]}
            </span>
          </TableCell>
          <TableCell>
            {word.cefr_level ? (
              <span
                className={cn(
                  'rounded-sm px-2 py-0.5 text-xs font-mono inline-flex items-center',
                  cefrBadgeColors[word.cefr_level] ?? 'bg-[#1e1e1e] text-[#888888]'
                )}
              >
                {word.cefr_level}
              </span>
            ) : (
              <span className="text-[#666666]">--</span>
            )}
          </TableCell>
          <TableCell className="font-mono text-[#888888]">
            {word.frequency_rank != null ? `#${word.frequency_rank.toLocaleString()}` : '--'}
          </TableCell>
        </TableRow>
      ))}
    </Table>
  );
}

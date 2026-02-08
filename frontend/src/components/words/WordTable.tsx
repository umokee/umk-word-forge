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
  0: 'bg-gray-500/10 text-gray-400',
  1: 'bg-blue-500/10 text-blue-400',
  2: 'bg-cyan-500/10 text-cyan-400',
  3: 'bg-green-500/10 text-green-400',
  4: 'bg-yellow-500/10 text-yellow-400',
  5: 'bg-orange-500/10 text-orange-400',
  6: 'bg-purple-500/10 text-purple-400',
  7: 'bg-[#00ff88]/10 text-[#00ff88]',
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
  A1: 'bg-[#00ff88]/10 text-[#00ff88]',
  A2: 'bg-green-500/10 text-green-400',
  B1: 'bg-yellow-500/10 text-yellow-400',
  B2: 'bg-orange-500/10 text-orange-400',
  C1: 'bg-red-500/10 text-red-400',
  C2: 'bg-purple-500/10 text-purple-400',
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

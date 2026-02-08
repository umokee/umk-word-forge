import { useNavigate } from 'react-router-dom';
import { BookOpen, Layers, ArrowLeftRight, X } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';

interface TrainingModeOption {
  id: 'words' | 'phrasal' | 'irregular';
  title: string;
  subtitle: string;
  description: string;
  icon: React.ReactNode;
  path: string;
  color: string;
}

const TRAINING_MODES: TrainingModeOption[] = [
  {
    id: 'words',
    title: 'Слова',
    subtitle: '10,000+ слов',
    description:
      'Изучение английских слов с переводом, транскрипцией, примерами и словосочетаниями',
    icon: <BookOpen size={32} />,
    path: '/train/words',
    color: '#00ff88',
  },
  {
    id: 'phrasal',
    title: 'Фразовые глаголы',
    subtitle: '300+ фраз',
    description:
      'look up, give in, turn out — глаголы с частицами, которые меняют значение',
    icon: <Layers size={32} />,
    path: '/train/phrasal',
    color: '#00aaff',
  },
  {
    id: 'irregular',
    title: 'Неправильные глаголы',
    subtitle: '200+ глаголов',
    description:
      'go-went-gone — три формы глаголов, которые нужно запомнить',
    icon: <ArrowLeftRight size={32} />,
    path: '/train/irregular',
    color: '#ff6b6b',
  },
];

export default function TrainSelector() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      {/* Header */}
      <div className="sticky top-0 z-10 border-b border-[#2a2a2a] bg-[#0a0a0a] px-6 py-4">
        <div className="mx-auto flex max-w-2xl items-center justify-between">
          <h1 className="text-lg font-bold text-[#e0e0e0]">Выберите режим</h1>
          <button
            onClick={() => navigate('/')}
            className="shrink-0 rounded-sm p-1.5 text-[#666666] transition-colors hover:bg-[#1e1e1e] hover:text-[#e0e0e0]"
          >
            <X size={20} />
          </button>
        </div>
      </div>

      {/* Mode selection */}
      <div className="mx-auto max-w-2xl px-6 py-12">
        <div className="grid gap-4">
          {TRAINING_MODES.map((mode) => (
            <button
              key={mode.id}
              onClick={() => navigate(mode.path)}
              className="group relative w-full overflow-hidden rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] p-6 text-left transition-all hover:border-[#3a3a3a] hover:bg-[#252525]"
            >
              {/* Accent border on hover */}
              <div
                className="absolute inset-y-0 left-0 w-1 opacity-0 transition-opacity group-hover:opacity-100"
                style={{ backgroundColor: mode.color }}
              />

              <div className="flex items-start gap-5">
                {/* Icon */}
                <div
                  className="flex h-14 w-14 shrink-0 items-center justify-center rounded-sm"
                  style={{ backgroundColor: `${mode.color}10`, color: mode.color }}
                >
                  {mode.icon}
                </div>

                {/* Content */}
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h2 className="text-xl font-bold text-[#e0e0e0]">
                      {mode.title}
                    </h2>
                    <span className="rounded-sm bg-[#2a2a2a] px-2 py-0.5 text-xs text-[#888888]">
                      {mode.subtitle}
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-[#888888]">{mode.description}</p>
                </div>

                {/* Arrow */}
                <div className="flex h-14 items-center text-[#3a3a3a] transition-colors group-hover:text-[#666666]">
                  <svg
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <polyline points="9 18 15 12 9 6" />
                  </svg>
                </div>
              </div>
            </button>
          ))}
        </div>

        {/* Quick info */}
        <div className="mt-8 rounded-sm border border-[#2a2a2a] bg-[#1e1e1e]/50 px-4 py-3">
          <p className="text-xs text-[#666666]">
            Каждый режим использует FSRS для оптимального интервального повторения.
            Прогресс сохраняется отдельно для каждой категории.
          </p>
        </div>
      </div>
    </div>
  );
}

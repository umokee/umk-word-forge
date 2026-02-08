import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Save, Loader2, CheckCircle } from 'lucide-react';

import { Header } from '@/components/layout/Header';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { getSettings, updateSettings } from '@/api/settings';
import { cn } from '@/lib/utils';
import type { Settings as SettingsType, SettingsUpdate } from '@/types';

// ---------------------------------------------------------------------------
// Toggle switch component
// ---------------------------------------------------------------------------

function Toggle({
  label,
  checked,
  onChange,
  description,
}: {
  label: string;
  checked: boolean;
  onChange: (val: boolean) => void;
  description?: string;
}) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm font-medium text-[#e0e0e0]">{label}</p>
        {description && (
          <p className="mt-0.5 text-xs text-[#666666]">{description}</p>
        )}
      </div>
      <button
        type="button"
        onClick={() => onChange(!checked)}
        className={cn(
          'relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full transition-colors',
          checked ? 'bg-[#00ff88]' : 'bg-[#2a2a2a]',
        )}
      >
        <span
          className={cn(
            'inline-block h-4 w-4 rounded-full bg-white transition-transform',
            checked ? 'translate-x-6' : 'translate-x-1',
          )}
        />
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Range slider component
// ---------------------------------------------------------------------------

function RangeSlider({
  label,
  value,
  min,
  max,
  step,
  onChange,
  formatValue,
  description,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (val: number) => void;
  formatValue?: (val: number) => string;
  description?: string;
}) {
  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <div>
          <label className="text-sm font-medium text-[#e0e0e0]">{label}</label>
          {description && (
            <p className="text-xs text-[#666666]">{description}</p>
          )}
        </div>
        <span className="font-mono text-sm text-[#00ff88]">
          {formatValue ? formatValue(value) : value}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="h-2 w-full cursor-pointer appearance-none rounded-sm bg-[#2a2a2a] [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-[#00ff88]"
      />
      <div className="mt-1 flex justify-between text-xs text-[#666666]">
        <span>{formatValue ? formatValue(min) : min}</span>
        <span>{formatValue ? formatValue(max) : max}</span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Radio group component
// ---------------------------------------------------------------------------

function RadioGroup({
  label,
  value,
  options,
  onChange,
  description,
}: {
  label: string;
  value: string;
  options: { value: string; label: string }[];
  onChange: (val: string) => void;
  description?: string;
}) {
  return (
    <div>
      <p className="mb-2 text-sm font-medium text-[#e0e0e0]">{label}</p>
      {description && (
        <p className="mb-2 text-xs text-[#666666]">{description}</p>
      )}
      <div className="flex flex-wrap gap-2">
        {options.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            className={cn(
              'rounded-sm border px-3 py-1.5 text-sm transition-colors',
              value === opt.value
                ? 'border-[#00ff88] bg-[#00ff88]/10 text-[#00ff88]'
                : 'border-[#2a2a2a] bg-[#1e1e1e] text-[#888888] hover:border-[#3a3a3a]',
            )}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Settings form skeleton
// ---------------------------------------------------------------------------

function SettingsSkeleton() {
  return (
    <div className="animate-pulse space-y-6">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="space-y-2">
          <div className="h-4 w-32 rounded bg-[#1e1e1e]" />
          <div className="h-10 w-full rounded bg-[#1e1e1e]" />
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Default settings
// ---------------------------------------------------------------------------

const defaultSettings: SettingsType = {
  daily_new_words: 10,
  session_duration_minutes: 15,
  max_reviews_per_session: 50,
  new_words_position: 'end',
  exercise_direction: 'mixed',
  show_transcription: true,
  show_example_translation: true,
  auto_play_audio: false,
  hint_delay_seconds: 10,
  preferred_exercises: [],
  keyboard_shortcuts: true,
  show_progress_details: true,
  session_end_summary: true,
  animation_speed: 'normal',
  font_size: 'normal',
  tts_enabled: true,
  tts_speed: 1.0,
  tts_voice: 'default',
  tts_auto_play_exercises: false,
  daily_goal_type: 'words',
  daily_goal_value: 20,
  gemini_api_key: null,
  ai_feedback_language: 'ru',
  ai_difficulty_context: 'simple',
};

// ---------------------------------------------------------------------------
// Settings page
// ---------------------------------------------------------------------------

export default function Settings() {
  const queryClient = useQueryClient();

  const { data: settings, isLoading, error } = useQuery({
    queryKey: ['settings'],
    queryFn: getSettings,
  });

  const [form, setForm] = useState<SettingsType>(defaultSettings);

  useEffect(() => {
    if (settings) {
      setForm({ ...defaultSettings, ...settings });
    }
  }, [settings]);

  const mutation = useMutation({
    mutationFn: (data: SettingsUpdate) => updateSettings(data),
    onSuccess: (updated) => {
      queryClient.setQueryData(['settings'], updated);
    },
  });

  const [showSaved, setShowSaved] = useState(false);

  const handleSave = async () => {
    await mutation.mutateAsync(form as SettingsUpdate);
    setShowSaved(true);
    setTimeout(() => setShowSaved(false), 2000);
  };

  const updateForm = <K extends keyof SettingsType>(
    key: K,
    value: SettingsType[K],
  ) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  if (isLoading) {
    return (
      <div>
        <Header title="Настройки" subtitle="Параметры обучения" />
        <Card className="max-w-2xl">
          <SettingsSkeleton />
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <Header title="Настройки" />
        <Card className="max-w-2xl text-center">
          <p className="text-[#f59e0b]">
            Не удалось загрузить настройки. Попробуйте позже.
          </p>
        </Card>
      </div>
    );
  }

  return (
    <div>
      <Header title="Настройки" subtitle="Параметры обучения" />

      <div className="max-w-2xl space-y-6">
        {/* Training section */}
        <Card>
          <h2 className="mb-5 text-base font-semibold text-[#e0e0e0]">
            Тренировка
          </h2>
          <div className="space-y-5">
            <RangeSlider
              label="Новых слов в день"
              description="Сколько новых слов добавлять ежедневно"
              value={form.daily_new_words}
              min={1}
              max={50}
              step={1}
              onChange={(val) => updateForm('daily_new_words', val)}
              formatValue={(val) => `${val} слов`}
            />

            <RangeSlider
              label="Длительность сессии"
              description="Время одной тренировки"
              value={form.session_duration_minutes}
              min={5}
              max={60}
              step={5}
              onChange={(val) => updateForm('session_duration_minutes', val)}
              formatValue={(val) => `${val} мин`}
            />

            <RangeSlider
              label="Макс. повторений за сессию"
              description="Лимит повторяемых слов"
              value={form.max_reviews_per_session}
              min={10}
              max={200}
              step={10}
              onChange={(val) => updateForm('max_reviews_per_session', val)}
            />

            <RadioGroup
              label="Новые слова в сессии"
              description="Где показывать новые слова"
              value={form.new_words_position}
              options={[
                { value: 'start', label: 'В начале' },
                { value: 'middle', label: 'В середине' },
                { value: 'end', label: 'В конце' },
              ]}
              onChange={(val) => updateForm('new_words_position', val as SettingsType['new_words_position'])}
            />

            <RadioGroup
              label="Направление упражнений"
              value={form.exercise_direction}
              options={[
                { value: 'en_to_ru', label: 'EN → RU' },
                { value: 'ru_to_en', label: 'RU → EN' },
                { value: 'mixed', label: 'Смешанное' },
              ]}
              onChange={(val) => updateForm('exercise_direction', val as SettingsType['exercise_direction'])}
            />

            <RangeSlider
              label="Задержка подсказки"
              description="Через сколько секунд показать подсказку"
              value={form.hint_delay_seconds}
              min={5}
              max={30}
              step={5}
              onChange={(val) => updateForm('hint_delay_seconds', val)}
              formatValue={(val) => `${val} сек`}
            />
          </div>
        </Card>

        {/* Daily Goal section */}
        <Card>
          <h2 className="mb-5 text-base font-semibold text-[#e0e0e0]">
            Дневная цель
          </h2>
          <div className="space-y-5">
            <RadioGroup
              label="Тип цели"
              value={form.daily_goal_type}
              options={[
                { value: 'words', label: 'Слова' },
                { value: 'minutes', label: 'Минуты' },
                { value: 'exercises', label: 'Упражнения' },
              ]}
              onChange={(val) => updateForm('daily_goal_type', val as SettingsType['daily_goal_type'])}
            />

            <RangeSlider
              label="Значение цели"
              value={form.daily_goal_value}
              min={5}
              max={100}
              step={5}
              onChange={(val) => updateForm('daily_goal_value', val)}
              formatValue={(val) =>
                form.daily_goal_type === 'words'
                  ? `${val} слов`
                  : form.daily_goal_type === 'minutes'
                    ? `${val} мин`
                    : `${val} упр.`
              }
            />
          </div>
        </Card>

        {/* Display section */}
        <Card>
          <h2 className="mb-5 text-base font-semibold text-[#e0e0e0]">
            Отображение
          </h2>
          <div className="space-y-5">
            <Toggle
              label="Показывать транскрипцию"
              description="IPA транскрипция при показе слова"
              checked={form.show_transcription}
              onChange={(val) => updateForm('show_transcription', val)}
            />

            <Toggle
              label="Перевод примеров"
              description="Показывать русский перевод примеров"
              checked={form.show_example_translation}
              onChange={(val) => updateForm('show_example_translation', val)}
            />

            <Toggle
              label="Детали прогресса"
              description="Показывать FSRS параметры на карточке слова"
              checked={form.show_progress_details}
              onChange={(val) => updateForm('show_progress_details', val)}
            />

            <Toggle
              label="Итоги сессии"
              description="Показывать экран с результатами после тренировки"
              checked={form.session_end_summary}
              onChange={(val) => updateForm('session_end_summary', val)}
            />

            <RadioGroup
              label="Размер шрифта"
              value={form.font_size}
              options={[
                { value: 'small', label: 'Маленький' },
                { value: 'normal', label: 'Обычный' },
                { value: 'large', label: 'Крупный' },
              ]}
              onChange={(val) => updateForm('font_size', val as SettingsType['font_size'])}
            />

            <RadioGroup
              label="Скорость анимаций"
              value={form.animation_speed}
              options={[
                { value: 'fast', label: 'Быстро' },
                { value: 'normal', label: 'Обычно' },
                { value: 'slow', label: 'Медленно' },
                { value: 'none', label: 'Без анимаций' },
              ]}
              onChange={(val) => updateForm('animation_speed', val as SettingsType['animation_speed'])}
            />
          </div>
        </Card>

        {/* TTS section */}
        <Card>
          <h2 className="mb-5 text-base font-semibold text-[#e0e0e0]">
            Озвучка (TTS)
          </h2>
          <div className="space-y-5">
            <Toggle
              label="TTS включён"
              description="Озвучивать слова при нажатии"
              checked={form.tts_enabled}
              onChange={(val) => updateForm('tts_enabled', val)}
            />

            <RangeSlider
              label="Скорость речи"
              value={form.tts_speed}
              min={0.5}
              max={1.5}
              step={0.1}
              onChange={(val) => updateForm('tts_speed', val)}
              formatValue={(val) => `${val.toFixed(1)}x`}
            />

            <Toggle
              label="Авто-озвучка в упражнениях"
              description="Автоматически озвучивать слово при показе"
              checked={form.tts_auto_play_exercises}
              onChange={(val) => updateForm('tts_auto_play_exercises', val)}
            />

            <Toggle
              label="Авто-воспроизведение"
              description="Озвучивать слово сразу при показе карточки"
              checked={form.auto_play_audio}
              onChange={(val) => updateForm('auto_play_audio', val)}
            />
          </div>
        </Card>

        {/* Interface section */}
        <Card>
          <h2 className="mb-5 text-base font-semibold text-[#e0e0e0]">
            Интерфейс
          </h2>
          <div className="space-y-5">
            <Toggle
              label="Горячие клавиши"
              description="1-4 для выбора, Enter для подтверждения, Esc для выхода"
              checked={form.keyboard_shortcuts}
              onChange={(val) => updateForm('keyboard_shortcuts', val)}
            />
          </div>
        </Card>

        {/* AI section */}
        <Card>
          <h2 className="mb-5 text-base font-semibold text-[#e0e0e0]">
            AI (Gemini)
          </h2>
          <div className="space-y-5">
            <Input
              label="API ключ Gemini"
              type="password"
              value={form.gemini_api_key || ''}
              onChange={(e) => updateForm('gemini_api_key', e.target.value || null)}
              placeholder="Введите ключ API..."
              hint="Для проверки предложений и генерации контекстов. Получить: aistudio.google.com"
            />

            <RadioGroup
              label="Язык фидбека AI"
              value={form.ai_feedback_language}
              options={[
                { value: 'ru', label: 'Русский' },
                { value: 'en', label: 'English' },
              ]}
              onChange={(val) => updateForm('ai_feedback_language', val as SettingsType['ai_feedback_language'])}
            />

            <RadioGroup
              label="Сложность AI-контекстов"
              description="Уровень сложности генерируемых примеров"
              value={form.ai_difficulty_context}
              options={[
                { value: 'simple', label: 'Простые (A1-A2)' },
                { value: 'medium', label: 'Средние (B1)' },
                { value: 'natural', label: 'Естественные (B2+)' },
              ]}
              onChange={(val) => updateForm('ai_difficulty_context', val as SettingsType['ai_difficulty_context'])}
            />
          </div>
        </Card>

        {/* Save button */}
        <div className="flex items-center gap-3 pb-8">
          <Button
            size="lg"
            onClick={handleSave}
            disabled={mutation.isPending}
            className="gap-2"
          >
            {mutation.isPending ? (
              <Loader2 size={18} className="animate-spin" />
            ) : (
              <Save size={18} />
            )}
            Сохранить
          </Button>

          {showSaved && (
            <span className="flex animate-fade-in items-center gap-1 text-sm text-[#00ff88]">
              <CheckCircle size={16} />
              Сохранено
            </span>
          )}

          {mutation.isError && (
            <span className="text-sm text-[#f59e0b]">
              Ошибка сохранения. Попробуйте ещё раз.
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

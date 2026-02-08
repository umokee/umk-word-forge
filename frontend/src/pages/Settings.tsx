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
        <p className="text-sm font-medium text-[#E8E8EC]">{label}</p>
        {description && (
          <p className="mt-0.5 text-xs text-[#5C5C66]">{description}</p>
        )}
      </div>
      <button
        type="button"
        onClick={() => onChange(!checked)}
        className={cn(
          'relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full transition-colors',
          checked ? 'bg-indigo-600' : 'bg-[#2A2A30]',
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
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (val: number) => void;
  formatValue?: (val: number) => string;
}) {
  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <label className="text-sm font-medium text-[#E8E8EC]">{label}</label>
        <span className="font-mono text-sm text-[#8B8B96]">
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
        className="h-2 w-full cursor-pointer appearance-none rounded-sm bg-[#2A2A30] accent-indigo-600 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-indigo-500"
      />
      <div className="mt-1 flex justify-between text-xs text-[#5C5C66]">
        <span>{min}</span>
        <span>{max}</span>
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
          <div className="h-4 w-32 rounded bg-[#1C1C20]" />
          <div className="h-10 w-full rounded bg-[#1C1C20]" />
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Settings page
// ---------------------------------------------------------------------------

export default function Settings() {
  const queryClient = useQueryClient();

  // Fetch current settings
  const { data: settings, isLoading, error } = useQuery({
    queryKey: ['settings'],
    queryFn: getSettings,
  });

  // Local form state
  const [form, setForm] = useState<SettingsType>({
    daily_new_words: 10,
    session_duration_minutes: 15,
    preferred_exercises: [],
    tts_enabled: true,
    tts_speed: 1.0,
    keyboard_shortcuts: true,
  });

  // API key fields (not part of backend settings schema, stored locally)
  const [geminiKey, setGeminiKey] = useState('');

  // Sync form with fetched settings
  useEffect(() => {
    if (settings) {
      setForm(settings);
    }
  }, [settings]);

  // Load API keys from localStorage
  useEffect(() => {
    setGeminiKey(localStorage.getItem('gemini_api_key') ?? '');
  }, []);

  // Mutation for saving settings
  const mutation = useMutation({
    mutationFn: (data: SettingsUpdate) => updateSettings(data),
    onSuccess: (updated) => {
      queryClient.setQueryData(['settings'], updated);
    },
  });

  const [showSaved, setShowSaved] = useState(false);

  const handleSave = async () => {
    // Save API keys to localStorage
    localStorage.setItem('gemini_api_key', geminiKey);

    // Save backend settings
    await mutation.mutateAsync({
      daily_new_words: form.daily_new_words,
      session_duration_minutes: form.session_duration_minutes,
      tts_enabled: form.tts_enabled,
      tts_speed: form.tts_speed,
      keyboard_shortcuts: form.keyboard_shortcuts,
    });

    setShowSaved(true);
    setTimeout(() => setShowSaved(false), 2000);
  };

  const updateForm = <K extends keyof SettingsType>(
    key: K,
    value: SettingsType[K],
  ) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  // -- Loading state -------------------------------------------------------
  if (isLoading) {
    return (
      <div>
        <Header title="Settings" subtitle="Configure your learning preferences" />
        <Card className="max-w-2xl">
          <SettingsSkeleton />
        </Card>
      </div>
    );
  }

  // -- Error state ---------------------------------------------------------
  if (error) {
    return (
      <div>
        <Header title="Settings" />
        <Card className="max-w-2xl text-center">
          <p className="text-red-400">
            Failed to load settings. Please try again later.
          </p>
        </Card>
      </div>
    );
  }

  return (
    <div>
      <Header title="Settings" subtitle="Configure your learning preferences" />

      <div className="max-w-2xl space-y-6">
        {/* Learning section */}
        <Card>
          <h2 className="mb-5 text-base font-semibold text-[#E8E8EC]">
            Learning
          </h2>
          <div className="space-y-5">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-[#E8E8EC]">
                Daily new words
              </label>
              <input
                type="number"
                min={1}
                max={50}
                value={form.daily_new_words}
                onChange={(e) =>
                  updateForm('daily_new_words', Number(e.target.value) || 10)
                }
                className="w-32 rounded-sm border border-[#2A2A30] bg-[#1C1C20] px-3 py-2 font-mono text-sm text-[#E8E8EC] outline-none focus:border-indigo-500"
              />
              <p className="mt-1 text-xs text-[#5C5C66]">
                Number of new words to introduce each day (1-50)
              </p>
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium text-[#E8E8EC]">
                Session duration (minutes)
              </label>
              <input
                type="number"
                min={1}
                max={60}
                value={form.session_duration_minutes}
                onChange={(e) =>
                  updateForm(
                    'session_duration_minutes',
                    Number(e.target.value) || 15,
                  )
                }
                className="w-32 rounded-sm border border-[#2A2A30] bg-[#1C1C20] px-3 py-2 font-mono text-sm text-[#E8E8EC] outline-none focus:border-indigo-500"
              />
              <p className="mt-1 text-xs text-[#5C5C66]">
                Target duration for a training session (1-60)
              </p>
            </div>
          </div>
        </Card>

        {/* Text-to-Speech section */}
        <Card>
          <h2 className="mb-5 text-base font-semibold text-[#E8E8EC]">
            Text-to-Speech
          </h2>
          <div className="space-y-5">
            <Toggle
              label="TTS enabled"
              description="Automatically play pronunciation for words"
              checked={form.tts_enabled}
              onChange={(val) => updateForm('tts_enabled', val)}
            />

            <RangeSlider
              label="TTS speed"
              value={form.tts_speed}
              min={0.7}
              max={1.2}
              step={0.1}
              onChange={(val) => updateForm('tts_speed', val)}
              formatValue={(val) => `${val.toFixed(1)}x`}
            />
          </div>
        </Card>

        {/* Interface section */}
        <Card>
          <h2 className="mb-5 text-base font-semibold text-[#E8E8EC]">
            Interface
          </h2>
          <Toggle
            label="Keyboard shortcuts"
            description="Use 1-4 to select options, Enter to confirm, Esc to exit"
            checked={form.keyboard_shortcuts}
            onChange={(val) => updateForm('keyboard_shortcuts', val)}
          />
        </Card>

        {/* API keys section */}
        <Card>
          <h2 className="mb-5 text-base font-semibold text-[#E8E8EC]">
            AI Provider Keys
          </h2>
          <div className="space-y-4">
            <Input
              label="Gemini API Key"
              type="password"
              value={geminiKey}
              onChange={(e) => setGeminiKey(e.target.value)}
              placeholder="Enter your Gemini API key..."
              hint="Used for AI-powered sentence checking and context generation"
            />
          </div>
        </Card>

        {/* Save button */}
        <div className="flex items-center gap-3">
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
            Save Settings
          </Button>

          {showSaved && (
            <span className="flex animate-fade-in items-center gap-1 text-sm text-emerald-400">
              <CheckCircle size={16} />
              Saved
            </span>
          )}

          {mutation.isError && (
            <span className="text-sm text-red-400">
              Failed to save. Please try again.
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

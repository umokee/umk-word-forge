import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

interface DailyChartProps {
  data: { date: string; count: number }[];
}

export function DailyChart({ data }: DailyChartProps) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <AreaChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
        <defs>
          <linearGradient id="dailyChartGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#6366F1" stopOpacity={0.3} />
            <stop offset="100%" stopColor="#6366F1" stopOpacity={0} />
          </linearGradient>
        </defs>
        <XAxis
          dataKey="date"
          tick={{ fill: '#8B8B96', fontSize: 12 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: '#8B8B96', fontSize: 12 }}
          axisLine={false}
          tickLine={false}
          allowDecimals={false}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: '#141416',
            border: '1px solid #2A2A30',
            borderRadius: '2px',
            color: '#E8E8EC',
            fontSize: 12,
          }}
          labelStyle={{ color: '#8B8B96' }}
          cursor={{ stroke: '#2A2A30' }}
        />
        <Area
          type="monotone"
          dataKey="count"
          stroke="#6366F1"
          strokeWidth={2}
          fill="url(#dailyChartGradient)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

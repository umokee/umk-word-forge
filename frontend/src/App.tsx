import { Routes, Route } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import Layout from './components/layout/Layout';

const Dashboard = lazy(() => import('./pages/Dashboard'));
const Train = lazy(() => import('./pages/Train'));
const TrainSelector = lazy(() => import('./pages/TrainSelector'));
const TrainPhrasal = lazy(() => import('./pages/TrainPhrasal'));
const TrainIrregular = lazy(() => import('./pages/TrainIrregular'));
const Words = lazy(() => import('./pages/Words'));
const WordDetail = lazy(() => import('./pages/WordDetail'));
const Stats = lazy(() => import('./pages/Stats'));
const Settings = lazy(() => import('./pages/Settings'));

function LoadingFallback() {
  return (
    <div className="flex items-center justify-center h-screen bg-[#0a0a0a]">
      <div className="animate-pulse text-zinc-500 text-sm">Loading...</div>
    </div>
  );
}

export default function App() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <Routes>
        {/* Training mode selector (full-screen) */}
        <Route path="/train" element={<TrainSelector />} />

        {/* Full-screen training routes (no layout chrome) */}
        <Route path="/train/words" element={<Train />} />
        <Route path="/train/phrasal" element={<TrainPhrasal />} />
        <Route path="/train/irregular" element={<TrainIrregular />} />

        {/* All other routes share the sidebar/header layout */}
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/words" element={<Words />} />
          <Route path="/words/:id" element={<WordDetail />} />
          <Route path="/stats" element={<Stats />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Routes>
    </Suspense>
  );
}

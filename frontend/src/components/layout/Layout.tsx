import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';

export default function Layout() {
  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      <Sidebar />
      <main className="ml-56 min-h-screen">
        <div className="px-8 py-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

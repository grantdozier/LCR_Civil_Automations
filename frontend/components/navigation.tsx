'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const modules = [
  { id: 'A', name: 'Area Calc', href: '/module-a', color: 'blue' },
  { id: 'B', name: 'Spec Extract', href: '/module-b', color: 'green' },
  { id: 'C', name: 'DIA Report', href: '/module-c', color: 'purple' },
  { id: 'D', name: 'Plan QA', href: '/module-d', color: 'orange' },
  { id: 'E', name: 'Proposals', href: '/module-e', color: 'pink' },
];

export function Navigation() {
  const pathname = usePathname();

  return (
    <nav className="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="flex items-center gap-2 font-bold text-xl text-slate-900 hover:text-blue-600 transition-colors">
            <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <span>LCR Drainage</span>
          </Link>

          <div className="flex items-center gap-2">
            {modules.map((module) => (
              <Link
                key={module.id}
                href={module.href}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  pathname === module.href
                    ? `bg-${module.color}-100 text-${module.color}-700 border border-${module.color}-300`
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                {module.id}
              </Link>
            ))}
          </div>

          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
          >
            API Docs
          </a>
        </div>
      </div>
    </nav>
  );
}

export default function Home() {
  return (
    <main className="container mx-auto px-4 py-16">
      <div className="text-center space-y-8">
        <div className="space-y-4">
          <h1 className="text-5xl font-bold text-slate-900">
            LCR Civil Drainage Automation
          </h1>
          <p className="text-xl text-slate-600 max-w-2xl mx-auto">
            Production-ready civil engineering automation platform for drainage analysis,
            regulatory compliance, and document generation
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto mt-12">
          <ModuleCard
            letter="A"
            title="Area Calculation"
            description="Automated drainage area calculation with weighted C-values"
            color="bg-blue-500"
            href="/module-a"
          />
          <ModuleCard
            letter="B"
            title="Spec Extraction"
            description="UDC & DOTD specification extraction with AI"
            color="bg-green-500"
            href="/module-b"
          />
          <ModuleCard
            letter="C"
            title="DIA Report Generator"
            description="Complete drainage impact analysis reports (Q=CiA)"
            color="bg-purple-500"
            href="/module-c"
          />
          <ModuleCard
            letter="D"
            title="Plan Review QA"
            description="Automated plan set compliance checking"
            color="bg-orange-500"
            href="/module-d"
          />
          <ModuleCard
            letter="E"
            title="Proposal Generator"
            description="Proposal and submittal document generation"
            color="bg-pink-500"
            href="/module-e"
          />
        </div>

        <div className="mt-16 space-y-4">
          <h2 className="text-2xl font-semibold text-slate-800">Quick Start</h2>
          <div className="bg-slate-900 text-slate-100 rounded-lg p-6 max-w-2xl mx-auto text-left">
            <code className="text-sm">
              docker-compose up -d<br />
              <span className="text-green-400"># API Docs:</span> http://localhost:8000/docs<br />
              <span className="text-green-400"># Web Portal:</span> http://localhost:3000
            </code>
          </div>
        </div>

        <div className="mt-12 flex gap-4 justify-center">
          <a
            href="/api/v1/docs"
            target="_blank"
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-semibold"
          >
            View API Docs
          </a>
          <a
            href="https://github.com"
            className="px-6 py-3 bg-slate-700 text-white rounded-lg hover:bg-slate-800 transition font-semibold"
          >
            GitHub Repository
          </a>
        </div>
      </div>
    </main>
  )
}

function ModuleCard({ letter, title, description, color, href }: {
  letter: string
  title: string
  description: string
  color: string
  href: string
}) {
  return (
    <a
      href={href}
      className="bg-white rounded-lg shadow-md p-6 border-2 border-slate-200 hover:border-slate-400 transition-all hover:shadow-lg block"
    >
      <div className={`w-12 h-12 ${color} rounded-full flex items-center justify-center mb-4`}>
        <span className="text-white text-2xl font-bold">{letter}</span>
      </div>
      <h3 className="text-lg font-semibold text-slate-800 mb-2">{title}</h3>
      <p className="text-slate-600 text-sm">{description}</p>
      <div className="mt-4 text-blue-600 text-sm font-semibold flex items-center gap-1">
        Launch Module
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </div>
    </a>
  )
}

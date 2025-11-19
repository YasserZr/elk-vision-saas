export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">ELK Vision SaaS</h1>
        <p className="text-xl text-gray-600 mb-8">
          Log Monitoring and Analytics Platform
        </p>
        <div className="space-x-4">
          <a
            href="/login"
            className="inline-block bg-primary text-white px-6 py-3 rounded-lg hover:bg-blue-600"
          >
            Login
          </a>
          <a
            href="/dashboard"
            className="inline-block bg-secondary text-white px-6 py-3 rounded-lg hover:bg-purple-600"
          >
            Dashboard
          </a>
        </div>
      </div>
    </main>
  )
}

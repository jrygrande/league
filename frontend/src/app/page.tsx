"use client"

import { useState } from "react"

export default function Home() {
  const [testConnection, setTestConnection] = useState<string>("")
  const [loading, setLoading] = useState(false)

  const testBackend = async () => {
    setLoading(true)
    try {
      const response = await fetch("http://localhost:8000/", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      })
      const data = await response.json()
      setTestConnection(`Backend connection successful: ${JSON.stringify(data)}`)
    } catch (error) {
      setTestConnection(`Backend connection failed: ${error}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen py-2">
      <main className="flex flex-col items-center justify-center w-full flex-1 px-20 text-center">
        <h1 className="text-6xl font-bold">
          Welcome to{" "}
          <span className="text-blue-600">
            Sleeper League Explorer
          </span>
        </h1>

        <p className="mt-3 text-2xl">
          Visualize player trade lineages and fantasy football analytics
        </p>

        <div className="flex flex-wrap items-center justify-around max-w-4xl mt-6 sm:w-full">
          <div className="p-6 mt-6 text-left border w-96 rounded-xl hover:text-blue-600 focus:text-blue-600">
            <h3 className="text-2xl font-bold">Frontend Setup ✓</h3>
            <p className="mt-4 text-xl">
              Next.js with TypeScript, Tailwind CSS, and shadcn/ui components ready for development.
            </p>
          </div>

          <div className="p-6 mt-6 text-left border w-96 rounded-xl hover:text-blue-600 focus:text-blue-600">
            <h3 className="text-2xl font-bold">Backend Connection</h3>
            <p className="mt-4 text-xl mb-4">
              Test the connection to your FastAPI backend.
            </p>
            <button
              onClick={testBackend}
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? "Testing..." : "Test Backend"}
            </button>
            {testConnection && (
              <p className="mt-2 text-sm text-gray-600 break-words">
                {testConnection}
              </p>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
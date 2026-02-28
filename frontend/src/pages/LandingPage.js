import React from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';

const features = [
  {
    title: 'AI Codebase Analysis',
    desc: 'Detect frameworks, tech stack, architecture, entry points — all automatically using static code analysis.',
    icon: '🔍',
  },
  {
    title: 'Security Scanner',
    desc: 'Find and remove API keys, tokens, passwords, and secrets. Protect your code before sharing.',
    icon: '🛡️',
  },
  {
    title: 'Auto Documentation',
    desc: 'Generate README, API docs, technical reports with one click. Export as Markdown or PDF.',
    icon: '📄',
  },
  {
    title: 'Architecture Diagrams',
    desc: 'Auto-generate architecture, flow, and dependency diagrams using Mermaid.js.',
    icon: '📊',
  },
  {
    title: 'AI Chatbot',
    desc: 'Ask questions about your codebase. Understand login flows, find unused files, detect circular deps.',
    icon: '🤖',
  },
  {
    title: 'Academic Project Tracking',
    desc: 'Role-based system for students, faculty, and HODs. Score projects, assign mentors, track progress.',
    icon: '🎓',
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      <Navbar />

      {/* Hero */}
      <section className="max-w-7xl mx-auto px-4 pt-20 pb-16 text-center">
        <div className="inline-flex items-center bg-primary-100 text-primary-700 px-4 py-1.5 rounded-full text-sm font-medium mb-6">
          ✨ Built for Colleges & Organizations
        </div>
        <h1 className="text-5xl font-extrabold text-gray-900 leading-tight mb-6">
          Understand Any Codebase<br />
          <span className="text-primary-600">In Under 2 Minutes</span>
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-10">
          Upload a ZIP or paste a GitHub URL. Get instant framework detection, security scanning,
          auto-generated docs, architecture diagrams, and an AI assistant — all powered by
          static code analysis.
        </p>
        <div className="flex justify-center gap-4">
          <Link
            to="/signup"
            className="bg-primary-600 text-white px-8 py-3 rounded-lg text-lg font-semibold hover:bg-primary-700 shadow-lg shadow-primary-200"
          >
            Get Started Free
          </Link>
          <a
            href="#features"
            className="border border-gray-300 text-gray-700 px-8 py-3 rounded-lg text-lg font-semibold hover:bg-gray-100"
          >
            Learn More
          </a>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="max-w-7xl mx-auto px-4 py-20">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-4">
          Everything You Need
        </h2>
        <p className="text-center text-gray-500 mb-12 max-w-xl mx-auto">
          From code analysis to project management — one platform for your entire academic workflow.
        </p>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((f, i) => (
            <div
              key={i}
              className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow"
            >
              <div className="text-4xl mb-4">{f.icon}</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{f.title}</h3>
              <p className="text-gray-600 text-sm">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="bg-white py-20">
        <div className="max-w-5xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">How It Works</h2>
          <div className="grid md:grid-cols-4 gap-8 text-center">
            {[
              { step: '1', title: 'Upload', desc: 'Upload ZIP or paste GitHub URL' },
              { step: '2', title: 'Analyze', desc: 'Static analysis detects everything' },
              { step: '3', title: 'Secure', desc: 'Scan and remove secrets' },
              { step: '4', title: 'Document', desc: 'Generate docs, diagrams, README' },
            ].map((s, i) => (
              <div key={i}>
                <div className="w-12 h-12 bg-primary-600 text-white rounded-full flex items-center justify-center text-xl font-bold mx-auto mb-4">
                  {s.step}
                </div>
                <h3 className="font-semibold text-gray-900 mb-1">{s.title}</h3>
                <p className="text-sm text-gray-500">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Roles */}
      <section className="max-w-5xl mx-auto px-4 py-20">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">Built for Everyone</h2>
        <div className="grid md:grid-cols-3 gap-8">
          {[
            { role: 'Student', desc: 'Upload projects, analyze code, generate documentation, and get AI assistance.', color: 'bg-blue-50 border-blue-200' },
            { role: 'Faculty', desc: 'Create project folders, view student repos, analyze and score projects.', color: 'bg-green-50 border-green-200' },
            { role: 'HOD', desc: 'Manage faculty & students, assign mentors, track department performance.', color: 'bg-purple-50 border-purple-200' },
          ].map((r, i) => (
            <div key={i} className={`rounded-xl p-6 border ${r.color}`}>
              <h3 className="text-lg font-bold text-gray-900 mb-2">{r.role}</h3>
              <p className="text-gray-600 text-sm">{r.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="bg-primary-600 py-16">
        <div className="max-w-3xl mx-auto text-center px-4">
          <h2 className="text-3xl font-bold text-white mb-4">Ready to Understand Your Code?</h2>
          <p className="text-primary-100 mb-8">
            Join colleges and organizations using CodeLens AI for smarter project management.
          </p>
          <Link
            to="/signup"
            className="bg-white text-primary-600 px-8 py-3 rounded-lg text-lg font-semibold hover:bg-gray-100"
          >
            Start Now — It's Free
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 py-8 text-center text-gray-400 text-sm">
        © 2026 CodeLens AI. Built for hackathons and beyond.
      </footer>
    </div>
  );
}

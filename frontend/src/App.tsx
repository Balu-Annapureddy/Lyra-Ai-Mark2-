import { useState } from 'react'
import ModelManager from './components/ModelManager'
import { Activity, Cpu, HardDrive } from 'lucide-react'

function App() {
    return (
        <div className="min-h-screen bg-gradient-to-br from-dark-900 via-dark-800 to-dark-900">
            {/* Header */}
            <header className="border-b border-white/10 glass">
                <div className="max-w-7xl mx-auto px-6 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center">
                                <Activity className="w-6 h-6 text-white" />
                            </div>
                            <div>
                                <h1 className="text-xl font-bold">Lyra AI Mark2</h1>
                                <p className="text-xs text-dark-400">Lightweight AI Operating System</p>
                            </div>
                        </div>

                        <div className="flex items-center space-x-4">
                            <div className="flex items-center space-x-2 text-sm text-dark-400">
                                <Cpu className="w-4 h-4" />
                                <span>Ready</span>
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-6 py-8">
                <ModelManager />
            </main>

            {/* Footer */}
            <footer className="border-t border-white/10 mt-12">
                <div className="max-w-7xl mx-auto px-6 py-4 text-center text-sm text-dark-400">
                    <p>Lyra AI Mark2 v2.0.0 • Built with safety and performance in mind</p>
                </div>
            </footer>
        </div>
    )
}

export default App

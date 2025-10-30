import { useState } from 'react'
import './App.css'

function App() {
  const [selectedFiles, setSelectedFiles] = useState([])
  const [question, setQuestion] = useState('')

  function handleFileChange(event) {
    const files = Array.from(event.target.files ?? [])
    setSelectedFiles(files)
  }

  function handleAnalyseClick() {
    // Placeholder action for Analyse button
    // Hook up to backend when available
    // e.g., upload selectedFiles then trigger analysis
    console.log('Analyse clicked with files:', selectedFiles)
  }

  function handleSend() {
    if (!question.trim()) return
    // Placeholder for sending the question to AI backend
    console.log('Send question:', question)
    setQuestion('')
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="app-container">
      <header className="header">
        <div className="brand">Intellico</div>
      </header>

      <main className="content">
        <section className="upload-card">
          <h2 className="upload-title">Upload papers</h2>
          <div className="upload-row">
            <input
              className="file-input"
              type="file"
              accept=".pdf,.doc,.docx,.txt"
              multiple
              onChange={handleFileChange}
            />
            <button className="analyse-btn" onClick={handleAnalyseClick}>
              Analyse
            </button>
          </div>
        </section>

        <div className="content-spacer" />
      </main>

      <div className="chatbar">
        <div className="chatbar-inner">
          <div className="chat-input-row">
            <input
              className="chat-input"
              type="text"
              placeholder="Ask the AI..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <button className="send-btn" onClick={handleSend}>Send</button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App


import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { sendMessage, ChatResponse } from '../utils/api'
import DutyCycleCalculator from './DutyCycleCalculator'
import ImageGallery from './ImageGallery'

interface Message {
  role: 'user' | 'assistant'
  content: string
  artifacts?: any[]
  images?: string[]
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | undefined>()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleNewChat = () => {
    setMessages([])
    setConversationId(undefined)
    setInput('')
  }

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    
    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setLoading(true)

    try {
      const response: ChatResponse = await sendMessage(userMessage, conversationId)
      
      // Set conversation ID if first message
      if (!conversationId) {
        setConversationId(response.conversation_id)
      }

      // Add assistant message
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.message,
        artifacts: response.artifacts,
        images: response.images
      }])
    } catch (error) {
      console.error('Error sending message:', error)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '❌ Sorry, there was an error processing your request. Please try again.'
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-200px)] bg-white rounded-lg shadow-lg">
      {/* Header with New Chat button */}
      {messages.length > 0 && (
        <div className="border-b border-slate-200 px-6 py-3 flex justify-between items-center">
          <span className="text-sm text-slate-600">
            {messages.length} messages
          </span>
          <button
            onClick={handleNewChat}
            className="px-4 py-2 text-sm bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-md font-medium"
          >
            🔄 New Chat
          </button>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🔧</div>
            <h2 className="text-2xl font-bold text-slate-800 mb-2">
              Vulcan OmniPro 220 Expert
            </h2>
            <p className="text-slate-600 mb-6">
              Ask me anything about the Vulcan OmniPro 220 welding system
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto">
              <button
                onClick={() => setInput("What's the duty cycle for MIG at 200A on 240V?")}
                className="p-3 text-left bg-slate-50 hover:bg-slate-100 rounded-lg border border-slate-200 text-sm"
              >
                💡 What's the duty cycle for MIG at 200A on 240V?
              </button>
              <button
                onClick={() => setInput("Show me the polarity setup for TIG welding")}
                className="p-3 text-left bg-slate-50 hover:bg-slate-100 rounded-lg border border-slate-200 text-sm"
              >
                🔌 Show me the polarity setup for TIG welding
              </button>
              <button
                onClick={() => setInput("I'm getting porosity in my flux-cored welds")}
                className="p-3 text-left bg-slate-50 hover:bg-slate-100 rounded-lg border border-slate-200 text-sm"
              >
                🔍 I'm getting porosity in my flux-cored welds
              </button>
              <button
                onClick={() => setInput("How do I install a wire spool?")}
                className="p-3 text-left bg-slate-50 hover:bg-slate-100 rounded-lg border border-slate-200 text-sm"
              >
                📋 How do I install a wire spool?
              </button>
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-3xl rounded-lg px-4 py-3 ${
                message.role === 'user'
                  ? 'bg-orange-600 text-white'
                  : 'bg-slate-100 text-slate-800'
              }`}
            >
              {message.role === 'assistant' ? (
                <div className="prose prose-sm max-w-none prose-headings:font-bold prose-p:my-2 prose-ul:my-2 prose-li:my-1">
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
              ) : (
                <div className="whitespace-pre-wrap">{message.content}</div>
              )}
              
              {/* Render artifacts */}
              {message.artifacts && message.artifacts.map((artifact, idx) => (
                <div key={idx} className="mt-4">
                  {artifact.type === 'duty_cycle_calculator' && (
                    <DutyCycleCalculator data={artifact.data} />
                  )}
                </div>
              ))}

              {/* Render images */}
              {message.images && message.images.length > 0 && (
                <div className="mt-4">
                  <ImageGallery images={message.images} />
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-100 rounded-lg px-4 py-3">
              <div className="flex items-center gap-2 text-slate-600">
                <div className="animate-bounce">●</div>
                <div className="animate-bounce" style={{ animationDelay: '0.1s' }}>●</div>
                <div className="animate-bounce" style={{ animationDelay: '0.2s' }}>●</div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-slate-200 p-4">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about duty cycles, polarity setup, troubleshooting..."
            className="flex-1 px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 resize-none"
            rows={2}
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className="px-6 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:bg-slate-300 disabled:cursor-not-allowed font-medium transition-colors"
          >
            {loading ? '...' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  )
}
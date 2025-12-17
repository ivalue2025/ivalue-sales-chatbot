// frontend/src/App.js
import React, { useState, useCallback, useEffect } from 'react';
import Chat from './components/Chat';
import QuestionPanel from './components/QuestionPanel';
import './styles.css';
import axios from 'axios';
import { Zap } from 'lucide-react';

function App() {
  const [isPanelOpen, setIsPanelOpen] = useState(true);
  const [selectedQuestion, setSelectedQuestion] = useState('');
  const [autoExecuteHandler, setAutoExecuteHandler] = useState(null);
  
  // Auto-load states
  const [isInitializing, setIsInitializing] = useState(true);
  const [initMessage, setInitMessage] = useState('Starting iValue AI Assistant...');
  const [autoLoadProgress, setAutoLoadProgress] = useState(0);

  // FIXED: Updated API_BASE to use Render backend URL
  const API_BASE = process.env.REACT_APP_API_BASE || 'https://ivalue-sales-chatbot.onrender.com';

  useEffect(() => {
    let progress = 0;
    let isLoaded = false;
    let lastUpdateTime = Date.now();

    const checkStatus = async () => {
      if (isLoaded) return;

      try {
        const response = await axios.get(`${API_BASE}/status`);
        
        if (response.data.data_loaded) {
          isLoaded = true;
          setAutoLoadProgress(100);
          setInitMessage('All set! Your sales data is ready.');
          setTimeout(() => setIsInitializing(false), 800);
          return;
        }
      } catch (err) {
        // Backend not ready yet
      }

      // Simulate realistic progress that keeps moving
      const now = Date.now();
      const timeSinceLast = now - lastUpdateTime;
      lastUpdateTime = now;

      if (!isLoaded) {
        let increment = 0;

        if (progress < 30) {
          // Fast initial: server start + file read
          increment = 1.2 + Math.random() * 1.5;
          setInitMessage('Starting server and reading sales file...');
        } else if (progress < 60) {
          // Steady: pandas loading rows
          increment = 0.8 + Math.random() * 1;
          setInitMessage('Analyzing 53,868 rows of data...');
        } else if (progress < 85) {
          // Slower: building partner/OEM stats
          increment = 0.4 + Math.random() * 0.6;
          setInitMessage('Building performance insights...');
        } else if (progress < 95) {
          // Very slow: final stats
          increment = 0.15 + Math.random() * 0.3;
          setInitMessage('Finalizing partner and customer analytics...');
        } else {
          // Tiny ticks near end
          increment = 0.08 + Math.random() * 0.1;
          setInitMessage('Almost there — preparing your AI assistant...');
        }

        progress = Math.min(progress + increment, 95);
        setAutoLoadProgress(Math.round(progress));
      }
    };

    // Initial check
    checkStatus();

    // Poll frequently for smooth animation
    const interval = setInterval(checkStatus, 1200);

    return () => clearInterval(interval);
  }, [API_BASE]);

  // Your existing handlers
  const handleQuestionSelect = useCallback((question) => {
    console.log('Question selected:', question);
    setSelectedQuestion(question);
    setTimeout(() => setSelectedQuestion(''), 500);
  }, []);

  const handleAutoExecute = useCallback((query) => {
    if (autoExecuteHandler) {
      autoExecuteHandler(query);
    } else {
      handleQuestionSelect(query);
    }
  }, [autoExecuteHandler, handleQuestionSelect]);

  const handleSetAutoExecuteHandler = useCallback((handler) => {
    setAutoExecuteHandler(() => handler);
  }, []);

  const togglePanel = useCallback(() => {
    setIsPanelOpen(prev => !prev);
  }, []);

  const handlePanelClose = useCallback(() => {
    setIsPanelOpen(false);
    setSelectedQuestion('');
  }, []);

  return (
    <div className="app">
      {/* AUTO-LOAD BUFFER WITH SMOOTH REALISTIC PROGRESS */}
      {isInitializing && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          background: 'linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          color: 'white',
          fontFamily: 'system-ui, -apple-system, sans-serif'
        }}>
          <Zap className="h-24 w-24 text-yellow-400 animate-pulse mb-8" />
          
          <h1 style={{ fontSize: '48px', fontWeight: 'bold', marginBottom: '16px' }}>
            iVALUE AI Assistant
          </h1>
          
          <p style={{ fontSize: '20px', opacity: 0.9, marginBottom: '32px' }}>
            {initMessage}
          </p>

          {/* Progress Label + Percentage */}
          <div style={{ width: '550px', maxWidth: '90%' }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              marginBottom: '12px',
              fontSize: '16px',
              opacity: 0.9
            }}>
              <span>Loading your sales insights</span>
              <span>{autoLoadProgress}%</span>
            </div>

            {/* Smooth Progress Bar with Shimmer */}
            <div style={{
              height: '24px',
              backgroundColor: 'rgba(255, 255, 255, 0.2)',
              borderRadius: '12px',
              overflow: 'hidden',
              boxShadow: '0 6px 20px rgba(0,0,0,0.4)'
            }}>
              <div 
                style={{
                  height: '100%',
                  width: `${autoLoadProgress}%`,
                  background: 'linear-gradient(90deg, #60a5fa, #34d399)',
                  borderRadius: '12px',
                  transition: 'width 0.8s ease',
                  position: 'relative',
                  overflow: 'hidden'
                }}
              >
                <div style={{
                  position: 'absolute',
                  top: 0, left: 0, right: 0, bottom: 0,
                  background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent)',
                  transform: 'translateX(-100%)',
                  animation: 'shimmer 2.5s infinite'
                }} />
              </div>
            </div>
          </div>

          <p style={{ marginTop: '40px', fontSize: '14px', opacity: 0.7 }}>
            This usually takes 10-25 seconds on first load
          </p>
        </div>
      )}

      {/* MAIN APP */}
      {!isInitializing && (
        <div className="app-layout">
          <QuestionPanel 
            onQuestionSelect={handleQuestionSelect}
            onAutoExecuteQuery={handleAutoExecute}
            isOpen={isPanelOpen}
            onToggle={togglePanel}
            onClose={handlePanelClose}
          />
          
          <div className={`main-content ${isPanelOpen ? 'panel-open' : 'panel-closed'}`}>
            <Chat 
              prefillQuestion={selectedQuestion} 
              isPanelOpen={isPanelOpen}
              onTogglePanel={togglePanel}
              onAutoExecuteQuery={handleSetAutoExecuteHandler}
            />
          </div>
        </div>
      )}

      {/* Mobile overlay */}
      {isPanelOpen && (
        <div className="mobile-overlay" onClick={handlePanelClose} />
      )}
    </div>
  );
}

export default App;
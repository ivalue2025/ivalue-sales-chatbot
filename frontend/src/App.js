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

  // API base for backend (local dev or Render)
  const API_BASE = process.env.REACT_APP_API_BASE || 'https://ivalue-sales-chatbot.onrender.com';

  useEffect(() => {
    let isMounted = true;
    let isLoaded = false;
    let lastUpdateTime = Date.now();
    let pollInterval;

    const checkStatus = async () => {
      if (isLoaded || !isMounted) return;

      try {
        const response = await axios.get(`${API_BASE}/status`, { timeout: 10000 }); // 10s timeout

        if (response.data.data_loaded) {
          isLoaded = true;
          setAutoLoadProgress(100);
          setInitMessage('All set! Your sales data is ready.');
          setTimeout(() => {
            if (isMounted) setIsInitializing(false);
          }, 800);
          clearInterval(pollInterval);
          return;
        }
      } catch (err) {
        // Expected on first load when backend is waking up
        console.warn('Backend waking up or not ready yet...', err.message || err);
      }

      // Keep progress moving smoothly even if backend isn't responding yet
      const now = Date.now();
      const timeSinceLast = now - lastUpdateTime;
      lastUpdateTime = now;

      if (!isLoaded && isMounted) {
        let increment = 0;

        if (autoLoadProgress < 40) {
          increment = 1.5 + Math.random() * 1.2;
          setInitMessage('Starting server and reading sales file...');
        } else if (autoLoadProgress < 70) {
          increment = 1 + Math.random() * 0.8;
          setInitMessage('Analyzing 53,868 rows of sales data...');
        } else if (autoLoadProgress < 90) {
          increment = 0.5 + Math.random() * 0.5;
          setInitMessage('Building performance insights and analytics...');
        } else {
          increment = 0.15 + Math.random() * 0.2;
          setInitMessage('Almost ready — warming up your AI assistant...');
        }

        setAutoLoadProgress(prev => Math.min(Math.round(prev + increment), 98));
      }
    };

    // Start checking immediately
    checkStatus();

    // Poll every 1.5 seconds
    pollInterval = setInterval(checkStatus, 1500);

    // Fallback: Force load after 90 seconds even if backend is slow
    const forceLoadTimeout = setTimeout(() => {
      if (!isLoaded && isMounted) {
        console.info('Force-loading app after 90s timeout');
        setAutoLoadProgress(100);
        setInitMessage('Ready! (Sales data loading in background)');
        setIsInitializing(false);
        isLoaded = true;
      }
    }, 90000); // 90 seconds

    // Cleanup on unmount
    return () => {
      isMounted = false;
      clearInterval(pollInterval);
      clearTimeout(forceLoadTimeout);
    };
  }, [API_BASE]);

  // Handlers
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
      {/* AUTO-LOAD BUFFER WITH SMOOTH PROGRESS */}
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
            This usually takes 10–90 seconds on first load after inactivity
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
              apiBase={API_BASE}
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
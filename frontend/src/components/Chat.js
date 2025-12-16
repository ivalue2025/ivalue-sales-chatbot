import React, { useState, useRef, useEffect, useCallback } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { FiSend, FiUpload, FiX } from 'react-icons/fi';
import { motion, AnimatePresence } from 'framer-motion';
import { FaChartLine, FaUsers, FaExchangeAlt, FaCalendarAlt } from 'react-icons/fa';
import RoleBasedDropdown from './RoleBasedDropdown';
import TokenInput from './TokenInput';

const Chat = ({ prefillQuestion, onAutoExecuteQuery }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [file, setFile] = useState(null);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [activeDropdown, setActiveDropdown] = useState(null);
  const [dropdownPosition, setDropdownPosition] = useState({ x: 0, y: 0 });
  const [currentTokenIndex, setCurrentTokenIndex] = useState(-1);
  const messagesEndRef = useRef(null);
  const inputContainerRef = useRef(null);

  // Sample animated emojis for different message types
  const messageEmojis = {
    revenue: '📈',
    partners: '🤝',
    comparison: '⚖️',
    breakdown: '🗓️',
    default: '💡'
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Function to handle auto-executed queries using the new auto-query endpoint
  const handleAutoExecuteQuery = useCallback(async (query) => {
    if (!query.trim()) return;
    
    const userMessage = { 
      text: query, 
      sender: 'user',
      emoji: getMessageEmoji(query)
    };
    setMessages(prev => [...prev, userMessage]);
    setShowSuggestions(false);
    setIsLoading(true);
    
    try {
      // Use the auto-query endpoint for automatic executions
      const response = await axios.post('http://localhost:5000/auto-query', { query });
      const botMessage = { 
        text: response.data.response, 
        sender: 'bot',
        emoji: getMessageEmoji(query)
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('API Error:', error);
      setMessages(prev => [...prev, { 
        text: "⚠️ Sorry, I couldn't process your request. Please try again.", 
        sender: 'bot',
        emoji: '❌'
      }]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Updated useEffect to handle auto-execution
  useEffect(() => {
    if (prefillQuestion) {
      if (onAutoExecuteQuery) {
        // Auto-execute the query without setting input
        onAutoExecuteQuery(prefillQuestion);
      } else {
        // Set input for manual execution (existing behavior)
        setInput(prefillQuestion);
        setShowSuggestions(false);
      }
    }
  }, [prefillQuestion, onAutoExecuteQuery]);

  const getMessageEmoji = (text) => {
    if (text.toLowerCase().includes('revenue')) return messageEmojis.revenue;
    if (text.toLowerCase().includes('partner')) return messageEmojis.partners;
    if (text.toLowerCase().includes('compare') || text.toLowerCase().includes('performance')) return messageEmojis.comparison;
    if (text.toLowerCase().includes('monthly') || text.toLowerCase().includes('breakdown')) return messageEmojis.breakdown;
    return messageEmojis.default;
  };

  // Enhanced function to handle token clicks with better debugging
  const handleTokenClick = (role, position, tokenIndex) => {
    console.log('Token clicked - Role:', role);
    console.log('Token clicked - Position:', position);
    console.log('Token clicked - Index:', tokenIndex);
    console.log('Current input:', input);
    
    setDropdownPosition(position);
    setActiveDropdown(role);
    setCurrentTokenIndex(tokenIndex); // Store the token index for context determination
  };

  // Enhanced function to insert selected value into input with better token replacement
  const handleDropdownSelect = (value) => {
    if (activeDropdown) {
      console.log('Dropdown selection:', value);
      console.log('Active dropdown role:', activeDropdown);
      console.log('Current token index:', currentTokenIndex);
      
      // Create a pattern that matches the specific token we want to replace
      // We need to be more precise about which token to replace
      const tokens = input.match(/\[[^\]]+\]/g) || [];
      console.log('All tokens in input:', tokens);
      
      if (currentTokenIndex >= 0 && currentTokenIndex < tokens.length) {
        // Find the token that matches our role
        const tokenToReplace = `[${activeDropdown}]`;
        const matchingTokenIndex = tokens.findIndex((token, index) => 
          token.toLowerCase() === tokenToReplace.toLowerCase() && index >= currentTokenIndex
        );
        
        if (matchingTokenIndex >= 0) {
          // Replace the token in the original input string
          let newInput = input;
          let replacementCount = 0;
          newInput = newInput.replace(/\[[^\]]+\]/g, (match) => {
            if (match.toLowerCase() === tokenToReplace.toLowerCase() && replacementCount === 0) {
              replacementCount++;
              return value;
            }
            return match;
          });
          
          console.log('New input after replacement:', newInput);
          setInput(newInput);
        } else {
          // Fallback: replace the first occurrence of the token
          const tokenPattern = new RegExp(`\\[${activeDropdown.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\]`, 'i');
          const newInput = input.replace(tokenPattern, value);
          console.log('Fallback replacement, new input:', newInput);
          setInput(newInput);
        }
      } else {
        // Fallback: replace the first occurrence of the token
        const tokenPattern = new RegExp(`\\[${activeDropdown.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\]`, 'i');
        const newInput = input.replace(tokenPattern, value);
        console.log('Index-based replacement failed, using fallback:', newInput);
        setInput(newInput);
      }
      
      setActiveDropdown(null);
      setCurrentTokenIndex(-1);
    }
  };

  // Updated handleSendMessage to accept a parameter
  const handleSendMessage = async (messageText = null) => {
    const messageToSend = messageText || input;
    if (!messageToSend.trim()) return;
    
    const userMessage = { 
      text: messageToSend, 
      sender: 'user',
      emoji: getMessageEmoji(messageToSend)
    };
    setMessages(prev => [...prev, userMessage]);
    
    // Only clear input if we're using the current input value
    if (!messageText) {
      setInput('');
    }
    
    setShowSuggestions(false);
    setIsLoading(true);
    
    try {
      const response = await axios.post('http://localhost:5000/query', { query: messageToSend });
      const botMessage = { 
        text: response.data.response, 
        sender: 'bot',
        emoji: getMessageEmoji(messageToSend),
        hasTable: response.data.response.includes('<table') // Flag for table content
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('API Error:', error);
      setMessages(prev => [...prev, { 
        text: "⚠️ Sorry, I couldn't process your request. Please try again.", 
        sender: 'bot',
        emoji: '❌'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  // Wrapper for form submission
  const handleFormSubmit = (e) => {
    e.preventDefault();
    handleSendMessage();
  };

  const handleFileUpload = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    const formData = new FormData();
    formData.append('file', selectedFile);
    setIsLoading(true);

    try {
      const response = await axios.post('http://localhost:5000/upload', formData);
      setMessages(prev => [...prev, {
        text: `✅ **File uploaded successfully!**\n- Name: ${response.data.filename}\n- Rows: ${response.data.rows.toLocaleString()}`,
        sender: 'bot',
        emoji: '📄'
      }]);
    } catch (error) {
      console.error('Upload Error:', error);
      setMessages(prev => [...prev, {
        text: "❌ Failed to upload file. Please try again.",
        sender: 'bot',
        emoji: '❌'
      }]);
    } finally {
      setIsLoading(false);
      setFile(null);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setInput(suggestion);
    setShowSuggestions(false);
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (inputContainerRef.current && !inputContainerRef.current.contains(event.target)) {
        setActiveDropdown(null);
        setCurrentTokenIndex(-1);
      }
    };

    if (activeDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [activeDropdown]);

  // Expose the auto-execute function to parent components
  useEffect(() => {
    if (onAutoExecuteQuery) {
      onAutoExecuteQuery(handleAutoExecuteQuery);
    }
  }, [onAutoExecuteQuery, handleAutoExecuteQuery]);

  // Add Script Execution Support
  useEffect(() => {
    // Execute any scripts in dynamically loaded content
    const executeScripts = () => {
      const messageContainers = document.querySelectorAll('.message-with-tables');
      messageContainers.forEach(container => {
        const scripts = container.querySelectorAll('script');
        scripts.forEach(script => {
          if (!script.hasAttribute('data-executed')) {
            script.setAttribute('data-executed', 'true');
            const newScript = document.createElement('script');
            newScript.textContent = script.textContent;
            document.head.appendChild(newScript);
            document.head.removeChild(newScript);
          }
        });
      });
    };

    // Execute scripts when messages change
    executeScripts();
  }, [messages]);

  // Custom component to render message content with table support
  const MessageContent = ({ message }) => {
    if (message.hasTable || message.text.includes('<table')) {
      return (
        <div className="message-with-tables">
          <div 
            className="table-content"
            dangerouslySetInnerHTML={{ 
              __html: message.text
                .replace(/### ([^#\n]+)/g, '<h3 class="table-section-header">$1</h3>')
                .replace(/## ([^#\n]+)/g, '<h2 class="main-section-header">$1</h2>')
                .replace(/❌/g, '<span class="error-icon">❌</span>')
                .replace(/⚠️/g, '<span class="warning-icon">⚠️</span>')
                .replace(/ℹ️/g, '<span class="info-icon">ℹ️</span>')
            }}
          />
        </div>
      );
    }
    
    return <ReactMarkdown>{message.text}</ReactMarkdown>;
  };

  const renderMessage = (message, index) => (
    <motion.div
      key={index}
      className={`message ${message.sender}-message ${message.hasTable ? 'has-table' : ''}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ 
        duration: 0.4,
        ease: [0.25, 0.1, 0.25, 1],
        delay: message.sender === 'user' ? 0 : 0.2
      }}
    >
      <div className="message-content">
        <div className="message-sender">
          {message.sender === 'bot' ? (
            <motion.div 
              className="ai-avatar"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: 'spring' }}
            >
              <div className="avatar-pulse"></div>
              <span>iValue AI</span>
            </motion.div>
          ) : 'You'}
        </div>
        <motion.div 
          className="message-text"
          initial={{ scale: 0.95 }}
          animate={{ scale: 1 }}
        >
          {message.emoji && (
            <motion.span 
              className="message-emoji"
              initial={{ scale: 0, rotate: -30 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ delay: 0.3 }}
            >
              {message.emoji}
            </motion.span>
          )}
          <MessageContent message={message} />
        </motion.div>
      </div>
    </motion.div>
  );

  const suggestions = [
    {
      text: "Show revenue trends for [Business Head] in [Year]",
      icon: <FaChartLine />,
      color: "#10a37f"
    },
    {
      text: "Top 5 partners by sales volume for [Channel Champ]",
      icon: <FaUsers />,
      color: "#3d8af7"
    },
    {
      text: "Compare OEM performance for [Regional Commercial Business Manager] in [Year]",
      icon: <FaExchangeAlt />,
      color: "#f59e0b"
    },
    {
      text: "Monthly sales breakdown for [Vertical Account] in [Year]",
      icon: <FaCalendarAlt />,
      color: "#ef4444"
    },
    {
      text: "Sales performance from [Name] to [Name] relationship",
      icon: <FaUsers />,
      color: "#8b5cf6"
    }
  ];

  return (
    <div className="chat-container">
      {/* Enhanced table-specific styles with interactive features */}
      <style jsx global>{`
        .message.has-table .message-text {
          max-width: 100%;
          width: 100%;
        }
        
        .table-content {
          width: 100%;
          overflow-x: auto;
        }
        
        .interactive-table-container {
          margin: 15px 0;
          border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
          overflow: hidden;
          background: white;
        }

        .interactive-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 12px;
        }

        .expand-column {
          width: 60px !important;
          background: linear-gradient(135deg, #1e40af 0%, #1d4ed8 100%) !important;
          text-align: center !important;
        }

        .expand-btn {
          background: none;
          border: none;
          color: white;
          cursor: pointer;
          font-size: 14px;
          width: 100%;
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.2s ease;
        }

        .expand-btn:hover {
          background-color: rgba(255, 255, 255, 0.1);
        }

        .expandable-row {
          background-color: #f8fafc !important;
        }

        .expandable-row.expanded {
          background-color: #e2e8f0 !important;
        }

        .sub-table-container {
          padding: 0;
          background-color: #f1f5f9;
        }

        .sub-table {
          width: 100%;
          border-collapse: collapse;
          margin: 0;
          background-color: white;
        }

        .sub-table th {
          background: linear-gradient(135deg, #64748b 0%, #475569 100%);
          color: white;
          font-weight: 500;
          padding: 8px 6px;
          text-align: left;
          font-size: 10px;
          border-right: 1px solid rgba(255,255,255,0.2);
        }

        .sub-table td {
          padding: 6px;
          border-right: 1px solid #d1d5db;
          border-bottom: 1px solid #d1d5db;
          font-size: 10px;
          color: #374151;
        }

        .sub-table tr:nth-child(even) {
          background-color: #f9fafb;
        }

        .sub-table tr:hover {
          background-color: #e5e7eb;
        }
        
        .table-content .data-table {
          min-width: 100%;
          border-collapse: collapse;
          margin: 10px 0;
          font-size: 12px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
          border-radius: 8px;
          overflow: hidden;
          background: white;
        }
        
        .table-content .data-table th {
          background: linear-gradient(135deg, #10a37f 0%, #0e8f6f 100%);
          color: white;
          font-weight: 600;
          padding: 12px 8px;
          text-align: left;
          border-right: 1px solid rgba(255,255,255,0.2);
          font-size: 11px;
          white-space: nowrap;
        }
        
        .table-content .data-table td {
          padding: 8px 6px;
          border-right: 1px solid #e5e7eb;
          border-bottom: 1px solid #e5e7eb;
          font-size: 11px;
          white-space: nowrap;
          color: #1f2937;
          font-weight: 500;
        }

        /* Specific styling for different cell types */
        .table-content .data-table td:first-child {
          color: #111827;
          font-weight: 600;
        }

        /* Numeric value cells */
        .table-content .data-table td:not(:first-child):not([style*="color:"]) {
          color: #374151;
          font-weight: 500;
          text-align: right;
        }
        
        .table-content .data-table tr:nth-child(even) {
          background-color: #f8f9fa;
        }
        
        .table-content .data-table tr:hover {
          background-color: #e8f5e8;
          transition: background-color 0.2s ease;
        }

        /* Enhanced styling for total rows */
        .table-content .data-table tr:has(td:first-child:contains("TOTAL")) td,
        .table-content .data-table tr[data-total="true"] td,
        .table-content .data-table tbody tr:last-child:has(td:first-child[style*="font-weight: 700"]) td {
          background-color: #f3f4f6 !important;
          font-weight: 700 !important;
          border-top: 2px solid #10a37f !important;
          color: #111827 !important;
        }
        
        .table-content .data-table .total-row td {
          background-color: #f3f4f6 !important;
          font-weight: 700 !important;
          border-top: 2px solid #10a37f !important;
          color: #111827 !important;
        }
        
        .table-section-header {
          color: #10a37f;
          font-size: 16px;
          font-weight: 600;
          margin: 20px 0 10px 0;
          border-bottom: 2px solid #10a37f;
          padding-bottom: 5px;
        }
        
        .main-section-header {
          color: #1f2937;
          font-size: 20px;
          font-weight: 700;
          margin: 25px 0 15px 0;
          text-align: center;
          background: linear-gradient(135deg, #10a37f 0%, #3d8af7 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }
        
        .error-icon, .warning-icon, .info-icon {
          font-size: 14px;
          margin-right: 5px;
        }
        
        .table-container {
          margin: 15px 0;
          overflow-x: auto;
          border-radius: 8px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        /* Keep the existing growth value coloring but ensure it overrides */
        .table-content td[style*="color: #10a37f"] {
          font-weight: 600 !important;
          color: #10a37f !important;
        }
        
        .table-content td[style*="color: #ef4444"] {
          font-weight: 600 !important;
          color: #ef4444 !important;
        }
        
        @media (max-width: 768px) {
          .table-content .data-table {
            font-size: 10px;
          }
          
          .table-content .data-table th,
          .table-content .data-table td {
            padding: 6px 4px;
            font-size: 10px;
          }
          
          .table-section-header {
            font-size: 14px;
          }
          
          .main-section-header {
            font-size: 18px;
          }

          .interactive-table {
            font-size: 10px;
          }

          .sub-table {
            font-size: 9px;
          }

          .expand-btn {
            font-size: 12px;
          }
        }
        
        /* Responsive table wrapper */
        .message.has-table {
          max-width: 95%;
        }
        
        .message.has-table .message-content {
          width: 100%;
        }

        /* Animation for expand/collapse */
        .sub-row {
          transition: all 0.3s ease;
        }

        .sub-row.hidden {
          opacity: 0;
          height: 0;
          overflow: hidden;
        }

        .sub-row.visible {
          opacity: 1;
          height: auto;
        }

        /* Smooth scrolling for interactive elements */
        .interactive-table-container {
          scroll-behavior: smooth;
        }

        /* Custom scrollbar for table containers */
        .table-content::-webkit-scrollbar {
          height: 8px;
        }

        .table-content::-webkit-scrollbar-track {
          background: #f1f1f1;
          border-radius: 4px;
        }

        .table-content::-webkit-scrollbar-thumb {
          background: #10a37f;
          border-radius: 4px;
        }

        .table-content::-webkit-scrollbar-thumb:hover {
          background: #0e8f6f;
        }
      `}</style>
      
      <motion.div 
        className="chat-header"
        initial={{ y: -50 }}
        animate={{ y: 0 }}
        transition={{ type: "spring", stiffness: 300, damping: 20 }}
      >
        <div className="logo-container">
          <motion.div 
            className="logo"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            <motion.img 
              src="/iValue_Logo.png"
              alt="iValue Logo"
              className="logo-image"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ 
                delay: 0.3,
                type: "spring",
                stiffness: 200,
                damping: 15
              }}
              whileHover={{ 
                scale: 1.05,
                rotate: 2
              }}
            />
          </motion.div>
          <motion.div 
            className="tagline"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
          >
            AI Sales Assistant
          </motion.div>
        </div>
        
        <motion.label 
          className="file-upload-label"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
        >
          <FiUpload />
          <span>Upload Data</span>
          <input 
            type="file" 
            onChange={handleFileUpload}
            accept=".xlsx,.xls"
            className="file-input"
            disabled={isLoading}
          />
        </motion.label>
      </motion.div>

      <div className="messages-container">
        {showSuggestions && messages.length === 0 ? (
          <motion.div 
            className="suggestions-container"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
          >
            <motion.div 
              className="welcome-message"
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.6 }}
            >
              <h3>How can I help you today?</h3>
              <p>Ask me anything about your sales data or upload an Excel file to get started.</p>
            </motion.div>
            
            <motion.div 
              className="suggestion-buttons"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.8 }}
            >
              {suggestions.map((suggestion, i) => (
                <motion.button
                  key={i}
                  onClick={() => handleSuggestionClick(suggestion.text)}
                  whileHover={{ 
                    y: -5, 
                    boxShadow: "0 8px 16px rgba(0,0,0,0.1)",
                    scale: 1.02
                  }}
                  whileTap={{ scale: 0.98 }}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.9 + i * 0.1, type: 'spring' }}
                  style={{ 
                    background: `linear-gradient(135deg, ${suggestion.color} 0%, ${darkenColor(suggestion.color, 20)} 100%)`,
                    borderLeft: `4px solid ${lightenColor(suggestion.color, 30)}`
                  }}
                >
                  <span className="suggestion-icon">{suggestion.icon}</span>
                  {suggestion.text}
                </motion.button>
              ))}
            </motion.div>
          </motion.div>
        ) : (
          <AnimatePresence>
            {messages.map(renderMessage)}
          </AnimatePresence>
        )}

        {isLoading && (
          <motion.div 
            className="message bot-message"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <div className="message-content">
              <div className="message-sender">
                <div className="ai-avatar">
                  <div className="avatar-pulse"></div>
                  <span>iValue AI</span>
                </div>
              </div>
              <div className="loading-dots">
                <motion.div
                  animate={{ 
                    y: [0, -10, 0],
                    backgroundColor: ["#10a37f", "#3d8af7", "#f59e0b"]
                  }}
                  transition={{ 
                    repeat: Infinity, 
                    duration: 1.2,
                    ease: "easeInOut"
                  }}
                ></motion.div>
                <motion.div
                  animate={{ 
                    y: [0, -10, 0],
                    backgroundColor: ["#3d8af7", "#f59e0b", "#10a37f"]
                  }}
                  transition={{ 
                    repeat: Infinity, 
                    duration: 1.2,
                    delay: 0.2,
                    ease: "easeInOut"
                  }}
                ></motion.div>
                <motion.div
                  animate={{ 
                    y: [0, -10, 0],
                    backgroundColor: ["#f59e0b", "#10a37f", '#3d8af7']
                  }}
                  transition={{ 
                    repeat: Infinity, 
                    duration: 1.2,
                    delay: 0.4,
                    ease: "easeInOut"
                  }}
                ></motion.div>
              </div>
            </div>
          </motion.div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <motion.form 
        onSubmit={handleFormSubmit}
        className="input-container"
        initial={{ y: 50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.4 }}
        ref={inputContainerRef}
      >
        <motion.div 
          className="input-wrapper"
          whileFocusWithin={{ 
            boxShadow: "0 0 0 2px var(--ivalue-primary-light)",
            borderColor: "var(--ivalue-primary-light)"
          }}
        >
          <TokenInput
            value={input}
            onChange={setInput}
            placeholder="Message iValue AI..."
            disabled={isLoading}
            onTokenClick={handleTokenClick}
          />
          <motion.button
            type="submit"
            disabled={isLoading || !input.trim()}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            className="send-button"
            animate={{
              rotate: input.trim() ? [0, 5, -5, 0] : 0,
              transition: { duration: 0.5 }
            }}
          >
            <FiSend />
          </motion.button>
        </motion.div>
        
        {/* Add the dropdown component with enhanced debugging */}
        <AnimatePresence>
          {activeDropdown && (
            <RoleBasedDropdown
              role={activeDropdown}
              onSelect={handleDropdownSelect}
              position={dropdownPosition}
              isActive={!!activeDropdown}
              onClose={() => {
                setActiveDropdown(null);
                setCurrentTokenIndex(-1);
              }}
              containerRef={inputContainerRef}
              fullInputContext={input}
              tokenIndex={currentTokenIndex} // Pass the token index
            />
          )}
        </AnimatePresence>
        
        {file && (
          <motion.div 
            className="file-preview"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
          >
            <span>{file.name}</span>
            <motion.button 
              onClick={() => setFile(null)}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              className="remove-file"
            >
              <FiX />
            </motion.button>
          </motion.div>
        )}
        
        <div className="disclaimer">
          <motion.div
            animate={{ opacity: [0.6, 1, 0.6] }}
            transition={{ repeat: Infinity, duration: 2 }}
          >
            iValue AI can make mistakes. Consider checking important information.
          </motion.div>
        </div>
      </motion.form>
    </div>
  );
};

// Helper functions for color manipulation
function lightenColor(color, percent) {
  const num = parseInt(color.replace("#", ""), 16);
  const amt = Math.round(2.55 * percent);
  const R = (num >> 16) + amt;
  const G = ((num >> 8) & 0x00FF) + amt;
  const B = (num & 0x0000FF) + amt;
  return `#${(
    0x1000000 +
    (R < 255 ? (R < 1 ? 0 : R) : 255) * 0x10000 +
    (G < 255 ? (G < 1 ? 0 : G) : 255) * 0x100 +
    (B < 255 ? (B < 1 ? 0 : B) : 255)
  )
    .toString(16)
    .slice(1)}`;
}

function darkenColor(color, percent) {
  const num = parseInt(color.replace("#", ""), 16);
  const amt = Math.round(2.55 * percent);
  const R = (num >> 16) - amt;
  const G = ((num >> 8) & 0x00FF) - amt;
  const B = (num & 0x0000FF) - amt;
  return `#${(
    0x1000000 +
    (R > 0 ? (R < 255 ? R : 255) : 0) * 0x10000 +
    (G > 0 ? (G < 255 ? G : 255) : 0) * 0x100 +
    (B > 0 ? (B < 255 ? B : 255) : 0)
  )
    .toString(16)
    .slice(1)}`;
}

export default Chat;
import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';

const TokenInput = ({ value, onChange, placeholder, disabled, onTokenClick }) => {
  const inputRef = useRef(null);
  const containerRef = useRef(null);
  const [tokens, setTokens] = useState([]);

  // Parse the value into tokens when it changes
  useEffect(() => {
    if (value) {
      const tokenRegex = /(\[[^\]]+\])/g;
      const parts = value.split(tokenRegex);
      const newTokens = parts.map((part, index) => {
        if (part.startsWith('[') && part.endsWith(']')) {
          const tokenContent = part.slice(1, -1).trim();
          return {
            type: 'token',
            value: part,
            content: tokenContent.toLowerCase(),
            display: part,
            key: index,
            originalIndex: index
          };
        }
        return {
          type: 'text',
          value: part,
          content: part,
          display: part,
          key: index,
          originalIndex: index
        };
      }).filter(token => token.value !== '');
      
      setTokens(newTokens);
    } else {
      setTokens([]);
    }
  }, [value]);

  const handleInputChange = (e) => {
    if (onChange) {
      onChange(e.target.value);
    }
  };

  const handleInputFocus = () => {
    inputRef.current?.focus();
  };

  const handleTokenClick = (token, event) => {
    if (token.type === 'token' && onTokenClick) {
      event.stopPropagation();
      
      const tokenElement = event.target;
      const tokenRect = tokenElement.getBoundingClientRect();
      const containerRect = containerRef.current?.getBoundingClientRect();
      
      if (!containerRect) return;
      
      // Calculate token type index
      let tokenTypeIndex = 0;
      
      if (token.content.toLowerCase() === 'name') {
        const tokensBeforeThis = tokens.slice(0, tokens.findIndex(t => t.key === token.key));
        tokenTypeIndex = tokensBeforeThis.filter(t => 
          t.type === 'token' && t.content.toLowerCase() === 'name'
        ).length;
      } else {
        tokenTypeIndex = tokens.filter(t => t.type === 'token').findIndex(t => t.key === token.key);
      }
      
      onTokenClick(
        token.content,
        {
          x: tokenRect.left - containerRect.left,
          y: tokenRect.bottom - containerRect.top
        },
        tokenTypeIndex
      );
    }
  };

  // Check if we have any tokens to determine if input should be transparent
  const hasTokens = tokens.some(token => token.type === 'token');

  return (
    <div 
      className="token-input-container" 
      onClick={handleInputFocus}
      ref={containerRef}
      style={{
        position: 'relative',
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        minHeight: '40px'
      }}
    >
      {/* Input field - make text transparent when tokens are present */}
      <input
        ref={inputRef}
        type="text"
        value={value || ''}
        onChange={handleInputChange}
        placeholder={placeholder}
        disabled={disabled}
        className="token-input-field"
        style={{
          width: '100%',
          background: 'transparent',
          border: 'none',
          outline: 'none',
          color: hasTokens ? 'transparent' : 'var(--white)', // Hide text when tokens present
          fontSize: 'var(--font-size-base)',
          padding: 'var(--spacing-sm) var(--spacing-md)',
          caretColor: 'var(--white)', // Keep cursor visible
        }}
      />
      
      {/* Overlay tokens on top of the input */}
      {hasTokens && (
        <div 
          className="tokens-display-overlay"
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            pointerEvents: 'none',
            display: 'flex',
            alignItems: 'center',
            padding: 'var(--spacing-sm) var(--spacing-md)',
            overflow: 'hidden'
          }}
        >
          {tokens.map(token => (
            <span
              key={token.key}
              className={`token ${token.type} ${token.type === 'token' ? 'clickable-token' : ''}`}
              onClick={(e) => {
                if (token.type === 'token') {
                  e.stopPropagation();
                  handleTokenClick(token, e);
                }
              }}
              style={{
                cursor: token.type === 'token' ? 'pointer' : 'default',
                backgroundColor: token.type === 'token' ? 'var(--ivalue-primary-light)' : 'transparent',
                color: token.type === 'token' ? 'white' : 'var(--white)', // Show text color for non-tokens
                padding: token.type === 'token' ? '2px 6px' : '0',
                borderRadius: token.type === 'token' ? '4px' : '0',
                margin: token.type === 'token' ? '0 2px' : '0',
                pointerEvents: token.type === 'token' ? 'auto' : 'none',
                fontSize: 'var(--font-size-base)',
                lineHeight: '1.5'
              }}
            >
              {token.display}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

export default TokenInput;
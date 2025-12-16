import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const RoleBasedDropdown = ({ 
  role, 
  onSelect, 
  position, 
  isActive,
  onClose,
  containerRef,
  fullInputContext = '', // Add this prop to get the full input context
  tokenIndex = -1 // Add tokenIndex parameter
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const dropdownRef = useRef(null);
  
  // Enhanced getRoleFromPlaceholder function with better token position tracking
  const getRoleFromPlaceholder = (placeholder, tokenIndex = -1) => {
    const lowerPlaceholder = placeholder.toLowerCase().trim();
    const lowerContext = fullInputContext.toLowerCase();
    
    console.log('Mapping placeholder:', `"${placeholder}"`);
    console.log('Full context:', `"${fullInputContext}"`);
    console.log('Token index:', tokenIndex);
    
    // Direct role mappings - these should take precedence
    const directRoleMapping = {
      'business head': 'Business Head',
      'group business manager': 'Group Business Manager',
      'channel champ': 'Channel Champ',
      'group channel champ': 'Group Channel Champ',
      'vertical account': 'Vertical Account',
      'regional commercial business manager': 'Regional Commercial Business Manager',
      'business manager': 'Regional Commercial Business Manager',
      'year': 'Year',
      'account': 'Vertical Account',
      'vertical champ': 'Vertical Champ',
      'oem': 'OEM',
      'partner': 'Partner',
      'end customer': 'End Customer',
      'customer': 'End Customer'
    };
    
    // Check for exact match first (except for 'name')
    if (lowerPlaceholder !== 'name' && directRoleMapping[lowerPlaceholder]) {
      console.log('Direct match found:', directRoleMapping[lowerPlaceholder]);
      return directRoleMapping[lowerPlaceholder];
    }
    
    // Check for partial matches in direct mapping (except for 'name')
    if (lowerPlaceholder !== 'name') {
      for (const [key, value] of Object.entries(directRoleMapping)) {
        if (lowerPlaceholder.includes(key)) {
          console.log('Partial match found:', value);
          return value;
        }
      }
    }
    
    // Enhanced handling for [Name] token
    if (lowerPlaceholder === 'name') {
      console.log('Processing [Name] token with context:', fullInputContext);
      console.log('Token index:', tokenIndex);
      
      // Extract all tokens from the context to understand the structure
      const tokens = fullInputContext.match(/\[[^\]]+\]/g) || [];
      console.log('All tokens in context:', tokens);
      
      // Split the full context into words to analyze position-based context
      const words = fullInputContext.toLowerCase().split(/\s+/);
      
      // If we have a specific token index, analyze the context around that specific token
      if (tokenIndex >= 0) {
        // Find the position of the specific [Name] token in the original string
        let nameTokenCount = 0;
        let targetTokenPosition = -1;
        
        // Find the character position of our specific [Name] token
        const nameTokenRegex = /\[name\]/gi;
        let match;
        while ((match = nameTokenRegex.exec(fullInputContext)) !== null) {
          if (nameTokenCount === tokenIndex) {
            targetTokenPosition = match.index;
            break;
          }
          nameTokenCount++;
        }
        
        console.log('Target token position in string:', targetTokenPosition);
        
        if (targetTokenPosition >= 0) {
          // Get the text before this specific [Name] token
          const textBeforeToken = fullInputContext.substring(0, targetTokenPosition).toLowerCase();
          const wordsBeforeToken = textBeforeToken.split(/\s+/).filter(word => word.length > 0);
          
          console.log('Text before token:', textBeforeToken);
          console.log('Words before token:', wordsBeforeToken);
          
          // Look for role keywords in the immediate vicinity (last 5 words) before this token
          const recentWords = wordsBeforeToken.slice(-5).join(' ');
          console.log('Recent words before token:', recentWords);
          
          // Define role detection patterns with priority order
          const rolePatterns = [
            { pattern: /\boem\b/, role: 'OEM' },
            { pattern: /\bpartner\b/, role: 'Partner' },
            { pattern: /\bend customer\b|\bcustomer\b/, role: 'End Customer' },
            { pattern: /\bbusiness head\b/, role: 'Business Head' },
            { pattern: /\bgroup business manager\b/, role: 'Group Business Manager' },
            { pattern: /\bgroup channel champ\b/, role: 'Group Channel Champ' },
            { pattern: /\bchannel champ\b/, role: 'Channel Champ' },
            { pattern: /\bvertical champ\b/, role: 'Vertical Champ' },
            { pattern: /\bregional commercial business manager\b|\bbusiness manager\b/, role: 'Regional Commercial Business Manager' },
            { pattern: /\bvertical account\b|\baccount\b/, role: 'Vertical Account' }
          ];
          
          // Check patterns against the text before this specific token
          for (const { pattern, role } of rolePatterns) {
            if (pattern.test(recentWords) || pattern.test(textBeforeToken)) {
              console.log('Pattern match found for token:', role);
              return role;
            }
          }
          
          // If no pattern match, look at the broader context for relationship patterns
          const fullContext = fullInputContext.toLowerCase();
          
          // Enhanced relationship detection for multiple [Name] tokens
          const multiNamePatterns = [
            {
              pattern: /business head.*?with.*?oem|oem.*?with.*?business head/i,
              roles: ['Business Head', 'OEM']
            },
            {
              pattern: /business manager.*?oem|oem.*?business manager/i,
              roles: ['Regional Commercial Business Manager', 'OEM']
            },
            {
              pattern: /group channel champ.*?partner|partner.*?group channel champ/i,
              roles: ['Group Channel Champ', 'Partner']
            },
            {
              pattern: /channel champ.*?partner|partner.*?channel champ/i,
              roles: ['Channel Champ', 'Partner']
            },
            {
              pattern: /vertical champ.*?customer|customer.*?vertical champ/i,
              roles: ['Vertical Champ', 'End Customer']
            }
          ];
          
          // Find which pattern matches and determine role based on token position
          for (const { pattern, roles } of multiNamePatterns) {
            if (pattern.test(fullContext)) {
              console.log('Multi-name pattern found:', pattern.toString());
              
              // Count how many [Name] tokens appear before our target position
              const textBeforeTarget = fullInputContext.substring(0, targetTokenPosition);
              const nameTokensBefore = (textBeforeTarget.match(/\[name\]/gi) || []).length;
              
              console.log('Name tokens before target:', nameTokensBefore);
              
              // Use the position to determine which role this should be
              if (nameTokensBefore === 0 && roles[0]) {
                console.log('First [Name] token, role:', roles[0]);
                return roles[0];
              } else if (nameTokensBefore >= 1 && roles[1]) {
                console.log('Second+ [Name] token, role:', roles[1]);
                return roles[1];
              }
            }
          }
        }
      }
      
      // Fallback: use original logic for single token or when position-based detection fails
      const context = fullInputContext.toLowerCase();
      
      // Individual role detection based on keywords in context
      const keywordToRole = [
        { keywords: ['business manager'], role: 'Regional Commercial Business Manager' },
        { keywords: ['group channel champ'], role: 'Group Channel Champ' },
        { keywords: ['channel champ'], role: 'Channel Champ' },
        { keywords: ['vertical champ'], role: 'Vertical Champ' },
        { keywords: ['business head'], role: 'Business Head' },
        { keywords: ['group business manager'], role: 'Group Business Manager' },
        { keywords: ['oem'], role: 'OEM' },
        { keywords: ['partner'], role: 'Partner' },
        { keywords: ['customer', 'end customer'], role: 'End Customer' },
        { keywords: ['vertical account'], role: 'Vertical Account' }
      ];
      
      for (const { keywords, role } of keywordToRole) {
        if (keywords.some(keyword => context.includes(keyword))) {
          console.log('Keyword context match:', role);
          return role;
        }
      }
      
      // Default fallback for [Name] if no context is detected
      console.log('No specific context detected for [Name], defaulting to Business Head');
      return 'Business Head';
    }
    
    console.log('No match found, defaulting to Business Head');
    return 'Business Head';
  };

  // Updated role-based data with all the correct names including Name role
  const roleData = {
    'Business Head': [
      'Brijesh Shrivastava', 'Sunil Kumar Pillai', 'Sushant Ranshur'
    ],
    'Group Business Manager': [
      'Manoranjan Rana', 'Amol Bharat Dalal', 'Ankit Pandey', 
      'Dipanjan Ghosh', 'Kanchan Ganeshrane', 'Mihir Ghosh', 
      'Mohamed Riyaz', 'Mukundan Gs', 'Saurabh Kumar', 
      'Rupa Sharma', 'Nagendra Bharadwaj'
    ],
    'Channel Champ': [
      'Aayush Kaul', 'Anu Johnson', 'Chaitanya Deshmukh', 
      'Adeel Ahmed', 'Mohit Chugh', 'Gaurav Upadhyay', 
      'Himanshu Sharma', 'Lalit S Sudrik'
    ],
    'Group Channel Champ': [
      'Jitender Sharma', 'Lalit S Sudrik', 
      'Sathyanarayna H S', 'Calvin Samuel'
    ],
    'Vertical Account': [
      'BFSI', 'Enterprises', 'Government', 'PSU-Gov'
    ],
    'Vertical Champ': [
      'Aarun Sudhir', 'Abinash Sahoo', 'Adarsh Priyatam', 
      'Ajay Vasoya', 'Akash Singhal', 'Amit Jain', 
      'Ankit Gupta', 'Arpit Bharti', 'Atul Sharma'
    ],
    'Regional Commercial Business Manager': [
      'Ankit Pandey', 'Animesh Saraswat', 'Aysha Nathiha A', 
      'Amol Bharat Dalal', 'Jalindra Chavan', 'Dipanjan Ghosh', 
      'Jatin Dev', 'Manoranjan Rana', 'Mohamed Riyaz', 
      'Mihir Ghosh', 'Kanchan Ganeshrane', 'Mohit Bohra', 
      'Rakesh Kumar Jena', 'Mukundan Gs', 'Nagendra Bharadwaj', 
      'Sorabh Saraswat', 'Rupa Sharma', 'Umesh K. Muralidhar'
    ],
    'Year': [
      '2022-23', '2023-24', '2024-25', '2025-26', '2026-27',
      '2027-28', '2028-29', '2029-30', '2030-31', '2031-32'
    ],
    'OEM': [
      'SENTINELONE',
      '1KOSMOS', 'A10', 'AKAMAI', 'ALGOSEC', 'Alcatel',
      'ANOMALI', 'APPNOMIC', 'ARCON', 'ARCSERVE', 'ARISTA',
      'Array', 'BLACKBERRY', 'CHECKPOINT', 'CLOUDFLARE', 'CLOUDERA',
      'CLOUDSEK', 'COHESITY', 'CONFLUENT', 'CYBERARK', 'DELINEA',
      'DYNATRACE', 'EnterpriseDB', 'ENTRUST', 'EXINDA', 'FORCEPOINT',
      'FORTRA', 'GCP CLOUD', 'Github', 'GOOGLE SECOPS', 'GRIDGAIN',
      'GURUCUL SOLUTIONS', 'HITACHI', 'INNSPARK', 'Instasafe', 'KEYSIGHT',
      'LENOVO', 'MASTERCARD', 'Morphisec', 'NETSCOUT', 'NETSKOPE',
      'NUTANIX', 'OPENTEXT', 'PROGIST', 'QUANTUM', 'RSA',
      'RUBRIK', 'Sapphire', 'SOLACE', 'SPLUNK', 'SOTI',
      'STRATUS', 'SUSE', 'TENABLE', 'THALES', 'VANTAGEO',
      'WebWerks', 'YUBICO'
    ],
    'Partner': [
        'Techjockey Infotech Pvt Ltd', 'Riskberg Consulting Pvt Ltd', 'Anantya Infratech',
        'RAH Infotech Pvt Ltd', 'Sify Technologies Ltd', 'Tecmee Technologies Pvt Ltd',
        'Integre Solutions Pvt Ltd', 'Golden Bright Star Pvt Ltd', 'Infosys Ltd'
    ],
    'End Customer': [
      'Infosys', 'Tata Consultancy', 'Wipro', 'HCL Technologies',
      'Cognizant', 'Accenture', 'Capgemini', 'IBM India'
    ],
    // Add Name role data that combines all relevant names
    'Name': [
      // Business Heads
      'Brijesh Shrivastava', 'Sunil Kumar Pillai', 'Sushant Ranshur',
      // Group Business Managers
      'Manoranjan Rana', 'Amol Bharat Dalal', 'Ankit Pandey', 
      'Dipanjan Ghosh', 'Kanchan Ganeshrane', 'Mihir Ghosh', 
      'Mohamed Riyaz', 'Mukundan Gs', 'Saurabh Kumar', 
      'Rupa Sharma', 'Nagendra Bharadwaj',
      // Channel Champs
      'Aayush Kaul', 'Anu Johnson', 'Chaitanya Deshmukh', 
      'Adeel Ahmed', 'Mohit Chugh', 'Gaurav Upadhyay', 
      'Himanshu Sharma', 'Lalit S Sudrik',
      // Group Channel Champs (some overlap with above)
      'Sathyanarayna H S', 'Calvin Samuel',
      // Vertical Champs
      'Aarun Sudhir', 'Abinash Sahoo', 'Adarsh Priyatam', 
      'Ajay Vasoya', 'Akash Singhal', 'Amit Jain', 
      'Ankit Gupta', 'Arpit Bharti', 'Atul Sharma',
      // Regional Commercial Business Managers (some overlap)
      'Animesh Saraswat', 'Aysha Nathiha A', 'Jalindra Chavan', 
      'Jatin Dev', 'Mohit Bohra', 'Rakesh Kumar Jena', 
      'Sorabh Saraswat', 'Umesh K. Muralidhar'
    ]
  };

  // Get the actual role name from the placeholder text, passing tokenIndex
  const actualRole = getRoleFromPlaceholder(role, tokenIndex);
  const items = roleData[actualRole] || [];
  
  // Handle both strings and numbers for filtering
  const filteredItems = items.filter(item => {
    if (typeof item === 'string') {
      return item.toLowerCase().includes(searchTerm.toLowerCase());
    } else if (typeof item === 'number') {
      return item.toString().includes(searchTerm);
    }
    return false;
  });

  // Calculate position to ensure dropdown is visible
  const calculatePosition = () => {
    if (!containerRef.current) return position;
    
    const containerRect = containerRef.current.getBoundingClientRect();
    const dropdownHeight = 300;
    const viewportHeight = window.innerHeight;
    
    const spaceBelow = viewportHeight - (containerRect.top + position.y + dropdownHeight);
    const spaceAbove = containerRect.top + position.y - dropdownHeight;
    
    if (spaceBelow < 50 && spaceAbove > 50) {
      return { x: position.x, y: position.y - dropdownHeight - 5 };
    }
    
    return { x: position.x, y: position.y + 5 };
  };

  const dropdownPosition = calculatePosition();

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [onClose]);

  // Debug logging to help troubleshoot
  console.log('Role placeholder received:', `"${role}"`);
  console.log('Token index:', tokenIndex);
  console.log('Actual role resolved:', actualRole);
  console.log('Available items:', items.length > 0 ? items : 'No items found');

  if (!isActive) return null;

  return (
    <motion.div
      ref={dropdownRef}
      className="role-dropdown"
      initial={{ opacity: 0, y: -10, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -10, scale: 0.95 }}
      transition={{ duration: 0.2 }}
      style={{
        position: 'absolute',
        left: dropdownPosition.x,
        top: dropdownPosition.y,
        zIndex: 1000,
        // Enhanced solid styling
        backgroundColor: '#2a2a2a', // Dark solid background
        border: '1px solid #444',
        borderRadius: '8px',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4), 0 4px 16px rgba(0, 0, 0, 0.2)',
        minWidth: '250px',
        maxWidth: '400px',
        maxHeight: '300px',
        overflow: 'hidden',
        backdropFilter: 'none' // Remove any backdrop filter
      }}
    >
      <div 
        className="dropdown-header"
        style={{
          padding: '12px 16px',
          backgroundColor: '#333',
          borderBottom: '1px solid #444',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
      >
        <span style={{
          fontWeight: '600',
          color: '#ffffff',
          fontSize: '14px'
        }}>
          Select {actualRole}
        </span>
        <button 
          className="close-dropdown" 
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            color: '#999',
            fontSize: '18px',
            cursor: 'pointer',
            padding: '0',
            width: '20px',
            height: '20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          ×
        </button>
      </div>
      
      <div 
        className="dropdown-search"
        style={{
          padding: '12px 16px',
          backgroundColor: '#2a2a2a',
          borderBottom: '1px solid #444'
        }}
      >
        <input
          type="text"
          placeholder={`Search ${actualRole}...`}
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          autoFocus
          style={{
            width: '100%',
            padding: '8px 12px',
            backgroundColor: '#1a1a1a',
            border: '1px solid #555',
            borderRadius: '6px',
            color: '#ffffff',
            fontSize: '14px',
            outline: 'none'
          }}
        />
      </div>
      
      <div 
        className="dropdown-list"
        style={{
          maxHeight: '200px',
          overflowY: 'auto',
          backgroundColor: '#2a2a2a',
          // Special styling for Year items
          display: actualRole === 'Year' ? 'grid' : 'block',
          gridTemplateColumns: actualRole === 'Year' ? 'repeat(2, 1fr)' : 'none',
          gap: actualRole === 'Year' ? '8px' : '0',
          padding: actualRole === 'Year' ? '12px' : '0'
        }}
      >
        {filteredItems.length > 0 ? (
          filteredItems.map((item, index) => (
            <motion.div
              key={index}
              className="dropdown-item"
              onClick={() => onSelect(item)}
              whileHover={{ backgroundColor: '#3a3a3a' }}
              transition={{ duration: 0.1 }}
              style={{
                padding: actualRole === 'Year' ? '8px 12px' : '10px 16px',
                cursor: 'pointer',
                color: '#ffffff',
                fontSize: '14px',
                borderBottom: index < filteredItems.length - 1 && actualRole !== 'Year' ? '1px solid #333' : 'none',
                userSelect: 'none',
                // Button-like styling for Year items
                borderRadius: actualRole === 'Year' ? '6px' : '0',
                backgroundColor: actualRole === 'Year' ? '#3a3a3a' : 'transparent',
                textAlign: actualRole === 'Year' ? 'center' : 'left',
                border: actualRole === 'Year' ? '1px solid #555' : 'none',
                margin: actualRole === 'Year' ? '0' : '0'
              }}
            >
              {item}
            </motion.div>
          ))
        ) : (
          <div 
            className="dropdown-empty"
            style={{
              padding: '20px 16px',
              color: '#999',
              textAlign: 'center',
              fontSize: '14px',
              gridColumn: actualRole === 'Year' ? '1 / -1' : 'auto'
            }}
          >
            No results found
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default RoleBasedDropdown;
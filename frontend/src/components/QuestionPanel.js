// components/QuestionPanel.js
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  FiChevronLeft, 
  FiChevronRight, 
  FiUsers, 
  FiTrendingUp, 
  FiPieChart,
  FiBarChart2,
  FiDollarSign,
  FiGlobe,
  FiBriefcase,
  FiUser,
  FiTarget,
  FiChevronDown,
  FiChevronUp,
  FiCalendar,
  FiMap,
  FiServer,
  FiShield,
  FiDatabase,
  FiLayers,
  FiChevronRight as FiChevronRightIcon,
  FiUserCheck,
  FiUserX,
  FiUserPlus,
  FiSearch,
  FiX,
  FiDatabase as FiDatabaseIcon,
  FiRefreshCw,
  FiUpload,
  FiCheck
} from 'react-icons/fi';

const QuestionPanel = ({ onQuestionSelect, onAutoExecuteQuery, isOpen, onToggle, uploadedData }) => {
  const [selectedMainCategory, setSelectedMainCategory] = useState(null);
  const [selectedSubCategory, setSelectedSubCategory] = useState(null);
  const [showYearOptions, setShowYearOptions] = useState(false);
  const [showRegionOptions, setShowRegionOptions] = useState(false);
  const [showOEMOptions, setShowOEMOptions] = useState(false);
  const [showPartnerOptions, setShowPartnerOptions] = useState(false);
  const [showVerticalAccountOptions, setShowVerticalAccountOptions] = useState(false);
  const [showChannelOptions, setShowChannelOptions] = useState(false);
  const [showBusinessHeadOptions, setShowBusinessHeadOptions] = useState(false);
  const [showBusinessManagerOptions, setShowBusinessManagerOptions] = useState(false);
  const [showGroupBusinessManagerOptions, setShowGroupBusinessManagerOptions] = useState(false);
  const [showChannelHeadOptions, setShowChannelHeadOptions] = useState(false);
  const [showGroupChannelChampOptions, setShowGroupChannelChampOptions] = useState(false);
  const [showEndCustomerOptions, setShowEndCustomerOptions] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  // Individual search states for each option panel
  const [oemSearch, setOemSearch] = useState('');
  const [partnerSearch, setPartnerSearch] = useState('');
  const [regionSearch, setRegionSearch] = useState('');
  const [verticalAccountSearch, setVerticalAccountSearch] = useState('');
  const [channelSearch, setChannelSearch] = useState('');
  const [businessHeadSearch, setBusinessHeadSearch] = useState('');
  const [businessManagerSearch, setBusinessManagerSearch] = useState('');
  const [groupBusinessManagerSearch, setGroupBusinessManagerSearch] = useState('');
  const [channelHeadSearch, setChannelHeadSearch] = useState('');
  const [groupChannelChampSearch, setGroupChannelChampSearch] = useState('');
  const [yearSearch, setYearSearch] = useState('');
  const [endCustomerSearch, setEndCustomerSearch] = useState('');

  // Extract unique values from uploaded data
  const extractUniqueValues = (data) => {
    if (!data || !Array.isArray(data) || data.length === 0) {
      return {
        oems: [],
        partners: [],
        regions: [],
        verticalAccounts: [],
        channels: [],
        businessHeads: [],
        businessManagers: [],
        groupBusinessManagers: [],
        channelHeads: [],
        groupChannelChamps: [],
        endCustomers: [],
        years: []
      };
    }

    const extractColumn = (data, possibleKeys) => {
      const values = new Set();
      data.forEach(row => {
        for (const key of possibleKeys) {
          if (row[key] && typeof row[key] === 'string' && row[key].trim()) {
            values.add(row[key].trim());
            break;
          } else if (row[key] && typeof row[key] === 'number') {
            values.add(row[key].toString());
            break;
          }
        }
      });
      return Array.from(values).sort((a, b) => a.localeCompare(b));
    };

    // Extract years from date columns
    const yearSet = new Set();
    data.forEach(row => {
      const dateKeys = ['Date', 'date', 'Invoice Date', 'Transaction Date', 'FY', 'Financial Year'];
      for (const key of dateKeys) {
        if (row[key]) {
          const dateStr = row[key].toString();
          const yearMatch = dateStr.match(/\b(20\d{2})\b/);
          if (yearMatch) {
            const year = parseInt(yearMatch[0]);
            yearSet.add(year);
            yearSet.add(`${year}-${(year + 1).toString().slice(2)}`);
            break;
          }
        }
      }
    });

    const extracted = {
      oems: extractColumn(data, ['OEM', 'oem', 'Oem', 'Vendor', 'Manufacturer', 'Product']),
      partners: extractColumn(data, ['Partner', 'partner', 'Channel Partner', 'Distributor', 'Reseller']),
      regions: extractColumn(data, ['Region', 'region', 'Location', 'Territory', 'Area']),
      verticalAccounts: extractColumn(data, ['Vertical Account', 'Vertical', 'vertical', 'Account Type', 'Industry', 'Sector']),
      channels: extractColumn(data, ['Channel', 'channel', 'Channel Type', 'Sales Channel', 'Route to Market']),
      businessHeads: extractColumn(data, ['Business Head', 'businessHead', 'BH', 'Head', 'Sales Head']),
      businessManagers: extractColumn(data, ['Business Manager', 'businessManager', 'BM', 'Manager', 'Account Manager']),
      groupBusinessManagers: extractColumn(data, ['Group Business Manager', 'groupBusinessManager', 'GBM', 'Group Manager']),
      channelHeads: extractColumn(data, ['Channel Head', 'channelHead', 'CH', 'Channel Manager']),
      groupChannelChamps: extractColumn(data, ['Group Channel Champ', 'groupChannelChamp', 'GCC', 'Channel Champion']),
      endCustomers: extractColumn(data, ['End Customer', 'Customer', 'Client', 'Account Name', 'Company']),
      years: Array.from(yearSet).sort().reverse()
    };

    return extracted;
  };

  // Dynamic data from uploaded file or fallback to hardcoded
  const extractedValues = uploadedData ? extractUniqueValues(uploadedData) : {
    oems: [],
    partners: [],
    regions: [],
    verticalAccounts: [],
    channels: [],
    businessHeads: [],
    businessManagers: [],
    groupBusinessManagers: [],
    channelHeads: [],
    groupChannelChamps: [],
    endCustomers: [],
    years: []
  };

  // Dynamic options with fallback
  const oemOptions = extractedValues.oems.length > 0 
    ? extractedValues.oems 
    : ['SENTINELONE',
    'HITACHI',
    'TRELLIX',
    'FORCEPOINT',
    'OPENTEXT',
    'TENABLE',
    'Alcatel',
    'ARISTA',
    'NETSCOUT',
    'Array',
    'THALES',
    'CHECKPOINT',
    'ENTRUST',
    'KEYSIGHT',
    'AKAMAI',
    'RIVERBED',
    'MANDIANT',
    'CLOUDFLARE',
    'CYBERARK',
    'YUBICO',
    'A10',
    'ARCSERVE',
    'NETSKOPE',
    'PARABLU',
    'DELINEA',
    'APPNOMIC',
    'IVANTI UK',
    'PROPHISH',
    'TITUS',
    'CLOUDERA',
    'OPG',
    'STRATUS',
    'COHESITY',
    'SUSE',
    'PROGIST',
    'NORDEN',
    'COSOSYS',
    'SECURONIX',
    'SPLUNK',
    'GRIDGAIN',
    'Github',
    'CONFLUENT',
    'ALGOSEC',
    'UTIMACO',
    'Pure Storage',
    'FIREEYE',
    'INFINITY LABS',
    'IVANTI',
    'SOLACE',
    'PERPETUUITI',
    'MUSARUBRA',
    'F5 NETWORKS',
    'VEEAM',
    'ORACLE',
    'SMOKSCREEN',
    'DYNATRACE',
    '-',
    'Efficient IP',
    'PERFMON',
    '1KOSMOS',
    'EXINDA',
    'PALO ALTO',
    'ACCOPS',
    'ARCON',
    'QualityKiosk',
    'RECORDED FUTURE',
    'GURUCUL SOLUTIONS',
    'SYMPHONYAI SUMMIT',
    'TELIMART',
    'RUBRIK',
    'DELL',
    'EnterpriseDB',
    'BLACKBERRY',
    'SYMANTEC',
    'DIGITAL.AI',
    'BARCO',
    'HP',
    'Sapphire',
    'Morphisec',
    'SUMO LOGIC',
    'FORTRA',
    'INNSPARK',
    'CYBERNEXA',
    'MASTERCARD',
    'HPE',
    'IVSERVICES',
    'FORTANIX',
    'ROBOXO',
    'ZSCALER',
    'Pi DataCenters Pvt. Ltd',
    'Safran Trusted 4D SAS',
    'GOOGLE SECOPS',
    'VANTAGEO',
    'ANOMALI',
    'IVALUE',
    'ASPL',
    'VELOX',
    'VERITAS',
    'Instasafe',
    'Brocade',
    'PERSISTENT',
    'PERKINS',
    'ELSY',
    'UBIQUITI',
    'AVALON',
    'DAHUA',
    'FELIX',
    'JUNIPER',
    'FENG',
    'RR CABLE',
    'SAMSUNG',
    'LENOVO',
    'SANDS',
    'nCipher',
    'Fortinet',
    'Dlink',
    'PICUS',
    'TANDBERG',
    'BROTHER',
    'CYBERJEET',
    'Fujitsu',
    'NETAPP',
    'FUJI ELECTRIC',
    'NETRACK',
    'ZEBRA',
    'BEETLE',
    'Canon',
    'Acer',
    'SECUREYE',
    'NUTANIX',
    'CLOUDSEK',
    'SimplifyIT',
    'TERAFENCE',
    'QUANTUM',
    'ARETE',
    'GCP CLOUD',
    'ZABBIX',
    'SOTI',
    'Need4Viz',
    'WebWerks',
    'CYWARE',
    'Chronicle Software Ltd',
    'RSA',
    'VEHERE',
    'RADWARE',
    'CISCO',
    'vMWare',
    'TEMENOS',
    'CYBLE',
    'PULSE SECURE',
    'EFICIENTIP',
    'VIRSEC',
    'MongoDB',
    'BMC',
    'SAFE-T',
    'Lakeside',
    'LOOKOUT',
    'TRENDMICRO',
    'GIEOM',
    'REVERIE'
  ];

  const partnerOptions = extractedValues.partners.length > 0 
    ? extractedValues.partners 
    : [
      'Techjockey Infotech Pvt Ltd',
      'Riskberg Consulting Pvt Ltd',
      'Anantya Infratech',
      'RAH Infotech Pvt Ltd',
      'Sify Technologies Ltd',
      'Tecmee Technologies Pvt Ltd',
      'Integre Solutions Pvt Ltd',
      'Golden Bright Star Pvt Ltd',
      'Infosys Ltd',
      'Intek Micro Systems Pvt Ltd',
      'Door Sanchar Systems',
      'Secure Network Solutions India Pvt Ltd',
      'Centre for Development of Telematics',
      'Microhard IT Solutions Pvt Ltd',
      'Hitachi Vantara India Pvt Ltd',
      'IBM India Pvt Ltd',
      'Tata Communications Ltd',
      'Starlight Data Solutions Pvt Ltd',
      'Digital Track Solutions Pvt Ltd',
      'Madras Security Printers Pvt Ltd',
      'Samir Computers',
      'Lyra Network Pvt Ltd',
      'Softcell Technologies Global Pvt Ltd',
      'StarOne IT Solutions India Pvt Ltd',
      'Computer Age Management Services Lt',
      'Emudhra Ltd',
      'Speed Sign Technologies Pvt Ltd',
      'Mudra Electronics Ltd',
      'Shaurya Prabhat Infratech',
      'Sify Digital Services Ltd',
      'Saaksan Technologies Pvt Ltd',
      'Netweb Technologies India Ltd',
      'Dciphers IT Solutions Pvt Ltd',
      'Kyndryl Solutions Pvt Ltd',
      'Biesse India Pvt Ltd',
      'Thrust Systems',
      'TNS Infrastructure Technology Pvt Ltd',
      'iValue InfoSolutions Ltd',
      'M K Info Systems Pvt Ltd',
      'NTT India Pvt Ltd',
      'Dynacons Systems & Solutions Ltd',
      'Deloitte Touche Tohmatsu India LLP',
      'I-source Infosystems Pvt Ltd',
      'Tata Consultancy Services Ltd',
      'Brandserv Technologies Pvt Ltd',
      'SoftwareOne India Pvt Ltd',
      'Arsenal Infosolutions Pvt Ltd',
      'Comnet Solutions Pvt Ltd',
      'DevTools',
      'ACE Tech Sys Pvt Ltd',
      'Quoinx Technologies Pvt Ltd',
      'Sundaram Home Finance Ltd',
      'Subha Technical Services Pvt Ltd',
      'Asia iValue Pte Ltd',
      'Knorr-Bremse Technology Center India Pvt Ltd',
      'Value Point Systems Pvt Ltd',
      'Tata Play Ltd',
      'Sonata Information Technology Ltd',
      'Arete IR LLP',
      'Phalgune Infotech Pvt Ltd',
      'HDFC Bank Ltd',
      'Shunya Technologies Pvt Ltd',
      'Hitachi Systems India Pvt Ltd',
      'Securevel Solutions Pvt Ltd',
      'KLX Cloud IT Pvt Ltd',
      'True Value Info Systems',
      'PCS Solutions',
      'Wipro Ltd',
      'Ericsson India Pvt Ltd',
      '5Sec Cyberpwn Technologies Pvt Ltd',
      'Know-All-Edge Networks Pvt Ltd',
      'Dualsys Techno Llp',
      'Informatics Technologies Pvt Ltd',
      'LDS Infotech Pvt Ltd',
      'Skylark Information Technologies Pvt Ltd',
      'Vibs Infosol Pvt Ltd',
      'Mikroz InfoSecurity Pvt Ltd',
      'HUBCOM TECHNO SYSTEM LLP',
      'V5 techsol India LLP',
      'S G Informatics India Pvt Ltd',
      'Compass IT Solutions and Services Pvt Ltd',
      'IT Solutions India Pvt Ltd',
      '3R Infotech Pvt Ltd',
      'CyberNxt Solutions LLP',
      'Doyen Infosolutions Pvt Ltd',
      'iSecureNet Solutions Pvt Ltd',
      'Binary Global Ltd',
      'LA Technologies Pvt Ltd',
      'Network Intelligence India Pvt Ltd',
      'Shashwat Solutions',
      'Sterlite Technologies Ltd',
      'Tata Digital Pvt Ltd',
      'Ellicium Solutions Pvt Ltd',
      'Wizertech Informatics Pvt Ltd',
      'Intouchworld',
      'Hewlett Packard Enterprise India Pvt Ltd',
      'NEXBASE TECHNOLOGIES',
      'Lauren Information Technologies Pvt',
      'Motherson Technology Services Ltd',
      'Datasoft Network Solutions Pvt Ltd',
      'Netcon Technologies India Pvt Ltd',
      'Targus Technologies Pvt Ltd',
      'Atrity Info Solutions Pvt Ltd',
      'Inspirisys Solutions Ltd',
      'Network Techlab India Pvt Ltd',
      'Wysetek Systems Technologists Pvt Ltd',
      'Yes Bank Ltd',
      'Icons',
      'Team Computers Pvt Ltd',
      'Akshara Enterprises India Pvt Ltd',
      'One97 Communications Ltd',
      'Synoptics Technologies Ltd',
      'Bharti Airtel Services Ltd',
      'Rise Tech Software Pvt Ltd',
      'Infocalix Technologies Pvt Ltd',
      'Wistron Infocomm Manufacturing I Pv (India) Pvt Ltd',
      'Unique Performance Techsoft Pvt Ltd',
      'Tata Technologies Ltd',
      'Esec Forte Technologies Pvt Ltd',
      'Vinca Cybertech Pvt Ltd',
      'Pentagon System and Services Pvt Lt',
      'ProTechmanize Solutions Pvt Ltd',
      'Inspira Enterprise India Ltd',
      'Liveon Biolabs Pvt Ltd',
      'Mayush IT Services Pvt Ltd',
      'Hyper Logic Systems Pvt Ltd',
      'KALYANI STRATEGIC MANAGEMENT Services Ltd',
      'Climate ETC Technology Services Pvt Ltd',
      'Rabita Software',
      'SkyNet Services',
      'Foresight Software Solutions Pvt Ltd',
      'Jemistry Info Solutions LLP',
      'ValuePoint TechSol Pvt Ltd',
      'TimeNet Solutions Pvt Ltd',
      'Infinity9',
      'Mahindra Defence Systems Ltd',
      'Sigma eSolution Pvt Ltd',
      'KPMG Assurance and Consulting Services LLP',
      'ARAVEEN TECHNOLOGIES',
      'Aujas Networks Pvt Ltd',
      'Aujas Cybersecurity Ltd',
      'Jesuit Technologies Pvt Ltd',
      'Manas Merchandise Pvt Ltd',
      'ACPL Systems Pvt Ltd',
      'Orbit Techsol India Pvt Ltd',
      'Larsen & Toubro Ltd',
      'SB Secure Data Centers India Pvt Ltd',
      'Alliance Pro IT Pvt Ltd',
      'EIT Services India Pvt Ltd',
      'Ashtech Infotech India Pvt Ltd',
      'Creative Infotech Solutions Pvt Ltd',
      'ANB Computer Solutions Pvt Ltd',
      'Kotak Securities Ltd',
      'Axis Bank Ltd',
      'Orisenc Technologies Pvt Ltd',
      'Tata Advanced Systems Ltd',
      'ELMACK ENGG SERVICES PVT LTD',
      'PFSI Solutions Pvt Ltd',
      'Silver Leaf Solutions Pvt Ltd',
      'Elite Computers',
      'R Soft Solutions',
      'National Payment Corporation of India',
      'NTT Global Data Centers & Cloud Infrastructure India Pvt Ltd',
      'Softline Services India Pvt Ltd',
      'Quess Corp Ltd',
      'PrimisPro IT Solutions',
      'Larsen & Toubro Infotech Ltd',
      'Auxiliary Digitech',
      'Allied Digital Services Ltd',
      'Data Tech Computers Pvt Ltd',
      'Zones Corporate Solutions Pvt Ltd',
      'AppsTech Solution',
      'Blue Star Engineering & Electronics Ltd',
      'ICVS E Solutions Pvt Ltd',
      'NST Pvt Ltd',
      'Globaltech And Infosec Pvt Ltd',
      'HCL Infosystems Ltd',
      'KC Enterprise',
      'Axis Tech',
      'Onnivation Ventures Pvt Ltd',
      'Cybernx Technologies Pvt Ltd',
      'Brilyant IT Solutions Pvt Ltd',
      'PSR IT Services Pvt Ltd',
      'Sycomp Technologies India Pvt Ltd',
      'Crayon Software Experts India Pvt L',
      'Dhanyaayai Enterprise Pvt Ltd',
      'Bid4Best Technologies Pvt Ltd',
      'Etherbit Pvt Ltd',
      'GTPL BROADBAND PVT LTD',
      'STA Infotech Pvt Ltd',
      'Coforge Ltd',
      'Ritcom Systems And Services',
      'Frontier Business Systems Pvt Ltd',
      'SISA Information Security Pvt Ltd',
      'Third I Information Security Pvt Ltd',
      'Benchmark Computer Solutions Ltd',
      'Creative Communication',
      'GiniMinds Solutions Pvt Ltd',
      'iVIS International Pvt Ltd',
      'Bharti Airtel Ltd',
      'Schneider Electric Systems India Pvt Ltd',
      'Sattrix Information Security Ltd',
      'Esconet Technologies Pvt Ltd',
      'Netlogic Solutions Pvt Ltd',
      'LTI Mindtree Ltd',
      'GREYNIUM INFORMATION Pvt Ltd',
      'Superior Digital Pvt Ltd',
      'Shreeji Network Solutions',
      'Digisec Technologies',
      'Swift IT Solutions',
      'WWT India Pvt Ltd',
      'AKS Information Technology Services Pvt Ltd',
      'ClubHack Labs LLP',
      'Assyst International Pvt Ltd',
      'SBA Info Solutions Pvt Ltd',
      'Mappd Systems Pvt Ltd',
      'Sunfire Technologies Pvt Ltd',
      'Unicom Infotel Pvt Ltd',
      'Alliant Technologies',
      'Vortex Electronics Pvt Ltd',
      'STL Digital Ltd',
      'Progression Infonet Pvt Ltd',
      'DC Infotech &  Communication ltd',
      'Comint Systems and Solutions Pvt Ltd',
      'Eikym Solutions Pvt Ltd',
      'Diamond Infotech Pvt Ltd',
      'Nelito Systems Pvt Ltd',
      'Preflex Solutions Pvt Ltd',
      'AS IT Consulting Pvt Ltd',
      'Xiarch Solutions Pvt Ltd',
      'Sunshine IT Infra Services Pvt Ltd',
      'Adweb Technologies Pvt Ltd',
      'Karnataka Bank Ltd',
      'Fortuneplus IT Net Works Pvt Ltd',
      'Sanskrit E Solutions & Services Pvt Ltd',
      'Hitachi Systems Micro Clinic Pvt Ltd',
      'Techspire Services Pvt Ltd',
      'Genpact India Pvt Ltd',
      'Takyon Networks Pvt Ltd',
      'Rsg Solutions Pvt Ltd',
      'Absolut Info Systems Pvt Ltd',
      'eNinja Technologies Pvt Ltd',
      'Konverge Technologies Pvt Ltd',
      'Bookmark Infotech LLP',
      'TechFlex Solutions Pvt Ltd',
      'Parity InfoTech Solutions Pvt Ltd',
      'Essen Vision Software Pvt Ltd',
      'Wheels India Ltd',
      'Nayara Energy Ltd',
      'Barbeque Nation Hospitality Ltd',
      'DRS IT Consultancy Pvt Ltd',
      'The Cosmos Co-Operative Bank Ltd',
      'Talakunchi Networks Pvt Ltd',
      'Raksha Technologies Pvt Ltd',
      'Uniware Systems Pvt Ltd',
      'Persistent Systems Ltd',
      'Clapback Pvt Ltd',
      'BlueEarth Softwares Pvt Ltd',
      'Star Comnet Pvt Ltd',
      'Acma Computers Ltd',
      'Rubic IT Solutions',
      'Velocis Systems Pvt Ltd',
      'IndusAuto Technologies',
      'IDFC First Bank Ltd',
      'Twenty Two by 7 Solutions Pvt Ltd',
      'Unisol IT Solutions Pvt Ltd',
      'Trueserve Technologies Pvt Ltd',
      'LRS Services Pvt Ltd',
      'Airtel Tchad SA',
      'Airtel Mobile Commerce Tchad (Trust) SARL',
      'AIRTEL CONGO S.A',
      'Airtel Congo S.A - Mobile Money',
      'Airtel RDC S.A',
      'INGRAM MICRO INDIA',
      'Ambisure Technologies Pvt Ltd',
      'AIRTEL MONEY RDC S.A',
      'Airtel Money SA',
      'NEC Corporation India Pvt Ltd​',
      'Airtel Networks Kenya Ltd',
      'Airtel Money Kenya Limited',
      'Airtel Madagascar SA',
      'Airtel Mobile Commerce Madagascar SA',
      'Airtel Malawi Ltd',
      'Airtel Malawi Mobile Commerce Ltd',
      'Celtel Niger S.A',
      'Airtel Money Niger S.A',
      'Airtel Rwanda Mobile Money Trust OU',
      'Airtel Tanzania Limited OU',
      'Airtel Money Tanzania Limited',
      'Airtel Uganda Ltd',
      'Airtel Uganda Airtel Money Trust OU',
      'Airtel Networks Ltd',
      'Airtel Network Zambia PLC',
      'Airtel Mobile Commerce Zambia Ltd',
      'The Saraswat Co-Operative Bank Ltd',
      'Cyborg Network Communication',
      'Questa Software Systems Pvt Ltd',
      'Midland Credit Management India Pvt Ltd',
      'Microsystems',
      'Zytech Infra Solutions Pvt Ltd',
      'Mahindra & Mahindra Financial Services Ltd',
      'Adit Microsys Pvt Ltd',
      'Pentagon System and Services Pvt Ltd',
      'Sapper Software Pvt Ltd',
      'Aspire NXT Pvt Ltd',
      'Ajax Network Solutions Pvt Ltd',
      'Sheeltron Digital Systems Pvt Ltd',
      'Technofirm Solutions LLP',
      'Creative Synergies Consulting India Pvt Ltd',
      'BSE Ltd',
      'Emarson Computers',
      'L&T Technology Services Ltd',
      'Jharkhand Agency For Promotion Of Information Technology',
      'Amber Distributions Pte Ltd',
      'Global Soft Technologies',
      'Seamless Infotech Pvt Ltd',
      'Headway IT Solutions',
      'IBRAHMA INFOSOLUTIONS',
      'Arrow PC Network Pvt Ltd',
      'Tecpact Technologies Pvt Ltd',
      'SISL Infotech Pvt Ltd',
      'Saitronics Systems Pvt Ltd',
      'CMS COMPUTERS LTD',
      'CONNECTIFY TECHNOLOGIES',
      'Network Intelligence Pvt Ltd',
      'Ambika Computer',
      'ITC Ltd',
      'LOGON Software India Pvt Ltd',
      'One Network Consulting Pvt Ltd',
      'Corporate Infotech Pvt Ltd',
      'ITCG Technologies LLP',
      'SK International',
      'B M Infotrade Pvt Ltd',
      'Unizent Technologies Pvt Ltd',
      'Tata Communications International Pte Ltd',
      'Ample Digital Pvt Ltd',
      'Verastar Solutions Pvt Ltd',
      'Biomatiques Identification Solutions Pvt Ltd',
      'Krazybee Services Pvt Ltd',
      'Bay Datacom Solutions Pvt Ltd',
      'Tech Mahindra Ltd',
      'Chahal Computer & Co',
      'Cybosecure Networks Pvt Ltd',
      'KEC International Ltd',
      'Benelec Infotech Pvt Ltd',
      'Inspace Technologies Pvt Ltd',
      'In Solutions Global Ltd',
      'Maplecloud Technologies',
      'Winnovative Solutions Pvt Ltd',
      'Rysun IT Solutions Pvt Ltd',
      'Dynamic Computer Services',
      'TransIndia Technologies',
      'Reliance Jio Infocomm Ltd',
      'Alstonia Consulting LLP',
      'Canara Bank',
      'ACPL Pte Ltd',
      'Synechron Technologies Pvt Ltd',
      'Ishan Infotech Ltd',
      'Amazure Technologies Pvt Ltd',
      'Global Sourcing',
      'Telecommunications Consultants India Ltd',
      'Magic Systems Pvt Ltd',
      'Airtel Networks Kenya Ltd.',
      'Airtel Networks Zambia plc',
      'Airtel Seychells Ltd',
      'MagNetix InfoSystems & Development Pvt Ltd',
      'QuantumShield Technologies LLP',
      'Netflow Technologies India Pvt Ltd',
      'SM Networks & Solutions Pvt Ltd',
      'Cezen Technologies Pvt Ltd',
      'Cyberspace Security Solutions Pvt Ltd',
      'Tvishi Technologies Pvt Ltd',
      'RLogic Technology Services India Pv',
      'Tata Play Broadband Pvt Ltd',
      'Airtel Gabon S.A.',
      'Intec Infonet Pvt Ltd',
      'EASTERN HORIZON',
      'Verse Innovation Pvt Ltd',
      'Johnson Controls India Pvt Ltd',
      'KISETSU SAISON FINANCE',
      'InstaSafe Technologies Pvt Ltd',
      'Wesecure Technologies',
      'Prime Infoserv LLP',
      'Pure Storage International Ltd',
      'Yubico AB',
      'Messung Systems Pvt Ltd',
      'Mantra Softech India Pvt Ltd',
      'HCL Technologies Ltd',
      'Technociate Solutions Pvt Ltd',
      'Indivillage Tech Solutions Llp',
      'GavBit Pvt Ltd',
      'Writer Business Services Pvt Ltd',
      'Birla Management Centre',
      'Rahi Systems Pvt Ltd',
      'Nimzo-I Technologies Pvt Ltd',
      'Airtel International LLP',
      'National Stock Exchange of India Ltd',
      'DiGiElevate Pvt Ltd',
      'Technology Plus Solution',
      'PRECISION PYRAMID PVT LTD',
      'Rizing LLC',
      'Vcom Technologies Pvt Ltd',
      'Kukreja Electronics Solution Pvt Ltd',
      'Gigabit Technologies Pvt Ltd',
      'FiniQe Technologies Pvt Ltd',
      'Orient Technologies Pvt Ltd',
      'Blue Berry e-services Pvt Ltd',
      'Orbit Netsolutions Pvt Ltd',
      'Quizizz Inc',
      'Vectrae Infotech Pvt Ltd',
      'ByteView Technologies Llp',
      'Medi Assist Insurance Tpa Pvt Ltd',
      'Tata Communications Germany Lt',
      'Tata Communications (UK) Ltd',
      'AXENSA TECHNOLOGIES',
      'Desknet Compute India Pvt Ltd',
      'Proactive Data Systems Pvt Ltd',
      'Micrologic Networks Pvt Ltd',
      'Triflo Technologies Pvt Ltd',
      'Anulap Enterprises Pvt Ltd',
      'e-Risk Solutions Pvt Ltd',
      'Airtel Nigeria Networks Ltd',
      'Smartcash Payment Service Bank Ltd',
      'Laya Tech Pvt Ltd',
      'Leon Communication Technologies Pvt Ltd',
      'Varnitech Solution Pvt Ltd',
      'Netplace Technologies Pvt Ltd',
      'Noventiq Services India Pvt Ltd',
      'UD trucks corporation',
      'ESAF SMALL FINANCE BANK',
      'Meta Infotech Pvt Ltd',
      'Vanaps Consulting Pvt Ltd',
      'SafeZone Secure Solutions Pvt Ltd',
      'Fencesense Technologies Llp',
      'ESF Labs Ltd',
      'Emarson Infotech Pvt Ltd',
      'CYRAAC Services Pvt Ltd',
      'TECHNUM OPUS PVT LTD',
      'IT TECNO AMC SOLUTIONS PVT LTD',
      'Us Technology International Pvt Ltd',
      'Hanu Software Solutions India Pvt Ltd',
      'Honeywell Automation India Ltd',
      'ABS India Pvt Ltd',
      'Nexteon  It Solutions Pvt Ltd',
      'Alethe Consulting Pvt Ltd',
      '64 Network Security Pvt Ltd',
      'Covalense Technologies Pvt Ltd',
      'Acuity Knowledge Centre India Pvt L',
      'Vertex Techno Solutions Bangalore Pvt Ltd',
      'Nsv Real Tech India Pvt Ltd',
      'LBR Infosolutions',
      'Acuity Knowledge Services India Pvt',
      'Netflow Technologies Pvt Ltd',
      'Laser Systems Pvt Ltd',
      'Niveshan Technologies India Pvt Ltd',
      'SVS Buildwel Pvt Ltd',
      'Versatile Infosecurity Pvt Ltd',
      'Netrika Consulting India Pvt Ltd',
      'JNR Management Resources Pvt Ltd',
      'Crystal Technologies System Pvt Ltd',
      'Magnum Networks Support Pvt Ltd',
      'Taarak India Pvt Ltd',
      'Techfruits Solutions Pvt Ltd',
      'SBI Funds Management Ltd',
      'Verinsoft',
      'Tim Infratech Pvt Ltd',
      'Aditya Birla Finance Ltd',
      'Epragathi Recycling',
      'FOXTECHNO SOLUTIONS',
      'Galaxy Office Automation Pvt Ltd',
      'IT Care',
      'Multiverse Solutions Pvt Ltd',
      'Rock ladder Technologies Pvt Ltd',
      'HUE Service Pvt Ltd',
      'Techbooks International Pvt Ltd',
      'Cartel InfoSystems Pvt Ltd',
      'Cray It Solutions Pvt Ltd',
      'Aspirify Enterprises Pvt Ltd',
      'Infrabeat Technologies Pvt Ltd',
      'Technobile Systems Pvt Ltd',
      'Sniper Systems & Solutions Pvt Ltd',
      'General Technologies',
      'Business Connect Ad Networks',
      'ESDS Software Solution Ltd',
      'R S Consulting Services',
      'Youdan Tech LLP',
      'The South Indian Bank Ltd',
      'TECHTRENO SOLUTIONS PVT LTD',
      'Amvion Labs Pvt Ltd',
      'Exl Service (Ireland) Ltd',
      'Hathway Cable & Datacom Ltd',
      'Digidata Infosystems Pvt Ltd',
      'Datamatics Global Services Ltd',
      'STI Infotech Pvt Ltd',
      'NSE Clearing Ltd',
      'SARM Innovation Pvt Ltd',
      'Credo Infotech Pvt Ltd',
      'KDDI India Pvt Ltd',
      'Easebuzz Pvt Ltd',
      'RBL Bank Ltd',
      'Techtotalers Pvt Ltd',
      'Mitu Sharma',
      'ENETSOL IT PVT LTD',
      'XANADU REALTY LTD',
      'Dr Lal PathLabs Ltd',
      'Kiosk Technologies Pvt Ltd',
      'ITCG Solutions Pvt Ltd',
      'IntactIT Infosystems Pvt Ltd',
      'Microlink Solutions Pvt Ltd',
      'E2E Networks Ltd',
      'Procain Consulting & Services Pvt Ltd',
      'Ronam Technologies Pvt Ltd',
      'Precision Infomatic M Pvt Ltd',
      'Claptek Pvt Ltd',
      'Kerala Communicators Cable Ltd',
      'Vidyatech Solutions Pvt Ltd',
      'Zerodha Broking Ltd',
      'Invecto Technologies Pvt Ltd',
      'Ralco Synergy Pvt Ltd',
      'Chintech Systems',
      'Grant Thornton Bharat LLP',
      'Nahar Integrated System Services Pvt Ltd',
      'REALSOFT CORPORATION (INDIA)',
      'HCL Technologies Ltd ( AH07 )',
      'Locuz Enterprise Solutions Ltd',
      'Talent Formula Pvt Ltd',
      'S D Fine Chem Ltd',
      'HCL Infotech Ltd',
      'Cyberforce Digital Pvt Ltd',
      'Shri Keshtra Info Technologies',
      'Embee Software Pvt Ltd',
      'Techsa Services Pvt Ltd',
      'Lyncbiz India Pvt Ltd',
      'Icertis India (ISPL & IPIPL)',
      'Nakshatra Infosolutions',
      'Philips India Ltd',
      'Micropoint Computers Pvt Ltd',
      'ANB Solutions Pvt Ltd',
      'MobileComm Technologies India Pvt Ltd',
      'Employees Provident Fund (EPFO)',
      'CTAP Systems Pvt Ltd',
      'Jana Small Finance Bank Ltd',
      'Tecplix Technologies Pvt Ltd',
      'Tata Communications Collaboration Services Pvt Ltd',
      'Syndrome Technologies Pvt Ltd',
      'Unnathi Digital Solutions LLP',
      'ARP TECHNOLOGY',
      'TechCiti Technologies Pvt Ltd',
      'Aurum Software',
      'Plutus Ventures',
      'Mindsnob Consulting Pvt Ltd',
      'Penetolabs Pvt Ltd',
      'Birla Management Centre Services Lt',
      'Convergys India Servies Pvt Ltd',
      'Macsart Technologies Pvt Ltd',
      'Tata Electronics Pvt Ltd',
      'TechInfobyte Solutions Pvt Ltd',
      'Orbit Techsol (W) Pvt Ltd',
      'Pyramid Cyber Security & Forensic Pvt Ltd',
      'Mphasis Ltd',
      'Taashee Linux Services Pvt Ltd',
      'Infosoft Digital Design & Services Pvt Ltd',
      'CSB Bank Ltd',
      'Paytm Payments Bank Ltd',
      'Presto Infosolutions Pvt Ltd',
      'Gujarat Fluorochemicals Ltd',
      'AB Tech',
      'Futurenet Technologies India Pvt Ltd',
      'Durr India Pvt Ltd',
      'AIP India IT Solutions & Services (OPC) Pvt Ltd',
      'Netsentries Infosec Solutions Pvt Ltd',
      'AuthBridge Research Services Pvt Ltd',
      'Chamundi Infotech  Pvt Ltd',
      'Titan Company Ltd',
      'Softlabs Infotech Pvt Ltd',
      'Ecs Infotech Pvt Ltd',
      'Qualcomm India Pvt Ltd',
      'Techsec Digital Global Pvt Ltd',
      'Asian Paints Ltd',
      'PruTech Solutions India Pvt Ltd',
      'Benevolence Technologies Pvt Ltd',
      'Adara IT Solutions',
      'Ace Com Services (OPC) Pvt Ltd',
      'HTH Global Network Pvt Ltd',
      'Technosprout Systems Pvt Ltd',
      'Gupshup Technology India Pvt Ltd',
      'Technosys Security Systems Pvt Ltd',
      'Acceron Infosol Pvt Ltd',
      'Artech Infosystems Pvt Ltd',
      'Sencillatec Solutions Pvt Ltd',
      'ITZ Cash (EPBIX)',
      'Digialert Solutions Pvt Ltd',
      'Inflow Technologies Pvt Ltd',
      'Force Identification Pvt Ltd',
      'Secure Solutions',
      'Ernst & Young LLP',
      'Shezar Web Technologies Pvt Ltd',
      'Sharekhan',
      'Teceze Consultancy Services Pvt Ltd',
      'MWYN Tech Pvt Ltd',
      'HOWELL PROTECTION SYSTEMS INDIA Pvt Ltd',
      'QOS Technology Pvt Ltd',
      'Secureinteli Technologies Pvt Ltd',
      'Matrix Security and Surveillance Pv',
      'Ebix Payment Services Pvt Ltd',
      'Syngene International Ltd',
      'NeoGrowth Credit Pvt Ltd',
      'Andhra Pradesh Mahesh Co-operative Urban Bank Ltd',
      'Insight Business Machines Pvt Ltd',
      'D M Systems Pvt Ltd',
      'Dreamzcraft Infomatics Pvt Ltd',
      'Vsecure Networks',
      'Cymune Cyber Security Services Pvt Ltd',
      'Convergys India Services Pvt Ltd',
      'Planet Infrastructure Management Pvt Ltd',
      'Cibera Defence Pvt Ltd',
      'Webdesk Technologies Pvt Ltd',
      'Printlink Computer and Communicatio Pvt Ltd',
      'Tech Consultant',
      'Maspro Technologies Pvt Ltd',
      'impulseitcs pvt ltd',
      'Teamwin Global Technologica Pvt Ltd',
      'NG Techassurance Pvt Ltd',
      'SEC Communications Pvt Ltd',
      'Intime Solutions',
      'Erasmith Technologies Pvt Ltd',
      'HIM Technology Pvt Ltd',
      'Aragen Life Sciences Ltd',
      'Nikom Infrasolutions Pvt Ltd',
      'Omega Healthcare Management Services Pvt Ltd',
      'Century Computers',
      'Itorizin Technology Solutions Pvt L',
      'Power Bridge Technologies Pvt Ltd',
      'Netcom Infotech Pvt Ltd',
      'NewGen IT Solutions and Services Pt',
      'Pi Datacenters Pvt Ltd',
      'Carbynetech India Pvt Ltd',
      'Hyundai Autoever India Pvt Ltd',
      'Vara Technology Pvt Ltd',
      'IOPS',
      'Netsys Network Pvt Ltd',
      'VSH Technologies',
      'Xploreteq Integrated Solutions India Pvt Ltd',
      'PCS Solutions Pvt Ltd',
      'Jair Network & Services Pvt Ltd',
      'Happiest Minds Technologies Ltd',
      'Techmatrix It Consulting Pvt Ltd',
      'Hue Services Pvt Ltd',
      'InvenTeq Software Services',
      'SNS Technocorp Pvt Ltd',
      'Power Bridge Systems Pvt Ltd',
      'Volksara Techno Solutions Pvt Ltd',
      'Kapstone Technological Services Llp',
      'Aditi Tech Consulting Pvt Ltd',
      'Flipkart Internet Pvt Ltd',
      'BirdRock Consulting',
      'Swajyot Technologies Pvt Ltd',
      'Comtel Infosystems Pvt Ltd',
      'Kiyaan IT Solutions Pvt Ltd',
      'Silicon Technologies Pte Ltd',
      'Concentrix Daksh Services India Pvt Ltd',
      'Jaypee Greens',
      'F5 Techno Solutions Pvt Ltd',
      'AltiSec Technologies Pvt Ltd',
      'GTS Technosoft Pvt Ltd',
      'Adroit Infoways',
      'Coforge Business Process Solutions Pvt Ltd',
      'Tekskills India Pvt Ltd',
      'Searce Cosourcing Services Pvt Ltd',
      'F1 Infotech Pvt Ltd',
      'Proxinet Technologies Pvt Ltd',
      'Finecons Pvt Ltd',
      'Shree Additives Pharma and Foods Pvt Ltd',
      'Planin Innovation And Consultancy Services Pvt Ltd',
      'Rudra Enterprises',
      'Deltaphi Labs Pvt Ltd',
      'Jainam Technologies Pvt Ltd',
      'Lenovo Global Technology (India) Pvt Ltd',
      'Svastika Infotech LLP',
      'Catalyst Business Partners LLC',
      'Bluecom Infotech Pvt Ltd',
      'Meridian IT India Pvt Ltd',
      'Yuvitech Solutions Pvt Ltd',
      'CCS Computers Pvt Ltd',
      'Airowire Networks Pvt Ltd',
      'Accel IT Services',
      'Emerging Techno kart Pvt Ltd',
      'Gati Express & Supply Chain Pvt Ltd',
      'Allcargo Logistics Ltd',
      'Kritech Technologies Pvt Ltd',
      'Prism Global Ltd Hong Kong',
      'Jio Platforms Ltd',
      'Terafence Pvt Ltd',
      'Infovirgin Technology Solutions Pvt',
      'Master Services',
      'Capsave Finance Pvt Ltd',
      'Carrier Media India Pvt Ltd',
      'Midea India Pvt Ltd',
      'Curvewave Technology Pvt Ltd',
      'Loyalty Juggernaut India Pvt Ltd',
      'EXL Service.com (I) Pvt Ltd',
      'Madras Networking Company',
      'CI Infotech Pvt Ltd',
      '3i Infotech Ltd',
      'Netalliance Solutions Pvt Ltd',
      'Hind Defence Equipment Pvt Ltd',
      'Dixit Infotech Services Pvt Ltd',
      'Felix Infotech Pvt Ltd',
      'Teqsys LLP',
      'Bhavy Digital Pvt Ltd',
      'PC Solutions Pvt Ltd',
      'Bulwark Systems',
      'Pragathi computers',
      'Aarna Global Infotech Solutions Pvt Ltd',
      'Infopercept Consulting Pvt Ltd',
      'Infoavana Technologies Pvt Ltd',
      'CerebrumX Labs Pvt Ltd',
      'PricewaterhouseCoopers Pvt Ltd',
      'Tmen Systems Pvt Ltd',
      'Technoware Systems India Pvt Ltd',
      'Innovative Telecom & Softwares Pvt Ltd',
      'Appleshine Appliances & Technologies Pvt Ltd',
      'EnovateIT Integrated Services Pvt Ltd',
      'XCT Solutions Pvt Ltd',
      'Cubix Tech Integration Pvt Ltd',
      'Inniti Network Solutions Llp',
      'Tuxcentrix Consultancy Pvt Ltd',
      'Razorpay Software Pvt Ltd',
      'Indian Overseas Bank',
      'Hero MotoCorp Ltd',
      'HDFC Securities Ltd',
      'ThinkWright Learning Services Pvt Ltd',
      'Momentum IT Services',
      'Bauer Equipment India Pvt Ltd',
      'Equinox Infotech',
      'CtrlS Datacenters Ltd',
      'Evantage IT Consulting Services Pvt',
      'ITKraft Solutions',
      'Business Automation Indore Pvt Ltd',
      'Larsen & Toubro Construction',
      'Flying Trade India Pvt Ltd',
      'Quadgen Wireless Solutions Pvt Ltd',
      'S2 Infotech International Ltd',
      'Zluri Technologies Pvt Ltd',
      'Foundever Crm India Pvt Ltd',
      'Cyberjeet Pvt Ltd',
      'Sree VijayaVittala Computers',
      'Accenture Solutions Pvt Ltd',
      'SecurView Systems Pvt Ltd',
      'Bitscape Infotech Pvt Ltd',
      'Indian Immunologicals Ltd',
      'Technoline Systems & Services',
      'CXIO Technologies Pvt Ltd',
      'Shobha Ltd',
      'Connectivity IT Solutions Pvt Ltd',
      'Miscot Systems Pvt Ltd',
      'Diageo Business Services India Pvt Ltd',
      'Altrozian Consulting Pvt Ltd',
      'Cynorsense Solutions Pvt Ltd',
      'Samite Solutions Pvt Ltd',
      'Fcoos Technologies Pvt Ltd',
      'Zillione Technologies Pvt Ltd',
      'Softcell Technologies Ltd',
      'Kepsure Solutions Pvt Ltd',
      'Mindsprint Digital (India) Pvt Ltd',
      'Hexagon B2B Solutions',
      'Tech Hat Pvt Ltd',
      'Prime Computers',
      'Auriseg Consulting Pvt Ltd',
      'Thumos Tech',
      'Mankha Electrotech Pvt Ltd',
      'Microtech Infoserve Pvt Ltd',
      'Ador Powertron Ltd',
      'Benchmark Computer Solution Ltd',
      'Cybercube Services Pvt Ltd',
      'Bekaert Industries Pvt Ltd',
      'Imperium Solutions',
      'IT Sense',
      'Codec Networks Pvt Ltd',
      'JR Global Consultancy Services Pvt Ltd',
      'Times Internet Ltd',
      'Select Softwares India Pvt Ltd',
      'Sarah Technologies',
      'Tech 4 Logic Pvt Ltd',
      'Infinite Computer Solutions  India Ltd',
      'iOCO Solutions GmbH',
      'Midevops Services Pvt Ltd',
      'Kochar Consultants Pvt Ltd',
      'VFM Systems & Services Pvt Ltd',
      'Techbag Digital Pvt Ltd',
      'Kruti Comp India Pvt Ltd',
      'E Matrix Corp',
      'NV Bekaert SA',
      'Computer Technologies Pvt Ltd',
      'ABT Ltd',
      'Softmart Solutions',
      'SOC Analyst Pvt Ltd',
      'Ramognee Technologies Pvt Ltd',
      'Satyajeet India Enterprises Pvt Ltd',
      'Cybersoft & Softwares Solutions Pvt Ltd',
      'Apvision Technologies',
      'Silicon Comnet Pvt Ltd',
      'CNLABS Test Services Pvt Ltd',
      'Web Werks India Pvt Ltd',
      'Presidio Information Risk Management LLP',
      'CyberAssure Services Pvt Ltd',
      'Caveo Infosystems India Pvt Ltd',
      'Ninesec Integration Pvt Ltd',
      'Indostar Capital finance Ltd',
      'TM Solutech Pvt Ltd',
      'TD Media Network Pvt Ltd',
      'Simple Tree LLP',
      'PVR Systems Pvt Ltd',
      'Sara Infoway ITES India Pvt Ltd',
      'Teg Global Infrastructures Pvt Ltd',
      'NTT Global DC & CI India Pvt Ltd',
      'Fineshift Software Pvt Ltd',
      'JBA INFOSOLUTIONS PVT LTD',
      'Airtel Digital Ltd',
      'Pvh Arvind Fashion Pvt Ltd',
      'Tafe Motors & Tractors Ltd',
      'Tafe Tractors & Farm Equipment Ltd',
      'Persistent Systems, Inc',
      'Cloudstrats Technologies Pvt Ltd',
      'Regent Digitech Pvt Ltd',
      'Sundaram Finance Ltd',
      'CyberI3Secure Consultants LLP',
      'Vetrix Info',
      'Shree Electricals And Engineers India  Pvt Ltd',
      'Expeditors International India Pvt Ltd',
      'DH Healthcare Software Services India Pvt Ltd',
      'Modern IT Infrastructures',
      'Nipun Net Solutions Pvt Ltd',
      'Chemtrols Infotech Pvt Ltd',
      'Quark Media Tech Pvt Ltd',
      'Softwide Security Co Ltd',
      'Adorit IT Services Pvt Ltd',
      'Anything MAC Pvt Ltd',
      'Mobicule Technologies Pvt Ltd',
      'Starnext Innovations Pvt Ltd',
      'Networkcity Innovations Pvt Ltd',
      'Serviceberry Technologies Pvt Ltd',
      'Thoughtsol Infotech Pvt Ltd',
      'Techtronics Global Innovations Pvt Ltd',
      'Eon Networks Pvt Ltd',
      'SN Technology',
      'Kemwell Biopharma Pvt  Ltd',
      'Dev IT Serv Pvt Ltd',
      'Check Point Software Technologies Ltd',
      'Hitachi Systems India Pvt Ltd SINGAPORE',
      'HCL America Inc',
      'Millennium ITESP Pvt Ltd',
      'Merck Serono Middle East FZ Ltd',
      'N-ABLE Pvt Ltd',
      'Colt Technology Services (UK)',
      'SHI Singapore Solutions Pte Ltd',
      'Trafigura Pte Ltd',
      'Teceze Ltd',
      'Redington Distribution Pte Ltd',
      'SoftwareONE Pte Ltd',
      'VFM Systems Hong Kong Ltd',
      'WNS North America Inc',
      'Wipro Limited, Singapore Main',
      'HCL Technologies UK Ltd',
      'Wipro Networks Pte Ltd',
      'Aquion Pty Ltd',
      'Mphasis Ltd',
      'Mobitel Pvt Ltd',
      'VFM Systems Hongkong Ltd',
      'Universal Procurement Systems Pte Ltd',
      'Jifflenow',
      'Mobileum Inc',
      'Dcyber Techlab Pvt Ltd',
      'Symphony EYC India Pvt Ltd',
      'Niometrics Pte Ltd',
      'Radix Cyber Intelligence Pvt Ltd',
      'ZS Associates, Inc',
      'Redington Ltd Singapore Branch',
      'Dhivehi Raajjeyge Gulhun PLC',
      'Hitachi Systems India Pvt Ltd Branch office Singapore',
      'GeoData Tech LLC',
      'Velocis Systems Pvt Ltd (Singapore Branch)',
      'Artech L.L.C.',
      'GlobalLogic India Pvt Ltd',
      'Artech Technology Canada Ltd',
      'Sprinklr Inc',
      'Netzary Infodynamics',
      'Splash Business Intelligence Inc',
      'Orchestra Technology',
      'Concentrix Services US Inc',
      'Flix 11 Pvt Ltd',
      'Geo Data Tech LLC',
      'Orbit Peripherals Pte Ltd',
      'Cyfuture India Pvt Ltd',
      'Black Box Technologies Pte Ltd',
      'Surya Foods',
      'Quest Global Engineering Services Pvt Ltd',
      'SoftwareOne Inc',
      'Perfetti Van Melle ICT B.V.',
      'HCL Axon Solutions',
      'HCL Vietnam Company Ltd',
      'HCL Guatemala',
      'HCL Technologies Philippines I',
      'HCL Singapore Pte Ltd',
      'HCL Technologies Mexico, S DE',
      'HCL Technologies Lanka Pvt Ltd',
      'HCL Technologies Malaysia SDN',
      'HCL (Brazil) Tecnologia da Inf',
      'LRN Corporation',
      'Laurus Labs Ltd',
      'FLAG Atlantic Uk Ltd',
      'Esec Forte Technologies Singapore Pte Ltd',
      'HCL Technologies Sweden AB',
      'CDW Technologies India Pvt Ltd',
      'Adtran Inc',
      'Networld Corporation',
      'A-Networks Pvt Ltd',
      'SentryLabs Pvt Ltd',
      'Bizoneer International LLC',
      'SGS MoÃ§ambique, LDA',
      'SGS MCNet Mocambique, Lda',
      'Eklvya Infotech',
      'Amnex Infotechnologies Pvt Ltd',
      'Crisil Ltd',
      'F5 Techno Solution Pvt Ltd',
      'Lyseis Technologies pvt Ltd',
      'Pioneer Technologies Pvt Ltd',
      'Infinite Computer Solutions (India) Ltd',
      'Beetel Teletech Ltd (Erstwhile Brightstar Telecommunica',
      'Intensity Global Technologies Pvt Ltd',
      'KCIS Info Solutions Pvt Ltd',
      'Enrich Data Services Pvt Ltd',
      'JAM Infosystems Pvt Ltd',
      'Cloudone Systems Pvt Ltd',
      'Technosys Integrated Solutions Pvt Ltd',
      'Novamesh Ltd',
      'Innovirtuz Technologies Pvt Ltd',
      'VSN International Pvt Ltd',
      'Xtelify Ltd Formerly Airtel Digital Ltd',
      'Rk Websoft Technologies Pvt Ltd',
      'Power Centre Pvt Ltd',
      'Bhutan Telecom Ltd',
      'DM System Pvt Ltd',
      'Ahana Systems & Solutions Pvt Ltd',
      'Pyramid IT Solutions Pvt Ltd',
      'Briskinfosec Technology And Consulting Pvt Ltd',
      'Netnxt Network Pvt Ltd',
      'Outsourcepartners International Pvt Ltd',
      'Eventus Techsol Pvt Ltd',
      'Qualys Security TechServices Pvt Lt',
      'Cito Infotech Pvt Ltd',
      'Cruxlytics Pvt Ltd',
      'Central Data Systems Pvt Ltd',
      'Safran Engineering Services India Pvt Ltd',
      'Banihal Technologies LLP',
      'Esoftron technolink pvt Ltd',
      'Neysa Networks Pvt Ltd',
      'Samsung India Electronics Pvt Ltd',
      'ITC Ltd FBD- Division',
      'CLOUDFENCE TECHNOLOGIES (OPC) Pvt Ltd',
      'Arcelormittal Nippon Steel India Ltd',
      'Huntmetrics Pvt Ltd',
      'Zero Dark 24 CySec LLP',
      'Whiz Works',
      'Innovaccer Analytics Pvt Ltd',
      'One Kosmos Marketing services Pvt Ltd',
      'Nopal Support Services Pvt Ltd',
      'Agmatel India Pvt Ltd',
      'Yalamanchili Software Exports Pvt Ltd',
      'Serv Cloud Business Solutions Llp',
      'Zoho Corporation Pvt Ltd',
      'Lindner India Construction Pvt Ltd',
      'Rent Alpha Pvt Ltd',
      'Webhelp India Pvt Ltd',
      'Ramkrishna Forgings Ltd',
      'Chavans Business Ventures Pvt Ltd',
      'cloud Dfn LLP',
      'Computer Care',
      'TVS Motor Company Ltd',
      'Unified Data Tech Solutions Pvt Ltd',
      'Mentor Systems',
      'Sparksupport Infotech Pvt Ltd',
      'Knewtech Vision',
      'Macaws Infotech',
      'CitiusCloud Service LLP',
      'Sundaram Infotech Solutions',
      'Aster Networks Pvt Ltd',
      'Smart Chip Pvt Ltd',
      'Denwo Enterprises',
      'Inospire Softwares',
      'Techsol',
      'Silicosys Technologies India Pvt Ltd',
      'Xtreme ICT Pvt Ltd',
      'Axis Computech And Peripherals Pvt Ltd',
      'Kerala State Electronics Development Corporation Ltd',
      'Avadhesh India Advisory Services Llp',
      'Induslnd Bank Ltd',
      'Evoke Technologies Pvt Ltd',
      'Orient Technologies Ltd',
      'Etek International India Pvt Ltd',
      'Eagle Techsec Communications India Pvt Ltd',
      'Vda Infosolutions Pvt Ltd',
      'FPS Innovation Labs Pvt Ltd',
      'Idnor Technologies Pvt Ltd',
      'Ankit Infosys',
      'Crayon Software Experts India Pvt Ltd',
      'SPUDWEB',
      'Shaurya Technosoft Pvt Ltd',
      'Concentrix Daksh India Services Pvt Ltd',
      'Vnextgen It Solutions Pvt Ltd',
      'Future Businesstech India Pvt Ltd',
      'Chronus Software (India) Pvt Ltd',
      'Saffron Networks Pvt Ltd',
      'Prudentbit',
      'Conquer Technologies',
      'Kavayahcloud Pvt Ltd',
      'Ninth Dimension IT Solutions Pvt Ltd',
      'Gnr Solutions Pvt Ltd',
      'Mashreq Bank PSC',
      'Kutch Copper Ltd',
      'Phalgune Infotech',
      'Cherrylabs Technology Pvt Ltd',
      'Mswipe Technologies Pvt Ltd',
      'Wistron InfoComm Manufacturing (India) Pvt Ltd',
      'Prasoft IT Service Pvt Ltd',
      'Mobile Commerce Congo S.A',
      'Cyberleap India Pvt Ltd',
      'Department of Rural Development',
      'Infosys BPM Ltd',
      'Persistent Systems Ltd United State',
      'E and E Enterprises',
      'Newel Infotech Pvt Ltd',
      'AS Information Technology Pvt Ltd',
      'G-Info Technology Solutions Pvt Ltd',
      'E Square System & Technologies Pvt Ltd',
      'Bloo Systems Inc',
      'ACS INFRA SOLUTIONS',
      'Vodafone Idea Ltd',
      'Cineweb Technologies Pvt Ltd',
      'Inmac Computers Pvt Ltd',
      'RSV Enterprises',
      'Netromics Engineering Solutions Pvt Ltd',
      'Gowra Bits & Bytes Pvt Ltd',
      'Unisoft Technologies',
      'Unitecore Pvt Ltd',
      'Rox Hi-Tech Ltd',
      'Royalx',
      'Smartavya Analytica Pvt Ltd',
      'Shakta Technologies Pvt Ltd',
      'Telco IT Infrastructure Solutions',
      'Xtranet Technologies Pvt Ltd',
      'Integrated Tech9labs Pvt Ltd',
      'R-logic Technology Services india Pvt Ltd',
      'Fencesense Technologies Pvt Ltd',
      'Manokamana Business Solutions Pvt Ltd',
      'Vihan Informatics pvt Ltd',
      'Hughes Systique Pvt Ltd',
      'SeconCloud IT Services Pvt Ltd',
      'Printlink Computer and Communication Pvt Ltd',
      'Firstsource Solutions Ltd',
      'Ararat Technologies',
      'Infinite Technologies',
      'Krutrim SI Designs Pvt Ltd',
      'One Kosmos Inc',
      'Cybervad Technologies Pvt Ltd',
      'Rapipay Fintech Pvt Ltd',
      'Cloud Tech',
      'Tucuxi Global Solutions Pvt Ltd',
      'Computer Generated Solutions India Pvt Ltd',
      'RPS Consulting Pvt Ltd',
      'Computer Age Management Services Ltd',
      'F9 Infotech It Solutions Pvt Ltd',
      'Infobahn Technical Solutions India Pvt Ltd',
      'Arete IR LLP-Claims',
      'ICICI Bank Ltd',
      'C-Edge Technologies Ltd',
      'Cyberintelsys Consulting Services Pvt  Ltd',
      'SRC Cyber Solutions LLP',
      'Indian Security & Fire Safety',
      'Quadrasystems.net India Pvt Ltd',
      'New Era Informatique Pvt Ltd',
      'WE Excel Softwares Pvt Ltd',
      'Precision Techserve Pvt Ltd',
      'Alitso India IT Consulting Pvt Ltd',
      'Mouri Tech Ltd',
      'S Cube Storage System Pvt Ltd',
      'Sutraa Technosoft Pvt Ltd',
      'J M Overseas India Pvt Ltd',
      'Imegh Pvt Ltd',
      'CoRover Pvt Ltd',
      'Artem Healthtech Pvt Ltd',
      'Binary Corporation',
      'Quantaco IT India Pvt Ltd',
      'Access Data Systems Pvt Ltd',
      'MV Business Solutions Pvt Ltd',
      'Mogthopia Giganthis',
      'StarTele Tech Pvt Ltd',
      'Ampcus Cyber India Pvt Ltd',
      'ITTREKKER',
      'Ridham Enterprise Pvt Ltd',
      'Pelorus Technologies Pvt Ltd',
      'Rain Industries Ltd',
      'Silicon Business Solutions Pvt Ltd',
      'Burns & McDonnell Engineering India Pvt Ltd',
      'Beetel Teletech Ltd',
      'Phigrid Consulting Pvt Ltd',
      'Devansys Techsol Pvt Ltd',
      'Artek Enterprises Pvt Ltd',
      'Anand Rathi Global Finance Ltd',
      'D2I Automation Pvt Ltd',
      'Anand Rathi Share & Stock Brokers Ltd',
      'Anand Rathi IT Pvt Ltd',
      'Anand Rathi Financial Services Ltd',
      'Anand Rathi International Ventures (IFSC) Pvt Ltd',
      'Anand Rathi Wealth Ltd',
      'Anand Rathi Advisors Ltd',
      'Anand Rathi Insurance Brokers Ltd',
      'AR Digital Wealth Pvt Ltd',
      'Freedom Intermediary Infrastructure Pvt Ltd',
      'LXME Money Pvt Ltd',
      'Gebbs Healthcare Solutions Pvt Ltd',
      'HFCL Ltd',
      'Meridian Infotech Ltd',
      'The Future Technology',
      'Stawerk Solutions Pvt Ltd',
      'DXC Technology India Pvt Ltd',
      'Icertis Solutions Pvt Ltd',
      'BPO Integra India Pvt Ltd',
      'Roman Networks Pvt Ltd',
      'Technopoint',
      'Synaptics India Pvt Ltd',
      'Anjanee It services Pvt Ltd',
      'MM9 Information Technologies Pvt Lt',
      'Geodatatek India Pvt Ltd',
      'Techdefence Labs Solutions Ltd',
      'Varnitech Solution',
      'E-Soft Online',
      'Accretive Technologies Pvt Ltd',
      'Peritas IT Solutions Pvt Ltd',
      'Intech Infotech',
      'Freshbus Pvt Ltd',
      'Meta Infotech Ltd',
      'Taco Punch Powertrain Pvt Ltd',
      'Neural Networks Pvt Ltd',
      'Paradigm IT Technologies Pvt Ltd',
      'Locuz Enterprise Solutions Pvt Ltd',
      'CorpAcademia iTechnovations Pvt Ltd',
      'Birla Management Centre Services Ltd',
      'Online Micro Services Pvt Ltd',
      'Ab Cartridge Hyderabad',
      'Infosprint Technologies Pvt Ltd',
      'Angel Broadcasting Network Pvt Ltd',
      'Techpoint Solutions Pvt Ltd',
      'AltF9 Technology Solutions Pvt Ltd',
      'Techowl Infosec Pvt Ltd',
      'Lapsys Infotech Pvt Ltd',
      'Citius Communications Pvt Ltd',
      'Cloud4C Services Pvt Ltd',
      'NXT SKILLS',
      'Nexsus Cyber Solutions (OPC) Pvt Ltd',
      'The Federal Bank Ltd',
      'Comptek Technology Pvt Ltd',
      'Airtel Congo (Rdc) S.A',
      'Airtel Tanzania PLC',
      'S P Sysnet Pvt Ltd',
      'Platinum Peripherals',
      'Elshaddai Network Solutions',
      'BY Technology',
      'Bharat Fritz Werner Ltd',
      'Newwave Computing Pvt Ltd',
      'Accenture Solutions Pvt Ltd IDB',
      'Dupointe Technologies Pvt Ltd',
      'Eterno Infotech Pvt Ltd',
      'Nepho Ambassadors Technology Pvt Ltd',
      'Verinsoft Pvt Ltd',
      'Lenity Health India Pvt Ltd',
      'Ecaps Computers India Pvt Ltd',
      'Digicat Technologies',
      'Nirugenix Technologies',
      'Ajsoft Computers Pvt Ltd',
      'Indemnity Technologies',
      'OnusWorks Software India Pvt Ltd',
      'Silver Touch Technologies Ltd',
      'Royal Sundaram General Insurance Company Ltd',
      'GitHub, Inc',
      'Healtech Software India Pvt Ltd',
      'Winnovation Education Services Pvt Ltd',
      'Travionyx Technologies Pvt Ltd',
      'Carrier Midea India Pvt Ltd',
      'Net Access India Ltd',
      'WINGS',
      'NMDC Data Centre Pvt Ltd',
      'Takyon Networks Ltd',
      'Vidhathri Techno Systems',
      'Techme Technologies Pte Ltd',
      'Yashicaa Technology',
      'Reliance Industries Ltd',
      'B T Infosys Pvt Ltd',
      'Epta Layers Networks Pvt Ltd',
      'Konverge Technologies Pvt Ltd Bangalore',
      'Baret Managed Services Pvt Ltd',
      'Eorbitor Technologies Pvt Ltd',
      'Akamai Technologies Solutions (India) Pvt Ltd',
      'Optimistic Technology Solutions Pvt Ltd',
      'Marushika Technology Advisors Ltd',
      'Translab Technologies Pvt Ltd',
      'Essway Cyber Security Solutions Pvt Ltd',
      'Cytrusst Intelligence Pvt Ltd',
      'Onpoint Technologies',
      'Icons Futuretech Pvt Ltd',
      'Team1 Consulting Pvt Ltd',
      'Data Cipher Solutions Pvt Ltd',
      'RepliSoft Technologies Pvt Ltd',
      'PCS TechSol',
      'Techpool Consultancy Services Pvt Ltd',
      'Rajiv Gandhi Cancer Institute & Research Centre',
      'Oritso Pvt Ltd',
      'Tevel Technologies Pvt Ltd',
      'Aerial Telecom Solutions Pvt Ltd',
      'Hexatech eSecurity Solutions Pvt Ltd',
      'KDP Technologies Pvt Ltd',
      'Tata Business Excellence Group',
      'HSO India Pvt Ltd',
      'Gruve Technologies (India) Pvt Ltd',
      'Algoritham Infrastructure Pvt Ltd',
      'Steel Strips Wheels Ltd',
      '3s Data Migration Services Pvt Ltd',
      'Techvistar IT Solutions Pvt Ltd',
      'Fusionmindit technologies india Pvt Ltd',
      'Grand Ortus Solutions Pvt Ltd',
      'Primus Partners Pvt Ltd',
      'Takyon Networks',
      'San Datrans Pvt Ltd',
      'Alldigi Tech Ltd',
      'Muthoot Finance Ltd',
      'NMDC Data Centre Pvt Ltd SEZ-UNIT',
      'Spectra Star Inc',
      'Sysware Infotech Pvt Ltd',
      'Techigent Technologies Pvt Ltd',
      'Tinycrows Pvt Ltd',
      'Ascom Infotech Pvt Ltd',
      'Asia Pacific Systems',
      'Darwin Digitech Pvt Ltd',
      'AIMXD Platforms Pvt Ltd',
      'Sequelstring AI Pvt Ltd',
      'Dataevolve Solutions Pvt Ltd',
      'Network Techlab (India) Ltd',
      'Stackup Technology Solutions Pvt Ltd',
      'Cybergrid Solutions India Pvt Ltd',
      'Cidermatics Pvt Ltd',
      'Leon Technologies Integrations Pvt Ltd',
      'National Informatics Unit NIU',
      'Connexions',
      'Swastik Communications',
      'SRSG Broadcast India Pvt Ltd',
      'Tractors and Farm Equipment Ltd',
      'Gujarat Fluorochemical Ltd',
      'MBM Newtech Pvt Ltd',
      'Adviacent Consulting Services Pvt Ltd',
      'Splunk Services Singapore Pte Ltd',
      'Corecard Software India Pvt Ltd',
      'BAPS Swaminarayan Sanstha',
      'Anandit Infotech India Pvt Ltd',
      'CD Technotex LLP',
      'Consolidated Techwere Pvt Ltd',
      'Netzine Systems',
      'Data Security Council of India',
      'Kinsfolk Technology Pvt Ltd',
      'Aanya Infotech',
      'White Oak Investment Management Pvt Ltd',
      'FortRise Business Solutions Pvt Ltd',
      'Syndrome Newedge Pvt Ltd',
      'Equitas Small Finance Bank Ltd',
      'Network Techlab (Singapore) Pte Ltd',
      'V S Information Systems Pvt Ltd',
      'OAK Integrated Systems Pvt Ltd',
      'VST ECS Philippines Inc',
      'Tata Technologies Pte Ltd',
      'Acsys Networks Pvt Ltd',
      'Ebony Holdings Pvt Ltd',
      'National Pen Co LLC',
      'Mazars Advisory LLP',
      'Skylark Information Technologies Pte Ltd',
      'Quantei Australia Pty Ltd',
      'CBC Tech Solutions Ltd',
      'Cargills Bank PLC',
      'Alphasonic Technologies (Pvt) Ltd',
      'iDream Technologies Pvt Ltd',
      'David Pieris Holdings Pvt Ltd',
      'Dristi Tech Pvt Ltd',
      'Quoinx Technologies Pte Ltd',
      'Tata Electronics Systems Solutions Pvt Ltd',
      'Cypher Technology Pvt Ltd',
      'Yantra Solution Pvt Ltd',
      'Vallibel Finance Plc',
      'Millennium ITESP Singapore Pte Ltd',
      'CRES Pte Ltd',
      'Trends and Technologies Inc',
      'Council of the Combatants of National Liberation',
      'Ncinga Pvt Ltd',
      'ARC ONE Pvt Ltd',
      'MsourcE India Pvt Ltd',
      'Metropolitan Technologies Pvt Ltd',
      'VS One World Pvt Ltd',
      'Keysight Technologies Singapore (Sales) Pte Ltd',
      'Advanced IT Solutions',
      'Adapt Information Technologies Pvt Ltd',
      'Mavenir Systems Inc',
      'Infosys Automotive and Mobility GmbH and Co KG',
      'Micronet lnformation System Pvt Ltd',
      'Grantha Networks Pvt Ltd',
      'Dynatech International Pvt Ltd',
      'Lanka Communication Services Pvt Ltd',
      'Infosys Technologies Ltd',
      'Services Tech Experience Inovacao E Tecnologia Em Relacionamento Ltda',
      'Wipro HR Services India Pvt Ltd',
      'Government Technology (GovTech) Agency',
      'Planet Resource and Ventures Pte Ltd',
      'Yantrik Prabidhi Pvt Ltd',
      'Cloud Tech Solutions Pvt Ltd',
      'Infosys Automotive and Mobility GmbH and Co.KG',
      'Gunship Technologies LLC',
      'Appolo Computers Pvt Ltd',
      'inMorphis Services Pvt Ltd',
      'MM9 Information Technologies Pvt Ltd',
      'Registrar General and Census commissioner',
      'Inspire I Tech Services Pvt Ltd',
      'IGT Solution Pvt Ltd',
      'Inmasa Technamic Solution Pvt Ltd',
      'Spontak Supplies Pvt Ltd',
      'Sanbay Networks Pvt Ltd',
      'Cloud4C Services FZ-LLC',
      'Sedin Technologies Pvt Ltd',
      'Trigem Infosolutions Ltd',
      'Arya Infotech Network Solution Pvt Ltd',
      'Gah It Services Opc Pvt Ltd',
      'As Acuity Infozone It Services LLP',
      'Dynamic Computer Marketing Enterpri Pvt Ltd',
      'Technology4you LLP',
      'Excellex Technologies Pvt Ltd',
      'Login Infotech Pvt Ltd',
      'Trade and Technology Pvt Ltd',
      'Idea Lake Information Technologies Pvt Ltd',
      'Sane Green Informatic Pvt Ltd',
      'Odessa Solutions Pvt Ltd',
      'Genpact India Ltd',
      'Saggu Engineers',
      'Sykes Business Services Of India Pvt Ltd',
      'Vinnytech Infras',
      'Micro Hard IT Solutions Pvt Ltd',
      'BT Japan Corporation',
      'Syntel Telecom Ltd',
      'Tecogis',
      'KGreen Consulting & Technologies Pv  Ltd',
      'Computer Exchange Pvt Ltd',
      'Alliance Tech Solution Pvt Ltd',
      'Sapience Analytics Pvt Ltd',
      'Alchemy Solutions',
      'SRN Technologies',
      'Coforge Smart Serve Ltd',
      'CMS IT Services Pvt Ltd',
      'Blue Lotus Technologies Pvt Ltd',
      'Sanghavi Beauty and Technologies Pvt Ltd',
      'Realto Solutions LLP',
      'Net Link Information Technology Pvt Ltd',
      'Smart Sotware Testing Solutions Ind Pvt Ltd',
      'Max International',
      'Auriga Pvt Ltd',
      'Optimum Contracts Pvt Ltd',
      'Vintech Electronic Systems Pvt Ltd',
      'Artech Information Systems',
      'Hosting Infrastructure Service And Solutions Pvt Ltd',
      'CloudAce Technologies',
      'Triangular Infosolutions Pvt Ltd',
      'Amtrak Technologies',
      'Online PSB Loans Ltd',
      'Subex Digital LLP',
      'CSS Corp Pvt Ltd',
      'Black Box Ltd',
      'Coredge.io India Pvt Ltd',
      'Dehradun Enet Solutions Pvt Ltd',
      'Marcellus Infotech Pvt Ltd',
      'Unique Solutions',
      'RV Forms & Gears LLP',
      'Amdocs Development Centre India LLP',
      'Fourth Dimension Technologies Pvt Ltd',
      'Logic E Engineer Pvt Ltd',
      'Cache Technologies',
      'Yotta Infrastructure Solutions Ltd',
      'Indiaitshop.com',
      'Lyseis Technologies',
      'Highradius Coorporation',
      'Aman Technologies',
      'Sharekhan Ltd',
      'Xceedance Consulting India Pvt Ltd',
      'CSB Data Consulting Pvt Ltd',
      'Sitel India Pvt Ltd',
      'Iris Computers Ltd',
      'LearningMate Solutions Pvt Ltd',
      'State Bank Of India',
      'Mphasis Corporation USA',
      'Esquare System & Technologies Pvt L',
      'Juspay Techonologies Pvt Ltd',
      'Smartnet Infotech & Services Pvt Lt',
      'Comparex India Pvt Ltd',
      'ProcessIT Global Pvt Ltd',
      'Hind Merchandise (OPC) Pvt Ltd',
      'A D N Fire Safety Pvt Ltd',
      'Escalates Tech India Pvt Ltd',
      'Renovision Automation Services Pvt Ltd',
      'Smartous Consulting Services Pvt Ltd',
      'Megahertz Infotech Pvt Ltd',
      'Sarala Agencies',
      'Nilvin Technologies Pvt Ltd',
      'Hinduja Leyland Finance Ltd',
      'VWR Lab Products Pvt Ltd',
      'Collabera Technologies Pvt Ltd',
      'Hewlett Packard Financial Services India Pvt Ltd',
      'Arris Group India Pvt Ltd',
      'Hinduja Housing Finance Ltd',
      'Intellect Design Arena Ltd',
      'Tecnimont Pvt Ltd',
      'Truecom Networks Pvt Ltd',
      'EDUPEDIA TECHNOLOGIES',
      'Innovative Techhub Pvt Ltd',
      'Alackrity Consols Pvt Ltd',
      'QCS Communication Technologies Pvt Ltd',
      'Cache Peripherals Pvt Ltd',
      'MDP Infra India Pvt Ltd',
      'Medi Assist Healthcare Services Ltd',
      'Movate Technologies Pvt Ltd',
      'Midevops Services  Pvt Ltd',
      'Solicon Pvt Ltd',
      'Grey Token',
      'Permit Deny Ltd',
      'Intellicus Technologies Pvt Ltd',
      'FOURTH DIMENSION SOLUTIONS LTD',
      'Employees Provident Fund Organization (EPFO)',
      'Wipro Limited',
      'Upmove Capital Pvt Ltd',
      'Bank of Baroda',
      'Rahi Systems Inc',
      'Vitage Systems Pvt Ltd',
      'ROX Trading & Systems Pvt Ltd',
      'Dishana Enterprises',
      'Qnomix Technologies',
      'Mieux Technologies Pvt Ltd',
      'Turbosmart Televentures Pvt Ltd',
      'Microland Ltd',
      'XSAT India Services Pvt Ltd',
      'RI Networks Pvt Ltd',
      'Airtel Tanzania Ltd',
      'Kalyx Infotech Pvt Ltd',
      'IBM Growth Markets LLC',
      'Acctura Technologies Pvt Ltd',
      'HIM TECHNOLOGY  DISTRIBUTION',
      'Allot System Integration Pvt Ltd',
      'Prastanam Computing Services',
      'Novac Technology Solutions Pvt Ltd',
      'Blore Technologies Pvt Ltd',
      'Eorbitor Techonologies Pvt Ltd',
      'CodeMax IT Solutions Pvt Ltd',
      'Analog 2 Digital Pvt Lt',
      'Saponyx Technologies Pvt Ltd',
      'Capgemini Technology Services India',
      'Sathvika Solutions',
      'Emicron Techsolutions Pvt Ltd',
      'ASPL Info Services Pvt Ltd',
      'Mould Training And Networks India Pvt Ltd',
      'Signzy Technologies Pvt Ltd',
      'Silvertouch Technologies Ltd',
      'Quadsel Systems Pvt Ltd',
      'Allience Technologies',
      'Smartsoft',
      'Starmax Computers India',
      'UBX Cloud Pvt Ltd',
      'Convergent Wireless Communications  Pvt Ltd',
      'IT Hub',
      'Amsys Infocom Pvt Ltd',
      'Tatvik System Solutions Pvt Ltd',
      'Esaf Small Finance Bank Ltd',
      'SmarTek21 Pvt Ltd',
      'Dualsys Tech Pvt Ltd',
      'BT Americas Inc',
      'PTC Software India Pvt Ltd',
      'Emad Kamaria CO',
      'Coinfinitive Solutions Pvt Ltd',
      'Infosys Poland sp z o o',
      'Infosys BPM Ltd Costa Rica',
      'Infosys McCamish systems LLC',
      'Infosys Czech Republic Ltd S.R.O',
      'Digital Risk LLC',
      'Fred Intelligence Ltd',
      'Adtran GmbH',
      'BMW AG',
      'Techknowlogic Consultants India Pvt Ltd',
      'NHQ Distributions Pvt Ltd',
      'Global Brand Pvt Ltd',
      'Zillione Business Solutions (Pvt) L',
      'J P Electronics PTE LTD',
      'SoftwareONE UK Ltd',
      'SoftwareONE Deutschland GmbH',
      'JQ Network Pte Ltd',
      'Omega Exim Ltd',
      'Divya Technologies Pvt Ltd',
      'SoftwareONE Australia Pty Ltd',
      'Perfetti Van Melle ICT B.V',
      'Kennametal Inc',
      'AIROWIRE NETWORKS PTE LTD',
      'Tech Mahindra ICT Services',
      'The Copy Cat Ltd'
      ];

  const regionOptions = extractedValues.regions.length > 0 
    ? extractedValues.regions 
    : ['North', 'South', 'West', 'HO', 'KNY'];

  const verticalAccountOptions = extractedValues.verticalAccounts.length > 0 
    ? extractedValues.verticalAccounts 
    : ['BFSI', 'Enterprises', 'Government', 'PSU-Gov', 'Regional Commercial'];

  const channelOptions = extractedValues.channels.length > 0 
    ? extractedValues.channels 
    : ['Tier-1', 'Tier-2', 'Tier-3', 'GCC', 'Direct'];

  const businessHeadOptions = extractedValues.businessHeads.length > 0 
    ? extractedValues.businessHeads 
    : ['Brijesh Shrivastava', 'Sunil Kumar Pillai', 'Sushant Ranshur'];

  const businessManagerOptions = extractedValues.businessManagers.length > 0 
    ? extractedValues.businessManagers 
    : [
        'Mohit Bohra', 'Ankit Pandey'
      ];

  const groupBusinessManagerOptions = extractedValues.groupBusinessManagers.length > 0 
    ? extractedValues.groupBusinessManagers 
    : [
        'Saurabh Kumar', 'Ankit Pandey'
      ];

  const channelHeadOptions = extractedValues.channelHeads.length > 0 
    ? extractedValues.channelHeads 
    : ['Jitender Sharma', 'Sathyanarayana H S', 'Lalit S Sudrik'];

  const groupChannelChampOptions = extractedValues.groupChannelChamps.length > 0 
    ? extractedValues.groupChannelChamps 
    : ['Jitender Sharma', 'Calvin Samuel'];

  const endCustomerOptions = extractedValues.endCustomers.length > 0 
    ? extractedValues.endCustomers 
    : [
      'Rattan India Group',
      'Ppap Automotive Ltd',
      'Komatsu India Pvt Ltd',
      'Indian Navy',
      'Airport Authority of India',
      'Pine Labs Pvt Ltd',
      'Colt Technologies Services India Pvt Ltd',
      'Indian Space Research Organisation',
      'Infosys Ltd',
      'Indian Railway Catering and Tourism Corporation Ltd',
      'Door Sanchar Systems',
      'Srei Infrastructure Finance Ltd',
      'Centre for Development of Telematics',
      'Cliantha Research Ltd',
      'Hitachi Vantara India Pvt Ltd',
      'Union Bank Of India',
      'Tata Communications Ltd',
      'Bharti Airtel Ltd',
      'Lakshmi Machine Works Ltd',
      'Karnataka Municipal Data Society',
      'Gujarat Mineral Development Corporate ltd',
      'Lyra Network Pvt Ltd',
      'Asian Institute Of Gastroenterology Pvt Ltd',
      'Muthoot Finance Ltd',
      'Computer Age Management Services Ltd',
      'Emudhra Ltd',
      'CtrlS Datacenters Ltd',
      'Integrated Technology Enabled Citizen Centric Services',
      'Centre for Development of Advanced Computing',
      'NK Securities Reserach Pvt Ltd',
      'Havells India Ltd',
      'CreditAccess Grameen Ltd',
      'Biesse india pvt Ltd',
      'Indian Institute of Technology',
      'City Union Bank Ltd',
      'Uttarakhand Police',
      'Sree Chitra Tirunal Institute for Medical Sciences & Technology',
      'iValue InfoSolutions Ltd',
      'Parliament House',
      'Central Bank of India',
      'UCO Bank',
      'Gujarat Narmada Valley Fertilizers & Chemicals Ltd',
      'Defence Research & Development Organization',
      'Air Works India Engineering Pvt Ltd',
      'Ministry Of Finance Central Board of Direct Taxes',
      'National High Speed Rail Corporation  Ltd',
      'Philips Electronics India Ltd',
      'Punjab National Bank',
      'Hitachi Payment Services Pvt Ltd',
      'Mercedes Benz Research And Development India Pvt Ltd',
      'Diageo Business Services India Pvt Ltd',
      'National Commodity & Derivatives Exchange Ltd',
      'Sundaram Home Finance Ltd',
      'Indian Navy Ministry of Defense',
      'Sify Digital Services Ltd',
      'LOLC Holdings PLC',
      'Knorr-Bremse Technology Center India Pvt Ltd',
      'HP PPS India Operations Ltd',
      'Hewlett Packard India Software Operation Pvt Ltd',
      'Binary Fountain Solutions India Pvt Ltd',
      'Optum Global Solutions India Pvt Ltd',
      'Tata Play Ltd',
      'Virtusa Consulting Services Pvt Ltd',
      'The India Cements Ltd',
      'KPR Mill Ltd',
      'HDFC Bank Ltd',
      'Indian Health Organisation Pvt Ltd',
      'YKK India Pvt Ltd',
      'Relaxo Footwear Ltd',
      'Rama Prasad Sanjiv Goenka Group',
      'IFFCO Tokio General Insurance Co Ltd',
      'KLX Cloud IT Pvt Ltd',
      'VMware Software India Pvt Ltd',
      'SRF Ltd',
      'Axtria India Pvt Ltd',
      'Agriculture Insurance Company of India Ltd',
      'Tafe Motors And Tractors Ltd',
      'Ushur Inc',
      'Sentinet Intelligence',
      'Bombay Stock Exchange Ltd',
      'Loylty Rewardz Mngt Pvt Ltd',
      'Tata Motors Ltd',
      'HRPL Restaurants Pvt Ltd',
      'Fullerton India Credit Company Ltd',
      'Nearby Technologies Pvt Ltd',
      'The Clearing Corporation of India Ltd',
      'Multi Commodity Exchange Of India Ltd',
      'Minda Corporation Ltd',
      'PNB Housing Finance Ltd',
      'IMI Mobile Pvt Ltd',
      'Hinduja Global Solutions Ltd',
      'V-Guard Industries Ltd',
      'Tata Consumer Products Ltd',
      'Ministry of Finance',
      'Acuity Knowledge Partners',
      'MMRDA',
      'HighRadius Corporation',
      'ZEE Entertainment Enterprises Ltd',
      'TVS Motor Company Ltd',
      'Himalaya Drug Company Pvt Ltd',
      'Jk Cement',
      'Cognizant Technology Solutions India Pvt Ltd',
      'Hero Corporate Pvt Ltd',
      'Goods and Service Tax Network',
      'Central Board of Excise & Customs',
      'MUFG Bank Ltd',
      'The British  School',
      'Gulf Oil Lubricants India Ltd',
      'BSE Ltd',
      'Nayara Energy Ltd',
      'Indoco Remedies Ltd',
      'Religare Broking  Ltd',
      'Angel Broking Ltd',
      'Network Intelligence India Pvt Ltd',
      'TDS Lithium-Ion Battery Gujarat Private',
      'L&T Technology Services Ltd',
      'Kirtane & Pandit LLP',
      'Larsen & Toubro Ltd',
      'Ogilvy and Mather Pvt Ltd',
      'Sterlite Technologies Ltd',
      'Tata Digital Pvt Ltd',
      'Godrej Industreis Ltd',
      'CRIF High Mark Credit Information Services Pvt Ltd',
      'Garden Reach Shipbuilders & Engineers Ltd',
      'KPMG Assurance and Consulting Services LLP',
      'Unique Identification Authority Of India',
      'NMS Works Software Pvt Ltd',
      'Lupin Ltd',
      'Honeywell Technology Solutions Lab Pvt Ltd',
      'TVM Signalling and Transporation Systems Pvt Ltd',
      'Milan Laboratories India Pvt Ltd',
      'Medi Assist Healthcare Services Ltd',
      'Bureau Veritas Consumer Product Services India Pvt Ltd',
      'Siemens Technology and Services Pvt Ltd',
      'Ministry of Electronics and Information Technology',
      'Par Formulations Pvt Ltd',
      'CSB Bank Ltd',
      'Tech Elecon Pvt Ltd',
      'The Bank of Nova Scotia',
      'Crisil Ltd',
      'YES Bank Ltd',
      'CitiusTech Healthcare Technology Pvt Ltd',
      'Cyient Ltd',
      'Synechron Technologies Pvt Ltd',
      'Reserve Bank of India',
      'VE Commercial Vehicles Ltd',
      'Chhattisgarh Infotech & Biotech Promotion Society',
      'One97 Communication Pvt Ltd',
      'Border Security Force',
      'Airtel Payment Bank Ltd',
      'Birlasoft Ltd',
      'Centre for Railway Information Systems',
      'US Technology International Pvt Ltd',
      'IBS Software Pvt Ltd',
      'Aarthi Scans Pvt Ltd',
      'Bharat Financial Inclusion Ltd',
      'Ict Service Management Solutions',
      'Wistron Infocomm Manufacturing (India) Pvt Ltd',
      'Wipro Ltd',
      'Tata Technologies Ltd',
      'ZOPPER INSURANCE BROKERS PVT LTD',
      'Honda Cars India Ltd',
      'Esec Forte Technologies Pvt Ltd',
      'Oil & Natural Gas Corporation Ltd',
      'Online PSB Loans Ltd',
      'Atlantic Global Shipping Pvt Ltd',
      'IDFC Bank Ltd',
      'Scymes Services Pvt Ltd',
      'CEAT LTD',
      'Tata Consultancy Services Ltd',
      'DCB Bank Ltd',
      'Bank of Maharashtra',
      'Liveon Biolabs Pvt Ltd',
      'Bank of Baroda',
      'ARIAS Society An Autonomous Body under',
      'NTT Communications India Network Services Pvt Ltd',
      'Ujjivan Financial Services Ltd',
      'Tata Motors Finance Ltd',
      'Climate ETC Technology Services pvt ltd',
      'Shakta Technologies Pvt Ltd',
      'PricewaterhouseCoopers Pvt Ltd',
      'Greenlam Industries Ltd',
      'Jemistry Info Solutions LLP',
      'Larsen & Toubro Financial Services',
      'Vikram Sarabhai Space Center',
      'Gujarat Mineral Development Corporation Ltd',
      'Page Industries Ltd',
      'Larsen & Toubro Finance Ltd',
      'IndusInd Bank Ltd',
      'UP Police',
      'Jharkhand Agency For Promotion Of Information Technology',
      'Gujarat Urja Vikas Nigam Ltd',
      'SBI Life Insurance Co Ltd',
      'Vijna Labs Pvt Ltd',
      'Equitas Small Finance Bank Ltd',
      'National Payment Corporation of India',
      'L&T Shipbuilding Ltd',
      'Oracle India Pvt Ltd',
      'Granicus Technologies India Private Ltd',
      'Usha International Ltd',
      'Thales India Pvt Ltd',
      'Telangana Fiber Grid Corporation Ltd',
      'Max Healthcare Institute Ltd',
      'SB Secure Data Centers India Pvt Ltd',
      'Ispace Software Solutions India Pvt Ltd',
      'Indian Overseas Bank',
      'Smartstream Technologies  India Pvt Ltd',
      'Envision Scientific Pvt Ltd',
      'Decypher Technologies',
      'Sukhvarsha Projects Pvt Ltd',
      'Kotak Securities Ltd',
      'Axis Bank Ltd',
      'Orisenc Technologies Pvt Ltd',
      'Sutherland Global Services Pvt Ltd',
      'Aviva Life Insurance Co India Ltd',
      'Access Healthcare Services Pvt Ltd',
      'Zilogic Systems Pvt Ltd',
      'Senco Gold Ltd',
      'Wonder Cement Ltd',
      'TeamLease Services Ltd',
      'Allsec Technologies Ltd',
      'Rahi Systems Pvt Ltd',
      'Netmagic IT Services Pvt Ltd',
      'Directorate Of Accounts And Treasuries',
      'Telangana State Scheduled Caste St India',
      'IBM India Pvt Ltd',
      'ACL Mobile Ltd',
      'Patra India Bpo Services Pvt Ltd',
      'Iris',
      'Alkem Laboratories Ltd',
      'Mphasis Ltd',
      'A3S TECH & COMPANY',
      'Ministry of Corporate Affairs',
      'People Strong Technology Pvt Ltd',
      'Adani Wilmar Ltd',
      'QX Global Services Pvt Ltd',
      'Mckinsey & Company India LLP',
      'Gujarat Metro Rail Corporation LImited',
      'Ashok Leyland Ltd',
      'Guidehouse India Pvt Ltd',
      'The Indian Hotels Company Ltd',
      'National Stock Exchange of India',
      'Paypal India Pvt Ltd',
      'Gujarat State Data Center',
      'Ienergizer IT Services Pvt Ltd',
      'HCL Infosystems Ltd',
      'LTI Mindtree Ltd',
      'KC Enterprise',
      'Cloudsek Information Security PVT LTD',
      'AllState India Pvt Ltd',
      'Modenik Lifestyle Pvt Ltd',
      'Dezerv Investments Pvt Ltd',
      'Small Business FinCredit India Pvt Ltd',
      'Novac Technology Solutions Pvt Ltd',
      'One Sigma Technologies Pvt Ltd',
      'Square International',
      'Ashley Alteams India Ltd',
      'Bihar State Electronics Development Corporation Ltd',
      'ValueLabs',
      'Indian Bank',
      'Sycomp Technologies India Pvt Ltd',
      'Ernst & Young LLP',
      'DarkHorse Digital Solution Pvt Ltd',
      'Alena Engineering',
      'NSDL e-Governance Infrastructure Ltd',
      'Etherbit Pvt Ltd',
      'Mahindra Finance',
      'GTPL Broadband Pvt Ltd',
      'Saregama India Ltd',
      'Loyalty Solutions & Research Pvt Ltd',
      'The South Indian Bank Ltd',
      'Government of Maharashtra',
      'Bharti Airtel Services Ltd',
      'SBI General Insurance Company Ltd',
      'Hindustan Copper Ltd',
      'UIDAI Technology Centre',
      'Indian Financial Technology & Allied Services',
      'Coal India Ltd',
      'Eduspark International Pvt Ltd',
      'Harman International India Pvt Ltd',
      'Bank of India',
      'SISA Information Security Pvt Ltd',
      'Third I Information Security Pvt Ltd',
      'ICICI Bank Ltd',
      'Riverstone Jewels LLP',
      'Cochin Shipyard Ltd',
      'National Thermal Power Corporation Ltd',
      'Tirumala Tirupati Devasthanams',
      'Bundl Technologies Pvt Ltd',
      'Tech Mahindra Ltd',
      'Technocraft Industries India Ltd',
      'All India Institutes of Medical Sciences',
      'National Health Authority',
      'Care Health Insurance Ltd',
      'Metropolitan Media Company Ltd',
      'OpsRamp India Pvt Ltd',
      'BPCL Kochi Refinery',
      'Niva Bupa Health Insurance Co Ltd',
      'Excelra Knowledge Solutions Pvt Ltd',
      'Hatsun Agro Product Ltd',
      'ZeaCloud Services Pvt Ltd',
      'MSTC Ltd',
      'Educational Initiatives Pvt Ltd',
      'Indian Army',
      'Greynium Information Technologies Pvt Ltd',
      'Cochin International Airport Ltd',
      'QuisLex Legal Services Pvt Ltd',
      'Infosys Public Services',
      'Superior Digital Pvt Ltd',
      'BG Chitale',
      'ATS Infrastructure Ltd',
      'Suez India Pvt Ltd',
      'Tractors And Farm Equipment Ltd',
      'EvoluteIQ Solutions Pvt Ltd',
      'AAA Technologies Pvt Ltd',
      'FinIQ Consulting India Pvt Ltd',
      'Small Industries Development Bank of India',
      'Piramal Pharma Ltd',
      'Assyst International Pvt Ltd',
      'Indian Financial Technology and Allied Services',
      'Shahi Exports Pvt Ltd',
      'Deutsche Telekom Digital Labs Pvt Ltd',
      'Ministry of External Affairs India',
      'Brilyant IT Solutions Pvt Ltd',
      'Pearson India Education Services Pvt Ltd',
      'Indiafirst Life Insurance Company Ltd',
      'Thermax Limited',
      'John Cockerill India Ltd',
      'Chaitanya India Fin Credit Pvt Ltd',
      'Bikanervala Foods Pvt Ltd.',
      'Ashika Stock Broking Ltd',
      'Chennai Pertoleum Corporation Ltd',
      'Nagarro software pvt ltd',
      'IDBI Bank Ltd',
      'Indian Air Force',
      'Flipkart Internet Pvt Ltd',
      'Nextbillion Technology Pvt Ltd',
      'Chattisgarh State Power Distribution Company Ltd.',
      'AKS Information Technology Services Pvt Ltd',
      'Philips India Ltd',
      'Electronics Corporation of India Ltd',
      'Orient Cement Ltd',
      'Income Tax Department Centralized Processing Centre',
      'Future Generali India Life Insurance Co Ltd',
      'Xiarch Solutions Pvt Ltd',
      'Frontizo Business Services Pvt Ltd',
      'Department of IT and communication',
      'ICICI Prudential Asset Management Company Ltd',
      'Engineers India Ltd',
      'Go Daddy India Domains and Hosting Services Pvt Ltd',
      'Gujarat Informatics Ltd',
      'Karnataka Bank Ltd',
      'Department of Posts',
      'Central Board of Indirect Taxes and Customs',
      'Inspector General of Police',
      'Star Union Dai-Ichi Life Insurance Company Ltd',
      'Canara Bank',
      'Maruti Suzuki India Ltd',
      'Reliance Industries Ltd',
      'Software Technology Parks of India',
      'Coforge Ltd',
      'Ministry of Skill Development & Entrepreneurship',
      'NIIT LTD',
      'Genpact India Pvt Ltd',
      'Takyon Networks Pvt Ltd',
      'Telus International Unit Xavient Pvt Ltd',
      'Rabwin Industries Pvt Ltd',
      'BDO India LLP',
      'Wipro GE Healthcare Pvt Ltd',
      'National Informatics Center',
      'Snap Camera India Pvt Ltd',
      'Vodafone India Ltd',
      'Sei Technology Pvt Ltd',
      'The Executive Centre India Private Limit',
      'NTT Global Data Centers & Cloud Infrastructure India Pvt Ltd',
      'STL Digital Ltd',
      'Securens Systems Pvt Ltd',
      'Heavy Water Board',
      'VVF INDIA LTD',
      'Pixelpro Management Pvt ltd',
      'The Saraswat Co Operative Bank Ltd',
      'Innodata India Pvt Ltd',
      'Cyril Amarchand Mangaldas Peninsula Chambers',
      'La Gajjar Machineries Pvt Ltd',
      'Wheels India Ltd',
      'Sahyadri Karad Hospital Pvt Ltd',
      'Surya Hospitals Pvt Ltd',
      'Mitsubishi Corporation India pvt ltd',
      'Sahyadri Hospital Pvt Ltd',
      'Infocepts Technologies Pvt Ltd',
      'Barbeque Nation',
      'IDFC First Bank Ltd',
      'I2k2 Networks Pvt Ltd',
      'Barauni Thermal Power Plant',
      'The Cosmos Co-operative Bank Ltd',
      'The Oriental Insurance Company Ltd',
      'WNS Global Services Pvt Ltd',
      'Star Health And Allied Insurance Co Ltd',
      'Himalaya Wellness Company',
      'Telangana State Co-operative Apex Bank Ltd',
      'Botree Software International Pvt Ltd',
      'Nucleus System Security Consultants Pvt Ltd',
      'Credit Agricole Cib services Pvt Ltd',
      'Export Credit Guarantee Corporation Of India Ltd',
      'Exl Service Ireland Ltd',
      'Brakes India Pvt Ltd',
      'RamaCivil India Constructions Pvt Ltd',
      'Merabo labs Pvt ltd',
      'Capital Small Finance Bank Ltd',
      'Crompton Greaves Consumer Electricals Ltd',
      'Vodafone Idea Ltd',
      'Kerala State Co-operative Bank Ltd',
      'Continuum India LLP',
      'Mindgate Solutions Pvt Ltd',
      'Indian Council of Agricultural Research',
      'Precision Biometric India Pvt Ltd',
      'SONY PICTURES NETWORKS INDIA PVT LTD',
      'Aricent Technologies Holdings Ltd',
      'Aditya Birla Financial Shared Services Ltd',
      'Bharat Electronics Ltd',
      'JK Tyre & Industries Ltd',
      'Giesecke & Devrient India Pvt Ltd.',
      'Gridco Ltd',
      'Tata Asset Management Pvt  Ltd',
      'Millennium Technosoft Pvt Ltd',
      'The Mehsana Urban Co-operative Bank Ltd',
      'Universal Sompo General Insurance Company Ltd',
      'Marks and Spencer Reliance India Pvt Ltd',
      'Airtel Tanzania Ltd',
      'Ministry Of Home Affairs',
      'CIPLA Ltd',
      'Prestige Estates Projects Ltd',
      'Canon India Pvt Ltd',
      'Smart Kalyan Dombivli Development Corporation Ltd',
      'Sony India Software Centre Pvt Ltd',
      'Motherson Technology Services Ltd',
      'Godrej Infotech Ltd',
      'MariApps Marine Solutions Pvt ltd',
      'Grab a Grub Services Pvt Ltd',
      'Ericsson India Global Service Pvt Ltd',
      'Aditya Birla Sun Life Insurance Company Ltd',
      'Allahabad Smart City Ltd',
      'Piramal Capital & Housing Finance Ltd',
      'Ramco Systems Ltd',
      'State Bank Of India',
      'Hq Northern Command',
      'FCI GBS India Pvt Ltd',
      'Omci Rig Technical & Support Services Pvt Ltd',
      'Midland Credit Management India Pvt Ltd',
      'Orissa bridge and construction corporation Ltd.',
      'Kerala State Electricity Board Ltd',
      'AU Small Finance Bank Ltd',
      'Zalaris HR Services India Pvt Ltd',
      'TECHNOCRAFT INDUSTRIES (INDIA) LTD',
      'Torrent Power Ltd',
      'Holy Family Hospital',
      'Kotak Mahindra Life Insurance Company Ltd',
      'Infostretch Corporation India Pvt Ltd',
      'Ipsen Technologies Pvt Ltd',
      'Sapper Software Pvt Ltd',
      'Piramal Enterprises Ltd',
      'Angel One Ltd',
      'WM Global Technology Services India Pvt Ltd',
      'Centillion Network Pvt Ltd',
      'Subex Digital LLP',
      'Schloss HMA Pvt ltd',
      'Torrent Gas Pvt Ltd',
      'Neuland Laboratories Ltd',
      'Altimetrik India Pvt Ltd',
      'Expeditors International India pvt ltd',
      'Head Digital Works Pvt Ltd',
      'Creative Synergies Consulting India Private Ltd',
      'Indian Oil Corporation Ltd',
      'Godrej Housing Finance Ltd',
      'Dehradun Smart City Ltd',
      'National Technical Research Organisation',
      'Jharkhand Agency For Promotion  Of Information Technology',
      'National Board of Revenue',
      'Mastek Ltd',
      'Make My Trip India Pvt Ltd',
      'Maven Wave Partners India Pvt Ltd',
      'L&T-MHI Power Boilers Pvt Ltd',
      'DMS Technologies Pvt Ltd',
      'Employees State Insurance Corporation',
      'R1 RCM Global Pvt Ltd',
      'Hotwax Systems Pvt Ltd',
      'Directorate Of Commercial Taxes',
      'Gail India Ltd',
      'Saitronics Systems Pvt Ltd',
      'Keralavision Broadband Ltd',
      'Kanpur Smart City Ltd',
      'Maveric Systems Ltd',
      'Centre for Development  of Advanced Computing',
      'Exotel Techcom Pvt Ltd',
      'National Bank for Agriculture and Rural Development',
      'Ambika Computer',
      'ITC Ltd',
      'Intas Pharmaceuticals Ltd',
      'UTI Asset Management Company Ltd',
      'Emaar India Ltd',
      'Xpress.ooo Solutions LLP',
      'MMS Maritime India Pvt Ltd',
      'Adama India Pvt Ltd',
      'Motilal Oswal Securities',
      'Sharp Software Development India Pvt Ltd',
      'Fundtech India Pvt Ltd',
      'Nucleus Software Exports Ltd',
      'Thomas Cook India Ltd',
      'Hexaware Technologies Ltd',
      'Airspan Networks (India) Pvt Ltd',
      'Bureau of Police Research  and Development',
      'Greaves Cotton Ltd',
      'Hero MotoCorp Ltd',
      'Wurth Information Technology India Pvt L',
      'Utkarsh Small Finance Bank Ltd',
      'ANI Technology Pvt Ltd',
      'Reserve Bank Information Technology Pvt Ltd',
      'TECHNOSOFT ENGINEERING PROJECTS LTD',
      'Iris Software Technologies Pvt Ltd',
      'Transworld Systems India Pvt Ltd',
      'The Printers (Mysore) Pvt Ltd',
      'Punjab State E-Governance Society',
      'O9 Solutions Management India Pvt Ltd',
      'Stock Holding Corporation of India Ltd',
      'Tata Communications International Pte Ltd',
      'NxtGen Datacenter & Cloud Technologies Pvt Ltd',
      'Pfsweb Global Services Pvy Ltd',
      'K.Govindaswamy Naidu Medical Trust',
      'Biomatiques Identification Solutions Pvt Ltd',
      'Uno Minda Ltd (Corporate Office),',
      'The Andhra Pradesh Mahesh Bank Cooperative Urban Bank Ltd',
      'KrazyBee Services Pvt Ltd',
      'Regalix India Pvt Ltd',
      'Netmagic Solutions Pvt Ltd',
      'Passport Seva Programme Passport & Visa Division',
      'Goods And Services Tax Network',
      'Dholera Industrial City Development Ltd',
      'Tokai Imperial Rubber India Pvt Ltd',
      'Locon Solutions Pvt Ltd',
      'National Register of Citizens (NRC),',
      'VXI Global Solutions India Pvt Ltd',
      'Narayana Hrudayalaya Ltd',
      'Mahalasa Constructions Pvt ltd',
      'Intelligence Bureau',
      'DLF Ltd',
      'Sundaram Finance Ltd',
      'Ayurvet Ltd',
      'Aurangabad Industrial Township Ltd',
      'Mindtree Ltd',
      'Royal Sundaram General Insurance Co Ltd',
      'Ignitarium Technology Solutions Pvt Ltd',
      'Garware Technical Fibres Ltd',
      'Inspace Technologies Pvt Ltd',
      'In Solutions Global Ltd',
      'JM Financial Properties and Holding Ltd',
      'Future Generali India Insurance Co Ltd Future Generali India Life Insurance Co',
      'Alinea Healthcare Pvt Ltd',
      'Truecom Networks Pvt Ltd',
      'Intertrust Group',
      'Mitsubishi Electric India Pvt Ltd',
      'Reliance Jio Infocomm Ltd',
      'India Post Payment Bank',
      'Interglobe Aviation Ltd',
      'ACPL Systems Pvt Ltd',
      'G-Info Technology Solutions Pvt Ltd',
      'National Institute of Urban Affairs',
      'Kushals Retail Pvt Ltd',
      'National Intelligence Grid NATGRID',
      'Grant Thornton Bharat LLP',
      'Dunzo Digital Pvt Ltd',
      'Kotak Mahindra Bank Ltd',
      'Assam Society for Comprehensive Financial Management System',
      'The Co-Operative Bank of Rajkot Ltd',
      'Teleperformance Global Services Pvt Ltd',
      'Wuerth India Pvt Ltd',
      'Synergistic Financial Network Pvt Ltd',
      'Raman Research Institute',
      'Government of Rajasthan',
      'Firstmeridian Business Services Pvt Ltd',
      'Motherhood Hospital',
      'Jubilant Pharmova Ltd',
      'Qburst Technologies Pvt Ltd',
      'Evolving Systems Networks India Pvt Ltd',
      'Fino Payments Bank Ltd',
      'Resiplex Hospitality & Developers Pvt Ltd',
      'Asian Paints Ltd',
      'Mahindra & Mahindra Ltd',
      'Exide Life Insurance Company Ltd',
      'ABB GISL',
      'Icons',
      'Tata Play Broadband Pvt Ltd',
      'Power Systems Operation Corporation Ltd',
      'Associated Hospitality & Developers Pvt ltd',
      'Enoah Isolution India Pvt Ltd',
      'National Remote Sensing Centre',
      'Oil India Ltd',
      'VerSe Innovation Pvt Ltd',
      'Alight Solutions Pvt Ltd',
      'Govt medical College Jind Huda Market',
      'Kisetsu Saison Finance India Pvt Ltd',
      'AT&T Communication services India Pvt Ltd',
      'InstaSafe Technologies Pvt Ltd',
      'Fab India Pvt Ltd',
      'Prudent Insurance Brokers Pvt Ltd',
      'Bank Note Paper Mill India Pvt Ltd',
      'Indira Gandhi Institute Of Medical Sciences',
      'Vision Rx Lab Pvt Ltd',
      'GE India Industrial Pvt Ltd',
      'Vinca Cybertech Pvt Ltd',
      'Paycrunch Pvt Ltd',
      'Sundarlal Sawaji Urban Co Operative Bank Ltd',
      'Trivitron HealthCare Pvt Ltd',
      'Navitas Life Sciences Pvt Ltd',
      '-',
      'DC Books',
      'Mantra Softech India Pvt Ltd',
      'Mosambee',
      'Serum Institute of India Pvt Ltd',
      'Gujarat Informatics India Ltd',
      'Wells Fargo & Company',
      'Network Intelligence Pvt Ltd',
      'Housing Development Finance Corporation',
      'HCL Technologies Ltd',
      'Saraswat infotech Pvt Ltd',
      'Indman Marine Management Pvt Ltd',
      'MiQ Digital India Pvt Ltd',
      'Indivillage Tech Solutions Llp',
      'Ethos Life Technologies Pvt Ltd',
      'KIA India Pvt Ltd',
      'GavBit Pvt Ltd',
      'Writer Business Services Pvt Ltd',
      'Tecnotree Convergence Pvt Ltd',
      'Finacus Solutions Pvt Ltd',
      'Bajaj Auto Ltd',
      'Flatworld Solutions Pvt Ltd',
      'Global Analytics India Pvt Ltd',
      'Kotak Mahindra Asset Management Co Ltd',
      'IBI Chematur Engineering and Consultancy Ltd',
      'Birla Management Centre Services Ltd',
      'Rajcomp Info Services Ltd',
      'Incture Techologie Pvt Ltd',
      'Anugraha Valve Castings Ltd',
      'KPIT Technologies Ltd',
      'MedGenome Labs Ltd',
      'Madhya Pradesh State Electronics Development Corporation Ltd',
      'Tejas Networks Ltd',
      'Samsung R&D Institute India Pvt Ltd',
      'Nimzo-I Technologies Pvt Ltd',
      'Tata Steel Ltd',
      'Kore Ai Software India Pvt Ltd',
      'GE Power Conversion India Pvt Ltd',
      'Sannam S4 Management Services (India) Pvt Ltd',
      'Abbott Healthcare Pvt Ltd',
      'Atlas Systems Pvt Ltd',
      'Indian Immunologicals Ltd',
      'Rizing LLC',
      'Catholic Syrian Bank',
      'United Spirits Ltd',
      'V-Ensure Pharma Technologies Pvt Ltd',
      'Myntra Designs Pvt Ltd',
      'EMC Software and Services India Pvt Ltd',
      'Voonik Technologies Pvt Ltd',
      'ABB India Ltd',
      'CyberQ Consulting Pvt Ltd',
      'Nelco Ltd',
      'SAP India Pvt Ltd',
      'Flitpay Pvt Ltd',
      'Vault Infosec',
      'MattsenKumar LLC',
      'Haryana Parivar Pehchan Authority',
      'Tnq Technologies Pvt Ltd',
      'Nucleus Corporate Services Pvt Ltd',
      'Kyocera Document Solutions India Pvt Ltd',
      'Jana Small Finance Bank Ltd',
      'Navitas Llp',
      'Saveetha Engineering College',
      'Parle Elizabeth Tools Pvt Ltd',
      'NGK Technologies India Pvt Ltd',
      'SBI Business Process Management Services Pvt Ltd',
      'Ashtvinayak Leisure Pvt Ltd',
      'Bihar Agricultural University',
      'Manappuram Finance Ltd',
      'Minda Industries Ltd',
      'Securities and Exchange Board Of India',
      'Quizizz Inc',
      'Apeejay Surrendra Park Hotel Ltd',
      'VFS Global Services Pvt Ltd',
      'Kotak Mahindra General Insurance Company Ltd',
      'Torrent Pharmaceuticals Ltd',
      'Altisource Business Solutions Pvt Ltd',
      'Vectrae Infotech Pvt Ltd',
      'Byteview Technologies LLP',
      'Medi Assist Insurance Tpa Pvt Ltd',
      'Tata Communications Germany Ltd',
      'Tata Communications UK Ltd',
      'Frog Cellsat Ltd',
      'ATC Tires Ltd',
      'MRF Ltd',
      'National Internet Exchange of India',
      'Movate Technologies Pvt Ltd',
      'Bajaj Finance Ltd',
      'JTEKT India Ltd',
      'Fidelity Business Services India Pvt Ltd',
      'Persistent Systems Ltd',
      'Accolite Digital India Pvt Ltd',
      'Atom Myanmar Ltd',
      'Aerial Telecom Solutions Pvt. Ltd.',
      'Triflo Technologies Pvt Ltd',
      'MoveInSync Technology Solutions Pvt Ltd.',
      'MPS Ltd',
      'Payatu Security Consulting Pvt Ltd',
      'Capgemini Technology Services India ltd',
      'National Informatics Center Services Incorporated',
      'National Informatics Center Services Inc',
      'Sundaram-Clayton Ltd',
      'J K Group',
      'Prochant India Pvt Ltd',
      'Prompt Equipments Pvt Ltd',
      'Assam Electronics Development Corporation Ltd',
      'Kalpataru Ltd',
      'Indraprastha Institute of Information Technology',
      'Rockman Industries Ltd',
      'Bangalore International Airport Ltd',
      'UD Trucks India Pvt Ltd',
      'Esaf Small Finance Bank Ltd',
      'HDB Financial Services Ltd',
      'Directorate General Of Civil Aviation',
      'Vanaps Consulting Pvt Ltd',
      'GEA BGR Energy System India Ltd',
      'ESF Labs Ltd',
      'Avalon Technologies Pvt Ltd',
      'Edexperiential & Infrastructure LLP',
      'Bharat Sanchar Nigam Ltd',
      'Vinsinfo Pvt Ltd',
      'Uber India Technology Pvt Ltd',
      'Dhanuka Agritech Ltd',
      'Cyraac Services Pvt Ltd',
      'Trident Ltd',
      'Dr Reddys Laboratories Ltd',
      'AuthBridge Research Services Pvt Ltd',
      'Radisys India Limited',
      'Concentrix Services India Pvt Ltd',
      'Route Mobile Ltd',
      'The Karur Vysya Bank Ltd',
      'IARM Information Security Pvt Ltd',
      'SVS International',
      'UMA Home Decor',
      'Blue Dart Express Ltd',
      'Postman Inc Postdot Technologies Pvt Ltd',
      'Hindustan Petroleum Corporation Ltd',
      'Bajaj Financial Securities Ltd',
      'Barclays Global Service Centre  Pvt Ltd',
      'Raptakos Brett & Co Ltd',
      'Manjushree Technopack Ltd',
      'Adrenalin eSystems Ltd',
      'DXC Technology India Pvt Ltd',
      'Fincare Small Finance Bank Ltd',
      'Ameya Logistics Pvt Ltd',
      'Isha Foundation',
      'National Crafts Museum & Hastkala Academy',
      'Vistara',
      'J.P. Morgan Services India Pvt Ltd',
      'DNSO-Indian Navy',
      'Lambda Therapeutic Research Ltd',
      'Ramky Infrastructure Ltd',
      'Rotomaker India Pvt Ltd',
      'Director of General of Police',
      'Government of Uttar Pradesh',
      'Acuity Knowledge Centre India Pvt Ltd',
      'Experian Services India Pvt ltd',
      'Aarti Pharmalabs Ltd',
      'ICICI Lombard General Insurance Company Ltd',
      'Standard Chartered Bank',
      'Acuity Knowledge Services India Pvt Ltd',
      'Cellulera Infotech Pvt Ltd',
      'Rently Software Development Pvt Ltd',
      'Reliance Communications Ltd',
      'Tata Advanced Systems Ltd',
      'RailTel Corporation of India Ltd',
      'Shri Ram Janaki  Medical College & Hospital Samastipur',
      'Muthoot Pappachan Technologies Ltd',
      'UST Global',
      'University Of Petroleum & Energy Studies',
      'Global University Systems',
      'Creative Arts Educations Society',
      'Netrika Consulting India Pvt Ltd',
      'Vedanta Ltd',
      'Directorate General of Foreign Trade',
      'Moradabad Smart City Ltd',
      'Agilus Diagnostics Ltd',
      'Yamuna International Airport Pvt Ltd',
      'JSW Steel Coated Products Ltd',
      'PPD Consultant Llp',
      'Sporta Technologies Pvt Ltd',
      'Contis Technologies Pvt Ltd',
      'Rapipay Fintech Pvt Ltd',
      'Kerala State IT Mission',
      'Digital Nirvana Information Systems India Pvt Ltd',
      'SBI Funds Management Pvt Ltd',
      'Hitachi Energy Technology Services Pvt Ltd',
      'Emcure Pharmaceuticals Ltd',
      'Raheja Universal Pvt Ltd',
      'Cosmo First Ltd',
      'Aditya Birla Finance Ltd',
      'Epragathi Recycling',
      'Payfront Technologies India Pvt Ltd',
      'Tranter India Pvt Ltd',
      'Sales Force India Pvt Ltd',
      'IOPS',
      'Vidyatech Solutions Pvt Ltd',
      'Emarson Infotech Pvt Ltd',
      'Export Import Bank of India ',
      'Facebook India Online Services Pvt Ltd',
      'Pixstone Images Pvt Ltd',
      'Nomura Research Institute Financial Technologies India Pvt Ltd',
      'Tavant Technologies India Pvt Ltd',
      'Ranchi Smart City Corporation Ltd',
      'Mohan Clothing Company Pvt Ltd',
      'Unilog Content Solutions Pvt Ltd',
      'Sri Ramakrishna Hospital',
      'Cigniti Technologies Ltd',
      'Raychem RPG Pvt Ltd',
      'Thangamayil Jewellery Ltd',
      'SMC Global Securites Ltd',
      'Deutsche Bank AG',
      'Aptara corporation',
      'Pramerica Life Insurance Ltd',
      'Xentrix Studios Pvt Ltd',
      'Skye Air Mobility Pvt Ltd',
      'Aspirify Enterprises Pvt Ltd',
      'Sri Lakshmi Narasimha Swamy Devasthanam Ahobilam',
      'Modern Road Makers Pvt Ltd',
      'Technobile Systems Pvt Ltd',
      'Fair Isaac India Software Pvt Ltd',
      'Life Insurance Corporation Of India',
      'Aarti Industries Ltd',
      'Welingkar Institute Of Management Develo',
      'RR Donnelley - India',
      'Addverb Technologies Ltd',
      'Kraft Heinz India Pvt Ltd',
      'Excellerate Enterprises',
      'ESDS Software Solution Ltd',
      'Nitta Gelatin India Ltd',
      'Sify Technologies Ltd',
      'Moshpit Technologies Pvt Ltd',
      'Sundaram Finance Holdings Ltd',
      'Winman Software India Llp',
      'Enstage Software Pvt Ltd',
      'Financial Softwares & Systems Pvt Ltd',
      'Applied Data Finance',
      'RSA Security Applications India Pvt Ltd',
      'Dr. Reddy Laboratories Ltd',
      'Redbus India Pvt Ltd',
      'Thales DIS Technology India Pvt Ltd',
      'Indinfravit Project Managers Pvt Ltd',
      'HDFC Life Insurance Company Ltd',
      'EXL Service.Com India Pvt Ltd',
      'Hathway Cable & Datacom Ltd',
      'Synclature Consultancy Pvt Ltd',
      'QRC Assurance & Solutions Pvt Ltd',
      'SREI Equipment Finance Ltd',
      'Studds Accessories Ltd',
      'Intellect Design Arena Ltd',
      'Finnew Solutions Pvt Ltd',
      'Maini Precision Product Ltd',
      'Tata Strategic Management Group',
      'Ajanta Pharma Ltd',
      'Brookfield',
      'Nitori India Pvt Ltd',
      'Bhartiya City Developers Pvt Ltd',
      'Nirmata Technologies India Pvt Ltd',
      'iHub Anubhuti-IIITD Foundation',
      'Bharti Reality Ltd',
      'Hindustan Aeronautics Ltd',
      'Easebuzz Pvt Ltd',
      'Ministry Of  External Affairs',
      'RBL Bank Ltd',
      'Dun & Bradstreet Technologies & Data Services',
      'Lifetime Wellness Rx International Ltd',
      'National Institute Of Mental Health And Neuro Sciences',
      'AG Resources India Pvt Ltd',
      'Lenskart Solutions Pvt Ltd',
      'PSR IT Services Pvt Ltd',
      'Mitu Sharma',
      'Qseap Infotech Private Limited',
      'MEL Training & Assessments Ltd',
      'Xanadu Realty Ltd',
      'OnionLife Pvt Ltd',
      'Dish TV India Ltd',
      'Infinite Computer Solutions  India Ltd',
      'Maharashtra Seamless Ltd',
      'Dr. Lal Pathlabs Ltd',
      'CGI Information Systems and Management Consultants Pvt Ltd',
      'Accel It Services Pvt Ltd',
      'Bharat Aluminium Company Ltd',
      'Institute of Rural Management Anand',
      'Sapphire Foods India Ltd',
      'Gujarat State Petronet Ltd',
      'Amara Raja Batteries Ltd',
      'E2E Networks Ltd',
      'Needle Industries (India) Private Limite',
      'ICAR ATARI Zone VI Guwahati',
      'Texports Syndicate India Ltd',
      'Sequent Scientific Ltd',
      'Procain Consulting and Services Pvt Ltd',
      'KEI Industries Ltd',
      'Instant Global Paytech Pvt Ltd',
      'Taurus IT Solutions',
      'Tata Consultancy Services-BaNCS',
      'ZS Associates, Inc',
      'Kerala Communicators Cable Ltd',
      'Zerodha broking Pvt Ltd',
      'PTC India Financial Services Ltd',
      'Bharat Co-operative Bank Mumbai Ltd',
      'TDS Lithium-Ion Battery Gujarat Pvt',
      'Shri Ram Janmabhoomi Teerth Kshetra',
      'Microwave Tube Research & Development Centre',
      'Gujarat Energy Transmission Corporation Ltd',
      'Microsoft Corporation India Pvt Ltd',
      'Ergo Technology & Services Pvt Ltd',
      'KPMG',
      'NSEIT Ltd',
      'Nittany Creative Services Llp',
      'Nahar Integrated System Services Pvt Ltd',
      'BSE Technologies Pvt Ltd',
      'HCL Technologies Ltd ( AH07 )',
      'Iris Active Communications Pvt Ltd',
      'Dabur India Ltd',
      'Felix Generics Pvt Ltd',
      'Dalmia Cement (Bharat) Ltd',
      'Indus Valley Partners',
      'Navikenz India Pvt Ltd',
      'New India Cooperative Bank',
      'ORIENT ELECTRIC LIMITED',
      'Talent Formula Pvt Ltd',
      'Indigrid Ltd India Grid Trust',
      'S D Fine Chem Ltd',
      'Global Health Ltd',
      'Tata Elxsi Limited',
      'Adani Enterprises Ltd',
      'Shri Keshtra Info Technologies',
      'Techbooks International Pvt Ltd',
      'Excelsoft Technologies Pvt Ltd',
      'Icertis India (ISPL & IPIPL)',
      'QX Global Services LLP',
      'Bhabha Atomic Research Centre',
      'Jewelex India Pvt Ltd',
      'MobileComm Technologies India Pvt Ltd',
      'Annet Technologies(Mumbai) LLP',
      'Intercraft Trading Pvt Ltd',
      'Albonair India Pvt Ltd',
      'LNJ Bhilwara Group',
      'MG Motor India Pvt Ltd',
      'O2 Power Pvt Ltd',
      'Wishnet Pvt Ltd',
      'Employees Provident Fund Organisation',
      'Sarjen Systems Pvt Ltd',
      'Paragon Business Solutions Ltd',
      'Integreon Managed Solutions India Pvt Ltd',
      'Expleo India Infosystems Pvt Ltd',
      'Interglobe',
      'Directorate of Income Tax',
      'Simplify Healthcare',
      'Matrimony.Com Pvt Ltd',
      '75f Smart Innovations India Pvt ltd',
      'T-Systems Information and Communication Technology India Pvt Ltd',
      'BDX Data Centers India',
      'Tecplix Technologies Pvt Ltd',
      'A B Dahotre and Co',
      'Trenetra AVIT Solutions Pvt Ltd',
      'Netskope Software India Pvt Ltd',
      'National Payments Corporation of India',
      'Ashirvad Pipes Pvt Ltd',
      'Siemens Ltd',
      'Mandke Foundation KHAD',
      'FirstSource Solutions Ltd',
      'Amdocs Development Center India Pvt Ltd',
      'Shoppers Stop Ltd',
      'Sula Vineyards Ltd',
      'Infinx Services Pvt. Ltd.',
      'Peneto Labs Pvt Ltd',
      'Convergys India Servies Pvt Ltd',
      'Telangana State Technology Services',
      'JWIL INFRA LTD',
      'Tata Electronics Pvt Ltd',
      'Resilient Innovations Pvt Ltd',
      'Aditya Birla Fashion and Retail Ltd',
      'Standard Chartered Securities (India) ltd',
      'Kals Distilleries Pvt Ltd',
      'The Central Financial Credit and  Investment Co-Operative India Ltd',
      'Vinculum Solutions Pvt Ltd',
      'Central Depository Services India Ltd',
      'Sapience Analytics Corp',
      'National Forensic Sciences University',
      'Bharat Petroleum Corporation Ltd',
      'Jubilant Food Works Ltd',
      'ABS India Pvt Ltd',
      'Olam Information Services Ltd',
      'Supra Pacific Financial Services Ltd',
      'Reverselogix Management India Pvt Ltd',
      'Young Brand Apparel Pvt Ltd',
      'KEB Hana Bank',
      'GMR Hyderabad International Airport Ltd',
      'Directorate of treasuries and Accounts Government of Madhya Pradesh',
      'Dhanlaxmi Bank Ltd',
      'Maharashtra Legislature Secretariat',
      'Brillio Technologies Pvt Ltd',
      'Vyapi Info Tech Pvt Ltd',
      'NKGSB Co-Op. Bank Ltd',
      'Fusion MicroFinance Pvt Ltd',
      'MMTV Ltd',
      'Larsen & Toubro Infotech Ltd',
      'Mangalore Refinery and Petrochemical Ltd',
      'Lifestyle International Pvt Ltd',
      'Paytm Payment Bank Ltd',
      'Bristlecone India Ltd',
      'Andhra Bank',
      'Coronis Ajuba Solutions Pvt Ltd',
      'Jocata Financial Advisory & Technology Services Pvt Ltd',
      'Wyyse Innovation Group Pvt Ltd',
      'Srin Soft Technologies Pvt Ltd',
      'Gujarat Fluorochemicals Ltd',
      'eClerx Services Ltd',
      'Matrix Business Services India Pvt Ltd',
      'Ganga Acrowools Ltd',
      'Durr India Pvt Ltd',
      'Shieldbyte Infosec Pvt Ltd',
      'Bandhan AMC Ltd',
      'Motilal Oswal Financial Services Ltd',
      'Cotelligent india Pvt Ltd',
      'Natures Basket Ltd',
      'Head of Global Security Operations',
      'Netsentries Infosec Solutions Pvt Ltd',
      'Shapoorji Pallonji Finance Pvt Ltd',
      'Transmarine Cargo Services Pvt. Ltd.',
      'Alpha Ori India Pvt Ltd',
      'Netcracker Technology India Pvt Ltd',
      'Zimyo Consulting Pvt  Ltd',
      'Omega Healthcare Management Services Pvt Ltd',
      'Apollo Hospitals Enterprise Ltd',
      'Synergistic Financial Networks Pvt. Ltd',
      'Tokyo Chemical Industry india Pvt Ltd',
      'Aneja Associates',
      'Titan Company Ltd',
      'Indostar Capital Finance Ltd',
      'DMI Finance Pvt Ltd',
      'Aujas Networks Pvt Ltd',
      'Central Reserve Police Force',
      'General Electric Company',
      'GE Precision Healthcare LLC',
      'Ecs Infotech Pvt Ltd',
      'Movin Express Pvt Ltd',
      'MasterCard Technology Pvt Ltd',
      'Qualcomm India Pvt Ltd',
      'Hansa Cequity',
      'Bidgely Technologies Pvt Ltd',
      'Spicejet Ltd',
      'Pune District Central Co-operative Bank Ltd',
      'Meta Infotech Pvt Ltd',
      'Godrej & Boyce Ltd',
      'Aramco Asia India Pvt Ltd',
      'Tripura State Co-operative Bank Ltd',
      'South Indian Bank Ltd',
      'Sonic Biochem Ext Pvt Ltd',
      'Innominds Software Pvt Ltd',
      'Karnataka Gramin Bank',
      'Future Generali India Insurance Co Ltd',
      'Navitasys India Pvt Ltd',
      'Agile Parking Solutions Pvt Ltd',
      'Sodexo SVC India Pvt Ltd',
      'Canara HSBC Life Insurance Company Ltd',
      'Sharekhan Ltd',
      'Renault Nissan Automotive India Pvt Ltd',
      'Samvardhana Motherson International Ltd',
      'Tata Sky Ltd',
      'Department of Information Technology & Electronics',
      'EXL Service',
      'Accutest Research Laboratories Pvt Ltd',
      'Government of Madhya Pradesh',
      '5Sec Cyberpwn Technologies Pvt Ltd',
      'Artech Infosystems Pvt Ltd',
      'Mouser Electronics India Pvt Ltd',
      'ITZCASH',
      'SNV Aviation Pvt Ltd (Akasa Air)',
      'Inflow Technologies Pvt Ltd',
      'Force Identification Pvt Ltd',
      'Federal Bank Ltd',
      'Hyundai Motor India Ltd',
      'Ernst & Young Services Pvt Ltd',
      'Studypad India Pvt. Ltd',
      'Prod Software India Private Ltd.',
      'VA Tech Wabag Ltd',
      'Uttar Pradesh Rajya Vidyut Utpadan Nigam Ltd',
      'Diu Smart City Ltd',
      'Arrk Solutions Pvt Ltd',
      'Shezartech',
      'Sharekhan',
      'North East Small Finance Bank Ltd',
      'Nanoprecise Data Services Pvt Ltd',
      'R Systems International Ltd',
      'Hitachi Cash Management services Pvt Ltd',
      'ITC Infotech India Ltd',
      'Mwyn Tech Pvt Ltd',
      'Gainwell Commosales Pvt Ltd',
      'All India Institute of Medical Science',
      'Vivriti Capital Pvt Ltd',
      'Vedanta Limited',
      'Andhra Pradesh State Fibernet Ltd',
      'SBI Mutual Fund Trustee Company Pvt Ltd',
      'Kirloskar Brothers Ltd',
      'Excelacom Technologies Pvt Ltd',
      'India1 Payments Ltd BTI Payments Pvt. Ltd',
      'Invoq Healthcare India Pvt Ltd',
      'Reventics Pvt Ltd',
      'Syngene International Ltd',
      'Acsia Technologies Pvt Ltd',
      'Soctronics Technologies Pvt Ltd',
      'Ey Global Delivery Services India Llp',
      'Invecas Technologies Pvt Ltd',
      'Digital Track Solutions Pvt Ltd',
      'Neogrowth Credit Pvt Ltd',
      'Sentiss Pharma Pvt Ltd',
      'Protectt.ai Labs Pvt Ltd',
      'Sasken Communication Technologies Ltd',
      'NLB Technology Services Pvt Ltd',
      'Pipeline Infrastructure Ltd',
      'Dreamzcraft Infomatics Pvt Ltd',
      'Cyble Infosec India Pvt Ltd',
      'Religare Support Services Ltd',
      'Vsecure Networks',
      'TVS Srichakra Ltd',
      'Cymune Cyber Security Services Pvt Ltd',
      'SecurEyes Techno Services Pvt Ltd',
      'Emerald Jewel Industry India Ltd',
      'Technosoft Global Services Pvt Ltd',
      'Accretive Cleantech Finance Pvt Ltd',
      'Convergys India Services Pvt Ltd',
      'Contai Co-operative Bank Ltd',
      'Cibera Defence Pvt Ltd',
      'PhonePe Pvt Ltd',
      'Pacific Consolidated Industries (pci) Gases India Pvt Ltd',
      'Innominds Software Sez India Pvt Ltd',
      'Coromandel International Ltd',
      'Alipur Zoological Garden',
      'Odisha Computer Application Centre',
      'Block By Block Builders India Pvt Ltd',
      'Tata AIA Life Insurance Company Ltd',
      'Highradius Technologies Pvt Ltd',
      'Venkataramanan Associates',
      'VWR Lab Products Pvt Ltd',
      'Vodafone Mobile Services Ltd',
      'Aditya Birla Capital Ltd',
      'Ministry of Defence - Department of Defence',
      'Suebel Seals International Pvt Ltd',
      'Broadcom Communications Technologies Pvt Ltd',
      'Sattrix Information Security Ltd',
      'Perfios Account Aggregation Services Pvt Ltd',
      'Mylan Laboratories Ltd',
      'Embassy Group',
      'NG Techassurance Pvt Ltd',
      'Jio Platforms Ltd',
      'Ecom Express Pvt Ltd',
      'Gavs Technologies Pvt Ltd',
      'Shell India Markets Pvt Ltd',
      'SBI Cards & Payments Services Ltd',
      'Century Plyboards Pvt Ltd',
      'Dhani Loans and Services Ltd',
      'Redington Ltd',
      'Atria Convergence Technologies Ltd',
      'Ramco Cements Ltd',
      'Clix Capital Services Pvt Ltd',
      'Thyssenkrupp Aerospace India Pvt Ltd',
      'Spencer Retail Ltd',
      'PCBL Ltd',
      'Institute of Liver & Biliary Sciences',
      'Associated IT Consultants Pvt Ltd',
      'Allstate Solutions Pvt Ltd',
      'Mcfadyen Consulting Software India Pvt Ltd',
      'Pan Asia Banking Corporation PLC',
      'Allegis Services India Pvt Ltd',
      'Department Of Information Technology & Communication',
      'Punjab & Sindh Bank',
      'Aragen Life science Ltd',
      'J P Morgan India Pvt Ltd',
      'Shardul Amarchand Mangaldas & Co',
      'SecurBay Services Pvt Ltd',
      'Creative Communication',
      'Meenakshi Infrastructures Pvt Ltd',
      'Satish Dhawan Space Centre SHAR',
      'Dhanuka Laboratories Ltd',
      'Data Software Research Company Pvt Ltd',
      'ITOrizin Technology Solutions Private Li',
      'Redserv Global Solutions Ltd',
      'RPSG Ventures Limited',
      'Hi-Q Electronics Pvt Ltd',
      'Bandhan Bank Ltd',
      'ITD CPC',
      'Sysfore Technologies pvt ltd',
      'Azentio Software Pvt Ltd',
      'Pi Datacenters Pvt Ltd',
      'India Glycols Ltd',
      'Wipro Enterprises Pvt Ltd',
      'Petron Group Of Companies',
      'Cadeploy Engineering Pvt. Ltd',
      'Flying Trade India Pvt Ltd',
      'Kewal Kiran Clothing Ltd',
      'Accelya Kale Solutions Ltd',
      'Concentrix Daksh Services India Pvt Ltd',
      'Artemis Medicare Services Ltd',
      'ABB Global Industries & Service Pvt Ltd',
      'Oil and Natural Gas Corporation Ltd ONGC',
      'Itilite Technologies Pvt Ltd',
      'Fractal Analytics Pvt Ltd',
      'General Aeronautics Pvt Ltd',
      'The Mashreq Bank',
      'Magna Automotive India Pvt Ltd',
      'Nichirin Imperial Autoparts India Pvt Ltd',
      'Mirae Asset Capital Markets (India) Pvt Ltd',
      'Talakunchi Networks Pvt Ltd',
      'Sagility India Pvt Ltd',
      'Polyplex Corporation Ltd',
      'Happiest Minds Technologies Ltd',
      'United India Insurance Co Ltd',
      'Pingsafe India Pvt ltd',
      'HDFC Ltd',
      'Institute for Development and Research in Banking Technology',
      'Directorate of AFNET, Indian Air Force',
      'Indian AirForce',
      'Home Credit India Finance Pvt Ltd',
      'Bata India Ltd',
      'Vasta Bio-informatics Pvt Ltd',
      'Indian Energy Exchange Ltd',
      'Mindsprint Pte Ltd',
      'Adani Port & Special Economic Zone Ltd',
      'Indian Institute of Management',
      'Quick Heal Technologies Ltd',
      'Vellore Institute Of Technology',
      'National Highways Authority Of India',
      'Tata Power Delhi Distribution Ltd',
      'Ab Inbev Gcc Services India Pvt Ltd',
      'Big Tree Entertainment Pvt Ltd',
      'Schneider Electric Pvt Ltd',
      'Web Werks India Pvt Ltd',
      'Aditi Tech Consulting Pvt Ltd',
      'Avanse Financial Services Ltd',
      'CommScope Networks  India Pvt Ltd',
      'TNQ Book and Journals Pvt Ltd',
      'TAAL Tech India Pvt Ltd',
      'Databricks India Pvt Ltd',
      'Hero Corporate Services Pvt Ltd',
      'G Mobile Devices Pvt Ltd',
      'Airbus Group India Pvt Ltd',
      'SSP Pvt Ltd',
      'Lodha Group',
      'Simform Solutions Pvt Ltd',
      'GRI TOWERS INDIA PRIVATE LIMITED',
      'Integra Software Services Pvt Ltd',
      'Shriram Pistons and Rings Ltd',
      'ICICI SECURITIES LTD',
      'CAMS Pvt Ltd',
      'Emp claims Pvt Ltd',
      'Nasdaq Corporate Solutions (India) Pvt Ltd',
      'QE Securities LLP',
      'Damodar Valley Corporation Ltd',
      'Jaypee Greens Golf & Spa Resorts',
      'Bank of India Investment Managers Pvt Ltd',
      'Xoriant Solutions Pvt Ltd',
      'SMFG India Credit Co Ltd Formerly Fullerton India Credit',
      'IHB Ltd',
      'Ask Wealth Advisors Pvt Ltd',
      'Hinduja Global Solutions Healthcare Ltd C/O Sagility India Private Limited',
      'Coforge Business Process Solutions Pvt ltd',
      'Brookfeild Renewable Operating India Pvt Ltd',
      'Sheela Foam Pvt Ltd',
      'Elgi Ultra Industries Ltd',
      'Transport Corporation of India Ltd',
      'Vendasta technology india pvt ltd',
      'Tech Mahindra Business Services Ltd',
      'SEIL Energy India Ltd',
      'Yoganandh & Ram LLP',
      'Yoganandh and Ram - India',
      'Dynacons Systems & Solutions Ltd',
      'Tech Vikas Pvt Ltd',
      'My Home Industries Pvt Ltd',
      'Colorplast Systems Pvt Ltd',
      'Chaitanya Godavari Grameena Bank',
      'Ethiraj College for Women',
      'KSPG Automotive India Pvt Ltd',
      'Shree Additives Pharma and Foods Pvt Ltd',
      'Evergent Technologies Pvt Ltd',
      'Panjab University',
      'Kolkata Municipal Corporation',
      'BlueBear Technology Pvt Ltd',
      'Rossell Techsys',
      'Deltaphi Labs Pvt Ltd',
      'IDFC Asset Management Company Ltd',
      'Bank of Baroda RRB',
      'Quest Global Engineering Pvt Ltd',
      'The Assam Co-Operative Apex Bank Ltd',
      'PayU Finance India Pvt Ltd',
      'Krutrim SI Designs Pvt Ltd',
      'Ather energy Pvt Ltd',
      'Standardisation Testing and Quality Certification',
      'Exide Industries Ltd',
      'National Thermal Power Corporation Dadri',
      'Saraswat Co Operative Bank Ltd',
      'Jansamarth (OPL)',
      'Diligent Global Tech Consulting Pvt Ltd',
      'Jump Trading Financial India Pvt Ltd',
      'Vaibhav Global Ltd',
      'The Federal Bank Ltd',
      'AIG Hospitals',
      'Dell International Services India Pvt Ltd',
      'Ramraj Cotton',
      'Trianz Holdings Pvt Ltd',
      'Mahindra and Mahindra Ltd',
      'Praj Industries Ltd',
      'VVDN Technologies Pvt Ltd',
      'SSR Global Skills Park',
      'Vistaar Financial Services Pvt Ltd',
      'Sony India Pvt Ltd',
      'International Industrial Springs',
      'Policy Bazar Insurance Web Aggregator Pvt Ltd',
      'IFFCO-MC Crop Science Pvt Ltd',
      'Airowire Networks Pvt Ltd',
      'Asirvad Micro Finance Ltd',
      'Bluecloud Services Pvt Ltd',
      'Olam Information Services Pvt Ltd',
      'Mazagon Dock Shipbuilders Ltd',
      'Escorts Kubota Ltd',
      'Hindustan Ports Pvt Ltd',
      'Indiabulls Housing Finance Ltd',
      'Ministry of Defence',
      'Allcargo Logistics Ltd',
      'Kallappanna Awade  Ichalkaranji Janata Sahkari Bank LTD',
      'Aujas Cybersecurity Ltd',
      'National E-Governance Services Ltd',
      'Axis Finance Ltd',
      'Deltabulk Shipping India Pvt Ltd',
      'Arise IIP India Pvt Ltd',
      'One Mobikwik Systems Ltd',
      'kirloskar Industries Ltd',
      'National Capital Region Transport Corporation',
      'Anadrone Systems Pvt Ltd',
      'FPL Technologies Pvt Ltd',
      'Onwards technologies Pvt Ltd',
      'The Akola-Washim District Central Co-op. Bank Ltd',
      'Nemko India Pvt Ltd',
      'One97 Communications Ltd',
      'GMR Consulting Services Ltd',
      'Geojit Financial Services Ltd',
      'Shivtel Communications Pvt Ltd',
      'Numaligarh Refinery Ltd',
      'GMR Airports Ltd',
      'Interra Systems India Pvt Ltd',
      'Nurture Agtech Pvt Ltd',
      'Beckman Coulter India Pvt Ltd',
      'Carrier Media India Pvt Ltd',
      'Midea India Pvt Ltd',
      'Payu Payments Pvt Ltd',
      'International Institute for Population Sciences (IIPS)',
      'Loyalty Juggernaut India Pvt Ltd',
      'Razorpay Software Pvt Ltd',
      'Oil and Natural Gas Corporation Ltd',
      'Citius IT Solutions Pvt Ltd',
      'PNB MetLife India Insurance Co. Ltd',
      'Trianz Digital Consulting Pvt Ltd',
      'VAPT Consultants Pvt Ltd',
      'Shinhan Bank',
      'Choice Equity Broking Pvt Ltd',
      'SRM Technologies Pvt Ltd',
      'Hindustan Coca-Cola Beverages Pvt.',
      'EYO Solutions India LLP',
      'Department of Planning and Development',
      'PI Industries Ltd',
      'VY Labs Technologies Pvt Ltd',
      'Himachal Pradesh Technical University',
      'Christian Medical College',
      'JSW Steel Ltd',
      'Infor (India) Pvt Ltd',
      'K7 Computing Pvt Ltd',
      'Samsung India Electronics Pvt Ltd',
      'Army Cyber Group ACG',
      'Seshaasai Business Forms Pvt Ltd',
      'Rajanna Foundation',
      'Soffit Infrastructure Services Pvt Ltd',
      'Dilip Buildcon Ltd',
      'Concentrix BPO Pvt Ltd',
      'Scripbox Investment Advisors Pvt Ltd',
      'Indian Council of Agricultural Reserach',
      'Sophos Technologies Pvt Ltd',
      'Prime Focus Technologies Ltd',
      'Infopercept Consulting Pvt Ltd',
      'Aquity Solutions India Pvt Ltd',
      'Infoavana Technologies Pvt Ltd',
      'Panasonic Life Solutions India Pvt Ltd',
      'Ventura India Pvt Ltd',
      'CerebrumX Labs Pvt Ltd',
      'Tmen Systems Pvt Ltd',
      'Aerial Delivery Research and Development Establishment',
      'Hubli Dharwad BRTS Company Ltd',
      'Virsec Systems India Pvt Ltd',
      'Finolex Cables Ltd',
      'Eastman Auto & Power Ltd',
      'Monotype Solutions India Pvt Ltd',
      'Epimoney Pvt Ltd',
      'Government E Marketplace',
      'UVJ Technologies Pvt Ltd',
      'Techowl Infosec Pvt Ltd',
      'Esskay Compuservices Pvt Ltd',
      'Office of the Registrar General and Census Commissioner',
      'Sequretek IT Solutions Pvt Ltd',
      'HDFC Securities Ltd',
      'ABP Pvt Ltd',
      'Designtech Systems Pvt Ltd',
      'Kyndryl Solutions Pvt Ltd',
      'Macleods Pharmaceuticals Ltd',
      'The Oil and Natural Gas Corporation Ltd',
      'Financial Intelligence Unit-India',
      'HomeTech EC Solutions',
      'Bauer Equipment India Pvt Ltd',
      'Zifo Technologies Pvt Ltd',
      'Veeda Clinical Research Ltd',
      'S&A Law Offices',
      'Mobileum India Pvt Ltd',
      '3DCAD India Pvt ltd',
      'HOMAG India Pvt Ltd',
      'Minosha India Ltd',
      'SDG Software India Pvt Ltd',
      'M2p Solutions Pvt Ltd',
      'HIL Ltd',
      'Thyssenkrupp India Pvt Ltd',
      'iQuanti India Pvt Ltd',
      'Jhansi Smart City Ltd',
      'Sheela Foam Ltd',
      'Transunion Cibil Ltd',
      'Wibmo Inc',
      'Government of Bihar',
      'Informatica Business Solutions Pvt Ltd',
      'Straive',
      'Godrej & Boyce Mfg Co Ltd',
      'Sterlite Power Transmission Ltd',
      'Bureauid India Pvt Ltd',
      'GMMCO Ltd',
      'Bhubaneswar Smart City Ltd',
      'Culver Max Entertainment Pvt Ltd',
      '(n) Code Solutions',
      'Panacea Biotec Pharma Ltd',
      'Datafield India Pvt Ltd',
      'Julius Baer Wealth Advisors (India) Pvt Ltd',
      'Blue Star Ltd',
      'JK Tyres & Industries Ltd',
      'Factset Systems India Pvt Ltd',
      'Extrovis Pvt Ltd',
      'Zluri Technologies Pvt Ltd',
      'Sitel India Pvt Ltd',
      'Teacher Tools Pvt Ltd',
      'Tata Aig General Insurance Company Ltd',
      'Epicenter Technologies Pvt Ltd',
      'Sree VijayaVittala Computers',
      'Thyssenkrupp Industrial Solutions India',
      'SecurView Systems Pvt Ltd',
      'LanceSoft India Pvt Ltd',
      'Kolte Patil Developers Ltd',
      'Tata Business Excellence Group',
      'The Shamrao Vithal Co-Op Bank Ltd',
      'Kansai Nerolac Paint Ltd',
      'Cholayil Pvt Ltd',
      'Arthanari Loom Centre (Textile) Pvt Ltd',
      'TVS Training & Services Ltd',
      'TVS STAFFING SOLUTIONS',
      'Epiroc Mining India Ltd',
      'Grant Thornton India LLP',
      'Maulana Azad Medical College',
      'ESAF Microfinance and Investments Pvt Ltd',
      'C-Edge Technologies Ltd',
      'Indigrid Ltd',
      'Sobha Ltd',
      'Government of Tamil Nadu',
      'Sterling Software Pvt Ltd',
      'Orissa Gramin Bank',
      'Amrita Vishwa Vidyapeetham',
      'Paramount Health Services & Insurance Tpa Pvt Ltd',
      'The Executive Centre India Pvt Ltd',
      'GSPANN Technologies Inc',
      'Goodluck India Ltd',
      'Vodafone - IBM Global India',
      'Tirupati Smart City Corporation Ltd',
      'Bimal Auto Agency India Pvt Ltd',
      'AGS Transact Technologies Ltd',
      'DocTutorials Edutech Pvt Ltd',
      'Rallis India Ltd',
      'Terumo Penpol Pvt Ltd',
      'L&T Metro Rail hyderabad Ltd',
      'Royal Sundaram General Insurance Company Ltd',
      'Fyers Securities Pvt Ltd',
      'RiskBerg Consulting Pvt Ltd',
      'Regional Cancer Centre',
      'Oaknorth (India) Pvt Ltd',
      'Dialog Axiata Plc',
      'Freecharge Payment Technologies Pvt Ltd',
      'Caterpillar Signs Pvt Ltd',
      'The Saraswat Co-operative Bank Ltd',
      'ValueLabs LLP',
      'ASK Investment Managers Ltd',
      'Nexteer Automotive India Pvt Ltd',
      'Glowtouch Technologies Pvt Ltd',
      'Orissa MetaLinks Pvt Ltd',
      'Public Works Department',
      'Flexmoney Technologies Pvt Ltd',
      'ANZ Bank India',
      'Hyderabad Police',
      'Auriseg Consulting Pvt Ltd',
      'Secureinteli Technologies Pvt Ltd',
      'Dainik Jagran',
      'LSI India Research & Development Pvt Ltd',
      'Nexteer Automotive Pvt Ltd',
      'Dakshin Haryana Bijli Vitran Nigam',
      'Napino Auto & Electronics Ltd',
      'National Thermal Power Corporation Ltd EOC',
      'Resource Infrastructure Management (india) Pvt Ltd',
      'Royal Classic Mills Pvt Ltd',
      'Cybercube Services Pvt Ltd',
      'Bekaert Industries Pvt Ltd',
      'Tevel Cyber Corps Pvt Ltd',
      'Oriental Aromatics Ltd',
      'Jindal Steel and Power Ltd',
      'Imperium Solutions',
      'Nihilent Ltd',
      'CIMB AI LABS Pvt Ltd',
      'ANZ Support Services India Pvt Ltd',
      'Toyota Kirloskar Motor Pvt Ltd',
      'Everrenew Energy Pvt Ltd',
      'Yogi Developers Corporation',
      'Sacha Technologies',
      'Synergy Maritime Pvt Ltd',
      'Faridabad Smart City',
      'Cloud Nine Hospitalities Pvt Ltd',
      'Codec Networks Pvt Ltd',
      'The Hongkong and Shanghai Banking Corporation Ltd',
      'Wakefit Innovations Pvt Ltd',
      'Startek',
      'Shriram Chits Tamilnadu Pvt Ltd',
      'Chhattisgarh State Power Distribution Company Ltd',
      'Janalakshmi Financial Services Pvt Ltd',
      'Encora Innovation Labs India Pvt Ltd',
      'Times Internet Ltd',
      'IMA-PG India Pvt Ltd',
      'Stonehill Education Foundation',
      'Sundaram Business Services Pvt Ltd',
      'Information Technology Development Agency',
      'GlobalLogic India Pvt Ltd',
      'Crowdstrike India Pvt Ltd',
      'NJ India Invest Pvt Ltd',
      'GT Nexus Software Pvt Ltd',
      'Bangalore Electricity Supply Company Ltd',
      'Harrisons Malayalam Ltd',
      'Sandoz Pvt Ltd',
      'ABC Consultants Pvt Ltd',
      'Midevops Services Pvt Ltd',
      'Prime Infoserve Ltd',
      'Lapiz Digital Services',
      'Karix Mobile Pvt Ltd',
      'Radisys India Ltd',
      'Indium Software India Ltd',
      'Kochar Consultants Pvt Ltd',
      'American School of Bombay',
      'Bennett , Coleman & Co Ltd',
      'Reward360 Global Services Pvt Ltd',
      'Rockwell Collins (India) Enterprise Pvt Ltd',
      'McKinsey Global Capabilities and Services Pvt Ltd',
      'Indian Computer Emergency Response Team Cert-in',
      'Tokita Seed India Pvt Ltd',
      'The New India Assurance Company Ltd',
      'Enverus India Pvt Ltd',
      'India Cast Media Distribution Pvt Ltd',
      'AQM Technologies Pvt Ltd',
      'Great Eastern Retail Pvt Ltd',
      'NV Bekaert SA',
      'Masters India IT Solutions Pvt Ltd',
      'Inquest Technologies Software Pvt Ltd',
      'Sthirah India Pvt Ltd',
      'Mahanagar Gas Ltd',
      'Cert-In Indian Computer Emergency Response Team',
      'Icertis Solutions Pvt Ltd',
      'ONGC Tripura Power Company Ltd',
      'National Securities Depository Ltd',
      'Sudarshan Chemical Industries Ltd',
      'Ordnance Factory Board',
      'SOC Analyst Pvt Ltd',
      'Manipal Health Enterprises Pvt Ltd',
      'Spark Financial Holdings Pvt Ltd',
      'OM Logistics Ltd',
      'Deenanath Mangeshkar Hospital & Research Center',
      'IIFL Securities Ltd',
      'Army Computer Emergency Response Team India (Cert-In)',
      'ACL Mobile Pvt Ltd',
      'Spice Money Ltd',
      'Interglobe Technologies IN',
      'DB Corp Ltd',
      'Coffee Day Global Pvt Ltd',
      'Solarwinds India Pvt Ltd',
      'Finbox',
      'Mother Dairy India Ltd',
      'Cnlabs Test Services Pvt Ltd',
      'Army Computer Emergency Response Team',
      'West Bengal Electronics Industry Development Corporation Ltd',
      'National Housing Bank',
      'Presidio Information Risk Management LLP',
      'Gxx India Pvt Ltd',
      'Commeasure Solutions India Pvt Ltd',
      'Mirae Asset Global Index Pvt Ltd',
      'Infinera India Pvt Ltd',
      'Chella Software Pvt Ltd',
      'The Tata Power Company Ltd',
      'Kankaria Maninagar Nagrik Sahakari Bank Ltd',
      'Avighna Systems Pvt Ltd',
      'Nikon India Pvt Ltd',
      'KGISL Technologies Pvt Ltd',
      'Surveysparrow Pvt Ltd',
      'Karunya Institute of Technology and Sciences',
      'Medtronic Engineering And Innovation Center Pvt Ltd',
      'Inter Gold India Pvt Ltd',
      'Bengaluru International Airport Ltd',
      'Punjab & Sind Bank CISO Cell',
      'Orient Technologies Ltd',
      'Edelweiss Business Services Ltd',
      'RMSI Pvt Ltd',
      'JSW Steels Pvt Ltd',
      'RPSG SPORTS PVT LTD',
      'Council Of Scientific & Industrial Research',
      'Sardar Vallabhbhai Sahakari Bank Ltd',
      'Benchmark Broadcast Systems',
      'Cavinkare Pvt Ltd',
      'Navi Technologies Pvt Ltd',
      'Shri Gorakhnath Mandir',
      'Hitachi Solutions India Pvt Ltd',
      'HealthAsyst Pvt Ltd',
      'AppViewX Pvt Ltd',
      'ICRA Analytics Ltd',
      'Suryoday Small Finance Bank Ltd',
      'National Informatics Centre Service Inc',
      'TVS Credit Services Ltd',
      'NTT Global DC & CI India Pvt Ltd',
      'NCDEX',
      'Janatics India Pvt Ltd',
      'Aurionpro Solutions Ltd',
      'Virtuous Transactional Analytics Pvt Ltd',
      'Aegon Life Insurance Company Ltd',
      'Airtel Digital Ltd',
      'PVH Arvind Fashion Pvt Ltd',
      'Beroe Consulting India Pvt Ltd',
      'The Comptroller and Auditor General of India',
      'Simon & Schuster Publishers India Pvt Ltd',
      'TLG India Pvt Ltd',
      'Zensar Technologies Ltd',
      'Brother Machinery India Pvt Ltd',
      'Shriram Finance Ltd',
      'JK Cement Ltd',
      'CG Power and Industrial Solutions Ltd',
      'Bhartiya Rail Bijlee Company Ltd',
      'Navin Fluorine International Ltd',
      'Bharat Forge Ltd',
      'Indian Potash Ltd',
      'Avenue Supermarts Ltd',
      'HDFC ERGO General Insurance Company Ltd',
      'Verizon Data Services India Pvt Ltd',
      'Agra Smart City Ltd',
      'Skillmine Technology Consulting Pvt Ltd',
      'Wipro Technologies',
      'Puravankara Projects Ltd',
      'Quest Global Engineering Services Pvt Lt',
      'Teamlease Digital Pvt Ltd',
      'Quess Corp Ltd',
      'DH Healthcare Software Services India Pvt Ltd',
      'Arihant Capital Markets Ltd',
      'Elgi Equipments Ltd',
      'National Institute of Electronics & Information Technology',
      'Shubham Housing Development Finance Comp',
      'Equentia SCF Technologies Pvt Ltd',
      'Alorica India Pvt Ltd',
      'Cloud4C Services Pvt Ltd',
      'Kfin Technologies Pvt Ltd',
      'Uttar Pradesh Power Corporation Ltd',
      'Hyundai Autoever India Pvt Ltd',
      'Sun Pharmaceutical Industries Ltd',
      'ISGEC SFW Boilers Pvt Ltd',
      'Evren Energys Pvt Ltd',
      'National Insurance Company Ltd',
      'Adorit IT Services Pvt Ltd',
      'UPL Ltd',
      'Cholamandalam General Insurance Company Ltd',
      'IGT Solution Pvt Ltd',
      'Mobicule Technologies Pvt Ltd',
      'TP Western Odisha Distribution Ltd',
      'Directorate of Forensic Science Laboratory',
      'Assam Power Distribution Company Ltd',
      'Glenmark Pharmaceuticals Ltd',
      'Clarista Inc',
      'Precision Plastic Industries Pvt Ltd',
      'PricewaterhouseCoopers Services LLP',
      'Holy Spirit Hospital',
      'Public Financial Management System PFMS',
      'Juniper Green Energy Pvt Ltd',
      'Crest Digitel Pvt Ltd',
      'Signzy Technologies Pvt Ltd',
      'KG Information Systems Pvt Ltd',
      'Kemwell Biopharma Pvt Ltd',
      'Muzaffarpur Smart City Ltd',
      'Manipal Technologies Ltd',
      'Sri Lanka Telecom Plc',
      'Merck Foundation',
      'Bangladesh Export Import Co. Ltd',
      'Sri Lanka Insurance Corporation',
      'AB Bank Ltd',
      'John Keells Holdings PLC',
      'Micro Focus Software India Pvt Ltd',
      'ByTechnical co Ltd',
      'Trafigura PTE Ltd',
      'ELP Aviation Software',
      'Smp Automotive Systems',
      'SMP Deutschland GmbH',
      'Agriculture Development Bank Ltd',
      'Piramal Healthcare Canada Ltd',
      'TVS Auto Bangladesh Ltd',
      'iGATE Global Solutions Pvt Ltd',
      'WNS North America Inc',
      'Nepal Army',
      'BRAC EPL Stock Brokerage Ltd',
      'SMP Automotive Interior Modules d.o.o. Ćuprija',
      'Refinitiv India Pvt Ltd',
      'Bangladesh Export Processing Zone Author',
      'Kamana Sewa Bikas Bank Ltd.',
      'Lumbini Bikas Bank Ltd',
      'TMF Group B V',
      'Dubai Islamic Bank',
      'LSEG Business Services Ltd',
      'Cargills Bank Ltd',
      'Mobitel Pvt Ltd',
      'Sequoia Capital India Operations II LLC',
      'Himalayan Bank Ltd',
      'Jifflenow',
      'Central Procurement Technical Unit',
      'T Mobile USA Inc',
      'Bechtel India Pvt Ltd',
      'Sampath Bank Plc',
      'Toll Bangladesh Ltd',
      'Egon Zehnder International Pvt Ltd',
      'Electoral Commission of South Africa (IEC)',
      'Shangri-LA Development Bank Ltd',
      'Symphony EYC India Pvt Ltd',
      'Onebill Software India Pvt Ltd',
      'Bangladesh Army',
      'Amicorp Holding Ltd',
      'N-Able Private Limited',
      'National Development Bank',
      'Mobileum Inc',
      'Laxmi Sunrise Bank Ltd',
      'BRAC Bank Ltd',
      'Ooredoo Maldives Public Ltd Company',
      'NetObjex India Pvt Ltd',
      'Aurora RCM',
      'Modhumoti Bank Ltd',
      'Mahalaxmi Bikas Bank  Ltd',
      'United Commercial Bank Ltd',
      'Nokia Solutions and Networks India Pvt Ltd',
      'IOPEX Technologies, Inc',
      'Commercial Bank of Ceylon PLC',
      'HCL America Inc',
      'Dhivehi Raajjeyge Gulhun PLC',
      'Accord Healthcare Ltd',
      'GSMData Tech Pvt Ltd',
      'First Security Islami Bank Ltd',
      'Brisca Management Services',
      'Al-Arafah Islami Bank Ltd',
      'Akij Venture Ltd',
      'Hewlett Packard India',
      'Amdocs Development Centre India LLP',
      'Artech LLC',
      'Kavis Pharma LLC',
      'Artech Technology Canada Ltd',
      'Laxmi Capital Market Ltd',
      'Nepal SBI Bank Ltd',
      'Incessant Rain Pvt. Ltd.',
      'Sprinklr India Pvt Ltd',
      'Autnhive Pvt Ltd',
      'Splash Business Intelligence Inc',
      'Mavenir Systems Inc',
      'Concentrix Services US Inc',
      'Equantum Pvt ltd',
      'Max Card Co Ltd',
      'Geo Data Tech Llc',
      'Cyfuture India Pvt Ltd',
      'Jndal India Thermal Power Ltd',
      'Machhapuchchhre Bank Ltd',
      'Nepal Infrastructure Bank Ltd',
      'eSewa Pvt Ltd',
      'NAGAD Ltd',
      'Startek Australia Pty Ltd',
      'Oriental Consultants Global Co. Ltd.',
      'Unit Co.,Ltd',
      'Express Systems Ltd',
      'Grameenphone Ltd',
      'Original Apparel Pvt Ltd',
      'Telecom Regulatory Commission of Sri Lan',
      'Islami Bank Bangladesh Limited',
      'V S Information Systems (Pvt) Ltd',
      'Abb Power Technology Services Pvt Ltd',
      'Surya Foods',
      'UXCam Inc',
      'NIC ASIA Bank Ltd',
      'NMB Bank Ltd',
      'Shiddharth Bank Ltd',
      'Evercare Hospital Dhaka',
      'Medi Help Hospital',
      'Jyoti Bikash Bank Nepal Ltd',
      'Midland Bank Limited',
      'TCS e-Serve International Ltd',
      'PT Astra Otoparts Tbk',
      'Perfetti Van Melle India Pvt Ltd',
      'HSBC Bangladesh',
      'Concentrix Solutions Corporation',
      'Welspun UK Ltd',
      'Epyllion Group Ltd',
      'LRN Technology and Content Solutions India Pvt Ltd',
      'SecurityHQ',
      'Sonata Software Ltd',
      'Laurus Labs Ltd',
      'FonePay',
      'FLAG Atlantic UK Ltd',
      'Lanka Communication Services Pvt Ltd',
      'Cloud Himalaya',
      'Global Rubber Industries Pvt Ltd',
      'New Asia Group',
      'One Bank Ltd',
      'HCL Technologies Sweden AB',
      'Wipro Consumer Care & Lighting',
      'JAT Holdings PLC',
      'Silabs India Pvt Ltd',
      'Adtran Networks India Pvt Ltd',
      'Lanka Garment Mfg Co pvt Ltd',
      'Antler Holdings Pvt Ltd',
      'Associated Motorways Pvt Ltd',
      'Central Depository Bangladesh Ltd',
      'Oxiqa Pvt Ltd',
      'Department Of Information Technology & Telecom',
      'City Brokerage Ltd',
      'Ministry of Land Management',
      'IDC Frontier Inc.',
      'Nepal Telecom',
      'Mphasis Corporation USA',
      'Commercial Insurance Brokers Pvt Ltd',
      'Mercantile Investment PLC',
      'Rwanda Information Society Authority',
      'SGS Moçambique, LDA',
      'SGS MCNet Macambique, Lda',
      'Uganda Development Bank Ltd',
      'Maharashtra Industrial Development Corporation',
      'Infosys BPM Ltd',
      'Psg Institute Of Medical Sciences & Research',
      'Municipal Administration Department of Government of Andhra Pradesh',
      'Computer Security Incident Response Team Power Sector (CSIRT- Power)',
      'Puma India Pvt Ltd',
      'North Bihar Power Distribution Company Ltd',
      'Alembic Pharmaceuticals Ltd',
      'National Informatics Centre',
      'Central Board of Direct Taxes',
      'RSG Media Systems Pvt Ltd',
      'Akums Drugs & Pharmaceuticals Ltd',
      'Shriram Veritech Solutions Pvt Ltd',
      'Powergrid Teleservices Ltd',
      'National Internet Exchange of India (NIXI)',
      'Madhya Pradesh Police Telecom',
      'Ageas Federal Life Insurance Co Ltd',
      'Controller General of Defence Account',
      'High Court of Madhya Pradesh',
      'Indian Bank Cooperative Urban Bank Ltd',
      'Tata Electronics Systems Solutions Pvt Ltd',
      'Garagepreneurs Internet Pvt Ltd',
      'Yash Highvoltage Ltd',
      'Paperchase Accountancy india Pvt Ltd',
      'Meril Life Sciences Pvt Ltd',
      'Britannia Industries Ltd',
      'Bhutan Telecom Ltd',
      'Knowcraft Analytics Pvt Ltd',
      'Controller of Certifying Authorities in India (CCA)',
      'Ambuja Neotia Heathcare Venuure Ltd',
      'Guiltfree Industries Ltd',
      'Elite Computers',
      'ArcelorMittal Nippon Steel India Ltd',
      'Conneqt Business Solutions Ltd',
      'Mandke Foundation',
      'Briskinfosec Technology And Consulting Pvt Ltd',
      'Herbolab India Pvt Ltd',
      'VVF Life Science South Africa (PTY) Ltd',
      'TeamLease HRTech Ltd',
      'Boeing International Corporation India Pvt Ltd',
      'JK Lakshmi Cement Ltd',
      'The Kumbakonam Mutual Benefit Fund Ltd',
      'Passport E Seva',
      'Atlassian India LLP',
      'Orchid Pharma Ltd',
      'Outsourcepartners International Pvt ltd',
      'Open Media Network Pvt Ltd',
      'Business Media Pvt Ltd',
      'Innovaccer Analytics Pvt Ltd',
      'Institute for Meditation and Inner Harmony',
      'The Udaipur Mahila Samridhi Urban Co-op Bank Ltd',
      'Digitral Pvt Ltd',
      'Kerala Vision Digital TV',
      'Bmm Ispat Ltd',
      'PharmNXT Biotech LLP',
      'CMR Green Technologies Ltd',
      'B9 Beverages Pvt. Ltd',
      'Apna Jobs',
      'TVS Supply Chain Solutions Ltd',
      'Qualys Security Tech Services Pvt Ltd',
      'Ushur Technologies Pvt Ltd',
      'Jayapriya Chit Funds Pvt Ltd',
      'Cito Infotech Pvt Ltd',
      'LG Electronics India Pvt Ltd',
      'Nirma Vidyavihar',
      'Office of the Chief Commissioner of Commercial Tax',
      'Apricot Foods Pvt Ltd',
      'Nikshan Electronics',
      'AXA Business Services Pvt Ltd',
      'L&T Finance Holding Ltd',
      'QRC Consulting & Solutions Pvt ltd',
      'Aker Powergas Pvt Ltd',
      'Inshorts',
      'Neysa Networks Pvt Ltd',
      'Optum Global Solutions Pvt Ltd',
      'Indus Infotech Pvt Ltd',
      'Electronics and Radar Development Establishment',
      'Comtel Services Pvt Ltd',
      'Biofourmis India Pvt Ltd',
      'ITC Ltd FBD-Division',
      'CG Logistics Pvt Ltd',
      'SARG Global Digital Pvt Ltd',
      'World Health Organization',
      'Pon Pure Chemical India Pvt Ltd',
      'Alepo Technologies Pvt Ltd',
      'Headquarter Integrated Defence Staff',
      'Cricheroes Pvt Ltd',
      'Hinduja Leyland Finance Ltd',
      'Younion Focused Marketing Services Pvt Ltd',
      'apollo247',
      'Torus Digital Pvt Ltd',
      'Slice',
      'Electro Mechanical Company LLC',
      'Blue Star Engineering & Electronics Ltd',
      'Sentient Intelligence',
      'KPI Green Energy Ltd',
      'Corrz Technosolutions Pvt Ltd',
      'Analog Port Pvt Ltd',
      'TeamLease Regtech Pvt Ltd',
      'Accorian',
      'One Kosmos Marketing services Pvt Ltd',
      'Starnext Innovations Pvt Ltd',
      'Ascent Consulting Services Pvt Ltd',
      'Sunrise Sports (I) Pvt Ltd',
      'Nopal Support Services Pvt Ltd',
      'Girnar Insurance Brokers Pvt Ltd',
      'Varni Labs Pte Ltd',
      'Greater Than Educational Technologies Pvt Ltd',
      'Profectus Capital Pvt Ltd',
      'Yalamanchili Software Exports Pvt Ltd',
      'The Udaipur Mahila Urban  Co.op Bank Ltd',
      'Serv Cloud Business Solutions Llp',
      'Zoho Corporation Pvt Ltd',
      'Lifecell International Pvt Ltd',
      'Ashapura Aromas Pvt Ltd',
      'Lindner India Construction Pvt Ltd',
      'Punjab National Bank eOBC',
      'Haridwar Medical College',
      'Wanbury Ltd',
      'Speed Sign Technologies Pvt Ltd',
      'Uno Minda Ltd',
      'Paharpur Cooling Towers Ltd',
      'Jaslok Hospital & Research Centre',
      'Webel Technology Ltd',
      'Directorate of Information Technology Electronics and Communications (DITEC)',
      'Haldia Petrochemicals Ltd',
      'Webhelp India Pvt Ltd',
      'Ramkrishna Forgings Ltd',
      'National University of Advanced Legal Studies',
      'Government  Guest House Samsstipur',
      'Care Health Insurance Ltd (CHIL',
      'Cyberion Labs',
      'Tessolve Semiconductor Pvt Ltd',
      'cloud Dfn LLP',
      'Capgemini India Pvt Ltd',
      'Garuda Power Pvt Ltd',
      'Larsen & Toubro, Heavy Engineering',
      'Sparksupport Infotech Pvt Ltd',
      'KornFerry International Pvt Ltd',
      'CyberNxt Solutions LLP',
      'Variety Info Solutions Pvt Ltd',
      'Chakra Biztech Solutions Pvt Ltd',
      'Envision Financial Systems India Pvt Ltd',
      'Rapido',
      'Heritage Novandie Foods Pvt Ltd',
      'Corps3 Infosoft (OPC) Pvt Ltd',
      'Puducherry e-Governance Society',
      'Hitachi Systems India Pvt Ltd',
      'Sundaram Infotech Solutions',
      'Nutan Nagarik Sahakari Bank Ltd',
      'Idemia India Pty Ltd',
      'Omnenest Technologies Pvt Ltd',
      'Workday India Pvt Ltd',
      'Advanced Sys-tek Pvt Ltd',
      'Agilisium Consulting India Pvt Ltd',
      'Centre for Advanced Systems',
      'Renew Now Solutions India Pvt Ltd',
      'Arvind Fashion Ltd',
      'Turbo Energy Pvt Ltd',
      'Polyplastics Industries India Pvt Ltd',
      'Andhra Pradesh Central Power Distributio',
      'Playsimple Games Pvt Ltd',
      'Infocepts Technologies Pvt Ltd (UNIT-III)',
      'SBI Capital Securities',
      'Kerala Commercial Tax Department',
      'Supreme Court of India',
      'Musigma Business Solutions Pvt Ltd',
      'Hewlett Packard Enterprise Globalsoft Pvt Ltd',
      'Dr. Reddy Institute Of Life Science',
      'Atlan Technologies Pvt Ltd',
      'HT Media Ltd',
      'Unity Small Finance Bank Ltd',
      'Nuclear Fuel Complex',
      'ReNew Power Pvt Ltd',
      'Evoke Technologies',
      'Bluechip Insurance Broking Pvt Ltd',
      'Team Vertex Cosmos Pvt Ltd',
      'Streamline healthcare solutions Pvt Ltd',
      'Nxtra Data Ltd',
      'National Thermal Power Corporation Sipat',
      'Exotel Techcom  Pvt Ltd',
      'Sfo Technologies Pvt Ltd',
      'The United Nilgiri Tea Estates Company Ltd',
      'Cashgrail Pvt Ltd Zupee',
      'Saravana stores (Tex)',
      'Rosmerta Technologies Ltd',
      'IBDIC Pvt Ltd',
      'Dhanalaxmi Bank Ltd',
      'Bitkuber Investments Pvt Ltd',
      'Rockstar Games India',
      'Department of Information Technology',
      'Valuefirst Digital Media Pvt Ltd',
      'Sundram Fasteners Ltd',
      'Somany Ceramics Ltd',
      'Ace Tech Sys Pvt Ltd',
      'Manappuram Asset Finance Ltd',
      'Cocoblu Retail Ltd',
      'IDBI Intech Ltd',
      'Haier Appliances (India) Pvt. Ltd.',
      'Inspira Enterprise India Ltd',
      'Heritage Foods Limited.',
      'Trading Technologies India Pvt Ltd',
      'Cashfree Payments India Pvt Ltd',
      'Hyundai Motors India Limited',
      'Sub-k Impact Solutions Ltd',
      'Quinnox Consultancy Services Ltd',
      'Blackstraw AI',
      'Payoda Technologies Pvt Ltd',
      'Shaurya Technosoft Pvt Ltd',
      'Captronic Systems Pvt Ltd',
      'Ample Technologies Pvt Ltd',
      'Institute Of Management Technology',
      'Premier Energies Ltd',
      'Microland Ltd',
      'Blue Chip Computer Consultant Pvt Ltd',
      'Chronus Software (India) Private Limited',
      'Ebix Technologies Pvt Ltd',
      'MetaMorphoSys Technologies Pvt Ltd',
      'Nagata India Pvt Ltd',
      'Hinduja Tech Ltd',
      'The Daily Thanthi',
      'A.Treds Ltd',
      'Metalman Auto Pvt Ltd',
      'Softura Pvt Ltd',
      'Resiplex Hospitality & Devlopers Pvt Ltd',
      'Commercial Tax Department',
      'Damodar Valley Corporation',
      'Acute Informatics Pvt Ltd',
      'Spx Flow Technology (india) Pvt Ltd',
      'KP Energy Limited ',
      'Digitap ai Enterprise Solutions Pvt Ltd',
      'The American International School',
      'Vega pay technology Pvt Ltd',
      'Aizant Drug Research Solutions Pvt Ltd',
      'Elucidata Data Consulting Pvt Ltd',
      'Evalueserve.com Pvt Ltd',
      'Oberoi Group',
      'Kavayahcloud Pvt Ltd',
      'Man Industries (India) Ltd',
      'MaxVal IP Services Pvt Ltd',
      'CloudFence Technologies OPC Pvt Ltd',
      'Neilsoft Pvt Ltd',
      'Bank of America Na',
      'Dataweave Software Pvt Ltd',
      'Accion Technologies Pvt Ltd',
      'Paschimanchal Vidyut Vitran Nigam',
      'Open Financial Technologies Pvt Ltd',
      'Gnr Solutions Pvt Ltd',
      'Mashreq Bank PSC',
      'Kutch Copper Ltd',
      'Kent',
      'Eversana India Pvt Ltd',
      'Porter (SmartShift Logistics Solutions Pvt Ltd)',
      'Vardhman Textiles Ltd',
      'Parle Agro Pvt Ltd',
      'Greenko Energy Projects Pvt Ltd',
      'Rajkot Nagarik Sahakari Bank Ltd',
      'Cherrylabs Technology Pvt Ltd',
      'Fareportal India Pvt Ltd',
      'ITI Asset Management Ltd',
      'Procdna Analytics Pvt Ltd',
      'Bnp Paribas India Solution Pvt Ltd',
      'Goodrich Aerospace Services Pvt Ltd',
      'Music Broadcast Ltd',
      'Mswipe Technologies Pvt Ltd',
      'Cadence Design Systems India Pvt Ltd',
      'MFilterIt',
      'Capita India Pvt Ltd',
      'Cyberleap India Pvt Ltd',
      'Ministry of Rural Development',
      'Worldline India Pvt Ltd',
      'Voltas Ltd',
      'Basilic Fly Studio Pvt Ltd',
      'Aistra Lab Inc',
      'Electronics and corporation of India Ltd',
      'Toshiba JSW Power Systems Pvt Ltd',
      'UNM Foundation',
      'Electronics And Information Techno logy Department',
      'Comnet Solutions Pvt Ltd',
      'Opsio Pvt Ltd',
      'Logicoy Software Technologies Pvt Ltd',
      'Housing and Urban Development Corporation Ltd',
      'Tinkas Industries Pvt Ltd',
      'Bloo Systems Inc',
      'Tanla Platforms Ltd',
      'Varanasi Multi-Modal Terminal',
      'Samsung R&D Institute India Bangalore Pvt Ltd',
      'Lemnisk Pte Ltd',
      'ICE Data Services India Pvt Ltd',
      'Hind Terminals Pvt Ltd',
      'LearningMate Solutions Pvt Ltd',
      'Comcast India Engineering Center I Llp',
      'Vedanta Ltd Alumina Plant Lanjigarh',
      'NYK Auto Logistics India Pvt Ltd',
      'KPMG Global Service Pvt Ltd',
      'Wellsky India Pvt Ltd',
      'Reservation Data Maintenance India Pvt Ltd',
      'Sakra World Hospital',
      'Hitachi Systems Micro Clinic Pvt Ltd',
      'Tirth Agro Technology Pvt Ltd',
      'Star India Pvt Ltd',
      'Bank of America',
      'PWD Haryana',
      'Bhartiya Urban Pvt Ltd',
      'Rela Hospitals Pvt Ltd',
      'Ushodaya Enterprises Pvt Ltd',
      'Unique Performance Techsoft Pvt Ltd',
      'United Consultancy Services Pvt Ltd',
      'DTDC Express Ltd',
      'Grid Controller of India Ltd',
      'Aptara Inc -Techbooks International Pvt Ltd',
      'HSBC Electronic Data Processing India Pvt Ltd',
      'Hongkong and Shanghai Banking Corporation Ltd',
      'Bonfiglioli Transmissions Pvt Ltd',
      'Saison Omni India Pvt Ltd',
      'Mumbai Bank',
      'Pitchers Internet Pvt Ltd',
      'Osource Global Pvt Ltd',
      'Orbicular Pharmaceutical Technologies Pvt Ltd',
      'SHL india Pvt Ltd',
      'Milky Mist Dairy Food Pvt Ltd',
      'Uniparts India Ltd',
      'Oasis Smart Sim',
      'Granules India Ltd',
      'Infogain India Pvt Ltd',
      'First Energy Pvt Ltd',
      'Ivy Mobility Solutions Pvt Ltd',
      'Upstox India',
      'Cadence Design System India Pvt Ltd',
      'Suven Pharmaceuticals Ltd',
      'Sarvagram',
      'NMDC Data Centre Pvt Ltd',
      'H & R Block India Pvt Ltd',
      'Intime Solutions',
      'NLC India Ltd',
      'Gumlet Technologies Pvt Ltd',
      'Celestica India Pvt Ltd',
      'Flexiloans Technologies Pvt Ltd',
      'Sun Knowledge Pvt Ltd',
      'Transaction Solutions International (India) Pvt Ltd',
      'Hughes Systique Pvt Ltd',
      'Alpha Design Technologies Pvt Ltd',
      'U P State Disaster Management Authority',
      'Tata Teleservices Ltd',
      'Tata Memorial Center',
      'Exl Service.com (I) Pvt Ltd',
      'Confederation of Indian Industry',
      'ICAR-- Indian Institute of Maize Research',
      'Sardonyx Technologies Pvt Ltd',
      'Gebbs Healthcare Solutions Pvt Ltd',
      'First Data India Pvt Ltd',
      'Secure Meters Ltd',
      'Council For The ISC Examinations',
      'Barclays Global Service Centre Pvt Ltd',
      'AntStack Technologies Pvt Ltd',
      'Shiv Nadar Institution of Eminence',
      'Government of Odisha',
      'Lighthouse Canton India',
      'Probo Media Technologies Pvt Ltd',
      'Acktron Security System Pvt Ltd',
      'RR Donnelley India Outsource Pvt Ltd',
      'Woodlands Multispeciality Hospital Ltd',
      'Invisia BPO Solutions  Pvt Ltd',
      '5X Data India Pvt Ltd',
      'Cartel Infosystems Pvt Ltd',
      'TV Today Network Ltd',
      'One Kosmos Inc',
      'Toyota Boshoku Automotive India Pvt Ltd',
      'Ambattur Fashion India Pvt Ltd',
      'CRIS - Central Railway Information',
      '24-7 Intouch India Pvt Ltd',
      'Zscaler Softech India Pvt Ltd',
      'Call Health Services Pvt Ltd',
      'Squadrun Solutions Pvt Ltd',
      'U.S. Library of Congress',
      'Machbizz Marketers Pvt Ltd',
      'Trillium It Solutions Pvt Ltd',
      'India International Centre',
      'Computer Generated Solutions India Pvt Ltd',
      'Socomec Innovative Power Solutions Pvt Ltd',
      'Cytel Statistical Software & Services Pvt Ltd',
      'Cybertech Systems & Software Ltd',
      'Smartshift Technologies Pvt Ltd',
      'Pocket Aces Pictures Pvt Ltd',
      'Truspeq Consulting Pvt Ltd',
      'Affinity Global Advertising Pvt Ltd',
      'Radico Khaitan Ltd',
      'Axis Capital Ltd',
      'Greenwich Metals India Pvt Ltd',
      'S.Chand and Company Ltd',
      'All India Institute Of Speech & Hearing',
      'Aditya Birla Capital Digital Ltd',
      'Synergy Technology Services Pvt Ltd',
      'Lattice Semiconductor (India) Pvt Ltd',
      'Novamesh Ltd',
      'Balkrishna Industries Ltd',
      'Crimson Interactive Pvt Ltd',
      'Indian Security & Fire Safety',
      'Quadrasystems.net (India) Pvt Ltd',
      'Jindal Power Ltd',
      'Healthnet Global Ltd',
      'Digital Age Strategies Pvt Ltd',
      'Allied Blenders And Distillers Ltd',
      'The Saurashtra Co Operative Bank Ltd',
      'STAR Hospitals',
      'Faridabad Metropolitan Development Authority',
      'Cci Systems Pvt Ltd',
      'BA Continuum India Pvt Ltd',
      'Toro Technology Center India',
      'Advantum Health Pvt Ltd',
      'Jammu & Kashmir Bank',
      'Comphealthcare',
      'Girnar Software Pvt Ltd',
      'Ministry of Power',
      'Nutrifresh Farm Tech India Pvt Ltd',
      'Hindustan Zinc Ltd',
      'Advance Valves Global LLP',
      'DataguardNXT India Pvt Ltd',
      'High Court of Judicature at Telangana',
      'Eventus TechSol Pvt Ltd',
      'Aditya Birla Money Ltd',
      'Butterfly Gandhimathi Appliances Ltd',
      'Action Construction Equipment Ltd (Unit-II)',
      'Plasser India Pvt Ltd',
      'KEC International Ltd',
      'Prodapt Solutions Pvt Ltd',
      'Manastu Space Technologies Pvt Ltd',
      'Novopor Advanced Science Pvt Ltd',
      'Dharampal Satyapal Ltd',
      'Skylark Information Technologies Pvt Ltd',
      'Needle Industries (India) Pvt Ltd',
      'Axis Securities Ltd',
      'Fab Hotels Pvt Ltd',
      'IIFL Finance Ltd',
      'Samsung C&T India Pvt Ltd',
      'Medanta',
      'Mathrubhumi Printing And Publishing Co Ltd',
      'Brihanmumbai Municipal Corporation',
      'LinkedIn',
      'Dedicated Freight Corridor Corporation of India Ltd',
      'HQ Eastern Command',
      'Pernod Ricard India Pvt Ltd',
      'Quantaco IT India Pvt Ltd',
      'Maharashtra Gramin Bank',
      'Ruckus Wireless Pvt Ltd',
      'Haoda Payment Solutions Pvt Ltd',
      'KIMS Nagercoil Institute Of Medical Sciences Pvt Ltd',
      'Chhaya Prakashani Ltd',
      'Worldline ePayments India Pvt Ltd',
      'seeds fincap pvt Ltd',
      'Netxcell Ltd',
      'DBS Bank India Ltd',
      'Expleo Solutions Ltd',
      'Cygnet Infotech Pvt Ltd',
      'Uttar Pradesh Development Systems Corporation Ltd',
      'Techspire Services Pvt Ltd',
      'Ampcus Cyber India Pvt Ltd',
      'Shramjivi Nagari Sahakari Society',
      'Codeblaze Solutions Pvt Ltd',
      'Telangana State Cyber Security Bureau (TSCSB)',
      'Tredence Analytics Solutions Pvt Ltd',
      'The Math Company Pvt Ltd',
      'Tata Elxsi Ltd',
      'One Mobikwik Systems Pvt Ltd',
      'Svava Technologies India Pvt Ltd (Syfe)',
      'Bharat Serums And Vaccines Ltd',
      'Audix Technologies',
      'Techflu Global Services Pvt Ltd',
      'National Commodity Clearing Ltd',
      'KPMG Advisory Services Pvt Ltd',
      'Public Works Directorate, Government Of West Bengal',
      'National Remote Sensing Centre Shadnagar',
      'Rain Industries Ltd',
      'TTEC India Customer Solutions Pvt Ltd',
      'Galaxy Health and Allied Insurance Company Ltd',
      'Jupiter Life Line Hospital',
      'Andhra Pradesh Mahesh Co-op Urban Bank Ltd',
      'EXIM Bank',
      'Northern Arc Capital Ltd',
      'Government of India',
      'Olam Agri Business services India Pvt Ltd',
      'Sant Nirankari Charitable Foundatio (SNCF)',
      'MarketXpander Services Pvt Ltd',
      'Suguna Foods Pvt Ltd',
      'Standard Chartered Bank Singapore',
      'Amdocs India Ltd',
      'Shapoorji Pallonji and Company Pvt Ltd',
      'Mentor Systems',
      'Anand Rathi Global Finance Ltd',
      'M3M india Pvt Ltd',
      'Anand Rathi Share & Stock Brokers Ltd',
      'Anand Rathi IT Pvt Ltd',
      'Anand Rathi Financial Services Ltd',
      'Anand Rathi International Ventures (IFSC) Pvt Ltd',
      'Anand Rathi Wealth Ltd',
      'Anand Rathi Advisors Ltd',
      'Anand Rathi Insurance Brokers Ltd',
      'AR Digital Wealth Pvt Ltd',
      'Freedom Intermediary Infrastructure Pvt Ltd',
      'LXME Money Pvt Ltd',
      'Ankit Infosys',
      'Banaras Hindu University',
      'Fedbank Financial Services Ltd',
      'Essar Steel India Ltd',
      'Atomx Corporation Pvt Ltd',
      'Red Elk Studios Pvt Ltd',
      'Stawerk Solutions Pvt Ltd',
      'Networkcity Innovations Pvt Ltd',
      'Variable Energy Cyclotron Centre',
      'META INFOTECH PRIVATE LIMITED',
      'BPO Integra India Pvt Ltd',
      'Moder Solutions India Pvt Ltd',
      'Coinbase India Services Pvt Ltd',
      'CDCX Technologies Pvt Ltd',
      'Indian Computer Emergency Response (Cert-In)',
      'Harman Finochem Ltd',
      'Synaptics India Pvt Ltd',
      'Aequs Pvt Ltd',
      'Venkateshwar Hospital',
      'SK Finance Ltd',
      'Korn Ferry',
      'Finova Technologies Pvt Ltd',
      'Belstar Microfinance Ltd',
      'GSM Outdoors LLC',
      'Yamaha Motor Solutions India Pvt Ltd',
      'PWW Distribution India Pvt Ltd',
      'Madiba Global Solutions Pvt Ltd',
      'Surya Financial Technologies Pvt Ltd',
      'Shapoorji Pallonji Co Ltd',
      'Tech Elecon Private Limited',
      'Velsera (PierianDx India Pvt Ltd)',
      'IQOR Global Services India Pvt Ltd',
      'Acidaes Solutions Pvt Ltd',
      'Healthedge Technologies India Pvt Ltd',
      'Stellar Innovations Pvt Ltd',
      'Estee Advisors Pvt Ltd',
      'Dassault Aircraft Services Pvt Ltd',
      'Ultragenic Research and Technologies Pvt Ltd',
      'Palo Alto Networks  India Pvt Ltd',
      'TSYS Card Tech services Pvt Ltd',
      'Rabita Software',
      'International Centre for Automotive Technology',
      'Ugro Capital',
      'Indian Council of Medical Research',
      'CDSL Ventures Ltd',
      'Freshbus Pvt Ltd',
      'Taco Punch Powertrain Pvt Ltd',
      'Vibs Infosol Pvt Ltd',
      'Tata Communications Collaboration Services Pvt Ltd (TCCSPL)',
      'Neural Networks Pvt Ltd',
      'Express Infrastructure Pvt ltd',
      'Paradigm IT Technologies Pvt Ltd',
      'Conquer Technologies',
      'Trinamix Systems Pvt Ltd',
      'Nxp India Pvt Ltd',
      'Magicbricks Realty Services Ltd',
      'Sudhakar PVC Products Pvt Ltd',
      'JS Auto Cast Foundry India Pvt Ltd',
      'DMI Housing Finance Pvt Ltd',
      'Pricol Pvt Ltd',
      'Vcom Technologies Pvt Ltd',
      'Tata AutoComp Systems Ltd',
      'Hi Q Electronics Pvt Ltd',
      'Rootquotient Technologies Pvt Ltd',
      'AM Green Ammonia (India) Pvt Ltd',
      'Adani Electricity Mumbai Ltd',
      'Jenburkt Pharmaceuticals Ltd',
      'Jekson Vision Pvt Ltd',
      'Indus Tower Ltd',
      'Corpacademia Itechnovations Pvt Ltd',
      'Bebo Technologies',
      'Visage Lines Personal Care Pvt Ltd',
      'The Automotive Research Association of India',
      'Jamna Auto Industries Ltd',
      'Epam Systems India Pvt Ltd',
      'Ujjivan Small Finance Bank Ltd',
      'Hero Cycles Ltd',
      'Sparsh Hospital',
      'National Test House',
      'Secure Network Solutions India Pvt Ltd',
      'Sicherten Info Consulting Pvt Ltd',
      'Cheers Interactive India Pvt Ltd',
      'Angel Broadcasting Network Pvt Ltd',
      'Hi Lex India Pvt Ltd',
      'White Oak Investment Management Pvt Ltd',
      'Expeditors International (India) Pvt Ltd',
      'Hitachi Hi-Rel Power Electronics pvt Ltd',
      'Indostar Home Finance Pvt Ltd',
      'RMS Risk Management Solutions India Pvt Ltd',
      'Defence Cyber Agency',
      'Touras India Pvt Ltd',
      'Air India Ltd',
      'Ugro Capital Ltd',
      'Adobe Systems India Pvt Ltd',
      'Statlight Software Solutions Pvt Ltd',
      'S R TRONICS',
      'Indian Synthetic Rubber Pvt Ltd',
      'Lloyd Shoes India Pvt Ltd',
      'Ippopay Technologies Pvt Ltd',
      'Senvion Wind Technologies Pvt Ltd',
      'Aquapharm Chemical Pvt Ltd',
      'Unichem Pharmaceuticals',
      'C.H. Robinson Worldwide Freight India Pvt Ltd',
      'Software Technology Park of India',
      'Deloitte Touche Tohmatsu India Llp',
      'Petrus Technologies Pvt Ltd',
      'Factentry Data Solutions Pvt Ltd',
      'Technique Control Facility Management Pvt Ltd',
      'Solix Softech Pvt Ltd',
      'Paytm Payments Bank Ltd',
      'Government of India Department of Space',
      'Icubix Infotech Ltd',
      'NSE Clearing Ltd',
      'Weapons and Electronics Systems Engineering Establishment',
      'Super Saravana Stores Emart Pvt Ltd',
      'Nuvama Wealth and Investment Ltd',
      'ASE Structure Design Pvt Ltd',
      'Platinum Peripherals',
      'NTPL Thermal Power Station',
      'Leixir Resources Pvt Ltd',
      'Dvara Money Pvt Ltd',
      'Galaxy Health & Allied Insurance Co Ltd',
      'UniteCore Pvt Ltd',
      'Paytm Money Ltd',
      'Master Capital Services Ltd',
      'Barclays Global Service Center Pvt Ltd',
      'Uflex Ltd',
      'Padget Electronics Pvt Ltd',
      'Bharat Fritz Werner',
      'Blr Logistics (I) Ltd',
      'Suez Projects Pvt Ltd',
      'Deloitte Shared Services India LLP',
      'Institute of Plasma Research',
      'Yakult Danone India Pvt Ltd',
      'Jio Financial Services Ltd',
      'Robert Bosch Engineering & Business Solutions Pvt Ltd',
      'Cyient DLM  Ltd',
      'Eterno Infotech Pvt Ltd',
      'Syntel Pvt Ltd',
      'WNS HealthHelp LLC-Houston',
      'Hyprbots Systems Pvt Ltd',
      'Feed Forward Technologies  Pvt Ltd',
      'Lenity Health India Pvt Ltd',
      'The Ramco Cements Ltd',
      'Erasmith Technologies Pvt Ltd',
      'Shriram Pistons & Rings Ltd',
      'IFB Industries Ltd',
      'Capsave Finance Pvt Ltd',
      'Liquidnitro Games Pvt Ltd',
      'Fractal Analytics Ltd',
      'Jadcherla expressways Pvt Ltd',
      'Data Marshall Pvt Ltd',
      'Rebaca Technologies Pvt Ltd',
      'University Of Jammu',
      'Toshiba Software India Pvt Ltd',
      'Homi Bhabha Cancer Hospital and Research',
      'AT&T Global Network Services India Pvt Ltd',
      'AT&T Global Network Services India',
      'CommScope Networks India Pvt Ltd',
      'North Eastern Regional Load Despatc Centre',
      'Comtel Infosystems Pvt Ltd',
      'Engineering Projects (India) Ltd',
      'Paychex IT Solutions India',
      'Fortune 3infonet Services',
      'Net Access India Ltd',
      'Quest Global Engineering Services Pvt Ltd',
      'Pyrotek India Pvt Ltd',
      'Speridian Technologies Pvt Ltd',
      'Royal Sundaram Alliance Insurance Company Ltd',
      'Modelama Exports Pvt Ltd',
      'Indian Institute of Hardware Technology Ltd',
      'Hyundai Motor India Engineering Pvt Ltd',
      'TMEIC Tumkur',
      'Octaten Universal Services Pvt Ltd',
      'Apollo Pipes Ltd',
      'HDFC Credila Financial Services Ltd',
      'Jakson Ltd',
      'Conduent Business Services India LLP',
      'ByTechnical Solution',
      'GitHub, Inc',
      'Spykar Lifestyles Pvt Ltd',
      'Healtech Software India Pvt Ltd',
      'Galgotias University',
      'Mydbops',
      'NIT Srinagar',
      'Ecofy Finance Pvt Ltd',
      'Sumitomo Mitsui Banking Corporation',
      'EXL Service India Pvt Ltd',
      'Tata Realty & Infrastructure Ltd',
      'Sant Nirankari Charitable Foundation',
      'Financial Technologies Ltd',
      'Kshema General Insurance Ltd',
      'Wirtgen India Pvt Ltd',
      'Strad Hosting and Development LLP',
      'Ivanti Technology India Private Limited',
      'Blue Yonder',
      'Ziff Davis Performance Marketing',
      'Fractal Analytics Inc',
      'Avaada Ventures Pvt Ltd',
      'SRL Diagnostics Ltd',
      'Algonomy Software Pvt ltd',
      'Writer Corporation',
      'Commercial Taxes Department',
      'Yotta Infrastructure Solutions LLP',
      'Bombay Mercantile Co-operative Bank Ltd.',
      'Prama Hikvision India Pvt Ltd',
      'Equifax Software System Pvt Ltd',
      'Gujarat Gas Ltd',
      'Society for Integrated Circuit Technology and Applied Research',
      'KIMS Healthcare Management Ltd',
      'Blueinfy Solutions Pvt Ltd',
      'VF Worldwide Holdings Ltd',
      'Patel Engineering Ltd',
      'Axa Global Business Services Pvt Ltd',
      'Protean eGov Technologies Ltd',
      'Tube Investments of India',
      'Power Grid Corporation of India Ltd',
      'Ace Infotech',
      'Bennett Coleman & Company Ltd/ Times Network Group',
      'Narayana Health',
      'Ratnakar Bank Ltd',
      'Paharpur 3p',
      'Samsung Data Systems India Pvt Ltd',
      'Capri Global Capital Ltd',
      'Jansuraksha (OPL - RRB)',
      'Wibmo',
      'Deccan Fine Chemicals india Pvt Ltd',
      'National Industries',
      'ION Trading India  Pvt Ltd',
      'Aadhar Housing Finance Ltd',
      'Polycab India Ltd',
      'Muthoot Fincorp Ltd',
      'Nido Home Finance Ltd',
      'Epta Layers Networks Pvt Ltd',
      'TMEIC Industrial Systems India Pvt Ltd',
      'OLX India Pvt Ltd',
      'Jumps Auto Industries Limited',
      'Akamai Technologies Solutions (India) Pvt Ltd',
      'Auxein Medical Pvt Ltd',
      'Ministry Of Coal',
      'Techno Electromech Pvt Ltd',
      'Dr B R Ambedkar National Institute of Technology',
      'Indian Institute of Remote Sensing',
      'Centre for Development of Advanced ComputingTechnopark',
      'Harman Connected Services Corporation India Pvt Ltd',
      'Coverself Technologies Pvt Ltd',
      'Thomas Cook (India) Ltd',
      'Vedanta Group (Unit: Sterlite Copper)',
      'Broadcast Audience Research Council',
      'SecuGen India Pvt Ltd',
      'All India Institute of Medical Sciences,',
      'Esskay',
      'CBCC Global Research LLP',
      'Black Box Network Services India Pvt Ltd',
      'Cytrusst Intelligence Pvt Ltd',
      'Neo Wealth and Asset Management',
      'Wal Mart India Pvt Ltd',
      'Zetwerk India Pvt Ltd',
      'Sirion Labs Pvt Ltd',
      'Sdl Ed Apps Llp',
      'Bitgo India Pvt Ltd',
      'Integrated Enterprises India Pvt Ltd',
      'Benelec Infotech Pvt Ltd',
      'Troo Tribe Tech Ltd',
      'Directorate of Treasury Pension and Entitlement',
      'Mitutoyo south Asia Pvt ltd',
      'Apollo Supply Chain Pvt  Ltd',
      'Institute of Banking  Personnel Selection',
      'Ittiam Systems Pvt Ltd',
      'Innovative Consumer Concepts(ICC)',
      'NLB Services Pvt. Ltd',
      'Datacipher Solutions Pvt Ltd',
      'Bharat Re-Insurance Brokers Pvt Ltd',
      'Hyundai Steel Anantapur Pvt Ltd',
      'Tower Research Capital India Pvt Ltd',
      'Tamilnadu Mercantile Bank Ltd',
      'Sarvatra Technologies Pvt Ltd',
      'Apollo Pharmacy',
      'Atos Global IT Solutions & Services Pvt Ltd',
      'Alstom Transport India Ltd',
      'Sanskar Info TV Pvt Ltd',
      'Greshma Shares & Stocks Ltd',
      'Kerala Infrastructure Investment Fund Board',
      'Thyssenkrupp Uhde India Pvt Ltd',
      'Inniti Network Solutions LLP',
      'Rajiv Gandhi Cancer Institute And Research Centre',
      'P A S Cotton Mills Pvt Ltd',
      'Finzoom Investment Advisors Pvt Ltd',
      'Shapoorji Pallonji and Co Pvt Ltd',
      'Centre for Development of Advance Computing',
      'Annova Solutions Pvt Ltd',
      'Hexatech eSecurity Solutions Pvt Ltd',
      'HDFC Asset Management Company Ltd',
      'Health Axis Pvt Ltd',
      'Choice Techlab Solutions Pvt Ltd',
      'Elevar Digitel Infrastructure Pvt Ltd',
      'NewAge Software & Solutions India Pvt Ltd',
      'American Embassy School',
      'Kuya Technologies Pvt Ltd',
      'Mensa Brands Technologies Pvt Ltd',
      'Github India Pvt Ltd',
      'Tesla India Motors and Energy Pvt Ltd',
      'Nova Techset Ltd',
      'Kewaunee Scientific Corporation India Pvt Ltd',
      'Religare Broking Ltd',
      'Experian Credit Information Company Pvt Ltd',
      'HSO India Pvt Ltd',
      'Majorel India Pvt Ltd',
      'TJSB Sahakari Bank Ltd',
      'OpenText',
      'Airbnb India Pvt Ltd',
      'Loreal India Pvt Ltd',
      'SBFC Finance Ltd',
      'Whizdm Innovations Pvt Ltd',
      'Claysys Technologies Pvt ltd',
      'Policybazaar Insurance Brokers Pvt Ltd',
      'Impelsys Pvt Ltd',
      'The Godhra Urban Co-Operative Bank',
      'CMS IT Services Pvt Ltd',
      'ROKI R&D India Pvt Ltd',
      'Concentrix Daksh India Pvt Ltd',
      'Compass IT Solutions and Services Pvt Ltd',
      'Bharat Biotech',
      'Tata Motors Passenger Vehicle Ltd',
      'Exim Transtrade India Pvt Ltd',
      'RxLogix Corporation India Pvt Ltd',
      'Unimoni Financial srevices Ltd',
      'BOB Card Ltd',
      'Pradhi Ai Solutions Pvt Ltd',
      'Steel Strips Wheels Limited',
      'Arya Construction',
      'Light Mechanics Pvt Ltd',
      'Alternative Business Intelligence Pvt Ltd',
      'Punjab Police',
      'Bluecom Technologies India Pvt Ltd',
      'Mjunction Services Ltd',
      'The Automotive Research Association of I',
      'Tech Vistar IT Solutions Pvt Ltd',
      'Progility Technologies Pvt Ltd',
      'Druva Data Solutions Pvt Ltd',
      'Deloitte Touche Tohmatsu Ltd',
      'Aspire Nxt Pvt Ltd',
      'Cybage Software Pvt Ltd',
      'Affluent Global Services Pvt Ltd',
      'Innovsource Services Pvt Ltd',
      'HLL Infratech Services Ltd',
      'Incedo Technology Solutions Ltd',
      'BizCarta Technologies India Pvt Ltd',
      'AuthenticOne',
      'NBC Bearings',
      'Alldigi Tech Ltd',
      'PalTech Consulting Pvt Ltd',
      'Accenture Services Pvt Ltd',
      'Prama India Pvt Ltd',
      'Cyberpwn Technologies Pvt Ltd',
      'Shiv Nadar Foundation',
      'Directorate of Information Technology',
      'Calpion Software Technologies Pvt Ltd',
      'Firstbase Media Pvt Ltd',
      'Ubona',
      'Samkrg Pistons & Rings Ltd',
      'India International Bullion Exchange IFSC Ltd',
      'Feedfront AI Technologies Pvt Ltd',
      'Odisha Gramya Bank',
      'Letsdefend Infosec',
      'Asia Pacific Systems',
      'Department of Youth Services and Sports',
      'Open Network for Digital Commerce',
      'National Institute of Technology',
      'EnquiryBot Technologies India Pvt Ltd',
      'Minix Holdings Pvt Ltd',
      'DRS IT Consultancy Pvt Ltd',
      'Zoho Payment Technologies Pvt Ltd',
      'KAI Manufacturing India Pvt Ltd',
      'RG Stone Urology & Laparoscopy Hospital - Unit of Scientific',
      'Greater Chennai Corporation',
      'Effigo Global Pvt Ltd',
      'Chevron Global Technology And Services Pvt Ltd',
      'Amphenol Interconnect India Pvt Ltd',
      'India Infoline Finance Ltd (IIFL)',
      'Turacoz Healthcare',
      'R S Infraprojects Pvt Ltd',
      'F5 Networks India Pvt Ltd',
      'We-Do-It India Pvt Ltd',
      'Avantha Technologies Limited',
      'Lexmark International (India) Pvt Ltd',
      'Pooja Forge Ltd',
      'Sinch Cloud Communication Services India Pvt Ltd',
      'Sahara Hospitality Ltd',
      'THE JHALOD URBAN CO-OP BANK LTD',
      'Drivestream India Pvt Ltd',
      'Societe Generale Global Solution Centre Pvt Ltd',
      'Jindal Saw Ltd',
      'Astral Ltd',
      'Data Security Council Of India',
      'Kar Nipuna Advisors Pvt Ltd',
      'IFB Automotive Pvt Ltd',
      'Mizuho Bank Ltd',
      'Xtelify Ltd',
      'BML Munjal University',
      'The Officer In Charge Comnetcentre',
      'Nuclear Power Corporation Of India Ltd',
      'Infinx Healthcare',
      'Foundever Business Services Of India Pvt Ltd',
      'Nuziveedu seeds Ltd',
      'Lennox India Technology Centre Pvt Ltd',
      'Kerala Cooporative Bank',
      'National Informatics Unit (NIU)',
      'Global Growth Arrevio Pvt Ltd',
      'Games24x7',
      'Lowe Services India Pvt Ltd',
      'National Dairy Development Board',
      'Nishith Desai Associates',
      'Stock Holding Document Management Services Ltd',
      'Opus Solution Pvt Ltd',
      'Bajaj Allianz Life Insurance Company Ltd',
      'Deloitte Consulting India Pvt Ltd',
      'Infotrellis India Pvt Ltd',
      'Sanyo Special Steel Manufacturing India Pvt Ltd',
      'Oracle India Pvt Ltd IDC',
      'Sardar Vallabhbhai Patel Institute of Medical Sciences and Research',
      'Crystal HR & Security Solutions pvt ltd',
      'Staples',
      'National Centre for Earth Science Studies',
      'India International Bullion Exchange',
      'Council Of Scientific And Industrial Research–National Institute Of Science',
      'Tata Power Renewable Energy Ltd',
      'Yamuna Expressway Industrial Development Authority',
      'Quantum Advisors Pvt Ltd',
      'Suez Project Pvt Ltd',
      'CloudMoyo India Pvt Ltd',
      'Bill Glosing India Pvt Ltd',
      'Connexions',
      'Flytxt mobile solutions Pvt Ltd',
      'Aster DM Health Care Ltd',
      'High Court Of Andhra Pradesh',
      'Netradyne Technology India Pvt Ltd',
      'Loginsoft india Pvt Ltd',
      'Sant Nirankari Mandal',
      'Avendus Capital Pvt Ltd',
      'Lohia Corp Ltd',
      'East Consultancy Services Pvt Ltd',
      'Nirma University',
      'Microsystems',
      'Canara Robeco Asset Management Company Ltd',
      'Central Warehousing Corporation',
      'Ais Business Solutions Pvt Ltd',
      'Splunk Services Singapore Pte Ltd',
      'ViaPlus',
      'Corecard Software India Pvt Ltd',
      'Safex Chemical India Ltd',
      'InterGlobe Technology Quotient Pvt Ltd',
      'BAPS Swaminarayan Sanstha',
      'Pacific Bpo Pvt Ltd',
      'Edvenswa Tech Pvt Ltd',
      'Electronics And Information Technology  Department',
      'Future Businesstech India Pvt Ltd',
      'Wells Fargo International Solutions Pvt Ltd',
      'CD Technotex LLP',
      'Zapier Inc',
      'Mindsprint Digital (India) Pvt Ltd',
      'Shriram Chits (India) Pvt Ltd',
      'FuturiQ Systems Pvt Ltd',
      'India Security Press',
      'Witzenmann India Pvt Ltd',
      'Oaknorth Global Pvt Ltd',
      'TruCap Finance Ltd',
      'Hindustan Pencils Pvt Ltd',
      'Altius Infrastructure',
      'Piramal Capital and Housing Finance Ltd',
      'Jodhpur Nagrik Sahakari Bank Ltd',
      'Goenka &  Associates Educational Trust',
      'NIA Software India Pvt Ltd',
      'Squared Circle E-Com Pvt Ltd',
      'Binary Global Ltd',
      'IITM Pravartak Technologies Foundation',
      'L&T Hydrocarbon Engineering Ltd',
      'Karnataka Power Transmission Corporation Ltd (KPTCL)',
      'Bandhan Life Insurance Ltd',
      'Tata Motors Ltd CV(Commercial Vehicles)',
      'Asiatic Mindshare Ltd',
      'International Centre for Diarrhoeal Dise',
      'United Commercial Bank PLC',
      'Alcatel-Lucent India Ltd',
      'Lanka Tiles PLC',
      'GE India Technology Centre Pvt Ltd',
      'Tech Mahindra',
      'Millennium ITESP Pvt Ltd',
      'Shine Resunga Development Bank Ltd',
      'Coca-cola Beverages Sri Lanka Ltd',
      'Karl Mayer Stoll Bangladesh Ltd',
      'Aegis Customer Support Services Pvt Ltd',
      'Startek (Aegis BPO Malaysia Sdn Bhd)',
      'Prime Minister’s Office - Tonga',
      'IT Consultants Ltd',
      'Bangladesh Navy',
      'International College of Business &Technology Ltd',
      'LK Domain Registry',
      'Royal Monetary Authority RMA',
      'Dungsam Cement Corporation Ltd',
      'Integrated Budget and Accounting System',
      'HCL Technologies Malaysia SDN',
      'One Bank PLC',
      'Katsuyama Pharmaceuticals K.K.',
      'Bangladesh Water Development Board',
      'Trilix S R L',
      'Ebony Holdings Pvt Ltd',
      'Cimpress India Pvt Ltd',
      'Bkash Ltd',
      'Micro Focus Software Inc',
      'Quantei Australia Pty Ltd',
      'ST Anthony’s Ventures Ltd',
      'Cargills Bank PLC',
      'Synergen Health (Pvt) Ltd',
      'Ncell Axiata Ltd',
      'LTL Galvanizers Pvt Ltd',
      'Prime Bank Ltd',
      'Itelasoft Pvt Ltd',
      'David Pieris Holdings (Pvt) Ltd',
      'Capital Alliance Ltd',
      'Universal Collage Lanka',
      'Bangladesh Air Force',
      'Sanasa Insurance Company Ltd',
      'Laxmi Laghubitta Bittiya Sanstha Lt',
      'Himalayan Life Insurance',
      'Prima Managment Services Pvt Ltd',
      'Bhutan Automation',
      'Bhutan Post',
      'Department of Immigration',
      'MAW Enterprises Pvt Ltd',
      'Bangladesh Police',
      'Onebill Software inc',
      'Emerchemie NB Ceylon Ltd',
      'Sri Lanka Computer Emergency Readiness',
      'Vallibel Finance Plc',
      'Autnhive Inc',
      'Sino Lanka Pvt Ltd',
      'A-Networks Pvt Ltd',
      'IFIC Bank PLC',
      'Maldives Transport and Contracting Company',
      'National Pension and Provident Fund',
      'Calcey Technologies Pvt Ltd',
      'Statestreet Global Advisors India Pvt Ltd',
      'Renew MicroFinance Pvt Ltd',
      'LOLC Technology Services Ltd',
      'Drukair Corporation Ltd',
      'Council of the Combatants of National Liberation',
      'DFCC Bank PLC',
      'Sri Lanka Air Force',
      'EAM Maliban Textiles',
      'Villa Shipping & Trading Company Pvt Ltd',
      'FAIRFIRST INSURANCE LTD',
      'Evonsys Llc',
      'The Public Private Partnership Commission',
      'Bottlers Nepal Ltd',
      'Global IME Bank Ltd',
      'Alliance Finance Co PLC',
      'Asian Life Insurance Company Ltd',
      'Laxmi Sunrise Capital Market Ltd',
      'Mutual Trust Bank Ltd',
      'Srilankan Catering Ltd',
      'Bracnet Ltd',
      'Msource India Pvt Ltd',
      'Itechro Pvt Ltd',
      'DSL IT Solutions Pvt Ltd',
      'Bank of Ceylon',
      'Continental Insurance Lanka Ltd',
      'Hatton National Bank PLC',
      'National Disaster Risk Reduction & Management Authority',
      'Sri Lanka Institute of Information Technology',
      'Pubali Bank PLC',
      'Maldives Port Authority',
      'Rabbit Solutions Pvt Ltd',
      'Royal Insurance Corporation of Bhutan Ltd',
      'Airtel Uganda Ltd',
      'Fintrex Finance Ltd',
      'BRAC Bank PLC',
      'Hansraj Hulaschand & Co. Pvt Ltd',
      'Lanka Canneries Pvt Ltd',
      'Burckhardt Compression India Pvt Ltd',
      'Ooredoo Maldives',
      'St.Anthony’s Hardware Pvt Ltd',
      'Maldives Islamic Bank PLC',
      'Quatrro Business Support Solutions Pvt Ltd',
      'National Savings Bank',
      'State Mortgage & Investment Bank',
      'Lanka Minerals and Chemicals Pvt Ltd',
      'Medi Health hospital',
      'Fiber@Home Ltd',
      'Telecommunications Regulatory Commission of Sri Lanka',
      'Ceylon Biscuits Ltd',
      'Infosys Automotive & Mobility GmbH & Co.KG (Infosys Ltd)',
      'Lion Brewery (Ceyon) Plc',
      'Chelcey Solutions Pvt Ltd',
      'Department of Inland Revenue MoF Sri Lanka',
      'Association for Social Advancement',
      'Trust Bank Ltd',
      'Colombo International Container Terminals Ltd',
      'CEAT Kalani International Pvt Ltd',
      'Electricity Generation Company of Bangladesh Ltd',
      'Allied Insurance Company of the Maldives Pvt Ltd',
      'Gapstars',
      'SLIIT-Kandy Uni Pvt Ltd',
      'Citizen Bank International Ltd',
      'The Rose Dresses Ltd',
      'MAS Capital Pvt Ltd',
      'State Electric Company Ltd',
      'Litro Gas Lanka Ltd',
      'Brandix Apparel Ltd',
      'Infosys Technologies Ltd',
      'Alcatel Lucent Technologies',
      'Concentrix',
      'Antler Group of Companies',
      'First Capital Holdings PLC',
      'Janashakthi Insurance PLC',
      'Wipro HR Services India Pvt ltd',
      'GovTech Agency',
      'Norvic International Hospital & Medical College Ltd',
      'Planet Resource and Ventures Pte Ltd',
      'WindForce PLC',
      'Amann Bangladesh Ltd',
      'Triveni Byapar Company Pvt Ltd',
      'Dutch Bangla Bank Ltd',
      'Moxy Hotels by Marriot',
      'Marriott Kathmandu',
      'Prime Commercial Bank Ltd',
      'Mercantile Investment and Finance Plc',
      'Bharti Airtel International (Netherlands) BV Kenya',
      'Oil & Natural Gas Corporation Limited',
      'Snapdeal Pvt Ltd',
      'Registrar General of India',
      'Delhi Police',
      'ATS Corporate Office, ATS Greens Ltd',
      'FNF India Pvt Ltd',
      'North East Frontier Railway',
      'CyberArk Software India Private Ltd',
      'Fastenal India Sourcing IT & Procurement Pvt Ltd',
      'AKT Business Services Pvt Ltd',
      'Safran Engineering Services India Pvt Ltd',
      'Wipro UPSA',
      'Sanbay Networks Pvt Ltd',
      'MCE Insurance Company Ltd',
      'Techdefence Labs Solutions Ltd',
      'National Industrial Corridor Development Corporation Ltd',
      'Shopify Commerce India Pvt. Ltd',
      'Bhagalpur Smart City Ltd',
      'Punjab & Maharashtra Co-Op Bank Ltd',
      'Tecnimont Private Limited',
      'Velocis Systems Pvt Ltd',
      'Mattsen Kumar Services Pvt Ltd',
      'TEG Analytics',
      'Saksoft Ltd',
      'Algosmic Pvt Ltd',
      'Impetus Infotech Pvt Ltd',
      'Indian Additives Ltd',
      'Government of Goa',
      'Delta Export',
      'Ample Digital Pvt Ltd',
      'Honda Trading Corporation', 
      'India Pvt Lt  India Pvt Ltd',
      'Excellex Technologies Pvt Ltd',
      'Qualitest India Pvt Ltd',
      'Colorshine Coated Pvt Ltd',
      'Margo Networks Pvt Ltd',
      'Techjockey Infotech Pvt Ltd',
      'ECGC Ltd',
      'NEC Corporation India Pvt Ltd',
      'Lyearn Software Development India Pvt Ltd',
      'Zupe Technology Pvt Ltd',
      'Apollo Tyres Ltd',
      'Epson India Pvt Ltd',
      'Elecon Engineering Company Ltd',
      'Haryana Power Generation Corporation Ltd',
      'Ananda Dairy Ltd',
      'TEG India Private Ltd',
      'Chhattisgarh State Power Distributor Company Ltd',
      'Toyota Tsusho System India Pvt Ltd',
      'Odessa Solutions Pvt Ltd',
      'National Institute Of Homeopathy',
      'Schneider Electric India Pvt Ltd',
      'Sykes Business Services Of India Pvt Ltd',
      'Director,Centre for Advanced Systems, ',
      'ERGO Technology & Services Private Limit',
      'Luxoft India LLP',
      'NTT India Pvt Ltd.',
      'Wealthstreet Advisors Pvt Ltd',
      'Collabera Technologies Pvt Ltd',
      'Coforge Dpa Pvt Ltd',
      'HCL Technologies Mexico, S. de R.L. de C',
      'Zones Corporate Solutions Pvt. Ltd',
      'Ephicacy Lifescience Analytics Pvt. Ltd.',
      '(simplifyhealthcare) Ognam Technology Se',
      'Honeywell Automation India Ltd',
      'Siemens Healthcare Pvt Ltd',
      'Syntel Telecom Ltd',
      'Tecogis',
      'Housing Development Finance  Corporation Limited',
      'Orient Paper Mills (Proprietors - Orient',
      'Akola Urban Cooperative Bank Ltd',
      'Beetel Teletech Ltd',
      'Uttar Pradesh Prisons Head Quarter',
      'Reliance General Insurance Company Limit',
      'USHA MARTIN LTD',
      'Infotel Business Solutions Ltd',
      'Sapience Analytics Pvt Ltd.',
      'Avercast Infotech Pvt. Ltd. (A TransImpact Company)',
      'Central Registry of Securitisation Asset Reconstruction&SecurityInterest of India',
      'Kyndryl Solutions Private Limited',
      'Walsons Services Private Limited',
      'Coforge Smart Serve Ltd',
      'Nykaa E-Retail Pvt Ltd',
      'Sanghavi Beauty & Technologies Pvt Ltd',
      'Applexus Technologies Private Limited',
      'ITER-India Institute For Plasma Research',
      'Rajasekar Srinivasan',
      'ProV Infotech Systems Pvt Ltd',
      'Kanpur Electricity Supply Company Limited',
      'Dewan Housing Finance Pvt.Ltd',
      'EMS & Solutions',
      'Idoraa Pvt Ltd',
      'Proof and Experimental Establishment',
      'SMART SOFTWARE TESTING SOLUTIONS INDIA P',
      'Synerzip Softech India Pvt. Ltd',
      'T-Mobile USA Inc',
      'Meesho Payments Pvt Ltd',
      'Assam Gas Company Ltd',
      'Shriram Transport Finance company Ltd',
      'Motif India Infotech Pvt Ltd',
      'Giesceke & Devrient India Pvt Ltd',
      'Tata Consultancy Services Ltd ',
      'Eikym Solutions Pvt Ltd',
      'Saikrishna & Associates',
      'BEML Ltd',
      'Smart Chip Pvt. Ltd.',
      'Bharti Realty Holdings Ltd',
      'NIT, Jalandhar',
      'Sequent Scientific Limited',
      'PTC Software India Pvt Ltd',
      'Reverse Logix Management India Pvt Ltd',
      'Miramed Ajuba Solutions Pvt Ltd',
      'Synokem Pharmaceuticals ltd.',
      'Cisco Systems India Pvt Ltd',
      'Samsung R&D Institute',
      'APL Logistics India Pvt Ltd',
      'Insurance Information Bureau of India',
      'Sundaram Clayton Limited',
      'D.D. Enterprises',
      'Cognologix Technologies Pvt Ltd',
      'Agra Airport',
      'Indian Agricultural Statistic Research I',
      'Millennium Semiconductors India Private',
      'World Vision Pvt Ltd',
      'Inspirisys Solutions Ltd',
      'Techouts Solutions India Pvt Ltd',
      'CSS Corp Pvt Ltd',
      'Mando Automotive India Pvt Ltd',
      'Accenture Solutions Pvt Ltd',
      'Supreme Petrochem ltd',
      'Ashok Piramal Group',
      'Department of Land Management and Archive',
      'Atul Ltd',
      'Think & Learn Pvt Ltd',
      'Biocon Pharma',
      'VIT University',
      'Sansad Television',
      'Hosur Industries Association',
      'Marcellus Infotech Pvt Ltd',
      'LBR Infosolutions Pvt. Ltd.',
      'Personiv Contact Centres India Pvt ltd',
      'Kashmir Power Distribution Corporation Ltd',
      'International Council of E Commerce',
      'UBS Securities India Pvt Ltd',
      'Deepak Fertilisers And Petrochemicals Corp Ltd',
      'Piccadily Holiday Resorts Ltd',
      'Moolchand Healthcare Pvt Ltd',
      'Adani Ports and Special Economic Zone Ltd',
      'GoTo Technologies India Private Limited',
      'Vadodara Municipal Corporation',
      'Neblio Technologies Pvt Ltd',
      'Digiotech Solutions Pvt Ltd',
      'Jammu University',
      'Xceedance Consulting India Private Limit',
      'Pearl Global Industries Limited',
      'Arevuk Advisory Services Pvt Ltd',
      'Dialpad Services Pvt Ltd',
      'Finnovation Tech Solutions Pvt Ltd (Kred',
      'Tata Communications Limited',
      'Hyclone Life Sciences Solutions India Pv',
      'Idemia Syscom India Pvt Ltd',
      'SONA BLW PRECISION FORGINGS LTD',
      'Pune Municipal Corporation',
      'Kepsure Solutions Pvt Ltd',
      'Learning Mate Solutions Private Limited',
      'Centre for E-Governance',
      'BSG IT Soft Pvt Ltd',
      'Harnessio R&D Labs India Pvt Ltd',
      'Odisha Computer Application Centre Bhubaneswar',
      'Zybisys Consulting Services',
      'Juspay Technologies Pvt Ltd',
      'Health Insurance TPA of India Ltd',
      'Doyen Infosolutions Pvt Ltd',
      'Shopsense Retail technologies Ltd',
      'Genesys International Corporation Ltd',
      'Shapoorji Pallonji Co Pvt Ltd',
      'Assam Rural Infrastructure and   Agricultural Services',
      'Jefferies India Pvt Ltd',
      'Born Commerce Pvt Ltd',
      'ICVS E SOLUTIONS PVT LTD',
      'SAJU G',
      'Avalon Technology And Services Pvt Ltd',
      'Odisha State Cooperative Bank Ltd',
      'Salesforce India Pvt Ltd',
      'General Insurance Corporation of India',
      'Biocon Ltd',
      'Caresoft Global Pvt Ltd',
      'Hind Merchandise (OPC) Pvt Ltd',
      'The Tamilnadu police',
      'Happiest Minds Technologies Pvt Ltd',
      'Lal Bahadur Shastri National Academy of Administration',
      'North Bengal Medical college and Hospital',
      'Gabriel India Ltd',
      'Silicon Comnet Private Limited',
      'Hitachi Consulting Software Services India Pvt Ltd',
      'Indian Institute of Technology Mandi',
      'Madhya Pradesh Power Generating Co. Ltd.',
      'Tally Solutions Pvt Ltd',
      'Suzuki Motor Gujarat Pvt. Ltd',
      'The Malayala Manorama Company Ltd',
      'The Akshaya Patra Foundation',
      'RK WEBSOFT TECHNOLOGIES PVT LTD',
      'Nash Industries India Pvt Ltd',
      'Transfast India Pvt Ltd',
      'Seamless Infotech Pvt Ltd',
      'BitCipher Labs LLP CoinSwitch Kuber',
      'BitCipher Labs LLP',
      'Nomura Services India Pvt Ltd',
      'AITC- EPAM Systems India Pvt Ltd',
      'IGO Solutions Pvt Ltd',
      'Attra Infotech Private Limited',
      'VISTAAR FINANCIAL SERVICES PRIVATE LIMIT',
      'Continental Automotive Components Pvt. Ltd',
      'VIS Networks Pvt Ltd',
      'Arris Group India Pvt Ltd',
      'Back Office IT Solutions Pvt Ltd',
      'Fortis Healthcare Ltd',
      'Solar Industries India Ltd',
      'Apvision Technologies',
      'Paisabazaar Marketing and Consulting Pvt Ltd',
      'Coface India Credit Management Services',
      'Delhi International Airport Ltd',
      'Terraform Global Pvt Ltd',
      'Bharti AXA Life Insurance',
      'Sane Green Informatic Pvt Ltd',
      'Olam International Ltd',
      'Jubilant Generics Ltd',
      'Equifax Software Systems Pvt Ltd',
      'Tecnimont Pvt Ltd',
      'SLK Global Solutions Pvt Ltd',
      'KANDUI INDUSTRIES PVT LTD',
      'Aspire Systems India Pvt Ltd',
      'Military College of Telecommunication',
      'Dialog Broadband Networks Pvt Ltd',
      'Coin DCX Neblio Technologies Pvt Ltd',
      'Great Software Laboratory Pvt. Ltd',
      'Intertrust Group.',
      'Rajkot Municipal Corporation',
      'Bruhat Bengaluru Mahanagara Palike',
      'Mahindra & Mahindra Financial Service Ltd',
      'Dahod Smart City Development Ltd',
      'UFO Moviez India Ltd',
      'Asian Institute of Gastroenterology Pvt',
      'Madhya Pradesh Madhya Kshetra Vidyut Vitaran Company Ltd',
      'Gorakhpur Airport',
      'Crimson Cloud Pvt Ltd',
      'Lite Bite Foods Pvt Ltd',
      'Fena (P) Ltd',
      'Grey Token',
      'General Pharmaceuticals Ltd',
      'Intellicus Technologies Pvt Ltd',
      'Autotech-Sirmax India Pvt Ltd',
      'First Solar Power India Pvt Ltd',
      'Zuci Systems India Pvt Ltd',
      'Press2 Dry Cleaning and Laundry Pvt Ltd',
      'Center for Railway Information Systems',
      'Cyforce Pvt Ltd',
      'Sundaram Clayton Ltd',
      'Kumaraguru College of Technology',
      'The Tata Power Central Odisha Distribution Ltd',
      'Grant Thornton Advisory Pvt Ltd',
      'Prime Focus Ltd',
      'LEH Airport',
      'CVR Labs Pvt Ltd',
      'Srinagar Airport',
      'HCL Comnet Ltd',
      'Suma Soft Pvt Ltd',
      'Braid Technologies Pvt Ltd',
      'SISL Infotech Pvt Ltd',
      'Harbinger Systems Pvt Ltd',
      'RLABS ENTERPRISE SERVICES LTD',
      'Tata Power SED',
      'Zen Quality Assurance Pvt Ltd',
      'Upmove Capital Pvt Ltd Smartcoin Financials PVT Ltd',
      'SRSG Broadcast (India) Pvt Ltd',
      'Patel Infrastructure Pvt Ltd',
      'ASPL Info Services Pvt Ltd',
      'Assam Police Headquarters',
      'Micron Technology Operations India LLP',
      'Dishana Enterprises',
      'Vasu Healthcare Pvt Ltd',
      'JK Papers Ltd',
      'Goldman Sachs Services Pvt Ltd',
      'Bajaj Motors Ltd',
      'Geological Survey Of India',
      'MP School',
      'Mother Dairy Fruit & Vegetable Pvt Ltd',
      'Mcube Advisors Pvt Ltd',
      'National Commodities Management Services',
      'Gameskraft',
      'Guwahati Smart City Ltd',
      'Kolte Patil Developers',
      'MSCI Services Pvt Ltd',
      'Ramrao Adik Institute of Technology',
      'SRINIVASA FARMS PVT LTD',
      'The Burdwan Central Co-operative Bank Lt',
      'Howden Solyvent (India) Pvt Ltd',
      'Finolex Industries Ltd',
      'Arvind Internet Ltd',
      'UPDATER SERVICES LTD',
      'Dodhia Synthetics Ltd',
      'United Commercial Bank',
      'CodeMax IT Solutions Pvt Ltd',
      'Religare Enterprise Ltd',
      'RPS Consulting Pvt Ltd',
      'SYNERGISTIC FINANCIAL NETWORKS PVT LTD',
      'ORCIMED LIFE SCIENCES PRIVATE LIMITED',
      'Department Of Science & Technology',
      'Webtel Electrosoft Pvt Ltd',
      'Renaissance Spacio',
      'Bystronic Laser India Pvt Ltd',
      'Latent View Analytics Ltd',
      'Jagran Prakashan Ltd',
      'Sathvika Solutions',
      'Advanced Technical Vehicles Program Department of Defence',
      'Gvc Services Pvt Ltd',
      'IVY Comptech Pvt Ltd',
      'SynRadar',
      'Ecocat India Pvt Ltd',
      'Smart City Thiruvananthapuram Ltd',
      'Shobha Ltd',
      'Isecurion Technology & Consulting Pvt Ltd',
      'FusionNet Web Services Pvt Ltd',
      'HCG',
      'Unichem Laboratories Ltd',
      'Inox Air Products Pvt Ltd',
      'Lodestone Software Services Pvt Ltd',
      'Infrastructure Development Corporation (',
      'Larsen & Toubro Hydrocarbon Engineering Ltd',
      'SourceHOV India Pvt Ltd',
      'Karkinos Healthcare Pvt Ltd',
      'Ethos Ltd',
      'Criterion Network Labs',
      'Gujarat State Handloom & Handicraft Development Corporation Limited',
      'Signum Electrowave Pvt Ltd',
      'Signum Electro Pvt Ltd',
      'Jay Jay Mills (India) Pvt Ltd',
      'Dharmanandan Diamonds Pvt Ltd',
      'Pennant Technologies Pvt Ltd',
      'Plastic Omnium Auto Inergy India Pvt Ltd',
      'Shree Cement Ltd',
      'Liquid Propulsion Systems Centre',
      'Cenveo Publisher Services India Pvt Ltd',
      'Delhi Gujarat Fleet Carrier Ltd',
      'Amrita Hospital',
      'National Skill Development Corporation',
      'Jawaharlal Nehru Port Trust',
      'The Akola Janata Commercial Co-Operative',
      'UBX Cloud',
      'Petronet LNG Limited',
      'Interropac Pvt Ltd',
      'Smart Chip Pvt Ltd',
      'UL Technology Solutions Pvt Ltd',
      'Shimla Smart City Ltd',
      'Council Of Scientific And Industrial Res Council Of Scientific And Industrial Res',
      'Altiostar Networks India Pvt Ltd',
      'Zones Corporate Solutions Pvt Ltd',
      'Border Guard Bangladesh',
      'NIDP Developers Pvt Ltd',
      'Tatvik System Solutions Pvt Ltd',
      'SmarTek21 Pvt Ltd',
      'Del Monte Foods Pvt Ltd',
      'Corel Pharma Chem',
      'Xebia IT Architects India Pvt Ltd',
      'Max Life Insurance Co Ltd',
      'RI Networks Pvt Ltd',
      'Electronics Corporation of Tamil Nadu',
      'Wockhardt Ltd',
      'Tata Hitachi Construction Machinery Company Pvt Ltd',
      'Mynd Solutions Pvt Ltd',
      'Tata Sia Airlines Ltd',
      'Larsen & Toubro Ltd Smart World & Communication',
      'Aegis Outsourcing South Africa Pty Ltd',
      'GlobalLogic India Private Limited',
      'Egypt Trust',
      'Coinfinitive Solutions Pvt Ltd',
      'NRB Bank Ltd',
      'Leggett and Platt',
      'BMW India Pvt Ltd',
      'NIC Asia Capital Ltd',
      'Global Brand Pvt Ltd',
      'CSC e Governance Services India Ltd',
      'Airtel Networks Zambia PLC',
      'Kumari Bank Limited',
      'Banglalink Digital Communications Ltd',
      'Perfetti Van Melle ICT B.V.',
      'Cvent India Pvt Ltd',
      'Citizens Bank International Ltd',
      'Nepal bank Ltd',
      'Directorate General of Forces Intelligence',
      'Kennametal Inc',
      'L&T Infotech',
      'Handicap International Federation',
      'Startek Inc',
      'Jindal Films Europe Kerkrade B.V.',
      'Bharti Airtel International'
    ];

  const yearOptions = extractedValues.years.length > 0 
    ? extractedValues.years 
    : ['2022-23', '2023-24', '2024-25'];

  // Main categories with their subcategories
  const mainCategories = [
    {
      id: 'individual-roles',
      title: 'Individual Role Categories',
      icon: <FiUsers />,
      description: 'Role-based queries and analytics',
      subcategories: [
        {
          id: 'business-head-queries',
          title: 'Business Head',
          icon: <FiUsers />,
          description: 'Business Head Queries'
        },
        {
          id: 'channel-champ-queries',
          title: 'Channel Champ',
          icon: <FiUsers />,
          description: 'Channel Champ Queries'
        },
        {
          id: 'group-business-manager-queries',
          title: 'Group Business Manager',
          icon: <FiUsers />,
          description: 'Group Business Manager Queries'
        },
        {
          id: 'group-channel-champ',
          title: 'Group Channel Champ',
          icon: <FiUsers />,
          description: 'Group Channel Champ Queries'
        },
        {
          id: 'business-manager',
          title: 'Business Manager',
          icon: <FiUsers />,
          description: 'Business Manager Queries'
        },
        {
          id: 'vertical-champ',
          title: 'Vertical Champ',
          icon: <FiUsers />,
          description: 'Vertical Champ Queries'
        },
        {
          id: 'oem-queries',
          title: 'OEM',
          icon: <FiUsers />,
          description: 'OEM Queries'
        },
        {
          id: 'vertical-account-queries',
          title: 'Vertical Account',
          icon: <FiUsers />,
          description: 'Vertical Account Queries'
        },
        {
          id: 'channel-queries',
          title: 'Channel',
          icon: <FiUsers />,
          description: 'Channel Queries'
        },
        {
          id: 'end-customer-queries',
          title: 'End Customer',
          icon: <FiUsers />,
          description: 'End Customer Queries'
        },
        {
          id: 'partner-queries',
          title: 'Partner',
          icon: <FiUsers />,
          description: 'Partner Queries'
        }
      ]
    },
    {
      id: 'cross-functional',
      title: 'Cross-Functional Categories',
      icon: <FiTrendingUp />,
      description: 'Strategic relationship analytics',
      subcategories: [
        {
          id: 'business-head-oem',
          title: 'Business Head ↔ OEM',
          icon: <FiUsers />,
          description: 'Business Head and OEM relationships'
        },
        {
          id: 'group-business-manager-oem',
          title: 'Group Business Manager ↔ OEM',
          icon: <FiBarChart2 />,
          description: 'Group Business Manager and OEM performance'
        },
        {
          id: 'business-manager-oem',
          title: 'Business Manager ↔ OEM',
          icon: <FiBriefcase />,
          description: 'Business Manager and OEM analysis'
        },
        {
          id: 'group-channel-champ-partner',
          title: 'Group Channel Champ ↔ Partner',
          icon: <FiTarget />,
          description: 'Group Channel Champ and Partner relationships'
        },
        {
          id: 'channel-champ-partner',
          title: 'Channel Champ ↔ Partner',
          icon: <FiUser />,
          description: 'Channel Champ and Partner performance'
        },
        {
          id: 'vertical-champ-customer',
          title: 'Vertical Champ ↔ End Customer',
          icon: <FiGlobe />,
          description: 'Vertical Champ and End Customer analysis'
        }
      ]
    }
  ];

  const getQuestionsForCategory = (categoryId) => {
    // Questions object would go here - skipped as requested
    return [];
  };

  const resetAllOptions = () => {
    setShowYearOptions(false);
    setShowRegionOptions(false);
    setShowOEMOptions(false);
    setShowPartnerOptions(false);
    setShowVerticalAccountOptions(false);
    setShowChannelOptions(false);
    setShowBusinessHeadOptions(false);
    setShowBusinessManagerOptions(false);
    setShowGroupBusinessManagerOptions(false);
    setShowChannelHeadOptions(false);
    setShowGroupChannelChampOptions(false);
    setShowEndCustomerOptions(false);
    setSelectedMainCategory(null);
    setSelectedSubCategory(null);
    
    // Clear all search inputs
    setOemSearch('');
    setPartnerSearch('');
    setRegionSearch('');
    setVerticalAccountSearch('');
    setChannelSearch('');
    setBusinessHeadSearch('');
    setBusinessManagerSearch('');
    setGroupBusinessManagerSearch('');
    setChannelHeadSearch('');
    setGroupChannelChampSearch('');
    setYearSearch('');
    setEndCustomerSearch('');
  };

  const handleMainCategoryClick = (mainCategoryId) => {
    if (selectedMainCategory === mainCategoryId) {
      // Collapse if clicking on already selected main category
      setSelectedMainCategory(null);
      setSelectedSubCategory(null);
    } else {
      // Expand the main category
      setSelectedMainCategory(mainCategoryId);
      setSelectedSubCategory(null);
    }
    resetAllOptions();
  };

  const handleSubCategoryClick = (subCategoryId) => {
    setSelectedSubCategory(subCategoryId);
    resetAllOptions();
  };

  const handleQuestionClick = (question) => {
    if (onQuestionSelect) {
      onQuestionSelect(question);
    }
  };

  // Generic handler for all select actions
  const handleGenericSelect = async (item, type) => {
    const command = `show performance for ${type} ${item}`;
    setIsLoading(true);
    
    if (onAutoExecuteQuery) {
      try {
        await onAutoExecuteQuery(command);
      } catch (error) {
        console.error('Error executing query:', error);
      }
    } else if (onQuestionSelect) {
      onQuestionSelect(command);
    }
    
    setIsLoading(false);
    resetAllOptions();
  };

  const handleYearSelect = async (year) => {
    const command = `generate regional performance table for ${year}`;
    setIsLoading(true);
    
    if (onAutoExecuteQuery) {
      try {
        await onAutoExecuteQuery(command);
      } catch (error) {
        console.error('Error executing query:', error);
      }
    } else if (onQuestionSelect) {
      onQuestionSelect(command);
    }
    
    setIsLoading(false);
    setShowYearOptions(false);
  };

  // Button click handlers
  const handleYearButtonClick = () => {
    setShowYearOptions(!showYearOptions);
    resetAllOptions();
    setShowYearOptions(true);
  };

  const handleRegionButtonClick = () => {
    setShowRegionOptions(!showRegionOptions);
    resetAllOptions();
    setShowRegionOptions(true);
  };

  const handleOEMButtonClick = () => {
    setShowOEMOptions(!showOEMOptions);
    resetAllOptions();
    setShowOEMOptions(true);
  };

  const handlePartnerButtonClick = () => {
    setShowPartnerOptions(!showPartnerOptions);
    resetAllOptions();
    setShowPartnerOptions(true);
  };

  const handleVerticalAccountButtonClick = () => {
    setShowVerticalAccountOptions(!showVerticalAccountOptions);
    resetAllOptions();
    setShowVerticalAccountOptions(true);
  };

  const handleChannelButtonClick = () => {
    setShowChannelOptions(!showChannelOptions);
    resetAllOptions();
    setShowChannelOptions(true);
  };

  const handleBusinessHeadButtonClick = () => {
    setShowBusinessHeadOptions(!showBusinessHeadOptions);
    resetAllOptions();
    setShowBusinessHeadOptions(true);
  };

  const handleBusinessManagerButtonClick = () => {
    setShowBusinessManagerOptions(!showBusinessManagerOptions);
    resetAllOptions();
    setShowBusinessManagerOptions(true);
  };

  const handleGroupBusinessManagerButtonClick = () => {
    setShowGroupBusinessManagerOptions(!showGroupBusinessManagerOptions);
    resetAllOptions();
    setShowGroupBusinessManagerOptions(true);
  };

  const handleChannelHeadButtonClick = () => {
    setShowChannelHeadOptions(!showChannelHeadOptions);
    resetAllOptions();
    setShowChannelHeadOptions(true);
  };

  const handleGroupChannelChampButtonClick = () => {
    setShowGroupChannelChampOptions(!showGroupChannelChampOptions);
    resetAllOptions();
    setShowGroupChannelChampOptions(true);
  };

  const handleEndCustomerButtonClick = () => {
    setShowEndCustomerOptions(!showEndCustomerOptions);
    resetAllOptions();
    setShowEndCustomerOptions(true);
  };

  const renderMainCategories = () => {
    return mainCategories.map(mainCategory => (
      <div key={mainCategory.id} className="main-category-container">
        <div 
          className={`category-item main-category ${selectedMainCategory === mainCategory.id ? 'active' : ''}`}
          onClick={() => handleMainCategoryClick(mainCategory.id)}
        >
          <div className="category-icon" style={{ background: 'var(--ivalue-primary)' }}>
            {mainCategory.icon}
          </div>
          <div className="category-titles">
            <div className="category-title">{mainCategory.title}</div>
            <div className="category-description">{mainCategory.description}</div>
          </div>
          <div className="expand-icon">
            {selectedMainCategory === mainCategory.id ? <FiChevronUp /> : <FiChevronRight />}
          </div>
        </div>
        
        {selectedMainCategory === mainCategory.id && (
          <div className="subcategories-container">
            {mainCategory.subcategories.map(subCategory => (
              <div 
                key={subCategory.id}
                className={`category-item sub-category ${selectedSubCategory === subCategory.id ? 'active' : ''}`}
                onClick={() => handleSubCategoryClick(subCategory.id)}
              >
                <div className="category-icon sub-icon" style={{ background: 'var(--ivalue-secondary)' }}>
                  {subCategory.icon}
                </div>
                <div className="category-titles">
                  <div className="category-title">{subCategory.title}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    ));
  };

  const getSelectedCategoryInfo = () => {
    if (!selectedSubCategory) return null;
    
    for (const mainCategory of mainCategories) {
      const subCategory = mainCategory.subcategories.find(sub => sub.id === selectedSubCategory);
      if (subCategory) {
        return subCategory;
      }
    }
    return null;
  };

  const selectedCategoryInfo = getSelectedCategoryInfo();

  // Render search bar for options
  const renderSearchBar = (value, onChange, placeholder, onClear) => (
    <div className="options-search-container">
      <div className="options-search-wrapper">
        <FiSearch className="options-search-icon" />
        <input
          type="text"
          placeholder={placeholder}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="options-search-input"
          autoFocus
        />
        {value && (
          <button onClick={onClear} className="options-clear-button">
            <FiX />
          </button>
        )}
      </div>
    </div>
  );

  // Filter options based on search
  const filterOptions = (options, search) => {
    if (!search.trim()) return options;
    const query = search.toLowerCase();
    return options.filter(option => 
      option && option.toString().toLowerCase().includes(query)
    );
  };

  // Generic options container renderer with search
  const renderOptionsContainer = (title, icon, description, options, searchValue, onSearchChange, onClearSearch, onSelect, isDynamic = false) => {
    const filteredOptions = filterOptions(options, searchValue);
    
    return (
      <div className="options-container">
        <div className="options-header">
          <div className="header-icon" style={{ background: 'var(--ivalue-primary)' }}>
            {icon}
          </div>
          <div>
            <div className="options-title-wrapper">
              <h4>{title}</h4>
              {isDynamic && uploadedData && (
                <span className="dynamic-badge">
                  <FiCheck size={12} />
                  <span>Live Data</span>
                </span>
              )}
            </div>
            <p>{description}</p>
            <div className="options-stats">
              <span className="options-count">
                {filteredOptions.length} of {options.length} options
                {searchValue && ` matching "${searchValue}"`}
              </span>
              {isDynamic && (
                <span className="data-source">
                  <FiUpload size={12} />
                  <span>From uploaded file</span>
                </span>
              )}
            </div>
          </div>
        </div>
        
        {/* Search Bar for this specific option */}
        {renderSearchBar(searchValue, onSearchChange, `Type to search ${title.toLowerCase()}...`, onClearSearch)}
        
        <div className="options-grid">
          {filteredOptions.map((option, index) => (
            <motion.button
              key={index}
              className="option-button"
              onClick={() => onSelect(option)}
              disabled={isLoading}
              whileHover={{ scale: 1.02, backgroundColor: 'var(--ivalue-primary-dark)' }}
              whileTap={{ scale: 0.98 }}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, delay: index * 0.01 }}
            >
              {isLoading ? 'Loading...' : option}
            </motion.button>
          ))}
          {filteredOptions.length === 0 && (
            <div className="no-results">
              <FiSearch size={32} className="no-results-icon" />
              <p>No {title.toLowerCase()} found for "{searchValue}"</p>
              <button onClick={onClearSearch} className="clear-search-btn">
                Clear search
              </button>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <>
      <div className={`question-panel ${isOpen ? 'open' : ''}`}>
        <div className="panel-header">
          <div className="header-content">
            <h3>Question Suggestions</h3>
            <p>Select a question to ask the AI</p>
          </div>
          <div className="data-info">
            <div className="ai-assistant-info">
              <span className="ai-icon">🤖</span>
              <div className="ai-details">
                <div className="ai-name">iValue AI Assistant</div>
                <div className="ai-data">
                  {uploadedData ? 'Live Sales Data' : 'Sample Data Analysis'}
                </div>
              </div>
            </div>
            {uploadedData && (
              <div className="data-status">
                <FiCheck className="status-icon" />
                <span>Dynamic Data Loaded</span>
              </div>
            )}
          </div>
        </div>

        <div className="panel-content">
          <div className="categories-sidebar">
            {/* Year Button */}
            <div 
              className={`quick-action-button ${showYearOptions ? 'active-highlighted' : ''}`}
              onClick={handleYearButtonClick}
            >
              <div className="category-icon" style={{ background: 'var(--ivalue-primary)' }}>
                <FiCalendar />
              </div>
              <div className="category-titles">
                <div className="category-title">Year</div>
                <div className="category-description">Select year period</div>
              </div>
              <div className="expand-icon">
                <FiChevronDown />
              </div>
            </div>

            {/* Region Button */}
            <div 
              className={`quick-action-button ${showRegionOptions ? 'active-highlighted' : ''}`}
              onClick={handleRegionButtonClick}
            >
              <div className="category-icon" style={{ background: 'var(--ivalue-primary)' }}>
                <FiMap />
              </div>
              <div className="category-titles">
                <div className="category-title">Region</div>
                <div className="category-description">Select region</div>
              </div>
              <div className="expand-icon">
                <FiChevronDown />
              </div>
            </div>

            {/* OEM Button */}
            <div 
              className={`quick-action-button ${showOEMOptions ? 'active-highlighted' : ''}`}
              onClick={handleOEMButtonClick}
            >
              <div className="category-icon" style={{ background: 'var(--ivalue-primary)' }}>
                <FiServer />
              </div>
              <div className="category-titles">
                <div className="category-title">OEM</div>
                <div className="category-description">Select OEM vendor</div>
              </div>
              <div className="expand-icon">
                <FiChevronDown />
              </div>
            </div>

            {/* Partner Button */}
            <div 
              className={`quick-action-button ${showPartnerOptions ? 'active-highlighted' : ''}`}
              onClick={handlePartnerButtonClick}
            >
              <div className="category-icon" style={{ background: 'var(--ivalue-primary)' }}>
                <FiShield />
              </div>
              <div className="category-titles">
                <div className="category-title">Partner</div>
                <div className="category-description">Select partner</div>
              </div>
              <div className="expand-icon">
                <FiChevronDown />
              </div>
            </div>

            {/* End Customer Button */}
            <div 
              className={`quick-action-button ${showEndCustomerOptions ? 'active-highlighted' : ''}`}
              onClick={handleEndCustomerButtonClick}
            >
              <div className="category-icon" style={{ background: 'var(--ivalue-primary)' }}>
                <FiUserCheck />
              </div>
              <div className="category-titles">
                <div className="category-title">End Customer</div>
                <div className="category-description">Select end customer</div>
              </div>
              <div className="expand-icon">
                <FiChevronDown />
              </div>
            </div>

            {/* Vertical Account Button */}
            <div 
              className={`quick-action-button ${showVerticalAccountOptions ? 'active-highlighted' : ''}`}
              onClick={handleVerticalAccountButtonClick}
            >
              <div className="category-icon" style={{ background: 'var(--ivalue-primary)' }}>
                <FiDatabase />
              </div>
              <div className="category-titles">
                <div className="category-title">Vertical Account</div>
                <div className="category-description">Select vertical account</div>
              </div>
              <div className="expand-icon">
                <FiChevronDown />
              </div>
            </div>

            {/* Channel Button */}
            <div 
              className={`quick-action-button ${showChannelOptions ? 'active-highlighted' : ''}`}
              onClick={handleChannelButtonClick}
            >
              <div className="category-icon" style={{ background: 'var(--ivalue-primary)' }}>
                <FiLayers />
              </div>
              <div className="category-titles">
                <div className="category-title">Channel</div>
                <div className="category-description">Select channel type</div>
              </div>
              <div className="expand-icon">
                <FiChevronDown />
              </div>
            </div>

            {/* Business Head Name Button */}
            <div 
              className={`quick-action-button ${showBusinessHeadOptions ? 'active-highlighted' : ''}`}
              onClick={handleBusinessHeadButtonClick}
            >
              <div className="category-icon" style={{ background: 'var(--ivalue-primary)' }}>
                <FiUserCheck />
              </div>
              <div className="category-titles">
                <div className="category-title">Business Head</div>
                <div className="category-description">Select business head</div>
              </div>
              <div className="expand-icon">
                <FiChevronDown />
              </div>
            </div>

            {/* Business Manager Name Button */}
            <div 
              className={`quick-action-button ${showBusinessManagerOptions ? 'active-highlighted' : ''}`}
              onClick={handleBusinessManagerButtonClick}
            >
              <div className="category-icon" style={{ background: 'var(--ivalue-primary)' }}>
                <FiUser />
              </div>
              <div className="category-titles">
                <div className="category-title">Business Manager</div>
                <div className="category-description">Select business manager</div>
              </div>
              <div className="expand-icon">
                <FiChevronDown />
              </div>
            </div>

            {/* Group Business Manager Name Button */}
            <div 
              className={`quick-action-button ${showGroupBusinessManagerOptions ? 'active-highlighted' : ''}`}
              onClick={handleGroupBusinessManagerButtonClick}
            >
              <div className="category-icon" style={{ background: 'var(--ivalue-primary)' }}>
                <FiUsers />
              </div>
              <div className="category-titles">
                <div className="category-title">Group Business Manager</div>
                <div className="category-description">Select group business manager</div>
              </div>
              <div className="expand-icon">
                <FiChevronDown />
              </div>
            </div>

            {/* Channel Head Button */}
            <div 
              className={`quick-action-button ${showChannelHeadOptions ? 'active-highlighted' : ''}`}
              onClick={handleChannelHeadButtonClick}
            >
              <div className="category-icon" style={{ background: 'var(--ivalue-primary)' }}>
                <FiUserX />
              </div>
              <div className="category-titles">
                <div className="category-title">Channel Head</div>
                <div className="category-description">Select channel head</div>
              </div>
              <div className="expand-icon">
                <FiChevronDown />
              </div>
            </div>

            {/* Group Channel Champ Name Button */}
            <div 
              className={`quick-action-button ${showGroupChannelChampOptions ? 'active-highlighted' : ''}`}
              onClick={handleGroupChannelChampButtonClick}
            >
              <div className="category-icon" style={{ background: 'var(--ivalue-primary)' }}>
                <FiUserPlus />
              </div>
              <div className="category-titles">
                <div className="category-title">Group Channel Champ</div>
                <div className="category-description">Select group channel champ</div>
              </div>
              <div className="expand-icon">
                <FiChevronDown />
              </div>
            </div>

            {/* Section spacer */}
            <div className="section-spacer"></div>

            {renderMainCategories()}
          </div>

          <div className="questions-container">
            {showYearOptions ? (
              <div className="options-container">
                <div className="options-header">
                  <div className="header-icon" style={{ background: 'var(--ivalue-primary)' }}>
                    <FiCalendar />
                  </div>
                  <div>
                    <h4>Select Year Period</h4>
                    <p>Choose a financial year for your analysis</p>
                  </div>
                </div>
                
                <div className="options-grid">
                  {yearOptions.map((year, index) => (
                    <motion.button
                      key={index}
                      className="option-button"
                      onClick={() => handleYearSelect(year)}
                      disabled={isLoading}
                      whileHover={{ scale: 1.02, backgroundColor: 'var(--ivalue-primary-dark)' }}
                      whileTap={{ scale: 0.98 }}
                    >
                      {isLoading ? 'Loading...' : year}
                    </motion.button>
                  ))}
                </div>
              </div>
            ) : showRegionOptions ? (
              renderOptionsContainer(
                'Select Region',
                <FiMap />,
                'Choose a region for your analysis',
                regionOptions,
                regionSearch,
                setRegionSearch,
                () => setRegionSearch(''),
                (region) => handleGenericSelect(region, 'region'),
                extractedValues.regions.length > 0
              )
            ) : showOEMOptions ? (
              renderOptionsContainer(
                'Select OEM',
                <FiServer />,
                'Choose an OEM vendor for analysis',
                oemOptions,
                oemSearch,
                setOemSearch,
                () => setOemSearch(''),
                (oem) => handleGenericSelect(oem, 'OEM'),
                extractedValues.oems.length > 0
              )
            ) : showPartnerOptions ? (
              renderOptionsContainer(
                'Select Partner',
                <FiShield />,
                'Choose a partner for analysis',
                partnerOptions,
                partnerSearch,
                setPartnerSearch,
                () => setPartnerSearch(''),
                (partner) => handleGenericSelect(partner, 'partner'),
                extractedValues.partners.length > 0
              )
            ) : showEndCustomerOptions ? (
              renderOptionsContainer(
                'Select End Customer',
                <FiUserCheck />,
                'Choose an end customer for analysis',
                endCustomerOptions,
                endCustomerSearch,
                setEndCustomerSearch,
                () => setEndCustomerSearch(''),
                (endCustomer) => handleGenericSelect(endCustomer, 'end customer'),
                extractedValues.endCustomers.length > 0
              )
            ) : showVerticalAccountOptions ? (
              renderOptionsContainer(
                'Select Vertical Account',
                <FiDatabase />,
                'Choose a vertical account for analysis',
                verticalAccountOptions,
                verticalAccountSearch,
                setVerticalAccountSearch,
                () => setVerticalAccountSearch(''),
                (verticalAccount) => handleGenericSelect(verticalAccount, 'vertical account'),
                extractedValues.verticalAccounts.length > 0
              )
            ) : showChannelOptions ? (
              renderOptionsContainer(
                'Select Channel',
                <FiLayers />,
                'Choose a channel type for analysis',
                channelOptions,
                channelSearch,
                setChannelSearch,
                () => setChannelSearch(''),
                (channel) => handleGenericSelect(channel, 'channel'),
                extractedValues.channels.length > 0
              )
            ) : showBusinessHeadOptions ? (
              renderOptionsContainer(
                'Select Business Head',
                <FiUserCheck />,
                'Choose a business head for analysis',
                businessHeadOptions,
                businessHeadSearch,
                setBusinessHeadSearch,
                () => setBusinessHeadSearch(''),
                (businessHead) => handleGenericSelect(businessHead, 'business head'),
                extractedValues.businessHeads.length > 0
              )
            ) : showBusinessManagerOptions ? (
              renderOptionsContainer(
                'Select Business Manager',
                <FiUser />,
                'Choose a business manager for analysis',
                businessManagerOptions,
                businessManagerSearch,
                setBusinessManagerSearch,
                () => setBusinessManagerSearch(''),
                (businessManager) => handleGenericSelect(businessManager, 'business manager'),
                extractedValues.businessManagers.length > 0
              )
            ) : showGroupBusinessManagerOptions ? (
              renderOptionsContainer(
                'Select Group Business Manager',
                <FiUsers />,
                'Choose a group business manager for analysis',
                groupBusinessManagerOptions,
                groupBusinessManagerSearch,
                setGroupBusinessManagerSearch,
                () => setGroupBusinessManagerSearch(''),
                (groupBusinessManager) => handleGenericSelect(groupBusinessManager, 'group business manager'),
                extractedValues.groupBusinessManagers.length > 0
              )
            ) : showChannelHeadOptions ? (
              renderOptionsContainer(
                'Select Channel Head',
                <FiUserX />,
                'Choose a channel head for analysis',
                channelHeadOptions,
                channelHeadSearch,
                setChannelHeadSearch,
                () => setChannelHeadSearch(''),
                (channelHead) => handleGenericSelect(channelHead, 'channel head'),
                extractedValues.channelHeads.length > 0
              )
            ) : showGroupChannelChampOptions ? (
              renderOptionsContainer(
                'Select Group Channel Champ',
                <FiUserPlus />,
                'Choose a group channel champ for analysis',
                groupChannelChampOptions,
                groupChannelChampSearch,
                setGroupChannelChampSearch,
                () => setGroupChannelChampSearch(''),
                (groupChannelChamp) => handleGenericSelect(groupChannelChamp, 'group channel champ'),
                extractedValues.groupChannelChamps.length > 0
              )
            ) : selectedCategoryInfo ? (
              <>
                <div className="questions-header">
                  <div className="header-icon" style={{ background: 'var(--ivalue-primary)' }}>
                    {selectedCategoryInfo.icon}
                  </div>
                  <h4>{selectedCategoryInfo.title} Questions</h4>
                </div>

                <div className="questions-list">
                  {getQuestionsForCategory(selectedSubCategory).map((question, index) => (
                    <div 
                      key={index}
                      className="question-item"
                      onClick={() => handleQuestionClick(question)}
                    >
                      <div className="question-content">
                        <div className="question-text">{question}</div>
                        <div className="question-arrow">→</div>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="no-selection">
                <div className="no-selection-content">
                  <div className="no-selection-icon">
                    <FiTrendingUp size={48} />
                  </div>
                  <h4>Select a Category</h4>
                  <p>Choose a main category and then a subcategory to view available questions</p>
                  {uploadedData && (
                    <div className="uploaded-data-info">
                      <FiCheck size={16} />
                      <span>Using dynamic data from uploaded file</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <button className="panel-toggle" onClick={onToggle}>
        {isOpen ? <FiChevronLeft /> : <FiChevronRight />}
      </button>
      
      <style jsx>{`
        .main-category-container {
          margin-bottom: 8px;
        }

        .main-category {
          border-left: 3px solid transparent;
          cursor: pointer;
          transition: all 0.2s ease;
          padding: 16px 20px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
          display: flex;
          align-items: center;
        }

        .main-category.active {
          border-left-color: var(--ivalue-primary);
          background: rgba(var(--ivalue-primary-rgb), 0.1);
        }

        .main-category .expand-icon {
          margin-left: auto;
          opacity: 0.6;
          transition: transform 0.2s ease;
          color: var(--text-secondary);
        }

        .main-category .category-icon {
          margin-right: 12px;
          flex-shrink: 0;
        }

        .main-category .category-titles {
          flex: 1;
          min-width: 0;
        }

        .main-category .category-title {
          font-weight: 600;
          font-size: 15px;
          color: var(--text-primary);
          margin-bottom: 2px;
        }

        .main-category .category-description {
          font-size: 12px;
          color: var(--text-secondary);
          opacity: 0.8;
        }

        .subcategories-container {
          margin-left: 20px;
          border-left: 2px solid rgba(var(--ivalue-primary-rgb), 0.2);
          padding-left: 10px;
          margin-top: 8px;
        }

        .sub-category {
          margin-bottom: 4px;
          border-left: 2px solid transparent;
          cursor: pointer;
          transition: all 0.2s ease;
          padding: 12px 16px;
          display: flex;
          align-items: center;
        }

        .sub-category.active {
          border-left-color: var(--ivalue-secondary, var(--ivalue-primary));
          background: rgba(var(--ivalue-secondary-rgb, var(--ivalue-primary-rgb)), 0.1);
        }

        .sub-icon {
          transform: scale(0.8);
          margin-right: 12px;
        }

        .no-selection {
          display: flex;
          align-items: center;
          justify-content: center;
          height: 100%;
          padding: 40px;
        }

        .no-selection-content {
          text-align: center;
          opacity: 0.6;
        }

        .no-selection-icon {
          margin-bottom: 20px;
          color: var(--ivalue-primary);
        }

        .no-selection h4 {
          margin-bottom: 10px;
          color: var(--text-primary);
        }

        .no-selection p {
          color: var(--text-secondary);
          font-size: 14px;
          line-height: 1.5;
        }

        .uploaded-data-info {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          margin-top: 16px;
          padding: 8px 16px;
          background: rgba(72, 187, 120, 0.1);
          border: 1px solid rgba(72, 187, 120, 0.2);
          border-radius: 6px;
          color: #48BB78;
          font-size: 14px;
          font-weight: 500;
        }

        /* Quick Action Button Styles */
        .quick-action-button {
          display: flex;
          align-items: center;
          padding: 16px 20px;
          cursor: pointer;
          border-left: 3px solid transparent;
          transition: all 0.2s ease;
          margin-bottom: 0;
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
          background: transparent;
        }
        
        .quick-action-button:hover {
          background: rgba(var(--ivalue-primary-rgb), 0.08);
        }
        
        .quick-action-button.active-highlighted {
          border-left-color: #10B981;
          background: linear-gradient(135deg, 
            rgba(16, 185, 129, 0.15) 0%, 
            rgba(16, 185, 129, 0.25) 50%, 
            rgba(16, 185, 129, 0.15) 100%);
          box-shadow: inset 0 1px 3px rgba(16, 185, 129, 0.2), 
                      0 0 0 1px rgba(16, 185, 129, 0.1);
        }
        
        .quick-action-button.active-highlighted .category-icon {
          background: #10B981 !important;
          box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
          transform: scale(1.05);
        }
        
        .quick-action-button.active-highlighted .category-title {
          color: #10B981;
          font-weight: 700;
        }
        
        .quick-action-button.active-highlighted .expand-icon {
          color: #10B981;
          opacity: 1;
          transform: scale(1.1);
        }

        .quick-action-button .category-icon {
          margin-right: 12px;
          flex-shrink: 0;
          transition: all 0.2s ease;
        }

        .quick-action-button .category-titles {
          flex: 1;
          min-width: 0;
        }

        .quick-action-button .category-title {
          font-weight: 600;
          font-size: 15px;
          color: var(--text-primary);
          margin-bottom: 2px;
          transition: all 0.2s ease;
        }

        .quick-action-button .category-description {
          font-size: 12px;
          color: var(--text-secondary);
          opacity: 0.8;
        }

        .quick-action-button .expand-icon {
          margin-left: 8px;
          opacity: 0.7;
          transition: all 0.2s ease;
          color: var(--text-secondary);
        }

        /* Section spacer */
        .section-spacer {
          height: 1px;
          background: rgba(255, 255, 255, 0.1);
          margin: 12px 16px;
        }

        /* Options Container */
        .options-container {
          padding: 24px;
          height: 100%;
          display: flex;
          flex-direction: column;
        }
        
        .options-header {
          margin-bottom: 16px;
          display: flex;
          align-items: flex-start;
          gap: 16px;
          padding: 0 8px;
        }

        .options-header .header-icon {
          width: 48px;
          height: 48px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }

        .options-title-wrapper {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 4px;
        }

        .options-header h4 {
          color: var(--text-primary);
          font-size: 18px;
          margin: 0;
        }

        .dynamic-badge {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          padding: 2px 8px;
          background: rgba(72, 187, 120, 0.2);
          border: 1px solid rgba(72, 187, 120, 0.3);
          border-radius: 12px;
          font-size: 11px;
          font-weight: 600;
          color: #48BB78;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .options-header p {
          color: var(--text-secondary);
          font-size: 14px;
          margin-bottom: 8px;
        }

        .options-stats {
          display: flex;
          align-items: center;
          gap: 16px;
          font-size: 12px;
          color: var(--text-secondary);
        }

        .options-count {
          display: inline-flex;
          align-items: center;
          gap: 4px;
        }

        .data-source {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          color: #48BB78;
        }

        /* Data status in header */
        .data-status {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 4px 10px;
          background: rgba(72, 187, 120, 0.1);
          border: 1px solid rgba(72, 187, 120, 0.2);
          border-radius: 12px;
          font-size: 12px;
          font-weight: 600;
          color: #48BB78;
          margin-left: 8px;
        }

        .status-icon {
          font-size: 10px;
        }

        /* Options Search Bar */
        .options-search-container {
          margin-bottom: 20px;
          padding: 0 8px;
        }

        .options-search-wrapper {
          position: relative;
          display: flex;
          align-items: center;
        }

        .options-search-icon {
          position: absolute;
          left: 12px;
          color: var(--text-secondary);
          font-size: 16px;
        }

        .options-search-input {
          width: 100%;
          padding: 12px 40px 12px 40px;
          background: rgba(255, 255, 255, 0.1);
          border: 1px solid rgba(255, 255, 255, 0.2);
          border-radius: 8px;
          color: var(--text-primary);
          font-size: 14px;
          transition: all 0.2s ease;
        }

        .options-search-input:focus {
          outline: none;
          border-color: var(--ivalue-primary);
          background: rgba(255, 255, 255, 0.15);
          box-shadow: 0 0 0 2px rgba(var(--ivalue-primary-rgb), 0.2);
        }

        .options-search-input::placeholder {
          color: var(--text-secondary);
          opacity: 0.7;
        }

        .options-clear-button {
          position: absolute;
          right: 10px;
          background: transparent;
          border: none;
          color: var(--text-secondary);
          cursor: pointer;
          padding: 4px;
          border-radius: 4px;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.2s ease;
        }

        .options-clear-button:hover {
          color: var(--text-primary);
          background: rgba(255, 255, 255, 0.1);
        }

        .options-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
          gap: 12px;
          flex: 1;
          align-content: flex-start;
          overflow-y: auto;
          max-height: calc(100vh - 250px);
          padding-right: 4px;
        }

        .options-grid::-webkit-scrollbar {
          width: 6px;
        }

        .options-grid::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 3px;
        }

        .options-grid::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.2);
          border-radius: 3px;
        }

        .options-grid::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.3);
        }

        .option-button {
          background: rgba(var(--ivalue-primary-rgb), 0.2);
          border: 1px solid rgba(var(--ivalue-primary-rgb), 0.3);
          color: var(--text-primary);
          padding: 16px 12px;
          border-radius: 12px;
          font-weight: 500;
          font-size: 14px;
          cursor: pointer;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          justify-content: center;
          text-align: center;
          min-height: 52px;
          word-break: break-word;
          white-space: normal;
        }

        .option-button:hover:not(:disabled) {
          background: rgba(var(--ivalue-primary-rgb), 0.3);
          border-color: rgba(var(--ivalue-primary-rgb), 0.5);
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }

        .option-button:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }

        .no-results {
          grid-column: 1 / -1;
          text-align: center;
          padding: 40px 20px;
          color: var(--text-secondary);
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 12px;
        }

        .no-results-icon {
          opacity: 0.5;
          margin-bottom: 8px;
        }

        .no-results p {
          font-size: 14px;
          opacity: 0.7;
          margin: 0;
        }

        .clear-search-btn {
          background: rgba(var(--ivalue-primary-rgb), 0.2);
          border: 1px solid rgba(var(--ivalue-primary-rgb), 0.3);
          color: var(--text-primary);
          padding: 8px 16px;
          border-radius: 6px;
          font-size: 13px;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .clear-search-btn:hover {
          background: rgba(var(--ivalue-primary-rgb), 0.3);
        }

        /* Panel header updates */
        .panel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 20px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .header-content h3 {
          margin: 0 0 4px 0;
          font-size: 18px;
          color: var(--text-primary);
        }

        .header-content p {
          margin: 0;
          font-size: 14px;
          color: var(--text-secondary);
        }

        .data-info {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .ai-assistant-info {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 8px 12px;
          background: rgba(59, 130, 246, 0.1);
          border-radius: 8px;
        }

        .ai-icon {
          font-size: 20px;
        }

        .ai-details {
          display: flex;
          flex-direction: column;
        }

        .ai-name {
          font-weight: 600;
          font-size: 14px;
          color: var(--text-primary);
        }

        .ai-data {
          font-size: 12px;
          color: var(--text-secondary);
        }
      `}</style>
    </>
  );
};

export default QuestionPanel;
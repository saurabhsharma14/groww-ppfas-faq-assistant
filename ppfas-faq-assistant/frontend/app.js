document.addEventListener('DOMContentLoaded', () => {
  const chatForm = document.getElementById('chat-form');
  const chatInput = document.getElementById('chat-input');
  const sendBtn = document.getElementById('send-btn');
  const chatWindow = document.getElementById('chat-window');
  const charCount = document.getElementById('char-count');
  const charCounter = document.querySelector('.char-counter');
  
  const MAX_CHARS = 300;
  const API_URL = 'https://web-production-d515e.up.railway.app/ask'; // Ensure the backend is running here
  
  let consecutiveRefusals = 0;

  // Handle character count
  chatInput.addEventListener('input', () => {
    const length = chatInput.value.length;
    charCount.textContent = length;
    
    sendBtn.disabled = length === 0 || chatInput.value.trim() === '';
    
    if (length >= MAX_CHARS * 0.9) {
      charCounter.classList.add('near-limit');
      charCounter.classList.remove('at-limit');
    } else {
      charCounter.classList.remove('near-limit');
      charCounter.classList.remove('at-limit');
    }
    
    if (length >= MAX_CHARS) {
      charCounter.classList.remove('near-limit');
      charCounter.classList.add('at-limit');
    }
  });

  const allQuestions = [
    { icon: '📈', text: 'What is the expense ratio of Parag Parikh Flexi Cap Fund?' },
    { icon: '🚪', text: 'What is the exit load of the ELSS Tax Saver Fund?' },
    { icon: '💰', text: 'What is the minimum SIP amount for Parag Parikh Liquid Fund?' },
    { icon: '💼', text: 'What is the total AUM of the Conservative Hybrid Fund?' },
    { icon: '📅', text: 'Is there a lock-in period for the ELSS Tax Saver Fund?' },
    { icon: '⏱️', text: 'What is the minimum lump sum investment for the Flexi Cap Fund?' },
    { icon: '📉', text: 'What is the benchmark index for the Liquid Fund?' },
    { icon: '🏆', text: 'Who is the fund manager for the ELSS Tax Saver Fund?' },
    { icon: '⚠️', text: 'What is the risk level of the Arbitrage Fund?' }
  ];

  const exampleContainer = document.getElementById('example-questions');
  if (exampleContainer) {
    const shuffled = [...allQuestions].sort(() => 0.5 - Math.random());
    const selected = shuffled.slice(0, 5);
    
    selected.forEach(q => {
      const btn = document.createElement('button');
      btn.className = 'example-btn';
      btn.innerHTML = `<span class="btn-icon">${q.icon}</span><span class="btn-text">${q.text}</span>`;
      
      btn.addEventListener('click', () => {
        chatInput.value = q.text;
        chatInput.dispatchEvent(new Event('input'));
        chatForm.dispatchEvent(new Event('submit'));
      });
      
      exampleContainer.appendChild(btn);
    });
  }

  // Scroll to bottom
  const scrollToBottom = () => {
    const chatContainer = document.querySelector('.chat-container');
    chatContainer.scrollTo({
      top: chatContainer.scrollHeight,
      behavior: 'smooth'
    });
  };

  // Add user message
  const addUserMessage = (text) => {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message user-message';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = text;
    
    msgDiv.appendChild(contentDiv);
    chatWindow.appendChild(msgDiv);
    scrollToBottom();
  };

  // Add assistant message
  const addAssistantMessage = (data) => {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message assistant-message';
    
    if (data.is_refusal) {
      msgDiv.classList.add('refusal');
      consecutiveRefusals++;
    } else {
      consecutiveRefusals = 0;
    }

    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'avatar-container';
    avatarDiv.innerHTML = '<div class="avatar">🤖</div>';
    msgDiv.appendChild(avatarDiv);

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const textP = document.createElement('p');
    // Parse markdown bold: **text** -> <strong>text</strong>
    textP.innerHTML = data.answer.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    contentDiv.appendChild(textP);

    if (data.source_url) {
      const footerDiv = document.createElement('div');
      footerDiv.className = 'msg-footer';
      
      const extractTitleFromUrl = (url) => {
        try {
          const urlObj = new URL(url);
          const pathSegments = urlObj.pathname.split('/').filter(Boolean);
          const lastSegment = pathSegments[pathSegments.length - 1];
          if (lastSegment) {
            return lastSegment.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
          }
        } catch (e) {}
        return url;
      };
      
      const title = extractTitleFromUrl(data.source_url);
      
      const sourceLine = document.createElement('div');
      sourceLine.className = 'source-line';
      sourceLine.innerHTML = `Source:<br><a href="${data.source_url}" target="_blank" rel="noopener noreferrer" class="source-link">🔗 ${title}</a>`;
      footerDiv.appendChild(sourceLine);
      
      if (data.last_updated) {
        const updateLine = document.createElement('div');
        updateLine.textContent = `Last updated from sources: ${data.last_updated}`;
        footerDiv.appendChild(updateLine);
      }
      
      contentDiv.appendChild(footerDiv);
    }
    
    if (consecutiveRefusals >= 2) {
      const helpP = document.createElement('p');
      helpP.style.marginTop = '12px';
      helpP.style.fontSize = '0.85rem';
      helpP.innerHTML = '<em>Tip: Try asking factual questions like "What is the exit load?" or "What is the minimum SIP?"</em>';
      contentDiv.appendChild(helpP);
    }

    msgDiv.appendChild(contentDiv);
    chatWindow.appendChild(msgDiv);
    scrollToBottom();
  };

  // Add error message
  const addErrorMessage = (text) => {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message assistant-message error';
    
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'avatar-container';
    avatarDiv.innerHTML = '<div class="avatar">⚠️</div>';
    msgDiv.appendChild(avatarDiv);

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = text;
    
    msgDiv.appendChild(contentDiv);
    chatWindow.appendChild(msgDiv);
    scrollToBottom();
  };

  let typingInterval;
  
  // Add typing indicator
  const showTypingIndicator = () => {
    const indicatorDiv = document.createElement('div');
    indicatorDiv.className = 'message assistant-message typing-indicator';
    indicatorDiv.id = 'typing-indicator';
    
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'avatar-container';
    avatarDiv.innerHTML = '<div class="avatar">🤖</div>';
    indicatorDiv.appendChild(avatarDiv);

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content dynamic-thinking';
    
    const statuses = [
      'Thinking...',
      'Connecting to Groww...',
      'Fetching your information...',
      'Analyzing data...',
      'Crunching the numbers...',
      'Getting the facts...'
    ];
    
    let idx = 0;
    
    const statusText = document.createElement('span');
    statusText.id = 'thinking-text';
    statusText.textContent = statuses[0];
    
    typingInterval = setInterval(() => {
      idx = (idx + 1) % statuses.length;
      statusText.textContent = statuses[idx];
    }, 400);
    
    contentDiv.appendChild(statusText);
    indicatorDiv.appendChild(contentDiv);
    chatWindow.appendChild(indicatorDiv);
    scrollToBottom();
  };

  // Remove typing indicator
  const removeTypingIndicator = () => {
    if (typingInterval) clearInterval(typingInterval);
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
      indicator.remove();
    }
  };

  // Fetch with timeout
  const fetchWithTimeout = async (url, options, timeout = 10000) => {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);
    try {
      const response = await fetch(url, { ...options, signal: controller.signal });
      clearTimeout(id);
      return response;
    } catch (error) {
      clearTimeout(id);
      throw error;
    }
  };

  // Handle form submission
  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = chatInput.value.trim();
    if (!query) return;

    addUserMessage(query);
    chatInput.value = '';
    chatInput.dispatchEvent(new Event('input')); // Reset counter & button
    
    showTypingIndicator();

    try {
      const response = await fetchWithTimeout(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      }, 60000);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      removeTypingIndicator();
      addAssistantMessage(data);

    } catch (error) {
      removeTypingIndicator();
      if (error.name === 'AbortError') {
        addErrorMessage('Unable to connect (timeout). Please check your connection or try again later.');
      } else {
        addErrorMessage('Service temporarily unavailable. Please try again shortly or visit groww.in.');
      }
      console.error('Chat error:', error);
    }
  });
});

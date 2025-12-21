// API Configuration
const API_BASE_URL = 'http://localhost:8000/api';

// DOM Elements
const themeToggle = document.getElementById('themeToggle');
const newChatBtn = document.getElementById('newChatBtn');
const chatForm = document.getElementById('chatForm');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const messagesContainer = document.getElementById('messagesContainer');
const welcomeScreen = document.getElementById('welcomeScreen');
const chatHistory = document.getElementById('chatHistory');
const suggestionCards = document.querySelectorAll('.suggestion-card');

// State Management
let currentChatId = null;
let chatSessions = [];
let isLoading = false;

// Theme Management
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

// Auto-resize textarea
function autoResizeTextarea() {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 80) + 'px';
}

// Format timestamp
function formatTime(date) {
    const now = new Date();
    const diff = now - date;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (seconds < 60) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return date.toLocaleDateString();
}

// Create message element
function createMessageElement(message, isUser) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = isUser ? 'U' : 'AI';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    const header = document.createElement('div');
    header.className = 'message-header';
    
    const author = document.createElement('span');
    author.className = 'message-author';
    author.textContent = isUser ? 'You' : 'Bank Advisor';
    
    const time = document.createElement('span');
    time.className = 'message-time';
    time.textContent = formatTime(new Date());
    
    header.appendChild(author);
    header.appendChild(time);
    
    const text = document.createElement('div');
    text.className = 'message-text';
    text.innerHTML = formatMessage(message);
    
    content.appendChild(header);
    content.appendChild(text);
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    return messageDiv;
}

// Create loading indicator
function createLoadingElement() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant loading';
    messageDiv.id = 'loading-message';
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = 'AI';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    const dots = document.createElement('div');
    dots.className = 'loading-dots';
    dots.innerHTML = '<span></span><span></span><span></span>';
    
    content.appendChild(dots);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    return messageDiv;
}

// Format message text (basic markdown support + tables)
function formatMessage(text) {
    // Escape HTML first
    text = text.replace(/&/g, '&amp;')
               .replace(/</g, '&lt;')
               .replace(/>/g, '&gt;');
    
    // Detect and render charts
    text = text.replace(/\[CHART:(\w+)\|labels:([^|]+)\|data:([^|]+)\]/g, function(match, type, labels, data) {
        return createChartElement(type, labels.split(','), data.split(','));
    });
    
    // Detect and format tables (markdown style)
    text = text.replace(/(\|.+\|[\r\n]+\|[-:\s|]+\|[\r\n]+(?:\|.+\|[\r\n]*)+)/g, function(match) {
        return convertMarkdownTableToHTML(match);
    });
    
    // Code blocks
    text = text.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    
    // Inline code
    text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Bold
    text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    
    // Italic
    text = text.replace(/\*(.+?)\*/g, '<em>$1</em>');
    
    // Line breaks
    text = text.replace(/\n/g, '<br>');
    
    return text;
}

// Convert markdown table to HTML
function convertMarkdownTableToHTML(markdown) {
    const lines = markdown.trim().split(/[\r\n]+/);
    if (lines.length < 3) return markdown;
    
    let html = '<div class="table-wrapper"><table class="data-table">';
    
    // Header row
    const headers = lines[0].split('|').filter(cell => cell.trim());
    html += '<thead><tr>';
    headers.forEach(header => {
        html += `<th>${header.trim()}</th>`;
    });
    html += '</tr></thead>';
    
    // Skip separator line (lines[1])
    
    // Body rows
    html += '<tbody>';
    for (let i = 2; i < lines.length; i++) {
        const cells = lines[i].split('|').filter(cell => cell.trim());
        if (cells.length > 0) {
            html += '<tr>';
            cells.forEach(cell => {
                html += `<td>${cell.trim()}</td>`;
            });
            html += '</tr>';
        }
    }
    html += '</tbody></table></div>';
    
    return html;
}

function createChartElement(type, labels, data) {
    const chartId = 'chart-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    const canvas = document.createElement('canvas');
    canvas.id = chartId;
    canvas.width = 400;
    canvas.height = 200;
    
    // Use setTimeout to ensure the canvas is in the DOM before creating the chart
    setTimeout(() => {
        const ctx = document.getElementById(chartId).getContext('2d');
        new Chart(ctx, {
            type: type,
            data: {
                labels: labels,
                datasets: [{
                    label: 'Data',
                    data: data.map(d => parseFloat(d.trim())),
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }, 100);
    
    return canvas.outerHTML;
}

// Detect and format JSON as table
function formatJSONAsTable(jsonStr) {
    try {
        const data = JSON.parse(jsonStr);
        
        if (Array.isArray(data) && data.length > 0) {
            // Get all unique keys from all objects
            const allKeys = [...new Set(data.flatMap(obj => Object.keys(obj)))];
            
            let html = '<div class="table-wrapper"><table class="data-table">';
            
            // Header
            html += '<thead><tr>';
            allKeys.forEach(key => {
                html += `<th>${key}</th>`;
            });
            html += '</tr></thead>';
            
            // Body
            html += '<tbody>';
            data.forEach(row => {
                html += '<tr>';
                allKeys.forEach(key => {
                    const value = row[key] !== undefined ? row[key] : '';
                    html += `<td>${String(value)}</td>`;
                });
                html += '</tr>';
            });
            html += '</tbody></table></div>';
            
            return html;
        } else if (typeof data === 'object' && data !== null) {
            // Single object - display as key-value table
            let html = '<div class="table-wrapper"><table class="data-table">';
            html += '<thead><tr><th>Property</th><th>Value</th></tr></thead>';
            html += '<tbody>';
            
            Object.entries(data).forEach(([key, value]) => {
                html += `<tr><td><strong>${key}</strong></td><td>${String(value)}</td></tr>`;
            });
            
            html += '</tbody></table></div>';
            return html;
        }
    } catch (e) {
        return jsonStr;
    }
    
    return jsonStr;
}

// Add message to chat
function addMessage(message, isUser) {
    const messageElement = createMessageElement(message, isUser);
    messagesContainer.appendChild(messageElement);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Show loading indicator
function showLoading() {
    const loadingElement = createLoadingElement();
    messagesContainer.appendChild(loadingElement);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Hide loading indicator
function hideLoading() {
    const loadingElement = document.getElementById('loading-message');
    if (loadingElement) {
        loadingElement.remove();
    }
}

// API Calls
async function sendMessage(message) {
    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                chat_id: currentChatId,
                timestamp: new Date().toISOString()
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error sending message:', error);
        return {
            response: 'Sorry, I encountered an error. Please try again.',
            chat_id: currentChatId
        };
    }
}

async function sendMessageStream(message, onChunk) {
    try {
        const response = await fetch(`${API_BASE_URL}/chat/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                chat_id: currentChatId,
                timestamp: new Date().toISOString()
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep incomplete line in buffer
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = JSON.parse(line.slice(6));
                    
                    if (data.type === 'start') {
                        currentChatId = data.chat_id;
                    } else if (data.type === 'chunk') {
                        onChunk(data.content);
                    } else if (data.type === 'done') {
                        return { chat_id: data.chat_id };
                    } else if (data.type === 'error') {
                        throw new Error(data.error);
                    }
                }
            }
        }
    } catch (error) {
        console.error('Error streaming message:', error);
        throw error;
    }
}

async function createNewChat() {
    try {
        const response = await fetch(`${API_BASE_URL}/chat/new`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data.chat_id;
    } catch (error) {
        console.error('Error creating new chat:', error);
        return `chat_${Date.now()}`;
    }
}

async function getChatHistory() {
    try {
        const response = await fetch(`${API_BASE_URL}/chat/history`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data.chats || [];
    } catch (error) {
        console.error('Error fetching chat history:', error);
        return [];
    }
}

// Handle form submission
async function handleSubmit(e) {
    e.preventDefault();
    
    const message = messageInput.value.trim();
    if (!message || isLoading) return;
    
    // Add user message
    addMessage(message, true);
    messageInput.value = '';
    autoResizeTextarea();
    
    // Create new chat if needed
    if (!currentChatId) {
        currentChatId = await createNewChat();
        updateChatHistory();
    }
    
    // Show loading
    isLoading = true;
    sendBtn.disabled = true;
    
    // Create placeholder for streaming response
    const placeholderDiv = document.createElement('div');
    placeholderDiv.className = 'message assistant';
    placeholderDiv.id = 'streaming-message';
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = 'BA';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    const header = document.createElement('div');
    header.className = 'message-header';
    header.innerHTML = '<span class="message-author">Bank Advisor</span><span class="message-time">Just now</span>';
    
    const text = document.createElement('div');
    text.className = 'message-text';
    text.innerHTML = '<span class="cursor">▊</span>';
    
    content.appendChild(header);
    content.appendChild(text);
    placeholderDiv.appendChild(avatar);
    placeholderDiv.appendChild(content);
    messagesContainer.appendChild(placeholderDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    let fullMessage = '';
    
    try {
        // Stream the response
        await sendMessageStream(message, (chunk) => {
            // Remove cursor if exists
            const cursor = text.querySelector('.cursor');
            if (cursor) cursor.remove();
            
            // Append to full message
            fullMessage += chunk;
            
            // Show raw text while streaming (we'll format it at the end)
            text.textContent = fullMessage;
            
            // Add cursor back
            const cursorSpan = document.createElement('span');
            cursorSpan.className = 'cursor';
            cursorSpan.textContent = '▊';
            text.appendChild(cursorSpan);
            
            // Auto-scroll
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        });
        
        // Remove cursor when done
        const cursor = text.querySelector('.cursor');
        if (cursor) cursor.remove();
        
        // Now format the complete message with tables and markdown
        text.innerHTML = formatMessage(fullMessage);
        
        // Remove placeholder id
        placeholderDiv.removeAttribute('id');
        
    } catch (error) {
        console.error('Streaming error:', error);
        text.innerHTML = 'Sorry, I encountered an error. Please try again.';
    }
    
    isLoading = false;
    sendBtn.disabled = false;
    messageInput.focus();
    
    // Update chat history
    updateChatHistory();
}

// Handle new chat
async function handleNewChat() {
    currentChatId = null;
    messagesContainer.innerHTML = `
        <div class="message assistant">
            <div class="message-avatar">BA</div>
            <div class="message-content">
                <div class="message-header">
                    <span class="message-author">Bank Advisor</span>
                    <span class="message-time">Just now</span>
                </div>
                <div class="message-text">
                    <p>👋 Welcome! I'm your Bank Advisor. I can help you analyze customer data, identify patterns, and answer questions about your banking information. What would you like to know?</p>
                </div>
            </div>
        </div>
    `;
    messageInput.focus();
}

// Update chat history sidebar
async function updateChatHistory() {
    const chats = await getChatHistory();
    chatHistory.innerHTML = '';
    
    chats.forEach(chat => {
        const item = document.createElement('div');
        item.className = 'chat-history-item';
        if (chat.id === currentChatId) {
            item.classList.add('active');
        }
        item.textContent = chat.title || `Chat ${chat.id}`;
        item.addEventListener('click', () => loadChat(chat.id));
        chatHistory.appendChild(item);
    });
}

// Load specific chat
async function loadChat(chatId) {
    try {
        const response = await fetch(`${API_BASE_URL}/chat/${chatId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        currentChatId = chatId;
        messagesContainer.innerHTML = '';
        
        // Load messages
        data.messages.forEach(msg => {
            addMessage(msg.content, msg.role === 'user');
        });
        
        // Update active state
        document.querySelectorAll('.chat-history-item').forEach(item => {
            item.classList.remove('active');
        });
        event.target.classList.add('active');
    } catch (error) {
        console.error('Error loading chat:', error);
    }
}

// Handle suggestion cards
function handleSuggestionClick(e) {
    const card = e.currentTarget;
    const prompt = card.dataset.prompt;
    messageInput.value = prompt;
    messageInput.focus();
    handleSubmit(new Event('submit'));
}

// Event Listeners and Initialization
document.addEventListener('DOMContentLoaded', () => {
    // Initialize theme first
    initTheme();
    
    // Attach event listeners
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    if (newChatBtn) {
        newChatBtn.addEventListener('click', handleNewChat);
    }
    
    if (chatForm) {
        chatForm.addEventListener('submit', handleSubmit);
    }
    
    if (messageInput) {
        messageInput.addEventListener('input', autoResizeTextarea);
        
        // Keyboard shortcuts
        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
            }
        });
        
        messageInput.focus();
    }
    
    // Suggestion cards
    const suggestionCards = document.querySelectorAll('.suggestion-card');
    suggestionCards.forEach(card => {
        card.addEventListener('click', handleSuggestionClick);
    });
    
    // Load chat history
    updateChatHistory();
});

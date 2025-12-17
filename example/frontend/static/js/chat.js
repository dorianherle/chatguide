// ChatGuide Frontend JavaScript
let ws = null;
let isConnected = false;
let isAuditing = false;
let conversationHistory = [];
let currentTurn = 0;
let directorData = null;

document.addEventListener('DOMContentLoaded', function() {
    initializeChat();
    setupEventListeners();
});

function initializeChat() {
    connectWebSocket();
    lucide.createIcons();
}

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/chat`;

    ws = new WebSocket(wsUrl);

    ws.onopen = function(event) {
        console.log('Connected to chat server');
        isConnected = true;
        updateUIState();
    };

    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };

    ws.onclose = function(event) {
        console.log('Disconnected from chat server');
        isConnected = false;
        updateUIState();

        // Attempt to reconnect after 3 seconds
        setTimeout(() => {
            if (!isConnected) {
                console.log('Attempting to reconnect...');
                connectWebSocket();
            }
        }, 3000);
    };

    ws.onerror = function(error) {
        console.error('WebSocket error:', error);
    };
}

function handleWebSocketMessage(data) {
    switch(data.type) {
        case 'initial_state':
            handleInitialState(data);
            break;
        case 'bot_message':
            handleBotMessage(data);
            break;
        case 'audit_start':
            handleAuditStart();
            break;
        case 'audit_end':
            handleAuditEnd();
            break;
        case 'director_update':
            handleDirectorUpdate(data);
            break;
    }
}

function handleInitialState(data) {
    conversationHistory = data.conversation ? parseConversation(data.conversation) : [];
    currentTurn = data.turn_count || 0;
    directorData = data.director_data;

    updateChatDisplay();
    updateDirectorPanel();
    updateUIState();

    // Hide empty state if we have messages
    if (conversationHistory.length > 0) {
        document.getElementById('empty-state').classList.add('hidden');
    }
}

function handleBotMessage(data) {
    // Remove typing indicator
    hideTypingIndicator();

    const message = {
        type: 'bot',
        content: data.message,
        turn: data.turn_count
    };
    conversationHistory.push(message);
    currentTurn = data.turn_count;

    updateChatDisplay();
    updateDirectorPanel();
    updateUIState();
}

function handleAuditStart() {
    isAuditing = true;
    updateAuditUI();
    updateUIState();
}

function handleAuditEnd() {
    isAuditing = false;
    updateAuditUI();
    updateUIState();

    // Add log entry
    addDirectorLogEntry('BLOCK COMPLETE', 'Audit completed successfully');
}

function handleDirectorUpdate(data) {
    directorData = data.data;
    updateDirectorPanel();
}

function parseConversation(conversationString) {
    const lines = conversationString.trim().split('\n');
    const messages = [];

    for (const line of lines) {
        if (line.startsWith('You: ')) {
            messages.push({
                type: 'bot',
                content: line.substring(5)
            });
        } else if (line.startsWith('User: ')) {
            messages.push({
                type: 'user',
                content: line.substring(6)
            });
        }
    }

    return messages;
}

function updateChatDisplay() {
    const chatMessages = document.getElementById('chat-messages');
    const emptyState = document.getElementById('empty-state');

    // Clear existing messages
    const existingMessages = chatMessages.querySelectorAll('.message-bubble');
    existingMessages.forEach(msg => msg.remove());

    // Hide empty state if we have messages
    if (conversationHistory.length > 0) {
        emptyState.classList.add('hidden');
    } else {
        emptyState.classList.remove('hidden');
        return;
    }

    // Add messages
    conversationHistory.forEach((message, index) => {
        const messageElement = createMessageElement(message, index);
        chatMessages.insertBefore(messageElement, emptyState);
    });

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function createMessageElement(message, index) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message-bubble flex mb-4';

    if (message.type === 'user') {
        messageDiv.className += ' justify-end';
        messageDiv.innerHTML = `
            <div class="message-user text-white px-4 py-3 max-w-xs lg:max-w-md rounded-lg">
                ${escapeHtml(message.content)}
            </div>
        `;
    } else {
        messageDiv.className += ' justify-start';
        messageDiv.innerHTML = `
            <div class="message-bot text-slate-300 px-4 py-3 max-w-xs lg:max-w-md rounded-lg hover:cursor-pointer"
                 onclick="openTurnInspector(${index})">
                ${escapeHtml(message.content)}
            </div>
        `;
    }

    return messageDiv;
}

function updateDirectorPanel() {
    if (!directorData) return;

    // Update status pill
    updateStatusPill();

    // Update epoch progress
    const progressPercent = ((currentTurn % 3) / 3) * 100;
    document.getElementById('epoch-progress').style.width = `${progressPercent}%`;
    document.getElementById('current-turn').textContent = currentTurn % 3 || 3;

    // Update standing order
    const standingOrder = directorData.stage_direction || 'No active directive';
    document.getElementById('standing-order').textContent = standingOrder;

    // Update extracted knowledge
    const extractedData = directorData.extracted_data || {};
    document.getElementById('extracted-data').textContent = JSON.stringify(extractedData, null, 2);
}

function updateStatusPill() {
    const statusPill = document.getElementById('status-pill');

    if (isAuditing) {
        statusPill.textContent = 'AUDITING...';
        statusPill.className = 'px-3 py-1 rounded-full text-xs font-medium status-auditing text-white';
    } else {
        statusPill.textContent = 'MONITORING';
        statusPill.className = 'px-3 py-1 rounded-full text-xs font-medium status-monitoring text-white';
    }
}

function updateAuditUI() {
    const overlay = document.getElementById('audit-overlay');
    const progressBar = document.getElementById('epoch-progress');

    if (isAuditing) {
        overlay.classList.remove('hidden');
        progressBar.classList.add('progress-auditing');
    } else {
        overlay.classList.add('hidden');
        progressBar.classList.remove('progress-auditing');
    }
}

function addDirectorLogEntry(status, message) {
    const logContainer = document.getElementById('director-log');
    const timestamp = new Date().toLocaleTimeString();

    const logEntry = document.createElement('div');
    logEntry.className = `log-entry text-slate-400 mb-2 ${status === 'BLOCK COMPLETE' ? 'log-complete' : 'log-continuing'}`;

    logEntry.innerHTML = `
        <div class="text-xs text-slate-500">${timestamp}</div>
        <div class="text-xs font-medium ${status === 'BLOCK COMPLETE' ? 'text-green-400' : 'text-amber-400'}">
            ${status}
        </div>
        <div class="text-xs text-slate-400 mt-1">${message}</div>
    `;

    logContainer.appendChild(logEntry);
    logContainer.scrollTop = logContainer.scrollHeight;
}

function updateUIState() {
    const input = document.getElementById('message-input');
    const button = document.getElementById('send-button');

    if (!isConnected || isAuditing) {
        input.disabled = true;
        button.disabled = true;
        input.placeholder = isAuditing ? 'Waiting for Director...' : 'Connecting...';
    } else {
        input.disabled = false;
        button.disabled = false;
        input.placeholder = 'Enter your message...';
    }
}

function setupEventListeners() {
    const input = document.getElementById('message-input');
    const button = document.getElementById('send-button');

    // Send message on Enter key
    input.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Send message on button click
    button.addEventListener('click', sendMessage);

    // Close inspector modal
    document.getElementById('close-inspector').addEventListener('click', closeTurnInspector);
}

function sendMessage() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();

    if (!message || !isConnected || isAuditing) return;

    // Add user message to UI immediately
    const userMessage = {
        type: 'user',
        content: message
    };
    conversationHistory.push(userMessage);
    updateChatDisplay();

    // Send to server
    ws.send(JSON.stringify({
        type: 'user_message',
        message: message
    }));

    // Clear input
    input.value = '';

    // Add typing indicator
    showTypingIndicator();
}

function showTypingIndicator() {
    const chatMessages = document.getElementById('chat-messages');
    const typingDiv = document.createElement('div');
    typingDiv.id = 'typing-indicator';
    typingDiv.className = 'message-bubble flex justify-start mb-4';
    typingDiv.innerHTML = `
        <div class="message-bot text-slate-300 px-4 py-3 rounded-lg">
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;

    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function hideTypingIndicator() {
    const typingDiv = document.getElementById('typing-indicator');
    if (typingDiv) {
        typingDiv.remove();
    }
}

function openTurnInspector(messageIndex) {
    const message = conversationHistory[messageIndex];
    if (message.type !== 'bot') return;

    document.getElementById('inspector-message').textContent = message.content;
    document.getElementById('inspector-mandate').textContent = directorData?.stage_direction || 'No active directive';

    document.getElementById('turn-inspector-modal').classList.remove('hidden');
}

function closeTurnInspector() {
    document.getElementById('turn-inspector-modal').classList.add('hidden');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

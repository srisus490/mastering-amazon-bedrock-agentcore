/**
 * Chat Widget Component
 * Provides the UI for the conversational AI assistant
 * 
 * Requirements: 1.1, 1.2, 1.3, 1.4, 7.3, 9.1, 9.2, 9.3
 */

export class ChatWidget {
    constructor(chatManager, messageFormatter) {
        this.chatManager = chatManager;
        this.messageFormatter = messageFormatter;
        this.isExpanded = false;
        this.isTyping = false;
        this.container = null;
        this.messagesContainer = null;
        this.inputField = null;
        this._lastMessageTime = null;
    }

    /**
     * Initialize the chat widget
     * Requirements: 1.1, 1.2
     */
    initialize() {
        this.createWidget();
        this.setupEventListeners();
        this.loadExamples();
    }

    /**
     * Create the chat widget HTML structure
     * Requirements: 1.1, 1.2, 1.3
     */
    createWidget() {
        // Create container
        this.container = document.createElement('div');
        this.container.id = 'chat-widget';
        this.container.className = 'chat-widget';
        this.container.setAttribute('role', 'complementary');
        this.container.setAttribute('aria-label', 'AI Assistant Chat');

        // Create floating button
        const button = document.createElement('button');
        button.id = 'chat-toggle-btn';
        button.className = 'chat-toggle-btn';
        button.setAttribute('aria-label', 'Toggle AI Assistant');
        button.setAttribute('aria-expanded', 'false');
        button.innerHTML = `
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            <span id="chat-unread-badge" class="chat-unread-badge hidden"></span>
            <span id="chat-last-time" class="chat-last-time hidden"></span>
        `;

        // Create chat panel
        const panel = document.createElement('div');
        panel.id = 'chat-panel';
        panel.className = 'chat-panel hidden';
        panel.setAttribute('role', 'dialog');
        panel.setAttribute('aria-labelledby', 'chat-header-title');

        // Chat header
        const header = document.createElement('div');
        header.className = 'chat-header';
        header.innerHTML = `
            <h3 id="chat-header-title">AI Assistant</h3>
            <div class="chat-header-actions">
                <button id="chat-clear-btn" class="chat-icon-btn" aria-label="Clear conversation" title="Clear conversation">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                </button>
                <button id="chat-close-btn" class="chat-icon-btn" aria-label="Close chat" title="Close chat">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>
        `;

        // Messages container
        this.messagesContainer = document.createElement('div');
        this.messagesContainer.id = 'chat-messages';
        this.messagesContainer.className = 'chat-messages';
        this.messagesContainer.setAttribute('role', 'log');
        this.messagesContainer.setAttribute('aria-live', 'polite');
        this.messagesContainer.setAttribute('aria-atomic', 'false');

        // Examples container (shown when no messages)
        const examplesContainer = document.createElement('div');
        examplesContainer.id = 'chat-examples';
        examplesContainer.className = 'chat-examples';
        examplesContainer.innerHTML = `
            <p class="chat-examples-title">Try asking:</p>
            <div id="chat-examples-list"></div>
        `;

        // Input container
        const inputContainer = document.createElement('div');
        inputContainer.className = 'chat-input-container';
        inputContainer.innerHTML = `
            <textarea 
                id="chat-input" 
                class="chat-input" 
                placeholder="Ask about your data..."
                rows="1"
                aria-label="Chat message input"
            ></textarea>
            <button id="chat-send-btn" class="chat-send-btn" aria-label="Send message">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="22" y1="2" x2="11" y2="13"></line>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                </svg>
            </button>
        `;

        // Typing indicator
        const typingIndicator = document.createElement('div');
        typingIndicator.id = 'chat-typing';
        typingIndicator.className = 'chat-typing hidden';
        typingIndicator.setAttribute('aria-live', 'polite');
        typingIndicator.innerHTML = `
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
            <span class="typing-text">AI is thinking...</span>
        `;

        // Assemble panel
        panel.appendChild(header);
        panel.appendChild(this.messagesContainer);
        panel.appendChild(examplesContainer);
        panel.appendChild(typingIndicator);
        panel.appendChild(inputContainer);

        // Assemble widget
        this.container.appendChild(button);
        this.container.appendChild(panel);

        // Add to document
        document.body.appendChild(this.container);

        // Store references
        this.inputField = document.getElementById('chat-input');
    }

    /**
     * Setup event listeners
     * Requirements: 1.2, 1.3, 1.4
     */
    setupEventListeners() {
        // Toggle button
        const toggleBtn = document.getElementById('chat-toggle-btn');
        toggleBtn.addEventListener('click', () => this.toggle());

        // Close button
        const closeBtn = document.getElementById('chat-close-btn');
        closeBtn.addEventListener('click', () => this.collapse());

        // Clear button
        const clearBtn = document.getElementById('chat-clear-btn');
        clearBtn.addEventListener('click', () => this.clearConversation());

        // Send button
        const sendBtn = document.getElementById('chat-send-btn');
        sendBtn.addEventListener('click', () => this.sendMessage());

        // Input field - auto-resize and enter to send
        this.inputField.addEventListener('input', (e) => {
            this.autoResizeInput(e.target);
        });

        this.inputField.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // ESC to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isExpanded) {
                this.collapse();
            }
        });
    }

    /**
     * Load example questions from API
     * Requirements: 9.1, 9.2
     */
    async loadExamples() {
        try {
            const examples = await this.chatManager.getExamples();
            this.renderExamples(examples);
        } catch (error) {
            console.error('Failed to load examples:', error);
        }
    }

    /**
     * Render example questions
     * Requirements: 9.1, 9.2, 9.3
     */
    renderExamples(examples) {
        const examplesList = document.getElementById('chat-examples-list');
        if (!examplesList) return;

        examplesList.innerHTML = '';

        examples.forEach(example => {
            const button = document.createElement('button');
            button.className = 'chat-example-btn';
            button.textContent = example;
            button.setAttribute('aria-label', `Ask: ${example}`);
            button.addEventListener('click', () => {
                this.inputField.value = example;
                this.sendMessage();
            });
            examplesList.appendChild(button);
        });
    }

    /**
     * Toggle chat panel
     * Requirements: 1.2
     */
    toggle() {
        if (this.isExpanded) {
            this.collapse();
        } else {
            this.expand();
        }
    }

    /**
     * Expand chat panel
     * Requirements: 1.2
     */
    expand() {
        const panel = document.getElementById('chat-panel');
        const toggleBtn = document.getElementById('chat-toggle-btn');
        
        panel.classList.remove('hidden');
        toggleBtn.setAttribute('aria-expanded', 'true');
        this.isExpanded = true;

        // Clear the "last message" indicator — user is now reading
        document.getElementById('chat-unread-badge')?.classList.add('hidden');
        document.getElementById('chat-last-time')?.classList.add('hidden');
        
        this.inputField.focus();
        this.scrollToBottom();
    }

    collapse() {
        const panel = document.getElementById('chat-panel');
        const toggleBtn = document.getElementById('chat-toggle-btn');
        
        panel.classList.add('hidden');
        toggleBtn.setAttribute('aria-expanded', 'false');
        this.isExpanded = false;

        // Show last-message time if there's a conversation to return to
        this._updateToggleIndicator();
    }

    /** Show the last-message timestamp on the toggle button when panel is closed */
    _updateToggleIndicator() {
        if (!this._lastMessageTime || this.isExpanded) return;

        const badge = document.getElementById('chat-unread-badge');
        const timeEl = document.getElementById('chat-last-time');
        if (!badge || !timeEl) return;

        badge.classList.remove('hidden');
        timeEl.textContent = this.messageFormatter.formatTimestamp(this._lastMessageTime);
        timeEl.classList.remove('hidden');
    }

    /**
     * Send message to AI
     * Requirements: 1.3, 1.4
     */
    async sendMessage() {
        const message = this.inputField.value.trim();
        if (!message) return;

        this.inputField.value = '';
        this.autoResizeInput(this.inputField);

        const hasMessages = this.messagesContainer.children.length > 0;
        if (!hasMessages) {
            document.getElementById('chat-examples')?.classList.add('hidden');
        }

        this.addMessage('user', message);
        this.showTyping();

        try {
            const timeoutPromise = new Promise((_, reject) => {
                setTimeout(() => reject(new Error('Request timeout - the AI is taking too long to respond. Please try a simpler question.')), 60000);
            });

            // Collect active dashboard context so AI uses the same date range
            const dashboardContext = this._getDashboardContext();

            const response = await Promise.race([
                this.chatManager.sendQuery(message, dashboardContext),
                timeoutPromise
            ]);

            this.hideTyping();
            this.addMessage('assistant', response.response, response.data);

            if (response.cached) this.showCacheIndicator();

        } catch (error) {
            this.hideTyping();
            this.addMessage('error', error.message || 'Sorry, I encountered an error. Please try again.');
        }
    }

    /** Collect the currently active dashboard state to send as context */
    _getDashboardContext() {
        // stateManager is injected via setStateManager() called from app.js
        if (!this._stateManager) return null;
        try {
            const system = this._stateManager.getSelectedSystem();
            const range  = this._stateManager.getDateRange();
            return {
                selected_system: system || null,
                start_date: range.startDate ? range.startDate.toISOString().split('T')[0] : null,
                end_date:   range.endDate   ? range.endDate.toISOString().split('T')[0]   : null,
            };
        } catch (e) {
            return null;
        }
    }

    /** Called from app.js after both widget and stateManager are initialised */
    setStateManager(stateManager) {
        this._stateManager = stateManager;
    }

    /**
     * Add message to chat
     * Requirements: 1.3, 4.2, 4.3
     */
    addMessage(role, content, data = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message chat-message-${role}`;
        messageDiv.setAttribute('role', 'article');

        const bubble = document.createElement('div');
        bubble.className = 'chat-message-bubble';

        if (role === 'user') {
            bubble.textContent = content;
        } else if (role === 'assistant') {
            if (data && data.report_url) {
                // Comparison report — render summary text + a prominent link button
                bubble.innerHTML = `
                    <p>${content}</p>
                    <a href="${data.report_url}" target="_blank" class="chat-report-link">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                            <polyline points="15 3 21 3 21 9"/>
                            <line x1="10" y1="14" x2="21" y2="3"/>
                        </svg>
                        View Full Comparison Report
                    </a>
                `;
            } else if (data && Array.isArray(data) && data.length > 0) {
                bubble.innerHTML = `<p>${content}</p>${this.messageFormatter.formatTable(data)}`;
            } else {
                bubble.innerHTML = `<p>${content}</p>`;
            }
        } else if (role === 'error') {
            bubble.innerHTML = `<p class="error-text">⚠️ ${content}</p>`;
        }

        // Add timestamp
        const now = new Date();
        const timestamp = document.createElement('div');
        timestamp.className = 'chat-message-timestamp';
        timestamp.textContent = this.messageFormatter.formatTimestamp(now);
        
        messageDiv.appendChild(bubble);
        messageDiv.appendChild(timestamp);
        this.messagesContainer.appendChild(messageDiv);

        // Track last message time for the toggle indicator
        this._lastMessageTime = now;

        this.scrollToBottom();
    }

    /**
     * Show typing indicator
     * Requirements: 7.3
     */
    showTyping() {
        const typingIndicator = document.getElementById('chat-typing');
        if (typingIndicator) {
            typingIndicator.classList.remove('hidden');
            this.isTyping = true;
            this.scrollToBottom();
        }
    }

    /**
     * Hide typing indicator
     * Requirements: 7.3
     */
    hideTyping() {
        const typingIndicator = document.getElementById('chat-typing');
        if (typingIndicator) {
            typingIndicator.classList.add('hidden');
            this.isTyping = false;
        }
    }

    /**
     * Show cache indicator
     */
    showCacheIndicator() {
        const lastMessage = this.messagesContainer.lastElementChild;
        if (lastMessage) {
            const cacheTag = document.createElement('span');
            cacheTag.className = 'cache-indicator';
            cacheTag.textContent = '⚡ Cached';
            cacheTag.title = 'This response was retrieved from cache';
            lastMessage.querySelector('.chat-message-bubble').appendChild(cacheTag);
        }
    }

    /**
     * Clear conversation — no confirmation dialog, instant clear
     */
    async clearConversation() {
        this.messagesContainer.innerHTML = '';
        this._lastMessageTime = null;

        // Hide toggle indicator
        document.getElementById('chat-unread-badge')?.classList.add('hidden');
        document.getElementById('chat-last-time')?.classList.add('hidden');

        const examplesContainer = document.getElementById('chat-examples');
        if (examplesContainer) examplesContainer.classList.remove('hidden');

        this.chatManager.clearContext().catch(err => console.warn('clearContext error:', err));
    }

    /**
     * Auto-resize input field
     */
    autoResizeInput(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }

    /**
     * Scroll messages to bottom
     */
    scrollToBottom() {
        setTimeout(() => {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }, 100);
    }

    /**
     * Update examples based on dashboard context
     * Requirements: 9.4, 9.5
     */
    async updateExamples(systemId = null) {
        try {
            const examples = await this.chatManager.getExamples(systemId);
            this.renderExamples(examples);
        } catch (error) {
            console.error('Failed to update examples:', error);
        }
    }
}

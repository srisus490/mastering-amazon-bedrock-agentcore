/**
 * Chat Manager
 * Manages conversation state and API communication
 * 
 * Requirements: 5.1, 5.2, 5.5, 10.1, 10.2, 10.5
 */

export class ChatManager {
    constructor(apiClient) {
        this.apiClient = apiClient;
        this.context = [];
        this.sessionId = this.generateSessionId();
        this.maxContextSize = 10;
        console.log('ChatManager created with sessionId:', this.sessionId);
        
        // Load context from session storage
        this.loadFromSessionStorage();
    }

    /**
     * Send query to backend
     * Requirements: 2.1, 2.2, 2.3, 11.1, 11.2, 11.3, 11.4, 11.5
     */
    async sendQuery(query, dashboardContext = null) {
        try {
            const request = {
                query: query,
                context: this.context,
                session_id: this.sessionId,
                include_system_context: true,
                dashboard_context: dashboardContext || null
            };

            // Call API using APIClient
            const data = await this.apiClient.sendChatQuery(request);
            console.log('Received response:', data);

            // Add to context
            this.addMessage('user', query);
            this.addMessage('assistant', data.response);

            // Save to session storage
            this.saveToSessionStorage();

            return data;
        } catch (error) {
            console.error('Failed to send query:', error);
            
            // Provide user-friendly error messages
            const errorMessage = error.message || 'An unexpected error occurred';
            
            if (errorMessage.includes('Failed to fetch') || errorMessage.includes('NetworkError')) {
                throw new Error('Network connection lost. Please check your internet connection.');
            } else if (errorMessage.includes('429')) {
                throw new Error('Rate limit exceeded. Please wait a moment and try again.');
            } else if (errorMessage.includes('401') || errorMessage.includes('403')) {
                throw new Error('Authentication failed. Please check your credentials.');
            } else if (errorMessage.includes('503')) {
                throw new Error('AI service is temporarily unavailable. Please try again later.');
            } else if (errorMessage.includes('500')) {
                throw new Error('Server error. Please try again later.');
            }
            
            // Re-throw with original or user-friendly message
            throw new Error(errorMessage);
        }
    }

    /**
     * Add message to context
     * Requirements: 5.1, 5.2
     */
    addMessage(role, content) {
        const message = {
            id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            role: role,
            content: content,
            timestamp: new Date().toISOString(),
            data: null,
            tokens_used: null
        };

        this.context.push(message);

        // Enforce size limit (keep last 10 messages)
        if (this.context.length > this.maxContextSize) {
            this.context = this.context.slice(-this.maxContextSize);
            console.log('Context trimmed to', this.maxContextSize, 'messages');
        }

        console.log('Message added to context. Total messages:', this.context.length);
    }

    /**
     * Clear conversation context
     * Requirements: 5.5, 10.4
     */
    async clearContext() {
        try {
            // Clear local context
            this.context = [];

            // Clear session storage
            this.clearSessionStorage();

            // Call backend to clear cache
            await this.apiClient.clearChatCache(this.sessionId);

            console.log('Context cleared');
        } catch (error) {
            console.error('Failed to clear context:', error);
            // Don't throw - clearing is best-effort
        }
    }

    /**
     * Get example questions from backend
     * Requirements: 9.1, 9.2
     */
    async getExamples(systemId = null) {
        try {
            const data = await this.apiClient.getChatExamples(systemId);
            return data.examples || [];
        } catch (error) {
            console.error('Failed to get examples:', error);
            // Return default examples on error
            return [
                'What is the health status of all systems?',
                'Show me SLA violations from last week',
                'Which system has the most file arrivals?'
            ];
        }
    }

    /**
     * Save context to session storage
     * Requirements: 10.1, 10.2
     */
    saveToSessionStorage() {
        try {
            const data = {
                sessionId: this.sessionId,
                context: this.context,
                timestamp: new Date().toISOString()
            };

            sessionStorage.setItem('chat_context', JSON.stringify(data));
            console.log('Context saved to session storage');
        } catch (error) {
            console.error('Failed to save to session storage:', error);
        }
    }

    /**
     * Load context from session storage
     * Requirements: 10.1, 10.2
     */
    loadFromSessionStorage() {
        try {
            const stored = sessionStorage.getItem('chat_context');
            if (!stored) {
                console.log('No stored context found');
                return;
            }

            const data = JSON.parse(stored);
            
            // Check if context is from same session (within last 24 hours)
            const timestamp = new Date(data.timestamp);
            const now = new Date();
            const hoursSinceLastSave = (now - timestamp) / (1000 * 60 * 60);
            
            if (hoursSinceLastSave > 24) {
                console.log('Stored context is too old, discarding');
                this.clearSessionStorage();
                return;
            }

            // Restore context
            this.sessionId = data.sessionId || this.sessionId;
            this.context = data.context || [];
            
            console.log('Context loaded from session storage:', this.context.length, 'messages');
        } catch (error) {
            console.error('Failed to load from session storage:', error);
        }
    }

    /**
     * Clear session storage
     * Requirements: 10.4
     */
    clearSessionStorage() {
        try {
            sessionStorage.removeItem('chat_context');
            console.log('Session storage cleared');
        } catch (error) {
            console.error('Failed to clear session storage:', error);
        }
    }

    /**
     * Generate unique session ID
     * Requirements: 10.5
     */
    generateSessionId() {
        return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Get current context
     */
    getContext() {
        return this.context;
    }

    /**
     * Get session ID
     */
    getSessionId() {
        return this.sessionId;
    }
}

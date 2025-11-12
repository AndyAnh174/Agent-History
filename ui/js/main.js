const API_BASE = '';

// Tab switching
function switchTab(tabName) {
    console.log('Switching to tab:', tabName);
    
    // Hide hero section and show main content
    const heroSection = document.getElementById('hero-section');
    const mainContent = document.getElementById('main-content');
    
    if (heroSection) {
        heroSection.style.display = 'none';
        heroSection.classList.add('hidden');
    }
    
    if (mainContent) {
        mainContent.style.display = 'block';
        mainContent.style.visibility = 'visible';
        mainContent.classList.remove('hidden');
        console.log('Main content displayed, computed style:', window.getComputedStyle(mainContent).display);
        // Scroll to top of main content
        setTimeout(() => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }, 50);
    }
    
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.add('hidden');
        tab.style.display = 'none';
    });
    
    // Show selected tab
    const selectedTab = document.getElementById(`${tabName}-tab`);
    if (selectedTab) {
        selectedTab.classList.remove('hidden');
        selectedTab.style.display = 'block';
        selectedTab.style.visibility = 'visible';
        console.log('Tab shown:', tabName);
        console.log('Tab element:', selectedTab);
        console.log('Tab computed display:', window.getComputedStyle(selectedTab).display);
        console.log('Tab innerHTML length:', selectedTab.innerHTML.length);
    } else {
        console.error('Tab not found:', `${tabName}-tab`);
    }
    
    // Update active state for desktop menu
    document.querySelectorAll('.tab-link').forEach(link => {
        link.classList.remove('active', 'btn-active');
    });
    const activeLink = document.querySelector(`[data-tab="${tabName}"]`);
    if (activeLink) {
        activeLink.classList.add('active', 'btn-active');
    }
    
    // Update active state for mobile menu
    document.querySelectorAll('.dropdown .menu a').forEach(link => {
        link.classList.remove('active');
    });
}

// Start learning - hide hero, show main content
function startLearning() {
    const heroSection = document.getElementById('hero-section');
    const mainContent = document.getElementById('main-content');
    
    if (heroSection) {
        heroSection.style.display = 'none';
        heroSection.classList.add('hidden');
    }
    
    if (mainContent) {
        mainContent.style.display = 'block';
        mainContent.classList.remove('hidden');
    }
    
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        setTimeout(() => chatInput.focus(), 100);
    }
}

// Show/hide loading
function showLoading() {
    document.getElementById('loading-modal').showModal();
}

function hideLoading() {
    document.getElementById('loading-modal').close();
}

// Show error
function showError(message) {
    document.getElementById('error-message').textContent = message;
    const toast = document.getElementById('error-toast');
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), 5000);
}

// Add message to chat
function addChatMessage(message, isUser = false) {
    const messagesDiv = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat ${isUser ? 'chat-end' : 'chat-start'} chat-message`;
    
    const time = new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
    
    // If message contains markdown-content div, it's already processed
    // Otherwise, escape HTML for user messages
    let messageContent = message;
    if (isUser) {
        // Escape HTML for user messages (security)
        const div = document.createElement('div');
        div.textContent = message;
        messageContent = div.innerHTML.replace(/\n/g, '<br>');
    }
    
    messageDiv.innerHTML = `
        <div class="chat-image avatar">
            <div class="w-14 h-14 rounded-full flex items-center justify-center text-2xl shadow-lg" style="background: linear-gradient(135deg, ${isUser ? '#10b981 0%, #059669 100%' : '#dc2626 0%, #ea580c 100%'}); border: 3px solid #fbbf24;">
                ${isUser ? '👤' : '🤖'}
            </div>
        </div>
        <div class="chat-header font-bold text-lg" style="font-family: 'Nunito', sans-serif; color: #dc2626;">
            ${isUser ? 'Bạn' : 'Sử Việt AI'}
            <time class="text-xs opacity-70 ml-2">${time}</time>
        </div>
        <div class="chat-bubble rounded-2xl shadow-lg p-4 text-base font-semibold" style="background: linear-gradient(135deg, ${isUser ? '#10b981 0%, #059669 100%' : '#dc2626 0%, #ea580c 100%'}); color: white; border: 3px solid #fbbf24; font-family: 'Nunito', sans-serif;">
            ${messageContent}
        </div>
    `;
    
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Render sources
function renderSources(sources, containerId) {
    const container = document.getElementById(containerId);
    if (!sources || sources.length === 0) {
        container.innerHTML = '';
        return;
    }
    
    container.innerHTML = '<h4 class="font-bold mt-4 mb-4 text-2xl" style="font-family: \'Fredoka\', sans-serif; color: #dc2626; text-shadow: 2px 2px 0px #fbbf24;"><span class="text-2xl mr-2">📚</span>Nguồn tham khảo:</h4>';
    sources.forEach((source, idx) => {
        const sourceCard = document.createElement('div');
        sourceCard.className = 'card source-card mb-3 shadow-lg rounded-xl overflow-hidden';
        sourceCard.style.cssText = 'background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border: 3px solid #f59e0b;';
        sourceCard.innerHTML = `
            <div class="card-body p-4">
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <h5 class="font-bold text-lg mb-2" style="font-family: \'Fredoka\', sans-serif; color: #dc2626;">${source.title || `Nguồn ${idx + 1}`}</h5>
                        <p class="text-base font-semibold mt-1" style="font-family: \'Nunito\', sans-serif; color: #92400e;">${source.snippet || ''}</p>
                        ${source.score ? `<span class="badge text-sm font-bold px-3 py-1 mt-2 rounded-lg shadow-md" style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; border: 2px solid #fbbf24;">Độ liên quan: ${(source.score * 100).toFixed(1)}%</span>` : ''}
                    </div>
                </div>
            </div>
        `;
        container.appendChild(sourceCard);
    });
}

// Chat Form Handler
document.getElementById('chat-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const input = document.getElementById('chat-input');
    const question = input.value.trim();
    
    if (!question) return;
    
    addChatMessage(question, true);
    input.value = '';
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE}/api/rag/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
            const errorMsg = errorData.detail || `HTTP ${response.status}`;
            throw new Error(errorMsg);
        }
        
        const data = await response.json();
        hideLoading();
        
        // Render markdown to HTML
        let answerHtml = '';
        if (data.answer) {
            // Configure marked options
            marked.setOptions({
                breaks: true,
                gfm: true,
                headerIds: false,
                mangle: false
            });
            
            // Convert markdown to HTML
            answerHtml = marked.parse(data.answer);
            // Wrap in markdown-content div for styling
            answerHtml = `<div class="markdown-content">${answerHtml}</div>`;
        }
        
        if (data.sources && data.sources.length > 0) {
            answerHtml += '<div class="mt-4 pt-4" style="border-top: 3px solid rgba(255,255,255,0.3);">';
            answerHtml += '<p class="text-base font-bold mb-3" style="font-family: \'Fredoka\', sans-serif;">📚 Nguồn tham khảo:</p>';
            data.sources.forEach((source, idx) => {
                answerHtml += `
                    <div class="text-sm mb-2 font-semibold" style="font-family: \'Nunito\', sans-serif;">
                        <span class="badge text-xs font-bold px-2 py-1 mr-2 rounded-lg" style="background: rgba(255,255,255,0.3); border: 2px solid rgba(255,255,255,0.5);">[${idx + 1}]</span>
                        ${source.title || 'Nguồn không xác định'}
                    </div>
                `;
            });
            answerHtml += '</div>';
        }
        
        addChatMessage(answerHtml);
        
        // Highlight code blocks after adding message
        setTimeout(() => {
            const chatMessages = document.getElementById('chat-messages');
            const codeBlocks = chatMessages.querySelectorAll('pre code');
            codeBlocks.forEach(block => {
                hljs.highlightElement(block);
            });
        }, 100);
    } catch (error) {
        hideLoading();
        let errorMessage = 'Có lỗi xảy ra';
        if (error.message.includes('429') || error.message.includes('rate limit') || error.message.includes('quá tải')) {
            errorMessage = 'API đang quá tải. Vui lòng đợi một chút và thử lại.';
        } else if (error.message.includes('timeout') || error.message.includes('thời gian chờ')) {
            errorMessage = 'Yêu cầu quá thời gian chờ. Vui lòng thử lại.';
        } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            errorMessage = 'Không thể kết nối đến server. Vui lòng kiểm tra kết nối mạng.';
        } else {
            errorMessage = 'Có lỗi xảy ra: ' + error.message;
        }
        showError(errorMessage);
    }
});

// Summarize Form Handler
document.getElementById('summarize-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const topic = document.getElementById('summarize-topic').value.trim();
    const detailLevel = document.getElementById('summarize-detail').value;
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE}/api/rag/summarize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic, detail_level: detailLevel })
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
            const errorMsg = errorData.detail || `HTTP ${response.status}`;
            throw new Error(errorMsg);
        }
        
        const data = await response.json();
        hideLoading();
        
        // Render markdown to HTML for summarize
        let summaryHtml = '';
        if (data.summary) {
            marked.setOptions({
                breaks: true,
                gfm: true,
                headerIds: false,
                mangle: false
            });
            
            summaryHtml = marked.parse(data.summary);
            summaryHtml = `<div class="markdown-content">${summaryHtml}</div>`;
        }
        
        document.getElementById('summarize-content').innerHTML = summaryHtml;
        renderSources(data.sources, 'summarize-sources');
        document.getElementById('summarize-result').classList.remove('hidden');
        
        // Highlight code blocks
        setTimeout(() => {
            const summarizeContent = document.getElementById('summarize-content');
            const codeBlocks = summarizeContent.querySelectorAll('pre code');
            codeBlocks.forEach(block => {
                hljs.highlightElement(block);
            });
        }, 100);
    } catch (error) {
        hideLoading();
        let errorMessage = 'Có lỗi xảy ra';
        if (error.message.includes('429') || error.message.includes('rate limit') || error.message.includes('quá tải')) {
            errorMessage = 'API đang quá tải. Vui lòng đợi một chút và thử lại.';
        } else if (error.message.includes('timeout') || error.message.includes('thời gian chờ')) {
            errorMessage = 'Yêu cầu quá thời gian chờ. Vui lòng thử lại.';
        } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            errorMessage = 'Không thể kết nối đến server. Vui lòng kiểm tra kết nối mạng.';
        } else {
            errorMessage = 'Có lỗi xảy ra: ' + error.message;
        }
        showError(errorMessage);
    }
});

// Timeline Form Handler
document.getElementById('timeline-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const entity = document.getElementById('timeline-entity').value.trim();
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE}/api/rag/timeline`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ entity })
        });
        
        if (!response.ok) throw new Error('Không thể kết nối đến server');
        
        const data = await response.json();
        hideLoading();
        
        const timelineDiv = document.getElementById('timeline-content');
        timelineDiv.innerHTML = '';
        
        if (data.events && Array.isArray(data.events) && data.events.length > 0) {
            data.events.forEach((event, idx) => {
                const eventCard = document.createElement('div');
                eventCard.className = 'card mb-4 shadow-lg rounded-2xl overflow-hidden';
                eventCard.style.cssText = 'background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border: 3px solid #f59e0b;';
                eventCard.innerHTML = `
                    <div class="card-body p-5">
                        <div class="flex items-start gap-4">
                            <div class="badge badge-lg text-xl font-bold px-4 py-3 rounded-xl shadow-lg" style="background: linear-gradient(135deg, #dc2626 0%, #ea580c 100%); color: white; border: 3px solid #fbbf24; font-family: \'Fredoka\', sans-serif;">
                                <span class="text-lg mr-1">📅</span>${event.year || 'Không rõ'}
                            </div>
                            <div class="flex-1">
                                <h5 class="font-bold text-xl mb-2" style="font-family: \'Fredoka\', sans-serif; color: #dc2626;">${event.title || event.event || 'Sự kiện'}</h5>
                                <p class="text-base font-semibold" style="font-family: \'Nunito\', sans-serif; color: #92400e;">${event.description || ''}</p>
                            </div>
                        </div>
                    </div>
                `;
                timelineDiv.appendChild(eventCard);
            });
        } else {
            timelineDiv.innerHTML = '<p class="text-center text-xl font-bold" style="font-family: \'Nunito\', sans-serif; color: #92400e;">Không tìm thấy sự kiện nào.</p>';
        }
        
        renderSources(data.sources, 'timeline-sources');
        document.getElementById('timeline-result').classList.remove('hidden');
    } catch (error) {
        hideLoading();
        showError('Có lỗi xảy ra: ' + error.message);
    }
});

// MCQ Form Handler
document.getElementById('mcq-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const context = document.getElementById('mcq-context').value.trim();
    const numQuestions = parseInt(document.getElementById('mcq-num').value) || 3;
    
    if (context.length < 50) {
        showError('Văn bản phải có ít nhất 50 ký tự');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE}/api/mcq/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ context, num_questions: numQuestions })
        });
        
        if (!response.ok) throw new Error('Không thể kết nối đến server');
        
        const data = await response.json();
        hideLoading();
        
        const questionsDiv = document.getElementById('mcq-questions');
        questionsDiv.innerHTML = '';
        
        if (data.questions && Array.isArray(data.questions) && data.questions.length > 0) {
            data.questions.forEach((q, idx) => {
                const questionCard = document.createElement('div');
                questionCard.className = 'card shadow-lg rounded-2xl overflow-hidden mb-6';
                questionCard.style.cssText = 'background: linear-gradient(135deg, #ffffff 0%, #fef3c7 100%); border: 3px solid #f59e0b;';
                questionCard.innerHTML = `
                    <div class="card-body p-6">
                        <h4 class="card-title text-2xl mb-4" style="font-family: \'Fredoka\', sans-serif; color: #dc2626;">
                            <span class="badge text-lg font-bold px-4 py-2 mr-3 rounded-xl shadow-lg" style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; border: 3px solid #fbbf24;">
                                <span class="text-xl mr-1">❓</span>Câu ${idx + 1}
                            </span>
                            <span style="font-family: \'Nunito\', sans-serif; color: #92400e;">${q.question}</span>
                        </h4>
                        <div class="space-y-3 mt-4">
                            ${Object.entries(q.options || {}).map(([key, value]) => `
                                <div class="flex items-center gap-3 p-4 rounded-xl shadow-md" style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border: 2px solid ${key === q.correct_answer ? '#10b981' : '#f59e0b'};">
                                    <span class="badge text-lg font-bold px-4 py-2 rounded-xl" style="background: linear-gradient(135deg, ${key === q.correct_answer ? '#10b981 0%, #059669 100%' : '#dc2626 0%, #ea580c 100%'}); color: white; border: 2px solid #fbbf24;">
                                        ${key}
                                    </span>
                                    <span class="flex-1 font-semibold text-lg" style="font-family: \'Nunito\', sans-serif; color: #92400e;">${value}</span>
                                    ${key === q.correct_answer ? '<span class="badge text-base font-bold px-3 py-2 rounded-xl shadow-lg" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; border: 2px solid #fbbf24;"><span class="text-lg mr-1">✅</span>Đáp án đúng</span>' : ''}
                                </div>
                            `).join('')}
                        </div>
                        <div class="alert mt-5 p-4 rounded-xl shadow-lg" style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); border: 3px solid #3b82f6;">
                            <span class="text-2xl mr-3">💡</span>
                            <span class="text-base font-bold" style="font-family: \'Nunito\', sans-serif; color: #1e3a8a;"><strong>Giải thích:</strong> ${q.explanation || 'Không có giải thích'}</span>
                        </div>
                    </div>
                `;
                questionsDiv.appendChild(questionCard);
            });
        } else {
            questionsDiv.innerHTML = '<p class="text-center text-xl font-bold" style="font-family: \'Nunito\', sans-serif; color: #92400e;">Không thể tạo câu hỏi từ văn bản này.</p>';
        }
        
        document.getElementById('mcq-result').classList.remove('hidden');
    } catch (error) {
        hideLoading();
        showError('Có lỗi xảy ra: ' + error.message);
    }
});

// Image Generation Form Handler
document.getElementById('image-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const prompt = document.getElementById('image-prompt').value.trim();
    
    if (prompt.length < 10) {
        showError('Mô tả phải có ít nhất 10 ký tự');
        return;
    }
    
    // Basic frontend validation
    const promptLower = prompt.toLowerCase();
    const bannedKeywords = ['nude', 'naked', 'sex', 'violence', 'blood', 'drug', 'khỏa thân', 'bạo lực', 'ma túy'];
    const hasBannedKeyword = bannedKeywords.some(keyword => promptLower.includes(keyword));
    
    if (hasBannedKeyword) {
        showError('Nội dung không phù hợp. Vui lòng chỉ mô tả về lịch sử Việt Nam.');
        return;
    }
    
    // Check if related to Vietnamese history
    const historyKeywords = ['việt nam', 'vietnam', 'lịch sử', 'vua', 'triều đại', 'trận', 'nhà trần', 'nhà lý', 'quang trung', 'lý thường kiệt'];
    const hasHistoryKeyword = historyKeywords.some(keyword => promptLower.includes(keyword));
    
    if (!hasHistoryKeyword) {
        showError('Vui lòng mô tả về nhân vật, sự kiện, hoặc triều đại trong lịch sử Việt Nam.');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE}/api/rag/generate-image`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt })
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
            const errorMsg = errorData.detail || `HTTP ${response.status}`;
            throw new Error(errorMsg);
        }
        
        const data = await response.json();
        hideLoading();
        
        // Display the generated image
        const imageElement = document.getElementById('generated-image');
        const promptDisplay = document.getElementById('image-prompt-display');
        
        if (data.image_url) {
            imageElement.src = data.image_url;
            imageElement.alt = data.prompt || 'Generated image';
            promptDisplay.textContent = data.prompt || prompt;
            
            // Store image URL for download
            imageElement.dataset.imageUrl = data.image_url;
            
            document.getElementById('image-result').classList.remove('hidden');
            
            // Scroll to result
            setTimeout(() => {
                document.getElementById('image-result').scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 100);
        } else {
            throw new Error('Không nhận được ảnh từ server');
        }
    } catch (error) {
        hideLoading();
        let errorMessage = 'Có lỗi xảy ra';
        if (error.message.includes('429') || error.message.includes('rate limit') || error.message.includes('quá tải')) {
            errorMessage = 'API đang quá tải. Vui lòng đợi một chút và thử lại.';
        } else if (error.message.includes('timeout') || error.message.includes('thời gian chờ')) {
            errorMessage = 'Yêu cầu quá thời gian chờ. Vui lòng thử lại.';
        } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            errorMessage = 'Không thể kết nối đến server. Vui lòng kiểm tra kết nối mạng.';
        } else {
            errorMessage = 'Có lỗi xảy ra: ' + error.message;
        }
        showError(errorMessage);
    }
});

// Download image function
function downloadImage() {
    const imageElement = document.getElementById('generated-image');
    const imageUrl = imageElement.dataset.imageUrl || imageElement.src;
    
    if (!imageUrl || imageUrl === '') {
        showError('Không có ảnh để tải xuống');
        return;
    }
    
    try {
        // Create a temporary anchor element
        const link = document.createElement('a');
        link.href = imageUrl;
        link.download = `su-viet-image-${Date.now()}.png`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    } catch (error) {
        // Fallback: open in new tab
        window.open(imageUrl, '_blank');
    }
}

// Auto-focus on input when tab switches
document.querySelectorAll('.tab-link').forEach(link => {
    link.addEventListener('click', () => {
        setTimeout(() => {
            const activeTab = document.querySelector('.tab-content:not(.hidden)');
            const firstInput = activeTab?.querySelector('input, textarea');
            firstInput?.focus();
        }, 100);
    });
});


document.addEventListener('DOMContentLoaded', () => {
    
    const chatContainer = document.getElementById('chat-container');
    if (!chatContainer) return;

    const chatWindow = document.getElementById('chat-window');
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    const pdfInput = document.getElementById('pdf-input');
    const statusMessage = document.getElementById('status-message');
    let currentFilename = null;
    const modelName = chatContainer.dataset.model;
    const progressBarContainer = document.getElementById('progress-bar-container');
    const progressBar = document.getElementById('progress-bar');
    const CHAT_URL = chatContainer.dataset.chatUrl;
    const UPLOAD_URL = chatContainer.dataset.uploadUrl;
    const SUMMARIZE_URL = chatContainer.dataset.summarizeUrl;
    
    const translations = {
        en: {
            chat_title_prefix: "Chat with",
        greeting_initial: "Hello! I'm the {modelName} assistant. Please upload a PDF using the button to begin.",
        upload_placeholder_initial: "Please upload a PDF to begin...",
        upload_error: "Error processing file. Please try another.",
        chat_ready_status: "Ready to chat about",
        chat_placeholder_ready: "Type your question...",
        send_button: "Send",
        no_file_warning: "Please upload a PDF before asking questions.",
        lang_toggle: "AR",
        thinking: "Thinking...",
        responded_in: "Responded in {s}s",
        limit_reached: "You have reached your message limit for today.",
        file_too_large: "File is too large. The limit is 20MB.",
        uploading_status: "Uploading file...",
        summary_creating: "Creating summary...",
        embedding_status: "Analyzing content (this may take a moment)...",
        processing_timeout: "Processing timed out on the server. Please try a smaller file."
        },
        ar: {
            chat_title_prefix: "الدردشة مع",
        greeting_initial: "مرحباً! أنا المساعد {modelName}. يرجى تحميل ملف PDF باستخدام الزر للبدء.",
        upload_placeholder_initial: "يرجى تحميل ملف PDF للبدء...",
        upload_error: "خطأ في معالجة الملف. يرجى تجربة ملف آخر.",
        chat_ready_status: "جاهز للدردشة حول",
        chat_placeholder_ready: "اكتب سؤالك...",
        send_button: "إرسال",
        no_file_warning: "يرجى تحميل ملف PDF قبل طرح الأسئلة.",
        lang_toggle: "EN",
        thinking: "يفكر...",
        responded_in: "استجاب خلال {s}ث",
        limit_reached: "لقد وصلت إلى الحد الأقصى للرسائل لهذا اليوم.",
        file_too_large: "حجم الملف كبير جداً. الحد الأقصى هو 20 ميجابايت.",
        uploading_status: "جاري رفع الملف...",
        summary_creating: "جاري إنشاء الملخص...",
        embedding_status: "جاري تحليل المحتوى (قد يستغرق هذا بعض الوقت)...",
        processing_timeout: "انتهت مهلة المعالجة على الخادم. يرجى تجربة ملف أصغر."
            
        }
    };


    
    function saveHistory(historyArray) {
        if (currentFilename) {
            localStorage.setItem(`chatHistory_${currentFilename}`, JSON.stringify(historyArray));
        }
    }

    function loadHistory() {
        if (currentFilename) {
            return JSON.parse(localStorage.getItem(`chatHistory_${currentFilename}`) || '[]');
        }
        return [];
    }
    
    
    function renderTextMessage(sender, message, responseTimeText = null) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('chat-message', sender === 'user' ? 'user-message' : 'bot-message');
        messageElement.textContent = message;
        chatWindow.appendChild(messageElement);

        if (responseTimeText) {
            const timeInfo = document.createElement('div');
            timeInfo.classList.add('response-time');
            timeInfo.textContent = responseTimeText;
            chatWindow.appendChild(timeInfo);
        }
    }
    
    function renderSummary(summary, questions) {
        const T = translations[localStorage.getItem('lang') || 'en'];
        const container = document.createElement('div');
        container.classList.add('chat-message', 'bot-message', 'summary-container');

        let summaryHTML = `<strong>${T.summary_header}</strong><p style="margin: 5px 0 15px 0;">${summary}</p>`;
        
        if (questions && questions.length > 0) {
            summaryHTML += `<strong>${T.questions_header}</strong>`;
            const grid = document.createElement('div');
            grid.classList.add('suggested-questions-grid');
            questions.forEach(q => {
                const button = document.createElement('button');
                button.classList.add('suggested-question');
                button.textContent = q;
                button.onclick = () => {
                    chatInput.value = q;
                    handleSendMessage();
                };
                grid.appendChild(button);
            });
            container.innerHTML = summaryHTML;
            container.appendChild(grid);
        } else {
            container.innerHTML = summaryHTML;
        }
        
        chatWindow.appendChild(container);
    }

   
    function handleSendMessage() {
        const question = chatInput.value.trim();
        const T = translations[localStorage.getItem('lang') || 'en'];
        
        if (!question || !currentFilename) {
            if (!currentFilename) renderTextMessage('bot', T.no_file_warning);
            return;
        }

        let history = loadHistory();
        history.push({ type: 'text', sender: 'user', message: question });
        saveHistory(history);
        renderTextMessage('user', question);
        
        chatInput.value = '';
        renderTextMessage('bot', T.thinking); 

        const startTime = performance.now();
        fetch(CHAT_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question, filename: currentFilename, model: modelName })
        })
        .then(res => res.json())
        .then(data => {
            const allMessages = chatWindow.querySelectorAll('.bot-message');
            const thinkingMsg = allMessages[allMessages.length - 1];
            if (thinkingMsg && thinkingMsg.textContent === T.thinking) {
                thinkingMsg.remove();
            }

            const answer = data.answer || data.error;
            const responseTime = ((performance.now() - startTime) / 1000).toFixed(1);
            
            let history = loadHistory();
            history.push({ type: 'text', sender: 'bot', message: answer });
            saveHistory(history);
            renderTextMessage('bot', answer, T.responded_in.replace('{s}', responseTime));

            if (data.action === 'login_required') {
                document.getElementById('auth-modal-overlay')?.classList.remove('hidden');
            }
        });
    }

    function handleUpload(file) {
    currentFilename = file.name;
    localStorage.removeItem(`chatHistory_${currentFilename}`);
    chatWindow.innerHTML = '';
    
    const formData = new FormData();
    formData.append('pdf', file);
    const T = translations[localStorage.getItem('lang') || 'en'];

    
    progressBarContainer.classList.remove('hidden');
    statusMessage.style.color = 'var(--color-text-secondary)';
    progressBar.style.transition = 'width 0.5s ease-out'; 

    // Uploading the file
    statusMessage.textContent = T.uploading_status;
    progressBar.style.width = '10%';
    
    // Simulating the analysis on the backend
    setTimeout(() => {
        statusMessage.textContent = T.embedding_status;
        progressBar.style.transition = 'width 180s linear'; //The crawling
        progressBar.style.width = '85%';
    }, 1500);
    -
    
    fetch(UPLOAD_URL, { method: 'POST', body: formData })
    .then(response => {
        if (!response.ok) { 
            if (response.status === 413) { return Promise.reject(new Error(T.file_too_large)); }
            if (response.status === 500) { return Promise.reject(new Error(T.processing_timeout)); }
            return response.json().then(err => Promise.reject(new Error(err.error || 'Server error')));
        }
        return response.json();
    })
    .then(data => {
        
        // the function that handles the summary.
        progressBar.style.transition = 'width 0.5s ease-out';
        statusMessage.textContent = T.summary_creating;
        progressBar.style.width = '95%';
        
        initializeChatForFile(data.filename); 
        
        progressBar.style.width = '100%';
        
    })
    .catch(error => {
        progressBarContainer.classList.add('hidden');
        console.error('Upload process failed:', error);
        statusMessage.textContent = error.message || T.upload_error;
        statusMessage.style.color = 'red';
    })
    .finally(() => {
        if (currentFilename) {
            setTimeout(() => {
                progressBarContainer.classList.add('hidden');
            }, 2000); 
        }
    });
}

    function initializeChatForFile(filename) {
    currentFilename = filename;
    chatWindow.innerHTML = '';
    
    const history = loadHistory();
    const T = translations[localStorage.getItem('lang') || 'en']; 
    
    
    statusMessage.textContent = T.summary_creating; 
    chatInput.disabled = true;
    sendButton.disabled = true;

    if (history.length > 0) {
        
        history.forEach(item => {
            if (item.type === 'summary') {
                renderSummary(item.summary, item.questions);
            } else if (item.type === 'text') {
                renderTextMessage(item.sender, item.message);
            }
        });
        
        statusMessage.textContent = `${T.chat_ready_status} "${filename}".`;
        statusMessage.style.color = '#A3961C';
        chatInput.disabled = false;
        sendButton.disabled = false;
        chatInput.placeholder = T.chat_placeholder_ready;
        chatInput.focus();

    } else {
        
        fetch(SUMMARIZE_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename })
        })
        .then(res => res.json())
        .then(data => {
            if (data.summary) {
                const newHistory = [{ type: 'summary', summary: data.summary, questions: data.suggested_questions }];
                saveHistory(newHistory);
                renderSummary(data.summary, data.suggested_questions);
            }
            
            statusMessage.textContent = `${T.chat_ready_status} "${filename}".`;
            statusMessage.style.color = '#A3961C';
            chatInput.disabled = false;
            sendButton.disabled = false;
            chatInput.placeholder = T.chat_placeholder_ready;
            chatInput.focus();
        });
    }
}

    // EVENT LISTENERS 
    pdfInput.addEventListener('change', (e) => e.target.files[0] && handleUpload(e.target.files[0]));
    sendButton.addEventListener('click', handleSendMessage);
    chatInput.addEventListener('keypress', (e) => e.key === 'Enter' && handleSendMessage());
    
    // Modal Logic
    const loginModalButton = document.getElementById('login-modal-button');
    const authModalOverlay = document.getElementById('auth-modal-overlay');
    if (loginModalButton) {
        loginModalButton.addEventListener('click', () => authModalOverlay.classList.remove('hidden'));
    }
    document.getElementById('close-modal-button')?.addEventListener('click', () => authModalOverlay.classList.add('hidden'));
    document.getElementById('show-register-form')?.addEventListener('click', (e) => {
        e.preventDefault();
        document.getElementById('login-form-container').style.display = 'none';
        document.getElementById('register-form-container').style.display = 'block';
    });
    document.getElementById('show-login-form')?.addEventListener('click', (e) => {
        e.preventDefault();
        document.getElementById('register-form-container').style.display = 'none';
        document.getElementById('login-form-container').style.display = 'block';
    });
    const userMenuButton = document.getElementById('user-menu-button');
    const userMenuDropdown = document.getElementById('user-menu-dropdown');
    
    if (userMenuButton) {
        userMenuButton.addEventListener('click', () => {
            userMenuDropdown.classList.toggle('hidden');
        });
    }
    
    
    document.addEventListener('click', (event) => {
        if (userMenuButton && userMenuDropdown && !userMenuButton.contains(event.target) && !userMenuDropdown.contains(event.target)) {
            userMenuDropdown.classList.add('hidden');
        }
    });
    // Page Load Initialization
    const initialFilename = chatContainer.dataset.filename;
    if (initialFilename) {
        initializeChatForFile(initialFilename);
    } else {
        const T = translations[localStorage.getItem('lang') || 'en'];
        renderTextMessage('bot', T.greeting_initial.replace('{modelName}', modelName.toUpperCase()));
    }
});
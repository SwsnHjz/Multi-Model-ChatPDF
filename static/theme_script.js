document.addEventListener('DOMContentLoaded', () => {
    //logo link
    const logoLink = document.getElementById('logo-link');
    logoLink.addEventListener('click', (event) => {
        event.preventDefault();
        
        if (window.location.pathname === HOME_URL) {
             window.location.reload();
        } else {
            window.location.href = HOME_URL;
        }
    });
  
    //translation dictionary for homepage
    const translations = {
        en: {
            home_tagline: "Unlock the knowledge in your PDFs",
            home_subtitle: "Choose your AI assistant below to begin",
            model1_subs: "Powerful and versatile",
            model2_subs: "Fast and efficient",
            model3_subs: "Ideal for deep analysis",
            model4_subs: "Best for technical manuals",
            lang_toggle: "AR",
            register_success: "Your account has been created! You can now log in.",
            login_error: "Login Unsuccessful. Please check username and password.",
            username_exists: "Username already exists. Please choose a different one.",
            guest_mode_activated: "Guest mode activated. You have a 2-message limit.",
            login_or_guest_required: "Please log in or continue as a guest to use the chat.",
            email_exists: "That email is already registered. Please log in.",
            registration_success_check_email: "Registration successful! Please check your email to activate your account.",
            confirmation_link_invalid: "The confirmation link is invalid or has expired.",
            account_already_confirmed: "Your account has already been confirmed. Please log in.",
            account_confirmed_success: "Your account has been confirmed! You can now log in.",
            account_not_confirmed: "Your account has not been confirmed. Please check your email.",
            account_not_confirmed_check_email: "This account is not activated. Please check your email inbox (and spam folder) for a confirmation link.",
            login_button: "Login",
            modal_login_header: "Login",
            modal_username_label: "Username",
            modal_password_label: "Password",
            modal_register_prompt: "Don't have an account?",
            modal_register_link: "Register here",
            modal_guest_link: "Or, continue as Guest",
            modal_register_header: "Register",
            modal_register_button: "Register",
            modal_login_prompt: "Already have an account?",
            modal_login_link: "Login here",
            modal_email_label: "Email",
            divider_or: "OR",
            google_login_button: "Sign in with Google",
            logout_button: "Logout"
        },
        ar: {
            home_tagline: "اكتشف المعرفة الكامنة في ملفاتك.",
            home_subtitle: "اختر نموذجًا لبدء الدردشة مع مستنداتك.",
            model1_subs: "قوي و متعدد الاستخدامات",
            model2_subs: "سريع و فعال",
            model3_subs: "مثالي للتحليل الدقيق",
            model4_subs: "الأفضل للأدلة التقنية",
            lang_toggle: "EN",
            register_success: ".تم إنشاء حسابك بنجاح! يمكنك الآن تسجيل الدخول",
            login_error: ".فشل تسجيل الدخول. يرجى التحقق من اسم المستخدم وكلمة المرور",
            username_exists: ".اسم المستخدم موجود بالفعل. الرجاء اختيار اسم مختلف",
            guest_mode_activated: ".تم تفعيل وضع الزائر. لديك حد أقصى رسالتين",
            login_or_guest_required: ".الرجاء تسجيل الدخول أو المتابعة كزائر لاستخدام الدردشة",
            email_exists: "هذا الايميل مسجل بالفعل . يرجى تسجبل الدخول",
            registration_success_check_email: "تم التسجيل بنجاح! يُرجى مراجعة بريدك الإلكتروني لتفعيل حسابك.",
            confirmation_link_invalid: "رابط التأكيد غير صالح أو انتهت صلاحيته.",
            account_already_confirmed: "حسابك مؤكد بالفعل. يُرجى تسجيل الدخول.",
            account_confirmed_success: "تم تأكيد حسابك! يمكنك الآن تسجيل الدخول.",
            account_not_confirmed: "لم يتم تأكيد حسابك. يُرجى التحقق من بريدك الإلكتروني.",
            account_not_confirmed_check_email: ".هذا الحساب غير مفعل. الرجاء مراجعة بريدك الإلكتروني (ومجلد الرسائل غير المرغوب فيها) للحصول على رابط التفعيل"
            ,login_button: "تسجيل الدخول",
            modal_login_header: "تسجيل الدخول",
            modal_username_label: "اسم المستخدم",
            modal_password_label: "كلمة المرور",
            modal_register_prompt: "ليس لديك حساب؟",
            modal_register_link: "سجل هنا",
            modal_guest_link: "أو المتابعة كزائر",
            modal_register_header: "تسجيل",
            modal_register_button: "تسجيل",
            modal_login_prompt: "هل لديك حساب بالفعل؟",
            modal_login_link: "سجل الدخول هنا",
            modal_email_label: "البريد الإلكتروني"
            ,divider_or: "أو",
            google_login_button: "تسجيل الدخول باستخدام google",
            logout_button: "تسجيل الخروج"
        }
    };

    //theme and language toggles
    const themeToggle = document.getElementById('theme-toggle');
    const mainLogo = document.getElementById('main-logo');
    const langToggle = document.getElementById('lang-toggle');
    // login modal and user menu
    const loginModalButton = document.getElementById('login-modal-button');
    const authModalOverlay = document.getElementById('auth-modal-overlay');
    const closeModalButton = document.getElementById('close-modal-button');
    const showRegisterLink = document.getElementById('show-register-form');
    const showLoginLink = document.getElementById('show-login-form');
    const loginForm = document.getElementById('login-form-container');
    const registerForm = document.getElementById('register-form-container');
    const userMenuButton = document.getElementById('user-menu-button');
    const userMenuDropdown = document.getElementById('user-menu-dropdown');
    
    if (authModalOverlay && closeModalButton) {
    
    closeModalButton.addEventListener('click', () => {
       
        authModalOverlay.classList.add('hidden');
    });
}
    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        const emoji = document.getElementById('theme-emoji');
        if (theme === 'dark') {
            if (mainLogo) mainLogo.src = '/static/images/logo_yellow.png'; 
            if (emoji) emoji.textContent = '☀';
            
        } else {
            if (mainLogo) mainLogo.src = '/static/images/logo-Photoroom.png'; 
            if (emoji) emoji.textContent = '☾';
            
        }
    }

    function setLanguage(lang) {
        document.documentElement.setAttribute('lang', lang);
        document.documentElement.setAttribute('dir', lang === 'ar' ? 'rtl' : 'ltr');
        localStorage.setItem('lang', lang);

        document.querySelectorAll('[data-translate-key]').forEach(element => {
            const key = element.dataset.translateKey;
            if (translations[lang] && translations[lang][key]) {
                element.textContent = translations[lang][key];
            }
        });

        langToggle.textContent = translations[lang].lang_toggle;
    }
    
    //event listners for the toggles
    if (themeToggle) themeToggle.addEventListener('click', () => {
        let newTheme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        applyTheme(newTheme);
    });

    if (langToggle) langToggle.addEventListener('click', () => {
        let currentLang = localStorage.getItem('lang') || 'en';
        let newLang = currentLang === 'en' ? 'ar' : 'en';
        setLanguage(newLang);
    });

    document.querySelectorAll('.control-button').forEach(button => {
        button.addEventListener('mouseup', () => {
            button.blur();
        });
    });
    
  

// This handles the LOGGED-IN user state
if (userMenuButton) {
    userMenuButton.addEventListener('click', () => {
        userMenuDropdown.classList.toggle('hidden');
    });
    
    // This closes the dropdown when clicking elsewhere
    document.addEventListener('click', (event) => {
        if (!userMenuButton.contains(event.target) && !userMenuDropdown.contains(event.target)) {
            userMenuDropdown.classList.add('hidden');
        }
    });
}

// This handles the LOGGED-OUT and GUEST states
if (loginModalButton) {
    loginModalButton.addEventListener('click', () => {
        authModalOverlay.classList.remove('hidden');
    });

    const isGuest = document.querySelector('.guest-indicator') !== null;
    if (!isGuest) {
        document.querySelectorAll('.model-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault(); 
                loginModalButton.click(); 
            });
        });
    }
}


    // intialized theme and language
    const savedTheme = localStorage.getItem('theme') || 'light';
    const savedLang = localStorage.getItem('lang') || 'en';
    applyTheme(savedTheme);
    setLanguage(savedLang);
});
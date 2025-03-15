document.addEventListener("DOMContentLoaded", function () {
    const translations = {
        en: {
            "company-name": "RentEase",
            "nav-home": "Home",
            "nav-login": "Login",
            "nav-register": "Register",
            "dashboard-title": "Dashboard",
            "dashboard-desc": "Manage your rental properties here.",
            "property1-title": "House 1",
            "property1-location": "Location: New York",
            "property1-price": "Price: $1200/month",
            "property2-title": "House 2",
            "property2-location": "Location: Los Angeles",
            "property2-price": "Price: $1500/month"
        },
        mr: {
            "company-name": "रेन्टइझ",
            "nav-home": "मुख्यपृष्ठ",
            "nav-login": "लॉगिन",
            "nav-register": "नोंदणी",
            "dashboard-title": "डॅशबोर्ड",
            "dashboard-desc": "तुमच्या भाड्याच्या मालमत्ता व्यवस्थापित करा.",
            "property1-title": "घर १",
            "property1-location": "स्थान: न्यूयॉर्क",
            "property1-price": "किंमत: $1200/महिना",
            "property2-title": "घर २",
            "property2-location": "स्थान: लॉस एंजेलिस",
            "property2-price": "किंमत: $1500/महिना"
        }
    };

    const languageSelect = document.getElementById("language-select");

    function changeLanguage(lang) {
        document.querySelectorAll("[data-lang]").forEach(element => {
            const key = element.getAttribute("data-lang");
            if (translations[lang][key]) {
                element.textContent = translations[lang][key];
            }
        });
    }

    languageSelect.addEventListener("change", function () {
        const selectedLang = this.value;
        localStorage.setItem("selectedLanguage", selectedLang);
        changeLanguage(selectedLang);
    });

    // Load saved language preference
    const savedLanguage = localStorage.getItem("selectedLanguage") || "en";
    languageSelect.value = savedLanguage;
    changeLanguage(savedLanguage);
});

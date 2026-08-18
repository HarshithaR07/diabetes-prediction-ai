import os
from dotenv import load_dotenv

load_dotenv()

try:
    import anthropic
    API_KEY = os.getenv("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=API_KEY) if API_KEY else None
except ImportError:
    client = None

# ---------- OFFLINE (rule-based) responses, per language ----------
OFFLINE_RESPONSES = {
    "en": {
        "sugar": "Reduce refined sugar and sugary drinks. Choose whole fruits over fruit juice, and avoid sweets, sodas, and processed snacks.",
        "food": "Focus on whole grains, vegetables, lean protein, and healthy fats. Reduce refined carbs like white rice and maida-based foods.",
        "diet": "Focus on whole grains, vegetables, lean protein, and healthy fats. Reduce refined carbs like white rice and maida-based foods.",
        "exercise": "Aim for at least 30 minutes of moderate exercise (like brisk walking) 5 days a week. Include some strength training twice a week if possible.",
        "glucose": "Normal fasting glucose is under 100 mg/dL. If yours is elevated, reduce sugar intake, exercise regularly, and consult a doctor for monitoring.",
        "bmi": "A healthy BMI range is 18.5-24.9. If yours is higher, a combination of calorie control and regular exercise can help bring it down gradually.",
        "insulin": "High insulin levels can indicate insulin resistance. Low-glycemic-index foods and regular physical activity can help improve insulin sensitivity.",
        "symptoms": "Common Type 2 diabetes symptoms include excessive thirst, frequent urination, fatigue, and blurred vision. If you notice these, consult a doctor.",
        "medication": "I can't provide medication advice. Please consult a qualified doctor for anything related to prescriptions or dosage.",
        "stress": "Chronic stress can raise blood sugar levels. Try deep breathing, regular sleep, and light physical activity to help manage stress.",
        "water": "Staying well-hydrated supports healthy blood sugar levels. Aim for 8-10 glasses of water a day, and limit sugary beverages.",
        "default": "I can help with questions about diet, exercise, glucose, BMI, insulin, symptoms, or stress management related to diabetes. Could you rephrase your question around one of these topics?"
    },
    "hi": {
        "sugar": "परिष्कृत चीनी और मीठे पेय पदार्थों का सेवन कम करें। फलों के रस की जगह पूरे फल खाएं, और मिठाई, सोडा, और प्रोसेस्ड स्नैक्स से बचें।",
        "food": "साबुत अनाज, सब्जियां, लीन प्रोटीन, और स्वस्थ वसा पर ध्यान दें। सफेद चावल और मैदा से बने खाद्य पदार्थों जैसे परिष्कृत कार्ब्स को कम करें।",
        "diet": "साबुत अनाज, सब्जियां, लीन प्रोटीन, और स्वस्थ वसा पर ध्यान दें। सफेद चावल और मैदा से बने खाद्य पदार्थों जैसे परिष्कृत कार्ब्स को कम करें।",
        "exercise": "सप्ताह में कम से कम 5 दिन 30 मिनट का मध्यम व्यायाम (जैसे तेज चलना) करें। संभव हो तो सप्ताह में दो बार कुछ शक्ति प्रशिक्षण भी शामिल करें।",
        "glucose": "सामान्य फास्टिंग ग्लूकोज़ 100 mg/dL से कम होता है। यदि आपका अधिक है, तो चीनी का सेवन कम करें, नियमित व्यायाम करें, और निगरानी के लिए डॉक्टर से सलाह लें।",
        "bmi": "स्वस्थ बीएमआई सीमा 18.5-24.9 है। यदि आपका अधिक है, तो कैलोरी नियंत्रण और नियमित व्यायाम का संयोजन इसे धीरे-धीरे कम करने में मदद कर सकता है।",
        "insulin": "उच्च इंसुलिन स्तर इंसुलिन प्रतिरोध का संकेत दे सकता है। कम ग्लाइसेमिक-इंडेक्स वाले खाद्य पदार्थ और नियमित शारीरिक गतिविधि इंसुलिन संवेदनशीलता में सुधार कर सकते हैं।",
        "symptoms": "टाइप 2 मधुमेह के सामान्य लक्षणों में अत्यधिक प्यास, बार-बार पेशाब आना, थकान, और धुंधली दृष्टि शामिल हैं। यदि आप इन्हें देखते हैं, तो डॉक्टर से सलाह लें।",
        "medication": "मैं दवा संबंधी सलाह नहीं दे सकता। कृपया नुस्खे या खुराक से संबंधित किसी भी चीज़ के लिए एक योग्य डॉक्टर से परामर्श करें।",
        "stress": "पुराना तनाव रक्त शर्करा के स्तर को बढ़ा सकता है। तनाव प्रबंधन के लिए गहरी सांस लेना, नियमित नींद, और हल्की शारीरिक गतिविधि आज़माएं।",
        "water": "अच्छी तरह हाइड्रेटेड रहना स्वस्थ रक्त शर्करा के स्तर का समर्थन करता है। प्रतिदिन 8-10 गिलास पानी पिएं, और मीठे पेय पदार्थों को सीमित करें।",
        "default": "मैं आहार, व्यायाम, ग्लूकोज़, बीएमआई, इंसुलिन, लक्षण, या तनाव प्रबंधन से संबंधित प्रश्नों में मदद कर सकता हूं। कृपया इनमें से किसी एक विषय के आसपास अपना प्रश्न फिर से लिखें।"
    },
    "kn": {
        "sugar": "ಸಂಸ್ಕರಿಸಿದ ಸಕ್ಕರೆ ಮತ್ತು ಸಿಹಿ ಪಾನೀಯಗಳ ಸೇವನೆ ಕಡಿಮೆ ಮಾಡಿ. ಹಣ್ಣಿನ ರಸಕ್ಕಿಂತ ಸಂಪೂರ್ಣ ಹಣ್ಣುಗಳನ್ನು ಆಯ್ಕೆಮಾಡಿ, ಮತ್ತು ಸಿಹಿತಿಂಡಿಗಳು, ಸೋಡಾಗಳು ಮತ್ತು ಸಂಸ್ಕರಿಸಿದ ತಿಂಡಿಗಳನ್ನು ತಪ್ಪಿಸಿ.",
        "food": "ಧಾನ್ಯಗಳು, ತರಕಾರಿಗಳು, ಲೀನ್ ಪ್ರೋಟೀನ್ ಮತ್ತು ಆರೋಗ್ಯಕರ ಕೊಬ್ಬುಗಳ ಮೇಲೆ ಗಮನ ಹರಿಸಿ. ಬಿಳಿ ಅಕ್ಕಿ ಮತ್ತು ಮೈದಾ ಆಧಾರಿತ ಆಹಾರಗಳಂತಹ ಸಂಸ್ಕರಿಸಿದ ಕಾರ್ಬ್‌ಗಳನ್ನು ಕಡಿಮೆ ಮಾಡಿ.",
        "diet": "ಧಾನ್ಯಗಳು, ತರಕಾರಿಗಳು, ಲೀನ್ ಪ್ರೋಟೀನ್ ಮತ್ತು ಆರೋಗ್ಯಕರ ಕೊಬ್ಬುಗಳ ಮೇಲೆ ಗಮನ ಹರಿಸಿ. ಬಿಳಿ ಅಕ್ಕಿ ಮತ್ತು ಮೈದಾ ಆಧಾರಿತ ಆಹಾರಗಳಂತಹ ಸಂಸ್ಕರಿಸಿದ ಕಾರ್ಬ್‌ಗಳನ್ನು ಕಡಿಮೆ ಮಾಡಿ.",
        "exercise": "ವಾರದಲ್ಲಿ ಕನಿಷ್ಠ 5 ದಿನ 30 ನಿಮಿಷಗಳ ಮಧ್ಯಮ ವ್ಯಾಯಾಮ (ವೇಗದ ನಡಿಗೆಯಂತಹ) ಮಾಡಲು ಗುರಿಯಿಡಿ. ಸಾಧ್ಯವಾದರೆ ವಾರಕ್ಕೆ ಎರಡು ಬಾರಿ ಸ್ವಲ್ಪ ಶಕ್ತಿ ತರಬೇತಿಯನ್ನು ಸೇರಿಸಿ.",
        "glucose": "ಸಾಮಾನ್ಯ ಉಪವಾಸ ಗ್ಲೂಕೋಸ್ 100 mg/dL ಗಿಂತ ಕಡಿಮೆ ಇರುತ್ತದೆ. ನಿಮ್ಮದು ಹೆಚ್ಚಾಗಿದ್ದರೆ, ಸಕ್ಕರೆ ಸೇವನೆ ಕಡಿಮೆ ಮಾಡಿ, ನಿಯಮಿತವಾಗಿ ವ್ಯಾಯಾಮ ಮಾಡಿ, ಮತ್ತು ಮೇಲ್ವಿಚಾರಣೆಗಾಗಿ ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ.",
        "bmi": "ಆರೋಗ್ಯಕರ ಬಿಎಂಐ ವ್ಯಾಪ್ತಿ 18.5-24.9 ಆಗಿದೆ. ನಿಮ್ಮದು ಹೆಚ್ಚಾಗಿದ್ದರೆ, ಕ್ಯಾಲೊರಿ ನಿಯಂತ್ರಣ ಮತ್ತು ನಿಯಮಿತ ವ್ಯಾಯಾಮದ ಸಂಯೋಜನೆಯು ಅದನ್ನು ಕ್ರಮೇಣ ಕಡಿಮೆ ಮಾಡಲು ಸಹಾಯ ಮಾಡುತ್ತದೆ.",
        "insulin": "ಹೆಚ್ಚಿನ ಇನ್ಸುಲಿನ್ ಮಟ್ಟಗಳು ಇನ್ಸುಲಿನ್ ಪ್ರತಿರೋಧವನ್ನು ಸೂಚಿಸಬಹುದು. ಕಡಿಮೆ ಗ್ಲೈಸೆಮಿಕ್-ಸೂಚ್ಯಂಕ ಆಹಾರಗಳು ಮತ್ತು ನಿಯಮಿತ ದೈಹಿಕ ಚಟುವಟಿಕೆ ಇನ್ಸುಲಿನ್ ಸಂವೇದನೆಯನ್ನು ಸುಧಾರಿಸಲು ಸಹಾಯ ಮಾಡುತ್ತದೆ.",
        "symptoms": "ಸಾಮಾನ್ಯ ಟೈಪ್ 2 ಮಧುಮೇಹ ಲಕ್ಷಣಗಳಲ್ಲಿ ಅತಿಯಾದ ಬಾಯಾರಿಕೆ, ಆಗಾಗ್ಗೆ ಮೂತ್ರ ವಿಸರ್ಜನೆ, ಆಯಾಸ ಮತ್ತು ಮಸುಕಾದ ದೃಷ್ಟಿ ಸೇರಿವೆ. ನೀವು ಇವುಗಳನ್ನು ಗಮನಿಸಿದರೆ, ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ.",
        "medication": "ನಾನು ಔಷಧಿ ಸಲಹೆ ನೀಡಲು ಸಾಧ್ಯವಿಲ್ಲ. ದಯವಿಟ್ಟು ಪ್ರಿಸ್ಕ್ರಿಪ್ಷನ್ ಅಥವಾ ಡೋಸೇಜ್‌ಗೆ ಸಂಬಂಧಿಸಿದ ಯಾವುದೇ ವಿಷಯಕ್ಕೆ ಅರ್ಹ ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ.",
        "stress": "ದೀರ್ಘಕಾಲದ ಒತ್ತಡವು ರಕ್ತದ ಸಕ್ಕರೆ ಮಟ್ಟವನ್ನು ಹೆಚ್ಚಿಸಬಹುದು. ಒತ್ತಡ ನಿರ್ವಹಣೆಗಾಗಿ ಆಳವಾದ ಉಸಿರಾಟ, ನಿಯಮಿತ ನಿದ್ರೆ ಮತ್ತು ಹಗುರವಾದ ದೈಹಿಕ ಚಟುವಟಿಕೆಯನ್ನು ಪ್ರಯತ್ನಿಸಿ.",
        "water": "ಚೆನ್ನಾಗಿ ಹೈಡ್ರೀಕರಿಸಿದ ಸ್ಥಿತಿಯಲ್ಲಿರುವುದು ಆರೋಗ್ಯಕರ ರಕ್ತದ ಸಕ್ಕರೆ ಮಟ್ಟವನ್ನು ಬೆಂಬಲಿಸುತ್ತದೆ. ದಿನಕ್ಕೆ 8-10 ಲೋಟ ನೀರು ಕುಡಿಯಲು ಗುರಿಯಿಡಿ, ಮತ್ತು ಸಿಹಿ ಪಾನೀಯಗಳನ್ನು ಮಿತಿಗೊಳಿಸಿ.",
        "default": "ನಾನು ಆಹಾರ, ವ್ಯಾಯಾಮ, ಗ್ಲೂಕೋಸ್, ಬಿಎಂಐ, ಇನ್ಸುಲಿನ್, ಲಕ್ಷಣಗಳು ಅಥವಾ ಒತ್ತಡ ನಿರ್ವಹಣೆಗೆ ಸಂಬಂಧಿಸಿದ ಪ್ರಶ್ನೆಗಳಿಗೆ ಸಹಾಯ ಮಾಡಬಲ್ಲೆ. ದಯವಿಟ್ಟು ಈ ವಿಷಯಗಳಲ್ಲಿ ಒಂದರ ಸುತ್ತ ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಮರುರೂಪಿಸಿ."
    }
}

LANGUAGE_NAMES = {"en": "English", "hi": "Hindi", "kn": "Kannada"}


def get_offline_response(user_message, lang="en"):
    message_lower = user_message.lower()
    responses = OFFLINE_RESPONSES.get(lang, OFFLINE_RESPONSES["en"])

    keywords = ["sugar", "food", "diet", "exercise", "glucose", "bmi", "insulin", "symptoms", "medication", "stress", "water"]
    for keyword in keywords:
        if keyword in message_lower:
            return responses[keyword]
    return responses["default"]


def get_online_response(user_message, risk_tier="Unknown", lang="en"):
    if client is None:
        return None

    language_name = LANGUAGE_NAMES.get(lang, "English")

    try:
        system_prompt = (
            f"You are a helpful diabetes lifestyle assistant. The user's current risk tier is '{risk_tier}'. "
            f"Reply entirely in {language_name}. "
            "Give short, practical, non-medical lifestyle advice about diet, exercise, and habits for Type 2 diabetes prevention. "
            "Do not provide medication or dosage advice — tell the user to consult a doctor for that. "
            "Keep responses under 100 words."
        )
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )
        return response.content[0].text
    except Exception as e:
        print(f"Online chatbot failed: {e}")
        return None


def get_chatbot_response(user_message, risk_tier="Unknown", lang="en"):
    online_reply = get_online_response(user_message, risk_tier, lang)
    if online_reply:
        return {"reply": online_reply, "mode": "online"}
    else:
        offline_reply = get_offline_response(user_message, lang)
        return {"reply": offline_reply, "mode": "offline"}
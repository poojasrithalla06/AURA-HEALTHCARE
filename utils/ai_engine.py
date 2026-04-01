import subprocess

def detect_language(text):
    """Simple script-based language detection."""
    for char in text:
        # Hindi (Devanagari)
        if '\u0900' <= char <= '\u097F':
            return "Hindi"
        # Telugu
        if '\u0c00' <= char <= '\u0c7F':
            return "Telugu"
    return "English"

def query_local_llm(prompt):
    try:
        ollama_path = r"C:\Users\HP\AppData\Local\Programs\Ollama\ollama.exe"
        result = subprocess.run(
            [ollama_path, 'run', 'tinyllama'],
            input=prompt,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        raw_output = result.stdout.strip()
        
        # Aggressive cleaning for Small LLMs (TinyLLaMA)
        # 1. Remove anything before the LAST 'Assistant:' label if it exists
        if "Assistant:" in raw_output:
            raw_output = raw_output.split("Assistant:")[-1].strip()
        
        # 2. Remove anything after 'Human:' or 'User:' (hallucinated continuation)
        for stop_word in ["Human:", "User:", "<|user|>", "System instruction:"]:
            if stop_word in raw_output:
                raw_output = raw_output.split(stop_word)[0].strip()

        # 3. Strip common AI labels that TinyLLaMA tends to include despite instructions
        prefixes_to_remove = ["Healthcare Assistant:", "Assistant:", "Doctor:", "Aura:", "Aura AI:", "System:", "Response:", "AI:", "IMPORTANT:"]
        for prefix in prefixes_to_remove:
            if raw_output.lower().startswith(prefix.lower()):
                raw_output = raw_output[len(prefix):].strip()
            elif raw_output.lower().startswith("*" + prefix.lower() + "*"):
                raw_output = raw_output[len(prefix) + 2:].strip()
                
        # 4. Remove the instructions themselves if they leaked into the output
        if "- Respond ONLY in" in raw_output:
            # The model echoed the whole prompt
            lines = raw_output.split('\n')
            clean_lines = []
            for line in lines:
                if not any(instr in line for instr in ["Respond ONLY", "Do NOT use English", "Do NOT include names", "Keep response short", "Answer like a doctor"]):
                    clean_lines.append(line)
            raw_output = '\n'.join(clean_lines).strip()

        # 5. Clean LLM output: Remove ALL repeated lines
        clean_lines = []
        seen = set()
        for line in raw_output.split('\n'):
            line = line.strip()
            if not line: continue
            if line.lower() not in seen:
                clean_lines.append(line)
                seen.add(line.lower())
                
        raw_output = '\n'.join(clean_lines).strip()
        
        return raw_output
    except Exception as e:
        print(f"Ollama Error: {e}")
        return "I'm sorry, I'm having trouble connecting to my local brain right now. Please ensure Ollama is running."

def predict_risk(data):
    # Mock AI Algorithm
    # In real world: Load pickled scikit-learn model here
    
    age = data.get('age', 30)
    systolic_bp = data.get('systolic_bp', 120)
    diastolic_bp = data.get('diastolic_bp', 80)
    heart_rate = data.get('heart_rate', 70)
    glucose = data.get('glucose_level', 90)
    
    risk_score = 0
    
    # Simple Heuristic Rule-based "Model"
    if systolic_bp > 140 or diastolic_bp > 90:
        risk_score += 30
    elif systolic_bp > 120:
        risk_score += 15
        
    if heart_rate > 100 or heart_rate < 50:
        risk_score += 20
        
    if glucose > 140:
        risk_score += 25
    elif glucose < 70:
        risk_score += 15
        
    if age > 50:
        risk_score += 10
        
    risk_score = min(risk_score, 100) # Cap at 100
    
    explanation = []
    if risk_score > 60:
        explanation.append("Multiple risk factors detected: high BP/Glucose.")
    elif risk_score > 30:
        explanation.append("Moderate risk. Lifestyle changes recommended.")
    else:
        explanation.append("Healthy vitals. Maintain current routine.")
        
    return risk_score, " ".join(explanation)

def chat_response(message, language, user_id):
    # Mock NLP Chatbot
    msg = message.lower()
    
    # Auto-detect language if not explicitly set to non-English
    detected_lang = detect_language(msg)
    if detected_lang == "Hindi": language = 'hi'
    elif detected_lang == "Telugu": language = 'te'
    
    # Keyword mapping for different languages to internal intent
    intents = {
        'hello': ['hello', 'hi', 'hey', 'namaste', 'హలో', 'నమస్తే', 'नमस्ते', 'नमस्कार'],
        'headache': ['headache', 'head pain', 'తలనొప్పి', 'सिरदर्द', 'डोकेदुखी', 'തലവേദന', 'தலைவலி'],
        'fever': ['fever', 'జ్వరం', 'ఫీవర్', 'बुखार', 'ताप', 'പനി', 'காய்ச்சல்', 'favour'], # added 'favour' as a common typo
        'appointment': ['appointment', 'book', 'doctor', 'అపాయింట్మెంట్', 'డాక్టర్', 'अपॉइंटमेंट', 'डॉक्टर', 'അപ്പോയിന്റ്മെന്റ്', 'அப்பாயிண்ட்மெண்ட்'],
        'thanks': ['thanks', 'thank you', 'ధన్యవాదాలు', 'ధన్యవాదాలు', 'धन्यवाद', 'आभारी आहे', 'നന്ദി', 'நன்றி']
    }

    responses = {
        'en': {
            'hello': "Hello! I am Aura, your virtual healthcare assistant. I can help you check symptoms, monitor vitals, or book appointments. How are you feeling today?",
            'headache': "I'm sorry to hear about your headache. For mild cases, rest in a quiet, dark room and stay hydrated. However, if it's severe or accompanied by nausea or vision changes, please consult a doctor immediately.",
            'fever': "A fever usually indicates your body is fighting an infection. Rest well, drink plenty of fluids, and monitor your temperature carefully. If it stays above 102°F (39°C) or lasts more than 3 days, seek medical attention.",
            'appointment': "I can help you with that! You can navigate to the 'Book Appointment' section on your dashboard to see available specialists. Would you like me to guide you there?",
            'thanks': "You're very welcome! I'm here to help. Stay healthy!",
            'default': "I understand you're reachng out about your health. Could you please provide more details about your symptoms so I can assist you better? You can also book a consultation with our experts."
        },
        'hi': { # Hindi
            'hello': "नमस्ते! मैं ऑरा हूँ, आपकी स्वास्थ्य सहायक। मैं लक्षणों की जांच करने, स्वास्थ्य पर नज़र रखने या अपॉइंटमेंट बुक करने में आपकी मदद कर सकती हूँ। आज आप कैसा महसूस कर रहे हैं?",
            'headache': "सिरदर्द के बारे में जानकर दुख हुआ। हल्के सिरदर्द के लिए, आराम करें और पानी पिएं। यदि दर्द तेज है, तो कृपया डॉक्टर से मिलें।",
            'fever': "बुखार आमतौर पर संक्रमण का संकेत है। आराम करें और तरल पदार्थ पिएं। यदि बुखार 102°F से अधिक है, तो तुरंत डॉक्टर से संपर्क करें।",
            'appointment': "मैं आपकी मदद कर सकती हूँ! आप डैशबोर्ड पर जाकर अपॉइंटमेंट बुक कर सकते हैं।",
            'thanks': "आपका स्वागत है! अपना ख्याल रखें।",
            'default': "मैं समझ रही हूँ। क्या आप मुझे अपने लक्षणों के बारे में थोड़ा और बता सकते हैं?"
        },
        'te': { # Telugu
            'hello': "నమస్తే! నేను ఆరా, మీ వర్చువల్ హెల్త్‌కేర్ అసిస్టెంట్‌ని. నేను మీకు లక్షణాలను తనిఖీ చేయడంలో లేదా అపాయింట్‌మెంట్‌లను బుక్ చేయడంలో సహాయపడగలను. ఈ రోజు మీరు ఎలా ఉన్నారు?",
            'headache': "మీ తలనొప్పి గురించి వినడానికి బాధగా ఉంది. విశ్రాంతి తీసుకోండి మరియు నీరు ఎక్కువగా త్రాగండి. నొప్పి ఎక్కువగా ఉంటే వెంటనే డాక్టరును సంప్రదించండి.",
            'fever': "జ్వరం సాధారణంగా ఇన్ఫెక్షన్‌ని సూచిస్తుంది. బాగా విశ్రాంతి తీసుకోండి, తగినంత ద్రవాలు త్రాగండి. ఒకవేళ జ్వరం 102°F కంటే ఎక్కువగా ఉన్నా లేదా 3 రోజులకు పైగా ఉన్నా, డాక్టరును సంప్రదించండి.",
            'appointment': "నేను మీకు సహాయం చేయగలను! అపాయింట్‌మెంట్ బుక్ చేసుకోవడానికి మీరు మీ డాష్‌బోర్డ్ లోని 'Book Appointment' విభాగంలో చూడవచ్చు.",
            'thanks': "మీకు స్వాగతం! ఆరోగ్యంగా ఉండండి.",
            'default': "క్షమించండి, మీ సమస్య నాకు సరిగ్గా అర్థం కాలేదు. దయచేసి మీ లక్షణాల గురించి వివరించండి, నేను మీకు సహాయం చేస్తాను."
        },
        'mr': { # Marathi
            'hello': "नमस्कार! मी ऑरा आहे, तुमची आरोग्य सहाय्यक. मी तुम्हाला आज कशी मदत करू शकते?",
            'fever': "ताप येणे हे सहसा संसर्गाचे लक्षण असते. विश्रांती घ्या आणि पाणी भरपूर प्या. ताप वाढल्यास डॉक्टरांचा सल्ला घ्या.",
            'default': "मला तुमचे म्हणणे नीट समजले नाही. कृपया सविस्तर सांगा."
        },
        'ta': { # Tamil
            'hello': "வணக்கம்! நான் ஆரா, உங்கள் சுகாதார உதவியாளர். உங்களுக்கு இன்று நான் எப்படி உதவ முடியும்?",
            'fever': "காய்ச்சல் பொதுவாக ஒரு தொற்றுநோயைக் குறிக்கிறது. ஓய்வெடுங்கள், போதுமான அளவு தண்ணீர் குடிக்கவும். காய்ச்சல் நீடித்தால் மருத்துவரை அணுகவும்.",
            'default': "மன்னிக்கவும், நீங்கள் சொல்வது எனக்கு புரியவில்லை. தயவுசெய்து விரிவாக சொல்லுங்கள்."
        },
        'ml': { # Malayalam
            'hello': "നമസ്കാരം! ഞാൻ ഓറ, നിങ്ങളുടെ ആരോഗ്യ സഹായി. ഇന്ന് ഞാൻ നിങ്ങൾക്ക് എങ്ങനെ സഹായിക്കാം?",
            'fever': "പനി സാധാരണയായി ഒരു അണുബാധയെ സൂചിപ്പിക്കുന്നു. വിശ്രമിക്കുക, ധാരാളം വെള്ളം കുടിക്കുക. പനി കൂടിയാൽ ഡോക്ടറെ കാണുക.",
            'default': "ക്ഷമിക്കണം, എനിക്ക് മനസ്സിലായില്ല. ദയവായി കൂടുതൽ വിവരങ്ങൾ നൽകുക."
        }
    }
    
    # Determine the intent based on keywords
    intent_found = 'default'
    for intent, keywords in intents.items():
        if any(keyword in msg for keyword in keywords):
            intent_found = intent
            break
            
    # Get current language dictionary, fallback to English
    lang_dict = responses.get(language, responses['en'])
    
    # Return matched intent in the correct language
    return lang_dict.get(intent_found, lang_dict['default'])

def scan_prescription_with_ai(ocr_text):
    """Analyze OCR text from prescription to extract structured medical details."""
    prompt = (
        f"Analyze this medical prescription text and extract structured information. "
        f"Text: \"{ocr_text}\"\n\n"
        "Instructions:\n"
        "1. Identify Medicines\n"
        "2. Extract Dosage (e.g., 500mg, 1-0-1)\n"
        "3. Advice/Suggestions\n\n"
        "Format your response as a clean bulleted list only. Do not add intro or outro."
    )
    
    raw_response = query_local_llm(prompt)
    
    # Process structured response
    medicine_list = []
    dosage_info = []
    advice = []
    
    lines = raw_response.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip('- *#')
        if not line: continue
        
        low_line = line.lower()
        if "medicine" in low_line: current_section = "m"
        elif "dosage" in low_line or "quantity" in low_line: current_section = "d"
        elif "advice" in low_line or "suggestion" in low_line: current_section = "a"
        
        if current_section == "m" and "medicine" not in low_line: medicine_list.append(line)
        elif current_section == "d" and "dosage" not in low_line: dosage_info.append(line)
        elif current_section == "a" and "advice" not in low_line: advice.append(line)

    # Basic fallback if structured extraction fails due to Small LLM limitations
    if not medicine_list:
        medicine_list = ["Extraction failed - verify image quality."]
    
    return {
        "medicines": medicine_list,
        "dosage": dosage_info or ["Refer to prescription image"],
        "advice": advice or ["Maintain regular health checks."]
    }

def analyze_health_report_with_ai(report_text):
    """Analyze health report text using local LLM for summary, risk, suggestions, and diet."""
    prompt = (
        f"Analyze this health report and give:\n"
        f"- Summary\n"
        f"- Risk level (Low, Moderate, High, Critical)\n"
        f"- Suggestions\n"
        f"- Diet tips\n\n"
        f"Report Text: \"{report_text}\"\n\n"
        "Format your response as a clean bulleted list with these four headers. Do not add intro or outro."
    )
    
    raw_response = query_local_llm(prompt)
    
    # Process structured response
    summary = []
    risk_level = "Unknown"
    suggestions = []
    diet_tips = []
    
    lines = raw_response.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip('- *#')
        if not line: continue
        
        low_line = line.lower()
        if "summary" in low_line: current_section = "s"
        elif "risk level" in low_line: current_section = "r"
        elif "suggestion" in low_line: current_section = "su"
        elif "diet" in low_line: current_section = "d"
        
        if current_section == "s" and "summary" not in low_line: summary.append(line)
        elif current_section == "r" and "risk level" not in low_line: risk_level = line
        elif current_section == "su" and "suggestion" not in low_line: suggestions.append(line)
        elif current_section == "d" and "diet" not in low_line: diet_tips.append(line)

    return {
        "summary": " ".join(summary) if summary else "No summary available.",
        "risk_level": risk_level if risk_level != "Unknown" else "Moderate (AI could not determine)",
        "suggestions": suggestions or ["Consult a doctor for a detailed review."],
        "diet_tips": diet_tips or ["Follow a balanced diet based on your health conditions."]
    }

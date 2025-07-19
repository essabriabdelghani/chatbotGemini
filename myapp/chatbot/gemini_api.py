
import google.generativeai as genai
from django.conf import settings
import os

# Configurez votre clé API (à mettre dans settings.py ou variables d'environnement)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', getattr(settings, 'GEMINI_API_KEY', ''))

# Initialisation de l'API
genai.configure(api_key=GEMINI_API_KEY)

# Modèle configuré pour le chat
model = genai.GenerativeModel('gemini-pro')
chat = model.start_chat(history=[])


def query_gemini(prompt):
    """Envoie une requête à l'API Gemini et retourne la réponse"""
    try:
        response = chat.send_message(prompt)
        return response.text
    except Exception as e:
        return f"Erreur API Gemini: {str(e)}"


def speak(text):
    """Synthèse vocale (optionnelle)"""
    try:
        # Utilisation de gTTS ou autre librairie
        from gtts import gTTS
        import playsound
        import tempfile

        tts = gTTS(text=text, lang='fr')
        with tempfile.NamedTemporaryFile(delete=True) as fp:
            tts.save(f"{fp.name}.mp3")
            playsound.playsound(f"{fp.name}.mp3")
    except ImportError:
        print("Fonction vocale désactivée (librairies manquantes)")
    except Exception as e:
        print(f"Erreur vocale: {str(e)}")
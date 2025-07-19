from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import InscriptionForm, ConnexionForm
from django.contrib.auth import authenticate, login
import threading
import tkinter as tk
from tkinter import scrolledtext, simpledialog, filedialog
import requests
from datetime import datetime
import pyttsx3
import speech_recognition as sr
import sounddevice as sd
import os
import numpy as np

# Configuration globale du chatbot
API_KEY = "AIzaSyDw0pmHmM79DKsRqRSTpcln_5bP2ylXc3s"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"


def run_chatbot():
    """Fonction principale pour lancer l'interface Tkinter"""
    # Initialisation moteur vocal
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    for voice in voices:
        if "female" in voice.name.lower() or "zira" in voice.name.lower():
            engine.setProperty('voice', voice.id)
            break
    engine.setProperty('rate', 140)
    voice_enabled = [True]  # Liste pour passer par référence

    # Variables globales pour les widgets Tkinter
    global chat_area, entry, voice_btn

    def speak(text):
        if voice_enabled[0]:
            engine.say(text)
            engine.runAndWait()

    def chatbot(prompt):
        headers = {"Content-Type": "application/json"}
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            response = requests.post(GEMINI_URL, headers=headers, json=data)
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            return f"Erreur API: {response.status_code}"
        except Exception as e:
            return f"Erreur de connexion: {str(e)}"

    def save_history(timestamp, sender, message):
        with open("historique.txt", "a", encoding="utf-8") as f:
            f.write(f"{timestamp} {sender}: {message}\n")

    def display_message(msg, sender="bot", timestamp=""):
        chat_area.config(state=tk.NORMAL)
        style = "bot_style" if sender == "bot" else "user_style"
        chat_area.insert(tk.END, f"{timestamp}\n", style)
        chat_area.insert(tk.END, f"{msg}\n\n", style)
        chat_area.config(state=tk.DISABLED)
        chat_area.yview(tk.END)
        if sender == "bot":
            speak(msg)

    def send_message(event=None):
        user_input = entry.get()
        if not user_input.strip():
            return

        now = datetime.now().strftime("[%H:%M]")
        display_message(user_input, "user", now)
        save_history(now, "Vous", user_input)
        entry.delete(0, tk.END)

        # Obtenir la réponse du chatbot
        bot_response = chatbot(user_input)
        now = datetime.now().strftime("[%H:%M]")
        display_message(bot_response, "bot", now)
        save_history(now, "Bot", bot_response)

    def toggle_voice():
        voice_enabled[0] = not voice_enabled[0]
        voice_btn.config(text="🔊 Voix: ON" if voice_enabled[0] else "🔇 Voix: OFF")

    def listen_micro():
        recognizer = sr.Recognizer()
        fs = 44100
        duration = 3  # secondes

        try:
            chat_area.config(state=tk.NORMAL)
            chat_area.insert(tk.END, "\n🎙️ Enregistrement en cours...\n", "info")
            chat_area.config(state=tk.DISABLED)
            chat_area.yview(tk.END)

            recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
            sd.wait()
            audio = sr.AudioData(recording.tobytes(), fs, 2)

            text = recognizer.recognize_google(audio, language="fr-FR")
            send_message(text)
        except sr.UnknownValueError:
            display_message("❌ Je n'ai pas compris...", "bot")
        except Exception as e:
            display_message(f"❌ Erreur: {str(e)}", "bot")

    def nouveau_chat():
        chat_area.config(state=tk.NORMAL)
        chat_area.delete(1.0, tk.END)
        chat_area.insert(tk.END, "💬 Nouveau chat démarré...\n", "info")
        chat_area.config(state=tk.DISABLED)
        entry.delete(0, tk.END)
        if os.path.exists("historique.txt"):
            os.remove("historique.txt")

    def recherche_chat():
        mot = simpledialog.askstring("Recherche", "Entrer un mot-clé:")
        if not mot:
            return

        if not os.path.exists("historique.txt"):
            display_message("❌ Aucun historique trouvé.", "bot")
            return

        with open("historique.txt", "r", encoding="utf-8") as f:
            lignes = f.readlines()
            resultats = [l.strip() for l in lignes if mot.lower() in l.lower()]

            if resultats:
                display_message("🔍 Résultats:", "bot")
                for res in resultats:
                    chat_area.config(state=tk.NORMAL)
                    chat_area.insert(tk.END, f"{res}\n", "search")
                    chat_area.config(state=tk.DISABLED)
            else:
                display_message("🕵️ Aucun résultat trouvé.", "bot")

    def upload_image():
        filepath = filedialog.askopenfilename(
            title="Choisir une image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if filepath:
            now = datetime.now().strftime("[%H:%M]")
            display_message(f"🖼️ Image: {os.path.basename(filepath)}", "user", now)
            save_history(now, "Image", filepath)

    # Création de la fenêtre principale
    window = tk.Tk()
    window.title("Chatbot Gemini - Style ChatGPT")
    window.geometry("800x700")
    window.configure(bg="#f0f0f0")

    # Zone de chat
    chat_area = scrolledtext.ScrolledText(
        window,
        wrap=tk.WORD,
        state=tk.DISABLED,
        font=("Arial", 12),
        bg="white",
        padx=10,
        pady=10
    )
    chat_area.pack(padx=15, pady=15, fill=tk.BOTH, expand=True)

    # Configuration des styles de texte
    chat_area.tag_config("bot_style",
                         background="#e8f0fe",
                         foreground="#202124",
                         lmargin1=10,
                         lmargin2=10,
                         rmargin=50,
                         justify="left",
                         spacing3=5)

    chat_area.tag_config("user_style",
                         background="#d1e7dd",
                         foreground="#202124",
                         lmargin1=50,
                         lmargin2=10,
                         rmargin=10,
                         justify="right",
                         spacing3=5)

    chat_area.tag_config("search",
                         background="#fff3cd",
                         foreground="#000000")

    chat_area.tag_config("info",
                         foreground="#777",
                         font=("Arial", 10, "italic"))

    # Frame pour l'entrée et les boutons
    entry_frame = tk.Frame(window, bg="#f0f0f0")
    entry_frame.pack(fill=tk.X, padx=15, pady=10)

    # Champ de saisie
    entry = tk.Entry(entry_frame, font=("Arial", 12))
    entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
    entry.bind("<Return>", send_message)

    # Bouton Envoyer
    send_btn = tk.Button(entry_frame, text="➤", command=send_message,
                         bg="#4CAF50", fg="white", font=("Arial", 12), padx=10)
    send_btn.pack(side=tk.RIGHT)

    # Bouton Micro
    micro_btn = tk.Button(entry_frame, text="🎙️", command=listen_micro,
                          bg="#9C27B0", fg="white", font=("Arial", 12), padx=10)
    micro_btn.pack(side=tk.RIGHT, padx=(0, 10))

    # Frame pour les boutons secondaires
    button_frame = tk.Frame(window, bg="#f0f0f0")
    button_frame.pack(pady=10)

    # Bouton Voix
    voice_btn = tk.Button(button_frame, text="🔊 Voix: ON", command=toggle_voice,
                          bg="#2196F3", fg="white", font=("Arial", 11), padx=10)
    voice_btn.pack(side=tk.LEFT, padx=7)

    # Bouton Nouveau Chat
    newchat_btn = tk.Button(button_frame, text="🆕 Nouveau Chat", command=nouveau_chat,
                            bg="#607D8B", fg="white", font=("Arial", 11), padx=10)
    newchat_btn.pack(side=tk.LEFT, padx=7)

    # Bouton Recherche
    search_btn = tk.Button(button_frame, text="🔍 Rechercher", command=recherche_chat,
                           bg="#FFC107", fg="black", font=("Arial", 11), padx=10)
    search_btn.pack(side=tk.LEFT, padx=7)

    # Bouton Charger Image
    upload_btn = tk.Button(button_frame, text="📁 Charger Image", command=upload_image,
                           bg="#795548", fg="white", font=("Arial", 11), padx=10)
    upload_btn.pack(side=tk.LEFT, padx=7)

    # Message de bienvenue
    display_message("Bonjour ! Je suis votre assistant Gemini. Comment puis-je vous aider ?", "bot")

    # Lancement de la boucle principale
    window.mainloop()


def inscription(request):
    if request.method == 'POST':
        form = InscriptionForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            if User.objects.filter(email=email).exists():
                messages.error(request, "Cet email est déjà utilisé.")
                return render(request, 'myapp/inscription.html', {'form': form})

            User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            messages.success(request, "Inscription réussie ! Connectez-vous maintenant.")
            return redirect('connexion')
    else:
        form = InscriptionForm()
    return render(request, 'myapp/inscription.html', {'form': form})


def connexion(request):
    form = ConnexionForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']

        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)

            if user is not None:
                login(request, user)
                # Lancement du chatbot dans un thread séparé
                threading.Thread(target=run_chatbot, daemon=True).start()
                return render(request, 'myapp/chatbot_redirect.html')
            else:
                messages.error(request, "Mot de passe incorrect")
        except User.DoesNotExist:
            messages.error(request, "Email non enregistré. Voulez-vous vous inscrire ?")
            return redirect('inscription')

    return render(request, 'myapp/connexion.html', {'form': form})

def launch_chatbot(request):
    if not request.user.is_authenticated:
        return redirect('connexion')
    threading.Thread(target=run_chatbot, daemon=True).start()
    return render(request, 'myapp/chatbot_redirect.html')
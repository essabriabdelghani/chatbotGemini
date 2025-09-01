from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import InscriptionForm, ConnexionForm
from django.contrib.auth import authenticate, login
import threading
import tkinter as tk
from tkinter import scrolledtext, simpledialog, filedialog, messagebox, ttk
import requests
from datetime import datetime
import pyttsx3
import speech_recognition as sr
import sounddevice as sd
import os, pyperclip
import json
import threading
from tkhtmlview import HTMLLabel

# Configuration globale du chatbot
API_KEY = "AIzaSyDw0pmHmM79DKsRqRSTpcln_5bP2ylXc3s"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"


def run_chatbot():
    """Fonction principale pour lancer l'interface Tkinter"""
    # Initialisation moteur vocal
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    for voice in voices:
        if "female" in voice.name.lower() or "zira" in voice.name.lower() or "french" in voice.name.lower():
            engine.setProperty('voice', voice.id)
            break
    engine.setProperty('rate', 140)
    voice_enabled = [True]  # Liste pour passer par référence

    # Variables globales pour les widgets Tkinter
    global chat_area, entry, voice_btn, window, chats_listbox, current_chat_id

    # Gestion des chats multiples
    chats = {}
    current_chat_id = "chat_1"
    chats[current_chat_id] = {"history": [], "title": "Chat 1"}

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

    def save_history(chat_id, timestamp, sender, message):
        filename = f"historique_{chat_id}.txt"
        with open(filename, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} {sender}: {message}\n")

    def load_chat_history(chat_id):
        filename = f"historique_{chat_id}.txt"
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def display_message(msg, sender="bot", timestamp=""):
        if sender == "bot":
            # Convertir la réponse texte en pseudo-HTML
            html_msg = msg.replace("\n", "<br>")  # retour à la ligne
            html_msg = html_msg.replace("**", "<b>")  # gras Markdown simple
            html_msg = html_msg.replace("1.", "<br><b>1.</b>")  # numéros stylés
            html_msg = html_msg.replace("2.", "<br><b>2.</b>")
            html_msg = html_msg.replace("3.", "<br><b>3.</b>")

            # Créer un label HTML
            html_label = HTMLLabel(chat_area, html=html_msg, background="white")
            chat_area.window_create(tk.END, window=html_label)
            chat_area.insert(tk.END, "\n\n")
            chat_area.yview(tk.END)
        else:
            chat_area.config(state=tk.NORMAL)
            chat_area.insert(tk.END, f"{timestamp} Vous: {msg}\n\n", "user_style")
            chat_area.config(state=tk.DISABLED)
            chat_area.yview(tk.END)

    def show_code_window(code_text):
        """Bloc de code stylé façon ChatGPT avec boutons Copier et Modifier en haut à droite"""
        code_win = tk.Toplevel(window)
        code_win.title("Bloc de code")
        code_win.geometry("600x400")
        code_win.configure(bg="#1e1e1e")  # Fond sombre

        # Zone texte
        text_area = scrolledtext.ScrolledText(
            code_win, wrap=tk.WORD,
            font=("Consolas", 11),
            bg="#1e1e1e", fg="#ffffff", insertbackground="white",
            relief=tk.FLAT, bd=0
        )
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=(50, 10))
        text_area.insert(tk.END, code_text)
        text_area.config(state=tk.DISABLED)

        editing = {"value": False}

        # Cadre pour les boutons en haut à droite
        btn_frame = tk.Frame(code_win, bg="#1e1e1e")
        btn_frame.place(relx=1.0, y=10, anchor="ne")

        # Fonction hover
        def on_enter(e):
            e.widget['bg'] = '#1976D2'  # bleu foncé hover

        def on_leave(e):
            e.widget['bg'] = '#2196F3'  # bleu normal

        def on_enter_edit(e):
            e.widget['bg'] = '#388E3C'  # vert foncé hover

        def on_leave_edit(e):
            e.widget['bg'] = '#4CAF50'  # vert normal

        # Copier
        def copy_code():
            try:
                code_text = text_area.get("1.0", tk.END).strip()
                if code_text:
                    pyperclip.copy(code_text)
                    messagebox.showinfo("Copie", "✅ Code copié dans le presse-papier !")
                else:
                    messagebox.showwarning("Copie", "Le bloc de code est vide !")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de copier : {e}")

        # Modifier
        def toggle_edit():
            if not editing["value"]:
                text_area.config(state=tk.NORMAL)
                edit_btn.config(text="💾 Sauvegarder")
                editing["value"] = True
            else:
                text_area.config(state=tk.DISABLED)
                edit_btn.config(text="✏️ Modifier")
                editing["value"] = False

        copy_btn = tk.Button(btn_frame, text="📋 Copier", command=copy_code,
                             bg="#2196F3", fg="white", font=("Arial", 10, "bold"),
                             padx=12, pady=5, relief=tk.FLAT, bd=0)
        copy_btn.pack(side=tk.RIGHT, padx=5)
        copy_btn.bind("<Enter>", on_enter)
        copy_btn.bind("<Leave>", on_leave)

        edit_btn = tk.Button(btn_frame, text="✏️ Modifier", command=toggle_edit,
                             bg="#4CAF50", fg="white", font=("Arial", 10, "bold"),
                             padx=12, pady=5, relief=tk.FLAT, bd=0)
        edit_btn.pack(side=tk.RIGHT, padx=5)
        edit_btn.bind("<Enter>", on_enter_edit)
        edit_btn.bind("<Leave>", on_leave_edit)

        # Ombre légère (simulateur via Frame)
        shadow_frame = tk.Frame(code_win, bg="#121212")
        shadow_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        shadow_frame.lower(text_area)

    def display_message(msg, sender="bot", timestamp=""):
        chat_area.config(state=tk.NORMAL)
        style = "bot_style" if sender == "bot" else "user_style"
        chat_area.insert(tk.END, f"{timestamp}\n", style)
        chat_area.insert(tk.END, f"{msg}\n\n", style)
        chat_area.config(state=tk.DISABLED)
        chat_area.yview(tk.END)

        # Vérifie si la réponse contient du code (``` ... ```)
        if sender == "bot" and "```" in msg:
            parts = msg.split("```")
            for i in range(1, len(parts), 2):
                if i < len(parts):
                    code_block = parts[i].strip()
                    if code_block:  # Éviter les blocs vides
                        show_code_window(code_block)

        if sender == "bot":
            speak(msg)

    def send_message(event=None, text=None):
        user_input = text if text else entry.get()
        if not user_input.strip():
            return

        entry.delete(0, tk.END)
        entry.config(state=tk.DISABLED)
        send_btn.config(state=tk.DISABLED)

        now = datetime.now().strftime("[%H:%M]")
        display_message(user_input, "user", now)
        save_history(current_chat_id, now, "Vous", user_input)

        # Ajouter à l'historique du chat actuel
        chats[current_chat_id]["history"].append({"sender": "user", "message": user_input, "time": now})

        # Utiliser un thread pour ne pas bloquer l'interface
        threading.Thread(target=get_bot_response, args=(user_input,)).start()

    def get_bot_response(user_input):
        try:
            bot_response = chatbot(user_input)
            now = datetime.now().strftime("[%H:%M]")
            # Utiliser after pour mettre à jour l'interface depuis le thread principal
            window.after(0, lambda: display_message(bot_response, "bot", now))
            window.after(0, lambda: save_history(current_chat_id, now, "Bot", bot_response))

            # Ajouter à l'historique du chat actuel
            chats[current_chat_id]["history"].append({"sender": "bot", "message": bot_response, "time": now})

        except Exception as e:
            error_msg = f"Erreur: {str(e)}"
            window.after(0, lambda: display_message(error_msg, "bot"))
        finally:
            window.after(0, lambda: entry.config(state=tk.NORMAL))
            window.after(0, lambda: send_btn.config(state=tk.NORMAL))
            window.after(0, lambda: entry.focus())

    def toggle_voice():
        voice_enabled[0] = not voice_enabled[0]
        voice_btn.config(text="🔊 Voix: ON" if voice_enabled[0] else "🔇 Voix: OFF")

    def listen_micro():
        recognizer = sr.Recognizer()
        fs = 44100
        duration = 5  # Augmenté à 5 secondes
        try:
            chat_area.config(state=tk.NORMAL)
            chat_area.insert(tk.END, "\n🎙️ Enregistrement en cours... Parlez maintenant\n", "info")
            chat_area.config(state=tk.DISABLED)
            chat_area.yview(tk.END)
            window.update()

            recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
            sd.wait()
            audio = sr.AudioData(recording.tobytes(), fs, 2)
            text = recognizer.recognize_google(audio, language="fr-FR")
            send_message(text=text)
        except sr.UnknownValueError:
            display_message("❌ Je n'ai pas compris...", "bot")
        except Exception as e:
            display_message(f"❌ Erreur: {str(e)}", "bot")

    def nouveau_chat():
        global current_chat_id

        # Créer un nouveau chat
        chat_count = len(chats) + 1
        new_chat_id = f"chat_{chat_count}"
        new_chat_title = f"Chat {chat_count}"

        chats[new_chat_id] = {"history": [], "title": new_chat_title}

        # Mettre à jour la liste des chats
        update_chats_list()

        # Basculer vers le nouveau chat
        switch_chat(new_chat_id)

        chat_area.config(state=tk.NORMAL)
        chat_area.delete(1.0, tk.END)
        chat_area.insert(tk.END, f"💬 {new_chat_title} démarré...\n", "info")
        chat_area.config(state=tk.DISABLED)
        entry.delete(0, tk.END)

    def switch_chat(chat_id):
        global current_chat_id

        if chat_id == current_chat_id:
            return

        current_chat_id = chat_id

        # Mettre à jour l'affichage
        chat_area.config(state=tk.NORMAL)
        chat_area.delete(1.0, tk.END)

        # Charger l'historique du chat sélectionné
        for message in chats[chat_id]["history"]:
            display_message(message["message"], message["sender"], message["time"])

        chat_area.config(state=tk.DISABLED)

        # Mettre à jour la sélection dans la liste
        for i, chat_item in enumerate(chats_listbox.get(0, tk.END)):
            if chat_item.startswith(chats[chat_id]["title"]):
                chats_listbox.selection_clear(0, tk.END)
                chats_listbox.select_set(i)
                break

    def update_chats_list():
        chats_listbox.delete(0, tk.END)
        for chat_id, chat_data in chats.items():
            chats_listbox.insert(tk.END, chat_data["title"])

        # Sélectionner le chat actuel
        for i, chat_item in enumerate(chats_listbox.get(0, tk.END)):
            if chat_item.startswith(chats[current_chat_id]["title"]):
                chats_listbox.selection_clear(0, tk.END)
                chats_listbox.select_set(i)
                break

    def on_chat_select(event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            chat_title = event.widget.get(index)

            # Trouver l'ID du chat correspondant
            for chat_id, chat_data in chats.items():
                if chat_data["title"] == chat_title:
                    switch_chat(chat_id)
                    break

    def recherche_chat():
        mot = simpledialog.askstring("Recherche", "Entrer un mot-clé:")
        if not mot:
            return

        results = []
        for chat_id, chat_data in chats.items():
            for message in chat_data["history"]:
                if mot.lower() in message["message"].lower():
                    results.append(f"{chat_data['title']} - {message['time']}: {message['message']}")

        if results:
            display_message("🔍 Résultats:", "bot")
            for res in results:
                chat_area.config(state=tk.NORMAL)
                chat_area.insert(tk.END, f"{res}\n", "search")
                chat_area.config(state=tk.DISABLED)
        else:
            display_message("🕵️ Aucun résultat trouvé.", "bot")

    def upload_image():
        filepath = filedialog.askopenfilename(title="Choisir une image",
                                              filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.bmp")])
        if filepath:
            now = datetime.now().strftime("[%H:%M]")
            display_message(f"🖼️ Image: {os.path.basename(filepath)}", "user", now)
            save_history(current_chat_id, now, "Image", filepath)

            # Ajouter à l'historique du chat actuel
            chats[current_chat_id]["history"].append(
                {"sender": "user", "message": f"Image: {os.path.basename(filepath)}", "time": now})

            # Nouvelle fonctionnalité : analyse d'image avec Gemini
            try:
                with open(filepath, "rb") as img_file:
                    img_data = img_file.read()
                # Ici vous devriez implémenter l'appel API pour l'analyse d'image
                display_message("📸 Fonctionnalité d'analyse d'image bientôt disponible!", "bot")
            except Exception as e:
                display_message(f"❌ Erreur lors du chargement de l'image: {str(e)}", "bot")

    def exporter_chat():
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Fichier texte", "*.txt"), ("Tous les fichiers", "*.*")]
        )
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(chat_area.get("1.0", tk.END))
                display_message(f"💾 Chat exporté vers: {filepath}", "bot")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible d'exporter: {str(e)}")

    def apropos():
        messagebox.showinfo("À propos",
                            "Chatbot Gemini\n\n"
                            "Version: 2.0\n"
                            "Avec reconnaissance vocale et synthèse\n"
                            "API Google Gemini\n\n"
                            "Développé avec Python et Tkinter")

    # === Interface ===
    window = tk.Tk()
    window.title("Chatbot Gemini - Style ChatGPT")
    window.geometry("1000x700")
    window.configure(bg="#f0f0f0")

    # Centrer la fenêtre
    window.eval('tk::PlaceWindow . center')

    main_frame = tk.Frame(window, bg="#f0f0f0")
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Frame pour la sidebar et la liste des chats
    left_frame = tk.Frame(main_frame, bg="#2c3e50", width=200)
    left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10), pady=5)
    left_frame.pack_propagate(False)

    # Titre sidebar
    title_label = tk.Label(left_frame, text="Gemini Chat", bg="#2c3e50", fg="white",
                           font=("Arial", 14, "bold"))
    title_label.pack(pady=20)

    # Liste des chats
    chats_frame = tk.Frame(left_frame, bg="#2c3e50")
    chats_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    chats_label = tk.Label(chats_frame, text="Chats", bg="#2c3e50", fg="white",
                           font=("Arial", 12, "bold"))
    chats_label.pack(anchor="w", pady=(0, 5))

    # Liste déroulante des chats
    chats_listbox = tk.Listbox(chats_frame, bg="#34495e", fg="white",
                               selectbackground="#3498db", font=("Arial", 10),
                               relief=tk.FLAT, bd=0, highlightthickness=0)
    chats_listbox.pack(fill=tk.BOTH, expand=True)
    chats_listbox.bind('<<ListboxSelect>>', on_chat_select)

    # Ajouter une barre de défilement pour la liste des chats
    scrollbar = tk.Scrollbar(chats_listbox)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    chats_listbox.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=chats_listbox.yview)

    # Boutons dans la sidebar
    buttons_frame = tk.Frame(left_frame, bg="#2c3e50")
    buttons_frame.pack(fill=tk.X, padx=10, pady=10)

    voice_btn = tk.Button(buttons_frame, text="🔊 Voix: ON", command=toggle_voice,
                          bg="#3498db", fg="white", font=("Arial", 11),
                          padx=10, pady=8, relief=tk.FLAT, width=15)
    voice_btn.pack(fill=tk.X, pady=5)

    newchat_btn = tk.Button(buttons_frame, text="🆕 Nouveau Chat", command=nouveau_chat,
                            bg="#2ecc71", fg="white", font=("Arial", 11),
                            padx=10, pady=8, relief=tk.FLAT, width=15)
    newchat_btn.pack(fill=tk.X, pady=5)

    search_btn = tk.Button(buttons_frame, text="🔍 Rechercher", command=recherche_chat,
                           bg="#f39c12", fg="white", font=("Arial", 11),
                           padx=10, pady=8, relief=tk.FLAT, width=15)
    search_btn.pack(fill=tk.X, pady=5)

    upload_btn = tk.Button(buttons_frame, text="📁 Charger Image", command=upload_image,
                           bg="#9b59b6", fg="white", font=("Arial", 11),
                           padx=10, pady=8, relief=tk.FLAT, width=15)
    upload_btn.pack(fill=tk.X, pady=5)

    export_btn = tk.Button(buttons_frame, text="💾 Exporter Chat", command=exporter_chat,
                           bg="#1abc9c", fg="white", font=("Arial", 11),
                           padx=10, pady=8, relief=tk.FLAT, width=15)
    export_btn.pack(fill=tk.X, pady=5)

    about_btn = tk.Button(buttons_frame, text="ℹ️ À propos", command=apropos,
                          bg="#7f8c8d", fg="white", font=("Arial", 11),
                          padx=10, pady=8, relief=tk.FLAT, width=15)
    about_btn.pack(fill=tk.X, pady=5)

    content_frame = tk.Frame(main_frame, bg="#f0f0f0")
    content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    chat_area = scrolledtext.ScrolledText(content_frame, wrap=tk.WORD, state=tk.DISABLED,
                                          font=("Arial", 12), bg="white", padx=15, pady=15)
    chat_area.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

    chat_area.tag_config("bot_style", background="#e8f0fe", foreground="#202124",
                         lmargin1=10, lmargin2=10, rmargin=50, justify="left", spacing3=5)
    chat_area.tag_config("user_style", background="#d1e7dd", foreground="#202124",
                         lmargin1=50, lmargin2=10, rmargin=10, justify="right", spacing3=5)
    chat_area.tag_config("search", background="#fff3cd", foreground="#000000")
    chat_area.tag_config("info", foreground="#777", font=("Arial", 10, "italic"))

    entry_frame = tk.Frame(content_frame, bg="#f0f0f0")
    entry_frame.pack(fill=tk.X, padx=5, pady=10)

    entry = tk.Entry(entry_frame, font=("Arial", 12))
    entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
    entry.bind("<Return>", send_message)

    micro_btn = tk.Button(entry_frame, text="🎙️", command=listen_micro,
                          bg="#9C27B0", fg="white", font=("Arial", 12),
                          padx=12, pady=5, relief=tk.FLAT)
    micro_btn.pack(side=tk.RIGHT, padx=(0, 5))

    send_btn = tk.Button(entry_frame, text="Envoyer", command=send_message,
                         bg="#4CAF50", fg="white", font=("Arial", 12, "bold"),
                         padx=15, pady=5, relief=tk.FLAT)
    send_btn.pack(side=tk.RIGHT)

    # Focus sur l'entrée au démarrage
    entry.focus()

    # Initialiser la liste des chats
    update_chats_list()

    display_message("Bonjour ! Je suis votre assistant Gemini. Comment puis-je vous aider ?", "bot")

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
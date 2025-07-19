import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog, simpledialog
import os
from datetime import datetime
import sounddevice as sd
import speech_recognition as sr
from .gemini_api import query_gemini, speak  # Assurez-vous que ce module est correctement importé


class ChatbotApp:
    def __init__(self, master):
        self.master = master
        self.voice_enabled = True
        self.setup_ui()
        self.setup_menu()

    def setup_ui(self):
        self.master.title("Chatbot Gemini - Style ChatGPT")
        self.master.geometry("600x700")
        self.master.configure(bg="#f0f0f0")

        # Zone de chat
        self.chat_area = scrolledtext.ScrolledText(
            self.master,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Arial", 12),
            bg="white",
            padx=10,
            pady=10
        )
        self.chat_area.pack(padx=15, pady=15, fill=tk.BOTH, expand=True)

        # Configuration des styles de message
        self.chat_area.tag_config("bot_style", background="#e8f0fe", foreground="#202124",
                                  lmargin1=10, lmargin2=10, rmargin=50, justify="left", spacing3=5, font=("Arial", 12))
        self.chat_area.tag_config("user_style", background="#d1e7dd", foreground="#202124",
                                  lmargin1=50, lmargin2=10, rmargin=10, justify="right", spacing3=5, font=("Arial", 12))
        self.chat_area.tag_config("search", background="#fff3cd", foreground="#000000",
                                  lmargin1=10, lmargin2=10, rmargin=10)
        self.chat_area.tag_config("info", foreground="#777", font=("Arial", 10, "italic"))

        # Frame pour l'entrée de texte
        entry_frame = tk.Frame(self.master, bg="#f0f0f0")
        entry_frame.pack(fill=tk.X, padx=15, pady=10)

        self.entry = tk.Entry(entry_frame, font=("Arial", 12))
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), pady=5)
        self.entry.bind("<Return>", lambda event: self.send_message())

        # Bouton d'envoi
        send_btn = tk.Button(entry_frame, text="➤", command=self.send_message,
                             bg="#4CAF50", fg="white", font=("Arial", 12), padx=10, pady=5)
        send_btn.pack(side=tk.RIGHT)

        # Bouton micro
        micro_btn = tk.Button(entry_frame, text="🎙️", command=self.listen_micro,
                              bg="#9C27B0", fg="white", font=("Arial", 12), padx=10, pady=5)
        micro_btn.pack(side=tk.RIGHT, padx=(0, 10))

        # Frame pour les boutons optionnels
        button_frame = tk.Frame(self.master, bg="#f0f0f0")
        button_frame.pack(pady=10)

        # Bouton voix
        self.voice_btn = tk.Button(button_frame, text="🔊 Voix : ON", command=self.toggle_voice,
                                   bg="#2196F3", fg="white", font=("Arial", 11), padx=10, pady=5)
        self.voice_btn.pack(side=tk.LEFT, padx=7)

        # Bouton nouveau chat
        newchat_btn = tk.Button(button_frame, text="🆕 Nouveau Chat", command=self.nouveau_chat,
                                bg="#607D8B", fg="white", font=("Arial", 11), padx=10, pady=5)
        newchat_btn.pack(side=tk.LEFT, padx=7)

        # Bouton recherche
        search_btn = tk.Button(button_frame, text="🔍 Rechercher", command=self.recherche_chat,
                               bg="#FFC107", fg="black", font=("Arial", 11), padx=10, pady=5)
        search_btn.pack(side=tk.LEFT, padx=7)

        # Bouton upload image
        upload_btn = tk.Button(button_frame, text="📁 Charger Image", command=self.upload_image,
                               bg="#795548", fg="white", font=("Arial", 11), padx=10, pady=5)
        upload_btn.pack(side=tk.LEFT, padx=7)

    def setup_menu(self):
        menubar = tk.Menu(self.master)

        # Menu Fichier
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Nouveau Chat", command=self.nouveau_chat)
        file_menu.add_command(label="Rechercher", command=self.recherche_chat)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.master.quit)
        menubar.add_cascade(label="Fichier", menu=file_menu)

        # Menu Options
        options_menu = tk.Menu(menubar, tearoff=0)
        options_menu.add_command(label="Activer/Désactiver Voix", command=self.toggle_voice)
        menubar.add_cascade(label="Options", menu=options_menu)

        self.master.config(menu=menubar)

    def display_message(self, msg, sender="bot", timestamp=""):
        self.chat_area.config(state=tk.NORMAL)
        style = "bot_style" if sender == "bot" else "user_style"
        if timestamp:
            self.chat_area.insert(tk.END, f"{timestamp}\n", style)
        self.chat_area.insert(tk.END, f"{msg}\n\n", style)
        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.yview(tk.END)

    def send_message(self, text=None):
        user_input = text if text else self.entry.get()
        if not user_input.strip():
            return

        now = datetime.now().strftime("[%H:%M]")
        self.display_message(user_input, sender="user", timestamp=now)
        self.save_history(now, "Vous", user_input)
        self.entry.delete(0, tk.END)

        try:
            bot_response = query_gemini(user_input)
            now = datetime.now().strftime("[%H:%M]")
            self.display_message(bot_response, sender="bot", timestamp=now)
            self.save_history(now, "Bot", bot_response)

            if self.voice_enabled:
                speak(bot_response)
        except Exception as e:
            error_msg = f"Erreur lors de la requête: {str(e)}"
            self.display_message(error_msg, sender="bot")
            print(f"Erreur: {error_msg}")

    def toggle_voice(self):
        self.voice_enabled = not self.voice_enabled
        self.voice_btn.config(text="🔊 Voix : ON" if self.voice_enabled else "🔇 Voix : OFF")

    def listen_micro(self):
        recognizer = sr.Recognizer()
        fs = 44100
        duration = 3  # secondes

        try:
            self.display_message("🎙️ Enregistrement en cours...", sender="bot")

            with sd.InputStream(samplerate=fs, channels=1, dtype='int16') as stream:
                audio_data, _ = stream.read(int(duration * fs))
                audio = sr.AudioData(audio_data.tobytes(), fs, 2)

                text = recognizer.recognize_google(audio, language="fr-FR")
                self.send_message(text)

        except sr.UnknownValueError:
            self.display_message("❌ Je n'ai pas compris...", sender="bot")
        except sr.RequestError as e:
            self.display_message(f"🔌 Erreur API Google : {e}", sender="bot")
        except Exception as e:
            self.display_message(f"❌ Erreur inattendue : {str(e)}", sender="bot")

    def nouveau_chat(self):
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.delete(1.0, tk.END)
        self.display_message("💬 Nouveau chat démarré...", sender="bot")
        self.entry.delete(0, tk.END)
        try:
            with open("historique.txt", "w", encoding="utf-8") as f:
                f.write("=== Nouveau chat ===\n")
        except Exception as e:
            print(f"Erreur lors de la création du fichier historique: {str(e)}")

    def recherche_chat(self):
        mot = simpledialog.askstring("Recherche", "Entrer un mot-clé :")
        if not mot:
            return

        try:
            if not os.path.exists("historique.txt"):
                self.display_message("❌ Aucun historique trouvé.", sender="bot")
                return

            with open("historique.txt", "r", encoding="utf-8") as f:
                lignes = f.readlines()
                resultats = [l.strip() for l in lignes if mot.lower() in l.lower()]

                if not resultats:
                    self.display_message("🕵️ Aucun résultat trouvé.", sender="bot")
                    return

                self.display_message("🔍 Résultats :", sender="bot")
                self.chat_area.config(state=tk.NORMAL)
                for res in resultats:
                    self.chat_area.insert(tk.END, f"{res}\n", "search")
                self.chat_area.config(state=tk.DISABLED)

        except Exception as e:
            self.display_message(f"❌ Erreur lors de la recherche: {str(e)}", sender="bot")

    def upload_image(self):
        try:
            filepath = filedialog.askopenfilename(
                title="Choisir une image",
                filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.bmp")]
            )
            if filepath:
                now = datetime.now().strftime("[%H:%M]")
                self.display_message(f"🖼️ Image sélectionnée : {os.path.basename(filepath)}", sender="user",
                                     timestamp=now)
                self.save_history(now, "Vous (image)", filepath)
        except Exception as e:
            self.display_message(f"❌ Erreur lors du chargement de l'image: {str(e)}", sender="bot")

    def save_history(self, timestamp, sender, message):
        try:
            with open("historique.txt", "a", encoding="utf-8") as f:
                f.write(f"{timestamp} {sender}: {message}\n")
        except Exception as e:
            print(f"Erreur lors de l'écriture dans l'historique: {str(e)}")


def run():
    root = tk.Tk()
    app = ChatbotApp(root)
    root.mainloop()


if __name__ == "__main__":
    run()
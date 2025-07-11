import tkinter as tk
from tkinter import scrolledtext, ttk
import speech_recognition as sr
import pyttsx3
import datetime
import webbrowser
import threading
import requests
import json
from geopy.geocoders import Nominatim
import random
import os
import re

MEMORY_FILE = "memory.json"

class VoiceAssistant:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced RoboAssistant")
        self.root.geometry("850x670")
        self.root.configure(bg="#2c3e50")

        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', voices[1].id)

        self.recognizer = sr.Recognizer()
        self.memory = self.load_memory()

        self.weather_api_key = "140d8230fe1a9e9a701099695b677884"
        self.weather_base_url = "http://api.openweathermap.org/data/2.5/weather?"

        self.speaking = False

        self.create_ui()
        greeting = "Namaste! I'm your Advanced RoboAssistant. How can I help you today?"
        if self.memory.get("name"):
            greeting = f"Namaste {self.memory['name']}! I'm your RoboAssistant. How can I help you today?"
        self.speak_and_display(greeting)

    def create_ui(self):
        header = tk.Label(self.root, text="Advanced RoboAssistant", font=("Arial", 24, "bold"),
                          bg="#2c3e50", fg="#ecf0f1")
        header.pack(pady=10)

        self.display = scrolledtext.ScrolledText(self.root, width=95, height=25,
                                                 font=("Arial", 12), bg="#34495e", fg="#ecf0f1",
                                                 wrap=tk.WORD)
        self.display.pack(pady=10, padx=10)
        self.display.configure(state='disabled')

        input_frame = tk.Frame(self.root, bg="#2c3e50")
        input_frame.pack(pady=5)

        tk.Label(input_frame, text="You can type also:", bg="#2c3e50", fg="white", font=("Arial", 12)).pack(side=tk.LEFT)
        self.text_entry = tk.Entry(input_frame, width=50, font=("Arial", 12))
        self.text_entry.pack(side=tk.LEFT, padx=10)

        submit_btn = ttk.Button(input_frame, text="Submit", command=self.handle_text_input)
        submit_btn.pack(side=tk.LEFT, padx=5)

        store_btn = ttk.Button(input_frame, text="STORE", command=self.store_command)
        store_btn.pack(side=tk.LEFT, padx=5)

        button_frame = tk.Frame(self.root, bg="#2c3e50")
        button_frame.pack(pady=10)

        self.listen_btn = ttk.Button(button_frame, text="🎤 Speak", command=self.start_listening)
        self.listen_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(button_frame, text="⏹ Stop Speaking", command=self.stop_speaking)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        clear_btn = ttk.Button(button_frame, text="🩹 Clear", command=self.clear_screen)
        clear_btn.pack(side=tk.LEFT, padx=5)

        exit_btn = ttk.Button(button_frame, text="🚪 Exit", command=self.close_app)
        exit_btn.pack(side=tk.LEFT, padx=5)

    def load_memory(self):
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
        return {"name": "", "stored": []}

    def save_memory(self):
        with open(MEMORY_FILE, "w") as f:
            json.dump(self.memory, f)

    def speak_and_display(self, text):
        self.display.configure(state='normal')
        self.display.insert(tk.END, f"\n🤖 RoboAssistant: {text}\n")
        self.display.see(tk.END)
        self.display.configure(state='disabled')

        self.speaking = True
        self.engine.say(text)
        self.engine.runAndWait()
        self.speaking = False

    def display_only(self, text):
        self.display.configure(state='normal')
        self.display.insert(tk.END, f"\n🤖 RoboAssistant: {text}\n")
        self.display.see(tk.END)
        self.display.configure(state='disabled')

    def stop_speaking(self):
        if self.speaking:
            self.engine.stop()
            self.speaking = False
            self.speak_and_display("Stopped speaking.")

    def start_listening(self):
        self.listen_btn.config(state=tk.DISABLED)
        self.display.configure(state='normal')
        self.display.insert(tk.END, "\n🔊 Listening... (Speak now)\n")
        self.display.configure(state='disabled')
        threading.Thread(target=self.listen_for_command, daemon=True).start()

    def listen_for_command(self):
        with sr.Microphone() as source:
            try:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = self.recognizer.listen(source, timeout=4, phrase_time_limit=5)
                command = self.recognizer.recognize_google(audio).lower()
                self.display.configure(state='normal')
                self.display.insert(tk.END, f"\n👤 You: {command}\n")
                self.display.configure(state='disabled')
                self.process_command(command)
            except sr.WaitTimeoutError:
                self.speak_and_display("I didn't hear anything. Please try again.")
            except sr.UnknownValueError:
                self.speak_and_display("Sorry, I didn't understand that.")
            except Exception as e:
                self.speak_and_display(f"Error: {str(e)}")
        self.listen_btn.config(state=tk.NORMAL)

    def handle_text_input(self):
        command = self.text_entry.get().strip().lower()
        if command:
            self.display.configure(state='normal')
            self.display.insert(tk.END, f"\n👤 You: {command}\n")
            self.display.configure(state='disabled')
            self.text_entry.delete(0, tk.END)
            self.process_command(command)

    def store_command(self):
        command = self.text_entry.get().strip()
        if command:
            if "stored" not in self.memory:
                self.memory["stored"] = []
            self.memory["stored"].append(command)
            self.save_memory()
            self.text_entry.delete(0, tk.END)
            self.speak_and_display(f"Stored: '{command}'")

    def normalize_expression(self, expr):
        expr = expr.replace("into", "*")
        expr = expr.replace("multiplied by", "*")
        expr = expr.replace("x", "*")
        expr = expr.replace("divided by", "/")
        expr = expr.replace("plus", "+")
        expr = expr.replace("minus", "-")
        return expr

    def process_command(self, command):
        if any(kw in command for kw in ["hello", "hi", "namaste"]):
            self.speak_and_display("Hi! How can I assist you today?")

        elif "how are you" in command:
            self.speak_and_display("I'm doing great! Always ready to help you.")

        elif "what's up" in command or "whats up" in command:
            self.speak_and_display("Just processing your greatness! 😄")

        elif "good" in command or "nice joke" in command:
            self.speak_and_display("Glad you liked it!")

        elif "thank you" in command or "thanks" in command:
            self.speak_and_display("You're always welcome!")

        elif "bye" in command or "goodbye" in command:
            self.speak_and_display("Goodbye! Come back soon.")
            self.root.after(2000, self.close_app)

        elif "time" in command:
            now = datetime.datetime.now().strftime("%I:%M %p")
            self.speak_and_display(f"The time is {now}")

        elif "date" in command:
            today = datetime.datetime.now().strftime("%A, %d %B %Y")
            self.speak_and_display(f"Today is {today}")

        elif "calculate" in command:
            try:
                expr = command.replace("calculate", "").strip()
                expr = self.normalize_expression(expr)
                result = eval(expr)
                self.speak_and_display(f"The result is {result}")
            except:
                self.speak_and_display("Sorry, I couldn't calculate that.")

        elif "joke" in command:
            jokes = [
                "Why did the scarecrow win an award? Because he was outstanding in his field!",
                "Why don’t skeletons fight each other? They don’t have the guts!",
                "Why did the computer show up late to work? It had a hard drive!",
                "Hindi Joke: बच्चा - मम्मी मैं बड़ा होकर पायलट बनूंगा। मम्मी - तू चुप कर, रोटी खा और चुपचाप पड़ोस के बच्चे से कम मार्क्स ला!",
            ]
            self.speak_and_display(random.choice(jokes))

        elif "weather" in command:
            self.get_weather(command)

        elif "location" in command:
            self.get_location()

        elif "search" in command:
            topic = command.replace("search", "").strip()
            if topic:
                self.display_only(f"Searching for {topic}...\n(Result from web search)")
                webbrowser.open(f"https://www.google.com/search?q={topic}")

        elif "call me" in command:
            name = command.replace("call me", "").strip().title()
            if name:
                self.memory["name"] = name
                self.save_memory()
                self.speak_and_display(f"Got it! I'll call you {name} from now on.")

        elif any(kw in command for kw in ["what is my name", "what did i store", "remember anything", "recently stored"]):
            if self.memory.get("stored"):
                best_match = self.find_best_match(command)
                if best_match:
                    self.display_only(f"(Result from stored command)\n{best_match}")
                    return
            self.speak_and_display("I don't remember storing anything yet.")

        else:
            best_match = self.find_best_match(command)
            if best_match:
                self.display_only(f"Probably YOU MEANT:\n{best_match}\n(Result from stored command)")
            else:
                self.speak_and_display("Hmm... I didn't get that. Try something else.")

    def find_best_match(self, command):
        max_common_words = 0
        best_match = None
        command_words = set(command.lower().split())
        for stored in self.memory.get("stored", []):
            stored_words = set(stored.lower().split())
            common = command_words.intersection(stored_words)
            if len(common) > max_common_words:
                max_common_words = len(common)
                best_match = stored
        return best_match if max_common_words >= 3 else None

    def get_weather(self, command):
        try:
            city = command.replace("weather", "").strip() or "Delhi"
            url = f"{self.weather_base_url}appid={self.weather_api_key}&q={city}&units=metric"
            response = requests.get(url).json()
            if response.get("cod") != 200:
                self.speak_and_display("City not found.")
                return
            weather = response['weather'][0]['description']
            temp = response['main']['temp']
            self.speak_and_display(f"{city.title()} weather: {weather}, temperature is {temp}°C")
        except:
            self.speak_and_display("Sorry, I couldn't get the weather.")

    def get_location(self):
        try:
            response = requests.get("https://ipinfo.io/json").json()
            city = response.get("city", "")
            region = response.get("region", "")
            country = response.get("country", "")
            loc = response.get("loc", "")
            self.speak_and_display(f"Your approximate location: {city}, {region}, {country} (Coordinates: {loc})")
        except:
            self.speak_and_display("Location services unavailable.")

    def clear_screen(self):
        self.display.configure(state='normal')
        self.display.delete(1.0, tk.END)
        self.display.configure(state='disabled')
        self.speak_and_display("Screen cleared.")

    def close_app(self):
        self.speak_and_display("Shutting down. Goodbye!")
        self.root.after(1500, self.root.destroy)

if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceAssistant(root)
    root.mainloop()

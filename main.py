import threading
import speech_recognition as sr
from typing import List
import pyttsx3
import time
import random
import wikipedia
from email.message import EmailMessage
import smtplib

class JokeGenerator:
    def __init__(self):
        self.jokes = [
            "Why don't programmers like nature? It has too many bugs.",
            "Why don't Python programmers like to play hide and seek? Because good luck hiding when they can just import os and find you.",
            "I've heard AI is going to take over the world. Just what I need, more work."
        ]
    def get_random_joke(self) -> str:
        return random.choice(self.jokes)

class FactGenerator:
    def __init__(self):
        self.facts = [
            "The first computer mouse was made of wood!",
            "The first computer virus was created in 1983!",
            "The first computer programmer was Ada Lovelace!",
            "You're still using Python, aren't you?"
        ]
    def get_random_fact(self) -> str:
        return random.choice(self.facts)

class ReminderManager:
    def __init__(self):
        self.reminders = []
    def add_reminder(self, duration: int, message: str):
        threading.Thread(target=self.remind, args=(duration, message)).start()
    def remind(self, duration: int, message: str):
        time.sleep(duration * 60)
        print(f"Reminder: {message}")

class SpeechAssistant:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.joke_generator = JokeGenerator()
        self.fact_generator = FactGenerator()
        self.reminder_manager = ReminderManager()

    def speak(self, text: str) -> None:
        self.engine.say(text)
        self.engine.runAndWait()

    def listen(self) -> str:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("Listening...")
            try:
                audio = recognizer.listen(source)
                text = recognizer.recognize_google(audio, language='en-US')
                return text
            except sr.UnknownValueError:
                self.speak("Sorry, I didn't catch that.")
                return None
            except sr.RequestError as e:
                self.speak(f"Sorry, there was an error; {e}")
                return None

    def calculate(self, expression: str) -> str:
        try:
            math_text = expression.replace("calculate", "").strip()
            math_text = math_text.replace("plus", "+").replace("minus", "-")
            math_text = math_text.replace("times", "*").replace("divided by", "/")
            result = str(eval(math_text))
            return result
        except Exception as e:
            self.speak(f"Error: {str(e)}")
            return "Sorry, I couldn't perform that calculation."

    def search_wikipedia(self, query: str) -> str:
        try:
            result = wikipedia.summary(query, sentences=2)
            self.speak(result)
            return "Wikipedia results retrieved."
        except Exception as e:
            self.speak(f"Error: {str(e)}")
            return "Sorry, I couldn't find anything on Wikipedia."

    def set_reminder(self, duration: int, message: str) -> None:
        self.reminder_manager.add_reminder(duration, message)

    def process_command(self, text: str) -> None:
        print(f"User said: {text}")

        if any(word in text for word in ["hello", "hi", "hey", "sup", "greetings"]):
            self.speak("Hello!")
        elif "how are you" in text.lower():
            self.speak("I'm doing well, thank you for asking!")
        elif "meow" in text:
            self.speak("Are you a cat? What the sigma, I like cats.")
        elif "thanks" in text.lower():
            self.speak("You're welcome!")
        elif "goodbye" in text.lower():
            self.speak("Goodbye! Have a great day!")
            return
        elif "time" in text:
            current_time = time.strftime("%I:%M %p").lstrip("0")
            self.speak(f"The time is {current_time}")
        elif "calculate" in text:
            result = self.calculate(text)
            self.speak(result)
        elif "tell me a joke" in text.lower():
            self.speak(self.joke_generator.get_random_joke())
        elif "tell me a fact" in text.lower():
            self.speak(self.fact_generator.get_random_fact())
        elif "remind me" in text:
            try:
                parts = text.split()
                duration_idx = parts.index('in') + 1
                duration = int(parts[duration_idx].strip('minutes'))
                message_idx = parts.index('to') + 1
                message = ' '.join(parts[message_idx:])
                self.set_reminder(duration, message)
                self.speak(f"I'll remind you to {message} in {duration} minutes")
            except (ValueError, IndexError):
                self.speak("Sorry, I couldn't understand that reminder command.")
        elif "search wikipedia" in text.lower():
            query = text.split('for')[-1].strip()
            result = self.search_wikipedia(query)
        else:
            self.speak("Sorry, I didn't understand that command.")

def main() -> None:
    assistant = SpeechAssistant()

    def listen_and_process():
        while True:
            text = assistant.listen()
            if text:
                assistant.process_command(text)

    threading.Thread(target=listen_and_process).start()

if __name__ == "__main__":
    main()
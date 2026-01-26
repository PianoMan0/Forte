import argparse
import ast
import operator as op
import threading
import speech_recognition as sr
from typing import List, Optional
import pyttsx3
import time
import random
import wikipedia
import logging
import os
import sys

# Optional OpenRouter client (used for AI fallback)
try:
    from openrouter import OpenRouter
    OPENROUTER_AVAILABLE = True
except Exception:
    OpenRouter = None
    OPENROUTER_AVAILABLE = False

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
        ]

    def get_random_fact(self) -> str:
        return random.choice(self.facts)

class ReminderManager:
    def __init__(self):
        self.reminders = []  # list of tuples (timestamp, message)
        self.lock = threading.Lock()

    def add_reminder(self, duration: int, message: str):
        with self.lock:
            fire_at = time.time() + duration * 60
            self.reminders.append((fire_at, message))
        threading.Thread(target=self.remind, args=(duration, message), daemon=True).start()

    def list_reminders(self) -> List[str]:
        now = time.time()
        with self.lock:
            items = [f"in {int((fire_at-now)//60)}m: {msg}" if fire_at>now else f"due: {msg}" for fire_at, msg in self.reminders]
        return items

    def remind(self, duration: int, message: str):
        time.sleep(duration * 60)
        print(f"Reminder: {message}")

class SpeechAssistant:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.joke_generator = JokeGenerator()
        self.fact_generator = FactGenerator()
        self.reminder_manager = ReminderManager()
        self.enable_tts = True
        self.logger = logging.getLogger("Forte")
        self.openrouter_client = None
        # Initialize OpenRouter client if API key provided in env
        api_key = os.environ.get("OPENROUTER_API_KEY")
        server_url = os.environ.get("OPENROUTER_URL", "https://ai.hackclub.com/proxy/v1")
        model = os.environ.get("OPENROUTER_MODEL", "qwen/qwen3-32b")
        self._openrouter_model = model
        if api_key and OPENROUTER_AVAILABLE:
            try:
                self.openrouter_client = OpenRouter(api_key=api_key, server_url=server_url)
                self.logger.info("OpenRouter client initialized using model %s", self._openrouter_model)
            except Exception:
                self.logger.exception("Failed to initialize OpenRouter client")
                self.openrouter_client = None
        elif api_key and not OPENROUTER_AVAILABLE:
            self.logger.warning("OPENROUTER_API_KEY is set but `openrouter` package is not installed")

    def speak(self, text: str) -> None:
        if not self.enable_tts:
            self.logger.info("TTS disabled, would say: %s", text)
            return
        self.engine.say(text)
        self.engine.runAndWait()

    def listen(self) -> Optional[str]:
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
            # extract math expression
            math_text = expression.lower().replace("calculate", "").strip()
            math_text = (
                math_text.replace("plus", "+")
                .replace("minus", "-")
                .replace("times", "*")
                .replace("x", "*")
                .replace("divided by", "/")
            )

            def safe_eval(expr: str):
                # supported operators
                operators = {
                    ast.Add: op.add,
                    ast.Sub: op.sub,
                    ast.Mult: op.mul,
                    ast.Div: op.truediv,
                    ast.Pow: op.pow,
                    ast.USub: op.neg,
                }

                def _eval(node):
                    if isinstance(node, ast.Num):
                        return node.n
                    if isinstance(node, ast.BinOp):
                        return operators[type(node.op)](_eval(node.left), _eval(node.right))
                    if isinstance(node, ast.UnaryOp):
                        return operators[type(node.op)](_eval(node.operand))
                    raise ValueError("Unsupported expression")

                node = ast.parse(expr, mode="eval").body
                return _eval(node)

            result = str(safe_eval(math_text))
            return result
        except Exception as e:
            self.logger.exception("Calculation error")
            return "Sorry, I couldn't perform that calculation."

    def search_wikipedia(self, query: str) -> str:
        try:
            result = wikipedia.summary(query, sentences=2)
            self.speak(result)
            return result
        except Exception as e:
            self.logger.exception("Wikipedia search failed")
            return "Sorry, I couldn't find anything on Wikipedia."

    def ai_query(self, prompt: str) -> str:
        """Send prompt to OpenRouter and return assistant response, or an error message."""
        if not self.openrouter_client:
            return "AI not configured. Set OPENROUTER_API_KEY and install the openrouter package to enable AI responses."
        try:
            response = self.openrouter_client.chat.send(
                model=self._openrouter_model,
                messages=[{"role": "user", "content": prompt}],
                stream=False,
            )
            # Support different response shapes defensively
            try:
                return response.choices[0].message.content
            except Exception:
                # Fallback: try .choices[0].text
                try:
                    return response.choices[0].text
                except Exception:
                    return str(response)
        except Exception:
            self.logger.exception("OpenRouter query failed")
            return "Sorry, the AI request failed."

    def set_reminder(self, duration: int, message: str) -> None:
        self.reminder_manager.add_reminder(duration, message)

    def process_command(self, text: str) -> None:
        print(f"User said: {text}")

        text_lower = text.lower()

        if text_lower.strip() == "help":
            cmds = [
                "hello/hi", "how are you", "time", "calculate <expr>",
                "tell me a joke", "tell me a fact", "remind me in <n> minutes to <task>",
                "list reminders", "search wikipedia for <query>", "goodbye"
            ]
            self.speak("Available commands: " + ", ".join(cmds))
            return

        if any(word in text_lower for word in ["hello", "hi", "hey", "sup", "greetings"]):
            self.speak("Hello!")
        elif "how are you" in text_lower:
            self.speak("I'm doing well, thank you for asking!")
        elif "meow" in text_lower:
            self.speak("Are you a cat? What the sigma, I like cats.")
        elif "what is your name" in text_lower:
            self.speak("I am Forte")
        elif "who are you" in text_lower:
            self.speak("I am Forte")    
        elif "thanks" in text_lower:
            self.speak("You're welcome!")
        elif "goodbye" in text_lower:
            self.speak("Goodbye! Have a great day!")
            return
        elif "time" in text_lower:
            current_time = time.strftime("%I:%M %p").lstrip("0")
            self.speak(f"The time is {current_time}")
        elif "calculate" in text_lower:
            result = self.calculate(text)
            self.speak(result)
        elif "tell me a joke" in text_lower:
            self.speak(self.joke_generator.get_random_joke())
        elif "tell me a fact" in text_lower:
            self.speak(self.fact_generator.get_random_fact())
        elif "remind me" in text_lower:
            try:
                # Example: "remind me in 5 minutes to check the oven"
                import re
                match = re.search(r"remind me in (\d+) minute[s]? to (.+)", text_lower)
                if match:
                    duration = int(match.group(1))
                    message = match.group(2)
                    self.set_reminder(duration, message)
                    self.speak(f"I'll remind you to {message} in {duration} minutes")
                else:
                    self.speak("Sorry, I couldn't understand that reminder command.")
            except Exception:
                self.speak("Sorry, I couldn't understand that reminder command.")
        elif "list reminders" in text_lower:
            items = self.reminder_manager.list_reminders()
            if not items:
                self.speak("You have no reminders.")
            else:
                for it in items:
                    self.speak(it)
        elif "search wikipedia" in text_lower:
            # Example: "search wikipedia for Python programming"
            if "for" in text_lower:
                query = text_lower.split("for", 1)[1].strip()
            else:
                query = text_lower.replace("search wikipedia", "").strip()
            self.search_wikipedia(query)
        else:
            # Fallback: if AI configured, ask model to handle arbitrary queries
            ai_resp = self.ai_query(text)
            if ai_resp:
                self.speak(ai_resp)
            else:
                self.speak("Sorry, I didn't understand that command.")

def main() -> None:
    parser = argparse.ArgumentParser(description="Forte - a small speech assistant")
    parser.add_argument("--text", action="store_true", help="Run in text/CLI mode (no microphone listening)")
    parser.add_argument("--no-tts", action="store_true", help="Disable text-to-speech output")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    assistant = SpeechAssistant()
    if args.no_tts:
        assistant.enable_tts = False

    def listen_and_process():
        while True:
            text = assistant.listen()
            if text:
                assistant.process_command(text)

    try:
        if args.text:
            assistant.speak("Running in text mode. Type 'exit' to quit. Type 'help' for commands.")
            while True:
                text = input("> ")
                if not text:
                    continue
                if text.strip().lower() in ("exit", "quit", "goodbye"):
                    assistant.speak("Goodbye!")
                    break
                assistant.process_command(text)
        else:
            threading.Thread(target=listen_and_process, daemon=True).start()
            # Keep the main thread alive
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Exiting...")
        sys.exit(0)

if __name__ == "__main__":
    main()
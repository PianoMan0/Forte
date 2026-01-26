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
import requests
try:
    from googletrans import Translator
except Exception:
    Translator = None

# Default coordinates (user-provided)
DEFAULT_LAT = "39.6374"
DEFAULT_LON = "-75.6001"


        def convert_currency(self, amount: float, from_curr: str, to_curr: str) -> str:
            """Convert amount from one currency to another using exchangerate.host (no API key)."""
            try:
                url = "https://api.exchangerate.host/convert"
                params = {"from": from_curr.upper(), "to": to_curr.upper(), "amount": amount}
                r = requests.get(url, params=params, timeout=10)
                r.raise_for_status()
                data = r.json()
                if not data.get("success", True):
                    return "Currency conversion failed."
                result = data.get("result")
                resp = f"{amount} {from_curr.upper()} = {result:.2f} {to_curr.upper()}"
                self.speak(resp)
                return resp
            except Exception:
                self.logger.exception("Currency conversion failed")
                return "Sorry, I couldn't convert currencies right now."

        def translate_text(self, text: str, dest: str) -> str:
            """Translate `text` to language `dest` (language code like 'es' or 'fr')."""
            if Translator is None:
                self.logger.warning("googletrans not installed")
                return "Translation feature requires the 'googletrans' package. Please install it."
            try:
                translator = Translator()
                res = translator.translate(text, dest=dest)
                resp = f"Translation ({res.src} -> {res.dest}): {res.text}"
                self.speak(resp)
                return resp
            except Exception:
                self.logger.exception("Translation failed")
                return "Sorry, I couldn't translate that."

        def get_traffic(self, origin: str, destination: str) -> str:
            """Get estimated travel time in current traffic between origin and destination.
            Uses Google Maps Directions API; requires env var GOOGLE_MAPS_API_KEY."""
            api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
            if not api_key:
                return "Google Maps API key not set." 
            try:
                url = "https://maps.googleapis.com/maps/api/directions/json"
                params = {
                    "origin": origin,
                    "destination": destination,
                    "departure_time": "now",
                    "key": api_key,
                }
                r = requests.get(url, params=params, timeout=10)
                r.raise_for_status()
                data = r.json()
                if data.get("status") != "OK":
                    return f"Traffic API error: {data.get('status')}"
                route = data["routes"][0]
                leg = route["legs"][0]
                duration = leg.get("duration", {}).get("text")
                duration_in_traffic = leg.get("duration_in_traffic", {}).get("text")
                summary = route.get("summary", "")
                if duration_in_traffic:
                    resp = f"Route {summary}: estimated time in current traffic {duration_in_traffic} (normal {duration})."
                else:
                    resp = f"Route {summary}: estimated travel time {duration}."
                self.speak(resp)
                return resp
            except Exception:
                self.logger.exception("Traffic lookup failed")
                return "Sorry, I couldn't fetch traffic information."

        def set_reminder(self, duration: int, message: str) -> None:
            self.reminder_manager.add_reminder(duration, message)

        def add_note(self, note_text: str) -> str:
            """Append a quick note to journal.md with a timestamp."""
            try:
                path = os.path.join(os.path.dirname(__file__), "journal.md")
                ts = time.strftime("%Y-%m-%d %H:%M:%S")
                with open(path, "a", encoding="utf-8") as f:
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
                    import requests
                    try:
                        from googletrans import Translator
                    except Exception:
                        Translator = None

                    # Default coordinates (user-provided)
                    DEFAULT_LAT = "39.6374"
                    DEFAULT_LON = "-75.6001"


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
                            except Exception:
                                self.logger.exception("Wikipedia search failed")
                                return "Sorry, I couldn't find anything on Wikipedia."

                        def ai_query(self, prompt: str) -> str:
                            # AI removed; keep stub
                            return ""

                        def get_weather_by_coords(self, lat: str, lon: str, place_name: str = "your location") -> str:
                            """Query api.weather.gov using coordinates and return a short forecast string."""
                            try:
                                headers = {"User-Agent": "Forte/1.0 (contact)", "Accept": "application/ld+json"}
                                points_url = f"https://api.weather.gov/points/{lat},{lon}"
                                pr = requests.get(points_url, headers=headers, timeout=10)
                                pr.raise_for_status()
                                pdata = pr.json()
                                forecast_url = pdata.get("properties", {}).get("forecast")
                                if not forecast_url:
                                    return "Weather service did not return a forecast for that location."

                                fr = requests.get(forecast_url, headers=headers, timeout=10)
                                fr.raise_for_status()
                                fdata = fr.json()
                                periods = fdata.get("properties", {}).get("periods", [])
                                if not periods:
                                    return "No forecast data available."
                                p = periods[0]
                                name = p.get("name", "Now")
                                short = p.get("shortForecast", "")
                                temp = p.get("temperature")
                                unit = p.get("temperatureUnit", "")
                                resp = f"{name} in {place_name}: {short}, {temp} {unit}."
                                self.speak(resp)
                                return resp
                            except Exception:
                                self.logger.exception("Weather by coords failed")
                                return "Sorry, I couldn't fetch the weather for that location."

                        def get_weather(self, city: Optional[str]) -> str:
                            """Fetch weather for `city`, or use default coordinates if `city` is falsy.
                            Uses api.weather.gov (no API key)."""
                            try:
                                # If no city provided, use default coordinates
                                if not city or str(city).strip().lower() in ("my location", "here", "current location"):
                                    return self.get_weather_by_coords(DEFAULT_LAT, DEFAULT_LON, "your location")

                                # Otherwise try to geocode the city name to lat/lon using Nominatim
                                geo_url = "https://nominatim.openstreetmap.org/search"
                                gr = requests.get(geo_url, params={"q": city, "format": "json", "limit": 1}, headers={"User-Agent": "Forte/1.0 (contact)"}, timeout=10)
                                gr.raise_for_status()
                                results = gr.json()
                                if not results:
                                    return f"I couldn't find the location {city}."
                                lat = results[0]["lat"]
                                lon = results[0]["lon"]
                                return self.get_weather_by_coords(lat, lon, city)
                            except Exception:
                                self.logger.exception("Weather lookup failed")
                                return "Sorry, I couldn't fetch the weather."

                        def set_timer(self, seconds: int, message: str = "Timer complete") -> None:
                            """Set a one-shot timer that speaks `message` after `seconds` seconds."""
                            def _timer():
                                try:
                                    time.sleep(seconds)
                                    text = f"Timer: {message}"
                                    print(text)
                                    self.speak(text)
                                except Exception:
                                    self.logger.exception("Timer failed")
                            threading.Thread(target=_timer, daemon=True).start()

                        def convert_currency(self, amount: float, from_curr: str, to_curr: str) -> str:
                            """Convert amount from one currency to another using exchangerate.host (no API key)."""
                            try:
                                url = "https://api.exchangerate.host/convert"
                                params = {"from": from_curr.upper(), "to": to_curr.upper(), "amount": amount}
                                r = requests.get(url, params=params, timeout=10)
                                r.raise_for_status()
                                data = r.json()
                                if not data.get("success", True):
                                    return "Currency conversion failed."
                                result = data.get("result")
                                resp = f"{amount} {from_curr.upper()} = {result:.2f} {to_curr.upper()}"
                                self.speak(resp)
                                return resp
                            except Exception:
                                self.logger.exception("Currency conversion failed")
                                return "Sorry, I couldn't convert currencies right now."

                        def translate_text(self, text: str, dest: str) -> str:
                            """Translate `text` to language `dest` (language code like 'es' or 'fr')."""
                            if Translator is None:
                                self.logger.warning("googletrans not installed")
                                return "Translation feature requires the 'googletrans' package. Please install it."
                            try:
                                translator = Translator()
                                res = translator.translate(text, dest=dest)
                                resp = f"Translation ({res.src} -> {res.dest}): {res.text}"
                                self.speak(resp)
                                return resp
                            except Exception:
                                self.logger.exception("Translation failed")
                                return "Sorry, I couldn't translate that."

                        def get_traffic(self, origin: str, destination: str) -> str:
                            """Get estimated travel time in current traffic between origin and destination.
                            Uses Google Maps Directions API; requires env var GOOGLE_MAPS_API_KEY."""
                            api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
                            if not api_key:
                                return "Google Maps API key not set." 
                            try:
                                url = "https://maps.googleapis.com/maps/api/directions/json"
                                params = {
                                    "origin": origin,
                                    "destination": destination,
                                    "departure_time": "now",
                                    "key": api_key,
                                }
                                r = requests.get(url, params=params, timeout=10)
                                r.raise_for_status()
                                data = r.json()
                                if data.get("status") != "OK":
                                    return f"Traffic API error: {data.get('status')}"
                                route = data["routes"][0]
                                leg = route["legs"][0]
                                duration = leg.get("duration", {}).get("text")
                                duration_in_traffic = leg.get("duration_in_traffic", {}).get("text")
                                summary = route.get("summary", "")
                                if duration_in_traffic:
                                    resp = f"Route {summary}: estimated time in current traffic {duration_in_traffic} (normal {duration})."
                                else:
                                    resp = f"Route {summary}: estimated travel time {duration}."
                                self.speak(resp)
                                return resp
                            except Exception:
                                self.logger.exception("Traffic lookup failed")
                                return "Sorry, I couldn't fetch traffic information."

                        def set_reminder(self, duration: int, message: str) -> None:
                            self.reminder_manager.add_reminder(duration, message)

                        def add_note(self, note_text: str) -> str:
                            """Append a quick note to journal.md with a timestamp."""
                            try:
                                path = os.path.join(os.path.dirname(__file__), "journal.md")
                                ts = time.strftime("%Y-%m-%d %H:%M:%S")
                                with open(path, "a", encoding="utf-8") as f:
                                    f.write(f"- [{ts}] {note_text}\n")
                                resp = "Note saved."
                                self.speak(resp)
                                return resp
                            except Exception:
                                self.logger.exception("Failed to save note")
                                return "Sorry, I couldn't save that note."

                        def define_word(self, word: str) -> str:
                            """Get a brief definition for `word` using dictionaryapi.dev."""
                            try:
                                url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
                                r = requests.get(url, timeout=10)
                                r.raise_for_status()
                                data = r.json()
                                if isinstance(data, list) and data:
                                    meanings = data[0].get("meanings", [])
                                    if meanings:
                                        defs = meanings[0].get("definitions", [])
                                        if defs:
                                            definition = defs[0].get("definition")
                                            resp = f"{word}: {definition}"
                                            self.speak(resp)
                                            return resp
                                return "No definition found."
                            except Exception:
                                self.logger.exception("Definition lookup failed")
                                return "Sorry, I couldn't look up that word."

                        def process_command(self, text: str) -> None:
                            print(f"User said: {text}")
                            text_lower = text.lower()

                            if text_lower.strip() == "help":
                                cmds = [
                                    "hello/hi", "how are you", "time", "calculate <expr>",
                                    "tell me a joke", "tell me a fact", "remind me in <n> minutes to <task>",
                                    "list reminders", "search wikipedia for <query>", "weather in <city>",
                                    "translate <text> to <lang>", "traffic from <origin> to <destination>",
                                    "set timer for <n> seconds/minutes", "convert <amount> <FROM> to <TO>",
                                    "note <text>", "define <word>", "goodbye"
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
                                if "for" in text_lower:
                                    query = text_lower.split("for", 1)[1].strip()
                                else:
                                    query = text_lower.replace("search wikipedia", "").strip()
                                self.search_wikipedia(query)
                            elif "weather" in text_lower:
                                import re
                                m = re.search(r"(?:weather(?: in| for)? )(.+)", text_lower)
                                if m:
                                    city = m.group(1).strip()
                                    self.get_weather(city)
                                else:
                                    # No city provided; use default coordinates
                                    self.get_weather(None)
                            elif text_lower.startswith("set timer") or "timer for" in text_lower:
                                import re
                                m = re.search(r"(\d+)\s*(second|seconds|minute|minutes)", text_lower)
                                if m:
                                    val = int(m.group(1))
                                    unit = m.group(2)
                                    seconds = val * 60 if unit.startswith("minute") else val
                                    msg_m = re.search(r"(?:to|for)\s+(.+)$", text, re.I)
                                    msg = msg_m.group(1).strip() if msg_m else "Timer finished"
                                    self.set_timer(seconds, msg)
                                    self.speak(f"Timer set for {val} {unit}.")
                                else:
                                    self.speak("Please specify a duration like 'set timer for 10 seconds'.")
                            elif text_lower.startswith("convert") or (" to " in text_lower and any(c.isdigit() for c in text_lower)):
                                import re
                                m = re.search(r"(\d+(?:\.\d+)?)\s*([A-Za-z]{3})\s+to\s+([A-Za-z]{3})", text)
                                if not m:
                                    m = re.search(r"convert\s+(\d+(?:\.\d+)?)\s*([A-Za-z]{3})\s+to\s+([A-Za-z]{3})", text, re.I)
                                if m:
                                    amount = float(m.group(1))
                                    frm = m.group(2)
                                    to = m.group(3)
                                    self.convert_currency(amount, frm, to)
                                else:
                                    self.speak("Please say something like 'convert 10 USD to EUR'.")
                            elif text_lower.startswith("translate"):
                                import re
                                m = re.search(r"translate\s+(.+)\s+to\s+([a-zA-Z-]+)$", text, re.I)
                                if m:
                                    phrase = m.group(1).strip()
                                    lang = m.group(2).strip()
                                    self.translate_text(phrase, lang)
                                else:
                                    m2 = re.search(r"translate to\s+([a-zA-Z-]+)\s+(.+)$", text, re.I)
                                    if m2:
                                        lang = m2.group(1).strip()
                                        phrase = m2.group(2).strip()
                                        self.translate_text(phrase, lang)
                                    else:
                                        self.speak("Please provide text and a target language code, e.g. 'translate hello to es'.")
                            elif "traffic" in text_lower and "from" in text_lower and "to" in text_lower:
                                import re
                                m = re.search(r"traffic from (.+) to (.+)", text_lower)
                                if m:
                                    origin = m.group(1).strip()
                                    destination = m.group(2).strip()
                                    self.get_traffic(origin, destination)
                                else:
                                    self.speak("Please say 'traffic from <origin> to <destination>'.")
                            elif text_lower.startswith("note"):
                                # note Buy milk
                                note_text = text.partition(" ")[2].strip()
                                if note_text:
                                    self.add_note(note_text)
                                else:
                                    self.speak("Please provide text for the note, e.g. 'note buy milk'.")
                            elif text_lower.startswith("define"):
                                word = text.partition(" ")[2].strip()
                                if word:
                                    self.define_word(word)
                                else:
                                    self.speak("Please provide a word to define, e.g. 'define serendipity'.")
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
                                # Keep the main thread alive indefinitely
                                while True:
                                    time.sleep(1)
                        except KeyboardInterrupt:
                            logging.info("Exiting...")
                            sys.exit(0)


                    if __name__ == "__main__":
                        main()
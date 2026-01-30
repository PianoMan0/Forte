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
import subprocess
import shutil
import xml.etree.ElementTree as ET
import requests
import json
import re
try:
    from googletrans import Translator
except Exception:
    Translator = None


class JokeGenerator:
    def __init__(self):
        # support categories for more interesting jokes
        self.jokes = {
            "general": [
                "Why don't programmers like nature? It has too many bugs.",
                "I've heard AI is going to take over the world. Just what I need, more work."
            ],
            "python": [
                "Why don't Python programmers like to play hide and seek? Because good luck hiding when they can just import os and find you.",
                "I told my Python program a joke. It didn't laugh because it couldn't find the 'humor' module."
            ],
        }

    def get_random_joke(self, category: Optional[str] = None) -> str:
        if category:
            cat = category.lower()
            if cat in self.jokes and self.jokes[cat]:
                return random.choice(self.jokes[cat])
            # fallback to general
            return random.choice(self.jokes.get("general", ["I have no jokes right now."]))
        # pick from all jokes
        all_j = sum(self.jokes.values(), [])
        return random.choice(all_j) if all_j else "I have no jokes right now."


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
        # speaking flag to avoid re-capturing TTS audio
        self._speaking = threading.Event()
        # conversation context
        self.last_user_message: Optional[str] = None
        self.last_response: Optional[str] = None
        self.conversation_history: List[str] = []
        # Default coordinates (user requested):
        self.default_lat = 39.6374
        self.default_lon = -75.6001
        # Safety flags -- default to unsafe actions disabled
        self.allow_apps = False
        self.allow_volume = False
        # simple alias mapping for common short phrases
        self.aliases = {
            "hi": "hello",
            "hey": "hello",
            "what's your name": "what is your name",
            "whats your name": "what is your name",
        }
        # Limits to avoid resource exhaustion
        self.max_timers = 5
        self._timer_count = 0
        self._timer_lock = threading.Lock()
        # Notes storage
        self.notes_file = os.path.join(os.path.dirname(__file__), "notes.json")
        self.conversation_log = os.path.join(os.path.dirname(__file__), "conversation.log")
        try:
            if not os.path.exists(self.notes_file):
                with open(self.notes_file, "w", encoding="utf-8") as f:
                    f.write("[]")
        except Exception:
            self.logger.exception("Failed to initialize notes file")

    def speak(self, text: str) -> None:
        # one-second delay before every assistant response
        try:
            time.sleep(1)
        except Exception:
            pass
        # Always record the last response and history so text-mode still works
        self.last_response = text
        self.conversation_history.append(f"Assistant: {text}")
        try:
            with open(self.conversation_log, "a", encoding="utf-8") as cf:
                cf.write(f"Assistant: {text}\n")
        except Exception:
            self.logger.debug("Failed to write conversation log")

        if not self.enable_tts:
            # In non-TTS/text mode, print to stdout so the user sees responses
            try:
                print(f"Assistant: {text}")
            except Exception:
                # fallback to logger if stdout is unavailable
                self.logger.info("TTS disabled, would say: %s", text)
            return

        try:
            self._speaking.set()
            self.engine.say(text)
            self.engine.runAndWait()
        finally:
            # give a short buffer to ensure microphone doesn't pick up the TTS
            time.sleep(0.25)
            self._speaking.clear()

    def listen(self) -> Optional[str]:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            # wait if we're speaking to avoid feedback
            while self._speaking.is_set():
                time.sleep(0.05)
            print("Listening...")
            try:
                # set some reasonable timeouts so we don't hang forever
                audio = recognizer.listen(source, timeout=6, phrase_time_limit=12)
                text = recognizer.recognize_google(audio, language='en-US')
                return text
            except sr.WaitTimeoutError:
                return None
            except sr.UnknownValueError:
                # be concise; avoid speaking over background noise
                self.speak("Sorry, I didn't catch that.")
                return None
            except sr.RequestError as e:
                self.speak(f"Sorry, there was an error; {e}")
                return None

    def calculate(self, expression: str) -> str:
        try:
            math_text = expression.lower().replace("calculate", "").strip()
            math_text = (
                math_text.replace("plus", "+")
                .replace("minus", "-")
                .replace("times", "*")
                .replace("x", "*")
                .replace("divided by", "/")
            )

            def safe_eval(expr: str):
                operators = {
                    ast.Add: op.add,
                    ast.Sub: op.sub,
                    ast.Mult: op.mul,
                    ast.Div: op.truediv,
                    ast.Pow: op.pow,
                    ast.USub: op.neg,
                }

                def _eval(node):
                    if isinstance(node, ast.Constant):
                        return node.value
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
        except Exception:
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

    def get_weather(self, city: Optional[str] = None, lat: Optional[float] = None, lon: Optional[float] = None) -> str:
        """Fetch current weather using api.weather.gov.
        If lat/lon provided, use them. If city provided, geocode it. If none provided, use defaults.
        """
        try:
            if lat is None or lon is None:
                if city:
                    geo_url = "https://nominatim.openstreetmap.org/search"
                    gr = requests.get(
                        geo_url,
                        params={"q": city, "format": "json", "limit": 1},
                        headers={"User-Agent": "Forte/1.0 (email@example.com)"},
                        timeout=10,
                    )
                    gr.raise_for_status()
                    results = gr.json()
                    if not results:
                        return f"I couldn't find the location {city}."
                    lat = float(results[0]["lat"])
                    lon = float(results[0]["lon"])
                else:
                    lat = self.default_lat
                    lon = self.default_lon

            headers = {"User-Agent": "Forte/1.0 (email@example.com)", "Accept": "application/ld+json"}
            points_url = f"https://api.weather.gov/points/{lat},{lon}"
            pr = requests.get(points_url, headers=headers, timeout=10)
            pr.raise_for_status()
            pdata = pr.json()
            forecast_url = pdata.get("properties", {}).get("forecast")
            location_name = pdata.get("properties", {}).get("relativeLocation", {}).get("properties", {}).get("city")
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
            loc_display = city if city else (location_name or f"{lat},{lon}")
            resp = f"{name} in {loc_display}: {short}, {temp} {unit}."
            self.speak(resp)
            return resp
        except Exception:
            self.logger.exception("Weather lookup failed")
            return "Sorry, I couldn't fetch the weather."

    def set_timer(self, seconds: int, message: str = "Timer complete") -> None:
        # Prevent too many timers from being created
        with self._timer_lock:
            if self._timer_count >= self.max_timers:
                self.speak("Too many timers running; please wait before adding another.")
                return
            self._timer_count += 1

        def _timer():
            try:
                time.sleep(seconds)
                text = f"Timer: {message}"
                print(text)
                self.speak(text)
            except Exception:
                self.logger.exception("Timer failed")
            finally:
                with self._timer_lock:
                    self._timer_count = max(0, self._timer_count - 1)

        threading.Thread(target=_timer, daemon=True).start()

    # Volume control (Windows - uses pycaw if available)
    def set_volume(self, percent: int) -> str:
        if not self.allow_volume:
            return "Volume control is disabled. Run with --allow-volume to enable."
        try:
            if not sys.platform.startswith("win"):
                return "Volume control is only supported on Windows."
            if percent < 0 or percent > 100:
                return "Please provide a volume between 0 and 100."
            # Try pycaw (preferred)
            try:
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                speakers = AudioUtilities.GetSpeakers()
                interface = speakers.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
                volume.SetMasterVolumeLevelScalar(percent / 100.0, None)
                msg = f"Volume set to {percent}%"
                self.speak(msg)
                return msg
            except Exception:
                self.logger.debug("pycaw not available or failed; volume control not performed")
                return "Volume control is not available (pycaw/comtypes not installed)."
        except Exception:
            self.logger.exception("Failed to set volume")
            return "Sorry, I couldn't change the volume."

    def get_volume(self) -> str:
        if not self.allow_volume:
            return "Volume control is disabled. Run with --allow-volume to enable."
        try:
            if not sys.platform.startswith("win"):
                return "Volume info is only supported on Windows."
            try:
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                speakers = AudioUtilities.GetSpeakers()
                interface = speakers.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
                val = volume.GetMasterVolumeLevelScalar()
                pct = int(round(val * 100))
                msg = f"Current volume is {pct}%"
                self.speak(msg)
                return msg
            except Exception:
                self.logger.debug("pycaw not available; cannot read volume")
                return "Volume information not available (pycaw/comtypes not installed)."
        except Exception:
            self.logger.exception("Failed to get volume")
            return "Sorry, I couldn't read the volume."

    def open_app(self, app_name: str) -> str:
        if not self.allow_apps:
            return "Opening applications is disabled. Run with --allow-apps to enable."
        try:
            name = app_name.strip().lower()
            # Apps
            mapping = {
                "notepad": "notepad.exe",
                "edge": "msedge",
            }
            cmd = mapping.get(name, name)
            # If it's a known exe, try to launch via which or startfile
            found = shutil.which(cmd)
            if found:
                subprocess.Popen([found], shell=False)
                msg = f"Opening {app_name}"
                self.speak(msg)
                return msg
            # try startfile (works for registered protocols/paths)
            try:
                os.startfile(cmd)
                msg = f"Opening {app_name}"
                self.speak(msg)
                return msg
            except Exception:
                # fallback: try to run directly (may work for commands in PATH)
                try:
                    subprocess.Popen([cmd], shell=True)
                    msg = f"Opening {app_name}"
                    self.speak(msg)
                    return msg
                except Exception:
                    self.logger.exception("Failed to open app %s", app_name)
                    return f"I couldn't open {app_name}."
        except Exception:
            self.logger.exception("open_app failed")
            return "Sorry, I couldn't open that application."

    def get_latest_news(self, source: str = "google") -> str:
        try:
            # Use Google News RSS as default (no API key required)
            if source == "google":
                url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
            else:
                url = "http://feeds.bbci.co.uk/news/rss.xml"
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            root = ET.fromstring(r.content)
            items = root.findall('.//item')[:5]
            headlines = []
            for it in items:
                title = it.find('title').text if it.find('title') is not None else None
                link = it.find('link').text if it.find('link') is not None else None
                if title:
                    headlines.append((title, link))
            if not headlines:
                return "No news items found."
            # speak headlines
            self.speak("Here are the top headlines:")
            for title, link in headlines:
                self.speak(title)
            return "; ".join([h[0] for h in headlines])
        except Exception:
            self.logger.exception("News fetch failed")
            return "Sorry, I couldn't fetch the latest news."

    def convert_currency(self, amount: float, from_curr: str, to_curr: str) -> str:
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

    # Notes (persisted to notes.json)
    def _read_notes(self):
        try:
            with open(self.notes_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _write_notes(self, notes):
        try:
            with open(self.notes_file, "w", encoding="utf-8") as f:
                json.dump(notes, f, ensure_ascii=False, indent=2)
        except Exception:
            self.logger.exception("Failed to write notes")

    def add_note(self, text: str) -> str:
        notes = self._read_notes()
        note = {"id": int(time.time()), "text": text}
        notes.append(note)
        self._write_notes(notes)
        self.speak("Note saved.")
        return "Note saved."

    def list_notes(self) -> List[str]:
        notes = self._read_notes()
        if not notes:
            self.speak("You have no notes.")
            return []
        for n in notes:
            self.speak(f"Note {n['id']}: {n['text']}")
        return [n["text"] for n in notes]

    def delete_note(self, note_id: str) -> str:
        notes = self._read_notes()
        new = [n for n in notes if str(n.get("id")) != str(note_id)]
        if len(new) == len(notes):
            return "Note not found."
        self._write_notes(new)
        self.speak("Note deleted.")
        return "Note deleted."

    def define_word(self, word: str) -> str:
        try:
            url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
            r = requests.get(url, timeout=20)
            r.raise_for_status()
            data = r.json()
            meanings = data[0].get("meanings", [])
            if not meanings:
                return "No definition found."
            defs = meanings[0].get("definitions", [])
            if not defs:
                return "No definition found."
            definition = defs[0].get("definition")
            example = defs[0].get("example")
            resp = f"{word}: {definition}"
            if example:
                resp += f" Example: {example}"
            self.speak(resp)
            return resp
        except Exception:
            self.logger.exception("Definition lookup failed")
            return "Sorry, I couldn't find a definition."

    def set_reminder(self, duration: int, message: str) -> None:
        self.reminder_manager.add_reminder(duration, message)

    def process_command(self, text: str) -> None:
        if not text:
            return False
        print(f"User: {text}")
        self.last_user_message = text
        self.conversation_history.append(f"User: {text}")
        text_lower = text.lower()
        # apply simple alias normalization
        norm = text_lower.strip()
        if norm in self.aliases:
            text_lower = self.aliases[norm]

        if text_lower.strip() == "help":
            cmds = [
                "hello/hi", "how are you", "time", "calculate <expr>",
                "tell me a joke", "tell me a fact", "remind me in <n> minutes to <task>",
                "list reminders", "search wikipedia for <query>", "weather in <city>",
                "translate <text> to <lang>", "traffic from <origin> to <destination>",
                "set timer for <n> seconds/minutes", "convert <amount> <FROM> to <TO>",
                "take note <text>", "list notes", "delete note <id>", "define <word>",
                "goodbye"
            ]
            self.speak("Available commands: " + ", ".join(cmds))
            return False

        if any(word in text_lower for word in ["hello", "hi", "hey", "sup", "greetings"]):
            self.speak("Hello!")
        elif "how are you" in text_lower:
            self.speak("I'm doing well, thank you for asking!")
        elif "meow" in text_lower:
            self.speak("Are you a cat? What the sigma, I like cats.")
        elif "what is your name" in text_lower or "who are you" in text_lower:
            self.speak("I am Forte")
        elif "thanks" in text_lower:
            self.speak("You're welcome!")
        elif "six seven" in text_lower:
            self.speak("Six seven!")
        elif "will you be my friend" in text_lower:
            self.speak("Of course!")
        elif "want to be friends" in text_lower:
            self.speak("Of course!")
        elif "who created you" in text_lower:
            self.speak("Joel Gallagher created me!")
        elif "who made you" in text_lower:
            self.speak("Joel Gallagher made me!")
        elif "what can you do" in text_lower:
            self.speak("I can do a lot of things! Try asking me to tell a joke, a fun fact, calculate something, search wikipedia, and more! If I can't do something yet, nag my creator until he programs me to be able to do it!")  
        elif "goodbye" in text_lower:
            self.speak("Goodbye! Have a great day!")
            return True
        elif "time" in text_lower:
            current_time = time.strftime("%I:%M %p").lstrip("0")
            self.speak(f"The time is {current_time}")
        elif "calculate" in text_lower:
            result = self.calculate(text)
            self.speak(result)
        elif "tell me a joke" in text_lower or "joke" == text_lower.strip():
            # support "tell me a joke about python" or "tell me a python joke"
            m = re.search(r"joke(?: about)?\s+([A-Za-z]+)", text_lower)
            if m:
                cat = m.group(1)
                self.speak(self.joke_generator.get_random_joke(category=cat))
            else:
                # check patterns like 'tell me a python joke'
                m2 = re.search(r"tell me a\s+([A-Za-z]+)\s+joke", text_lower)
                if m2:
                    cat = m2.group(1)
                    self.speak(self.joke_generator.get_random_joke(category=cat))
                else:
                    self.speak(self.joke_generator.get_random_joke())
        elif "tell me a fact" in text_lower:
            self.speak(self.fact_generator.get_random_fact())
        elif "remind me" in text_lower:
            try:
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
            # If user says just 'weather', use defaults.
            m = re.search(r"(?:weather(?: in| for)? )(.+)", text_lower)
            if m:
                city = m.group(1).strip()
                self.get_weather(city=city)
            else:
                # no city provided, use default coords
                self.get_weather()
        elif text_lower.startswith("set timer") or "timer for" in text_lower:
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
        elif text_lower.strip() in ("repeat", "say that again", "what did you say"):
            if self.last_response:
                self.speak(self.last_response)
            else:
                self.speak("I don't have anything to repeat.")
        elif "another joke" in text_lower or "more jokes" in text_lower:
            self.speak(self.joke_generator.get_random_joke())
        elif text_lower.startswith("convert") or (" to " in text_lower and any(c.isdigit() for c in text_lower)):
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
            m = re.search(r"traffic from (.+) to (.+)", text_lower)
            if m:
                origin = m.group(1).strip()
                destination = m.group(2).strip()
                self.get_traffic(origin, destination)
            else:
                self.speak("Please say 'traffic from <origin> to <destination>'.")
        elif text_lower.startswith("take note") or text_lower.startswith("save note") or text_lower.startswith("note:"):
            # capture note text
            m = re.search(r"(?:take note|save note|note:)\s*(.+)", text, re.I)
            if m:
                note_text = m.group(1).strip()
                self.add_note(note_text)
            else:
                self.speak("Please provide note text, e.g. 'take note buy milk'.")
        elif "list notes" in text_lower:
            self.list_notes()
        elif text_lower.startswith("delete note"):
            m = re.search(r"delete note\s+(\d+)", text_lower)
            if m:
                nid = m.group(1)
                self.delete_note(nid)
            else:
                self.speak("Please give the numeric id of the note to delete.")
        elif text_lower.startswith("define "):
            m = re.search(r"define\s+([A-Za-z-]+)", text_lower)
            if m:
                word = m.group(1)
                self.define_word(word)
            else:
                self.speak("Please say 'define <word>'.")
        else:
            self.speak("Sorry, I didn't understand that command.")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Forte - a small speech assistant")
    parser.add_argument("--text", action="store_true", help="Run in text/CLI mode (no microphone listening)")
    parser.add_argument("--listen", action="store_true", help="Enable microphone listening mode")
    parser.add_argument("--allow-apps", action="store_true", help="Allow the assistant to open applications (opt-in)")
    parser.add_argument("--allow-volume", action="store_true", help="Allow the assistant to change system volume (opt-in)")
    parser.add_argument("--no-tts", action="store_true", help="Disable text-to-speech output")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    assistant = SpeechAssistant()
    # apply explicit safety opt-ins
    assistant.allow_apps = bool(getattr(args, "allow_apps", False))
    assistant.allow_volume = bool(getattr(args, "allow_volume", False))
    if args.no_tts:
        assistant.enable_tts = False

    def listen_and_process():
        while True:
            text = assistant.listen()
            if text:
                should_exit = assistant.process_command(text)
                if should_exit:
                    break

    try:
        # Default to microphone listening unless --text is provided
        if not args.text:
            assistant.speak("Microphone listening enabled. Say 'help' for commands.")
            # run in main thread so TTS/speaking syncs with listening
            listen_and_process()
        else:
            assistant.speak("Running in text mode. Type 'exit' to quit. Type 'help' for commands.")
            while True:
                text = input("> ")
                if not text:
                    continue
                if text.strip().lower() in ("exit", "quit", "goodbye"):
                    assistant.speak("Goodbye!")
                    break
                assistant.process_command(text)
    except KeyboardInterrupt:
        logging.info("Exiting...")
        sys.exit(0)


if __name__ == "__main__":
    main()
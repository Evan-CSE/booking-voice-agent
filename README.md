# 🎙️ AI Voice Calendar Scheduler

An end-to-end, self-hosted voice agent that acts as your personal scheduling assistant. The agent can converse with you in real-time, check your Google Calendar for conflicts, schedule new meetings, and send a summary email to the attendees.

This project is built from the ground up prioritizing **Clean Architecture**, sub-second WebRTC audio streaming, and 100% containerized self-hosted components (with the exception of the LLM).

---

## 🧠 AI Models Used

This assistant relies on a hybrid approach—combining lightning-fast cloud LLM reasoning with localized, self-hosted speech models for maximum privacy and control:

1. **LLM (Reasoning & Conversation):**
   - **Google Gemini 3 Flash Preview** (`gemini-3-flash-preview`)
   - Used via the `livekit-plugins-google` package. Chosen for its extreme speed and strong tool-calling capabilities.
2. **STT (Speech-to-Text):**
   - **Faster-Whisper** (`tiny` model, int8 quantization)
   - Self-hosted in a dedicated Docker container exposing an OpenAI-compatible REST API.
3. **TTS (Text-to-Speech):**
   - **Piper** (`en_US-lessac-medium.onnx`)
   - Self-hosted in a dedicated Docker container. It exposes a custom streaming endpoint that yields raw 24kHz PCM chunks sentence-by-sentence, drastically reducing "time-to-first-audio" latency compared to standard WAV generation.

---

## 🏗️ Architectural View (Clean Architecture)

The Python backend driving the agent (`livekit-agent`) has been meticulously refactored following **Clean Architecture** and SOLID principles to ensure separation of concerns:

```text
app/
├── domain/                  # 🟢 Core Business Logic
│   ├── models.py            # Data structures (MeetingRequest, User, MeetingResult)
│   └── interfaces.py        # Abstract Base Classes (CalendarRepository, EmailSender)
│
├── usecases/                # 🟡 Application Logic
│   └── schedule_meeting.py  # Orchestrates availability checks, event creation, and emails
│
├── infrastructure/          # 🔴 External Frameworks & Adapters
│   ├── google_calendar.py   # Implements CalendarRepository using Google API v3
│   ├── smtp_email.py        # Implements EmailSender using Python smtplib
│   └── livekit_agent.py     # Wraps use cases into LiveKit @function_tools
│
└── main.py                  # 🔵 Composition Root & Entrypoints
                             # Wires dependencies, configures LiveKit Worker & AIOHTTP server
```

- **Dependency Inversion:** The `VoiceAgentUseCase` has no idea about Google or SMTP. It only knows about the domain interfaces. The concrete infrastructure adapters are injected in `main.py`.
- **Modularity:** You can easily swap out `GoogleCalendarRepository` for an `OutlookCalendarRepository` by just updating `main.py`.

### System Services (Docker Compose)
- **`livekit-server`**: The core WebRTC SFU routing the audio streams.
- **`stt`**: The Faster-Whisper local API.
- **`tts`**: The Piper streaming local API.
- **`agent`**: The Python LiveKit worker (runs `app/main.py start`).
- **`web`**: The lightweight AIOHTTP web/token server (runs `app/main.py web`).

---

## 🚀 Live Demo & Testing Instructions

Project is not deployed yet. But you can test it locally.

[![Watch the Demo](https://img.youtube.com/vi/zwvGTtXNiSU/hqdefault.jpg)](https://youtu.be/zwvGTtXNiSU)


### How to Test the Agent Locally:
1. Ensure the stack is running (see *Setup Instructions* below).
2. Open your browser and navigate to `http://localhost:8080`.
3. Click the **"Connect & Speak"** button and grant microphone permissions.
4. The agent will greet you: *"Hello! I can help you schedule a meeting. What would you like to book?"*
5. Speak naturally! Try saying:
   > *"I need a 30-minute meeting tomorrow at 2 PM to discuss the new project. My name is Alice, and my email is alice@example.com."*
6. The agent will check your calendar, confirm the details, schedule the Google Calendar event, and send a real SMTP confirmation email.
7. You can view the live STT/TTS transcriptions in the chat window on the web page.

---

## 🛠️ Calendar Integration Details

This project securely integrates with the Google Calendar API:

1. **OAuth 2.0:** Uses `credentials.json` for a desktop application flow to generate a long-lived `token.json`.
2. **Conflict Checks:** Before scheduling, the agent lists events in the requested timeframe to ensure you are free.
3. **Timezone Enforcement:** The LLM is strictly instructed to format all extracted datetimes into `ISO 8601 (RFC3339)` format including your local timezone offset (e.g., `+06:00`).

---

## 💻 Running the Project Locally

### Prerequisites
- Docker & Docker Compose
- A Google Cloud Project with the Calendar API enabled (download the OAuth client ID as `credentials.json`).
- A Google AI Studio API Key (For Gemini).
- An SMTP account (like a Gmail App Password) for email dispatch.

### Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Evan-CSE/booking-voice-agent.git
   cd booking-voice-agent
   ```

2. **Environment Variables:**
   Copy the example environment file and fill in your keys.
   ```bash
   cp .env.example .env
   ```
   *Required:* `GOOGLE_API_KEY`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, and `SMTP_*` info.

3. **Google Credentials:**
   Place your downloaded `credentials.json` from the Google Cloud Console into the root of the project.

4. **Initialize Google Auth (First Run Only):**
   If you don't have a `token.json` yet, you need to run the calendar script locally to authenticate your browser.
   ```bash
   python -m app.infrastructure.google_calendar
   ```

5. **Start the Services:**
   Run the whole stack via Docker Compose:
   ```bash
   docker compose up --build -d
   ```

6. **Access the App:**
   Open your browser and navigate to:
   ```
   http://localhost:8080
   ```

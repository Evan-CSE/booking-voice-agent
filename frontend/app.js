const connectBtn = document.getElementById('connectBtn');
const statusEl = document.getElementById('status');
const audioElements = document.getElementById('audio-elements');
const chatContainer = document.getElementById('chat-container');

let room = null;

async function connect() {
    try {
        statusEl.innerText = "Status: Fetching Token...";
        connectBtn.disabled = true;

        // Give the agent time to be running if they were started simultaneously
        // In a real app we just fetch immediately.
        const res = await fetch('/token');
        if (!res.ok) {
            throw new Error(`Server returned ${res.status}`);
        }
        const data = await res.json();
        const { token, url } = data;

        if (!token || !url) {
            throw new Error("Missing LiveKit URL or Token in server response.");
        }

        statusEl.innerText = "Status: Connecting to LiveKit...";

        room = new LivekitClient.Room({
            adaptiveStream: true,
            dynacast: true,
        });

        // Set up Event Listeners
        room.on(LivekitClient.RoomEvent.TrackSubscribed, (track, publication, participant) => {
            if (track.kind === LivekitClient.Track.Kind.Audio) {
                const element = track.attach();
                audioElements.appendChild(element);
            }
        });

        room.on(LivekitClient.RoomEvent.TrackUnsubscribed, (track, publication, participant) => {
            track.detach();
        });

        // Listen for transcription events (STT/TTS text)
        room.on(LivekitClient.RoomEvent.TranscriptionReceived, (transcription, participant) => {
            // Only process the final/completed transcription text to avoid partial flickering
            const finalSegments = transcription.filter(seg => seg.final);
            if (finalSegments.length === 0) return;

            const text = finalSegments.map(seg => seg.text).join(' ').trim();
            if (!text) return;

            // Remove the placeholder if it's the first message
            if (chatContainer.innerHTML.includes('Transcriptions will appear here')) {
                chatContainer.innerHTML = '';
            }

            const isAgent = participant?.identity?.startsWith('agent') || !participant;
            const msgDiv = document.createElement('div');
            msgDiv.className = `chat-msg ${isAgent ? 'msg-agent' : 'msg-user'}`;
            msgDiv.innerHTML = `<strong>${isAgent ? 'Agent' : 'You'}:</strong> ${text}`;

            chatContainer.appendChild(msgDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight; // Auto-scroll
        });

        room.on(LivekitClient.RoomEvent.Disconnected, () => {
            statusEl.innerText = "Status: Disconnected";
            connectBtn.innerText = "Connect & Speak";
            connectBtn.disabled = false;
            audioElements.innerHTML = '';
            chatContainer.innerHTML = '<div style="text-align:center; color:#999; margin-top: 100px;">Transcriptions will appear here...</div>';
        });

        await room.connect(url, token);
        statusEl.innerText = "Status: Connected. Enabling Microphone...";

        // Enable microphone
        await room.localParticipant.setMicrophoneEnabled(true);

        statusEl.innerText = "Status: Listening... Say Hello!";
        connectBtn.innerText = "Disconnect";
        connectBtn.disabled = false;

        connectBtn.onclick = disconnect;

    } catch (e) {
        console.error(e);
        statusEl.innerText = `Status: Error - ${e.message}`;
        connectBtn.disabled = false;
    }
}

async function disconnect() {
    if (room) {
        await room.disconnect();
    }
    connectBtn.onclick = connect;
}

connectBtn.onclick = connect;

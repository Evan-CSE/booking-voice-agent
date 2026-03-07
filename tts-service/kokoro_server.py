from kokoro import KPipeline
from IPython.display import Audio, display, clear_output
import soundfile as sf
import numpy as np
import time
import io
import threading

# British English pipeline (use 'a' for American)
pipeline = KPipeline(lang_code='b')

text = '''
[Kokoro](/kˈOkəɹO/) is an open-weight TTS model with 82 million parameters. Despite its lightweight architecture, it delivers comparable quality to larger models while being significantly faster and more cost-efficient. With Apache-licensed weights, [Kokoro](/kˈOkəɹO/) can be deployed anywhere from production environments to personal projects.
'''

generator = pipeline(text, voice='bf_emma', speed=1.0)

def play_audio_chunk(audio_np, rate=24000):
    # Convert int16 numpy array → wav bytes in memory
    byte_io = io.BytesIO()
    sf.write(byte_io, audio_np, rate, format='WAV', subtype='PCM_16')
    byte_io.seek(0)
    display(Audio(byte_io.read(), rate=rate, autoplay=True))
    # Small pause helps chaining without overlap/clipping in notebook
    time.sleep(0.05)

print("Starting streaming playback...\n")

for i, (gs, ps, audio) in enumerate(generator):
    print(f"Chunk {i}: {gs} → {ps}")
    
    # audio is usually np.int16 at 24kHz
    play_audio_chunk(audio)
    
    # Optional: save chunk too
    # sf.write(f'chunk_{i}.wav', audio, 24000)
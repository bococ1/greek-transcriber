import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import av
import numpy as np
from openai import OpenAI
import queue
import tempfile
import soundfile as sf
import os

st.set_page_config(page_title="🎧 Real-Time Greek Transcriber", layout="centered")

st.title("🎙️ Live Speech-to-Greek Translator")
st.markdown("""
Speak through your microphone — your English speech will be **transcribed and translated into Greek** in real-time.
When you're done, download the full transcript as a `.txt` file below.
""")

client = OpenAI()
audio_q = queue.Queue()
if "conversation" not in st.session_state:
    st.session_state.conversation = []

class AudioProcessor(AudioProcessorBase):
    def recv_audio(self, frame: av.AudioFrame) -> av.AudioFrame:
        audio = frame.to_ndarray()
        audio_q.put(audio)
        return frame

webrtc_ctx = webrtc_streamer(
    key="speech-to-greek",
    mode=WebRtcMode.SENDRECV,
    audio_receiver_size=256,
    media_stream_constraints={"audio": True, "video": False},
    async_processing=True,
    audio_processor_factory=AudioProcessor,
)

chat_container = st.container()

def export_transcript():
    transcript_text = "\n\n".join(
        [f"🗣️ English: {e}\n🇬🇷 Greek: {g}" for e, g in st.session_state.conversation]
    )
    return transcript_text.encode("utf-8")

if webrtc_ctx.state.playing:
    st.info("🎤 Listening... speak naturally.")
    placeholder_status = st.empty()

    while True:
        try:
            audio_chunk = audio_q.get(timeout=3)
        except queue.Empty:
            continue

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            sf.write(tmp.name, audio_chunk, 48000)
            tmp_path = tmp.name

        try:
            result = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=open(tmp_path, "rb"),
            )
            english_text = result.text.strip()

            if english_text:
                translation = client.responses.create(
                    model="gpt-4.1-mini",
                    input=f"Translate this to Greek:\n\n{english_text}",
                )
                greek_text = translation.output[0].content[0].text.strip()
                st.session_state.conversation.append((english_text, greek_text))

                with chat_container:
                    for e, g in st.session_state.conversation[-10:]:
                        st.markdown(f"**🗣️ English:** {e}")
                        st.markdown(f"**🇬🇷 Greek:** {g}")
                        st.markdown("---")

        except Exception as e:
            placeholder_status.warning(f"⚠️ Error: {e}")
        finally:
            os.unlink(tmp_path)

if st.session_state.conversation:
    st.download_button(
        label="💾 Download Full Transcript (.txt)",
        data=export_transcript(),
        file_name="speech_to_greek_transcript.txt",
        mime="text/plain",
    )

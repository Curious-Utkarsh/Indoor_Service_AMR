#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

import whisper
import sounddevice as sd
import os
from scipy.io.wavfile import write
import google.generativeai as genai
from elevenlabs.client import ElevenLabs
from elevenlabs import play

import asyncio
from concurrent.futures import ThreadPoolExecutor
import json

from pathlib import Path

# ros2 topic pub --once /mobi/intents std_msgs/msg/String "data: 'undock'"


class VoiceLLMNode(Node):
    def __init__(self):
        super().__init__('voice_llm_node')
        self.thread_executor = ThreadPoolExecutor(max_workers=2)

        self.publisher_ = self.create_publisher(String, '/mobi/intents', 10)
        self.get_logger().info("Voice LLM node started")

        # Setup paths
        self.BASE_PATH = Path.home() / "mobi_ws" / "src" / "mobi_speech" / "output_voice"
        self.BASE_PATH.mkdir(parents=True, exist_ok=True)  # create if not exists
        os.makedirs(self.BASE_PATH, exist_ok=True)

        # Load Whisper
        self.get_logger().info("Loading Whisper model...")
        self.model = whisper.load_model("base")
        self.get_logger().info("Whisper model loaded")

        # Setup Gemini
        genai.configure(api_key=os.getenv('GEMINI_API_KEY', ''))  # export GEMINI_API_KEY=...
        self.gemini = genai.GenerativeModel('gemini-2.0-flash')

        # Setup ElevenLabs
        self.eleven_client = ElevenLabs(api_key=os.getenv('ELEVENLABS_API_KEY', ''))  # export ELEVENLABS_API_KEY=...

        self.get_logger().info("Ready for voice commands.")

    async def run_loop(self):
        while rclpy.ok():
            user_text = self.get_voice_input()
            if not user_text.strip():
                self.get_logger().info("No input. Try again.")
                continue
            if "exit" in user_text.lower():
                self.speak("Goodbye friend")
                break

            # Run both tasks concurrently
            loop = asyncio.get_event_loop()
            intent_future = loop.run_in_executor(self.thread_executor, self.get_command_intent, user_text)
            reply_future = loop.run_in_executor(self.thread_executor, self.get_general_response, user_text)


            intent_json_str, general_reply = await asyncio.gather(intent_future, reply_future)

            self.get_logger().info(f"Intent response: {intent_json_str}")
            
            try:
                intent_data = json.loads(intent_json_str)
                intent_value = intent_data.get("intent", "").strip()

                valid_intents = {"go_to_user", "dock", "undock", "go_to_kitchen", "stop"}

                if intent_value in valid_intents:
                    #self.speak(self.intent_to_speech(intent_value))
                    self.get_logger().info(f"Intent Value: {intent_value}")
                    msg = String()
                    msg.data = intent_value
                    self.publisher_.publish(msg)
                else:
                    #self.speak(general_reply)
                    self.get_logger().info(f"{general_reply}")

            except json.JSONDecodeError:
                #self.speak(general_reply)
                self.get_logger().info(f"{general_reply}")



    def intent_to_speech(self, intent_json: str) -> str:
        if "go_to_user" in intent_json:
            return "Okay, coming to you"
        elif "dock" in intent_json:
            return "Alright, going to dock"
        elif "undock" in intent_json:
            return "Undocking now"
        elif "go_to_kitchen" in intent_json:
            return "Heading to the kitchen"
        elif "stop" in intent_json:
            return "Okay, stopping"


    def get_voice_input(self):
        fs = 16000
        duration = 3
        wav_path = os.path.join(self.BASE_PATH, "input.wav")
        self.get_logger().info("Recording now...")
        audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()
        write(wav_path, fs, audio)

        self.get_logger().info("Transcribing...")
        result = self.model.transcribe(wav_path)
        self.get_logger().info(f"You said: {result['text']}")
        return result["text"]

    def get_command_intent(self, prompt):
        instruction = (
            "Return only one JSON: {\"intent\": \"<value>\"}. "
            "Allowed values: dock, undock, go_to_user, go_to_kitchen, stop, unknown. "
            "If unclear, always respond with: {\"intent\": \"unknown\"}."
        )
        final_prompt = f"{instruction}\n\nHuman said: {prompt}\nIntent:"

        try:
            response = self.gemini.generate_content(final_prompt)
            return response.text.strip()
        except Exception as e:
            self.get_logger().error(f"Gemini error: {e}")
            return "{\"intent\": \"error\"}"


    def get_general_response(self, prompt):
        personality = (
            "You are Mobi, a friendly home robot assistant. "
            "Reply in a fun and simple way like a helpful robot friend. "
            "Keep answers short and polite. Avoid punctuation, emojis, and complex sentences."
        )

        final_prompt = f"{personality}\n\nUser: {prompt}\nMobi:"
        try:
            response = self.gemini.generate_content(final_prompt)
            return response.text.strip()
        except Exception as e:
            self.get_logger().error(f"Gemini general response error: {e}")
            return "Sorry, I don't know."

    def speak(self, text):
        try:
            audio = self.eleven_client.text_to_speech.convert(
                text=text,
                voice_id="flq6f7yk4E4fJM5XTYuZ",  # Michael
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128"
            )
            play(audio)
        except Exception as e:
            self.get_logger().error(f"ElevenLabs TTS error: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = VoiceLLMNode()

    try:
        # Spin ROS in another thread
        executor = ThreadPoolExecutor()
        executor.submit(rclpy.spin, node)

        # Start asyncio loop and schedule the coroutine
        loop = asyncio.get_event_loop()
        loop.run_until_complete(node.run_loop())
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

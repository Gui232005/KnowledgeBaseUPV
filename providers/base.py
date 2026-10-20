"""
Log:
- YYYY-MM-DD - [NAME]: Describe the improvement made in this file.
- 2026-10-15 - [Guilherme Silva]: Improve the architecture of the project, creating a base class for the providers and making the code more modular and maintainable.
- 2026-10-15 - [AlexPT2k22]: Removed the unused `user` variable in connect_to_supabase (ruff F841).
- 2026-10-16 - [Guilherme Silva]: Start the ability to store the conversation in a JSON file, and to review the conversation and fix some issues.
- 2026-10-20 - [Guilherme Silva]: Ended the conversation_review method and added the ability to select a conversation file to review.
"""

from abc import ABC, abstractmethod
import os
import tempfile
import subprocess as standard_subprocess
import shutil
import time
import json
from dotenv import load_dotenv
from supabase import Client, create_client
import re

load_dotenv()

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class ModelProvider(ABC):
    def __init__(self, model_name: str, model_key: str):
        self.model_name = model_name
        self.model_key = model_key

    def print_info(self):
        print(f"Model Name: {self.model_name}, Model Key: {self.model_key}")

    def get_model_name(self):
        return self.model_name

    @abstractmethod
    def speak_with_model(question: str, output_type: str):
        pass

    @staticmethod
    def load_title():
        try:
            with open("memory.txt", "r", encoding="utf-8") as f:
                title = f.read().strip()
                print(f"\033[92mLoaded title from memory.txt: {title}\033[0m")
                return title
        except FileNotFoundError:
            return None
    
    def create_conversation(self, conversation_data, title):
        file = f"conversations/{title}"
        try:
            with open(file, "r", encoding="utf-8") as f:
                history = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            history = []
        history.append(conversation_data)
        with open(file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=4)

    @abstractmethod
    def conversation_review(conversation):
        pass

    @staticmethod
    def connect_to_supabase():
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        supabase.auth.sign_in_with_password({
            'email': USERNAME,
            'password': PASSWORD,
        })
        print("Connected to Supabase:", supabase)
        return supabase

    @staticmethod
    def run_video(code_str: str, quality: str = "l", preview: bool = True):
        # 1. Strip Markdown fences and non-breaking spaces
        clean = re.sub(r"^```python\s*|^```\s*", "", code_str.strip())
        clean = re.sub(r"```$", "", clean).strip().replace("\xa0", " ")

        # 2. Fix Code(...) argument incompatibilities1
        clean = re.sub(r"\bCode\(\s*code\s*=", "Code(code_string=", clean)
        clean = re.sub(
            r",\s*(?:code_)?style\s*=\s*['\"][^'\"]*['\"]",
            "",
            clean,
        )
        clean = re.sub(
            r"(?:code_)?style\s*=\s*['\"][^'\"]*['\"],\s*",
            "",
            clean,
        )
        clean = re.sub(
            r",\s*font(?:_name)?\s*=\s*['\"][^'\"]*['\"]",
            "",
            clean,
        )
        clean = re.sub(
            r"font(?:_name)?\s*=\s*['\"][^'\"]*['\"],\s*",
            "",
            clean,
        )

        # 3. Replace VGroup(*self.mobjects) with Group(*self.mobjects)
        clean = re.sub(
            r"VGroup\(\s*\*\s*\[([^\]]*self\.mobjects[^\]]*)\]\s*\)",
            r"Group(*[\1])",
            clean,
        )

        # 4. Inject compatibility helpers and responsive text sizing
        fallbacks = (
            "# Auto-injected compatibility helpers\n"
            "try:\n"
            "    ORANGE_E\n"
            "except NameError:\n"
            "    ORANGE_E = interpolate_color(ORANGE, BLACK, 0.5)\n"
            "try:\n"
            "    ORANGE_D\n"
            "except NameError:\n"
            "    ORANGE_D = interpolate_color(ORANGE, BLACK, 0.25)\n"
            "try:\n"
            "    PURPLE_E\n"
            "except NameError:\n"
            "    PURPLE_E = interpolate_color(PURPLE, BLACK, 0.5)\n"
            "try:\n"
            "    LIGHT_PURPLE\n"
            "except NameError:\n"
            "    LIGHT_PURPLE = interpolate_color(PURPLE, WHITE, 0.5)\n\n"
            "class BulletedList(VGroup):\n"
            "    def __init__(self, *items, font_size=28, buff=0.4, **kwargs):\n"
            "        dots_and_text = []\n"
            "        for item in items:\n"
            "            dot = Dot()\n"
            "            txt = Text(\n"
            "                str(item),\n"
            "                font_size=font_size,\n"
            "                **{\n"
            "                    key: value\n"
            "                    for key, value in kwargs.items()\n"
            "                    if key in ['color']\n"
            "                },\n"
            "            )\n"
            "            row = VGroup(dot, txt).arrange(RIGHT, buff=0.2)\n"
            "            dots_and_text.append(row)\n"
            "        super().__init__(*dots_and_text)\n"
            "        self.arrange(DOWN, aligned_edge=LEFT, buff=buff)\n"
            "\n"
            "_OriginalText = Text\n"
            "\n"
            "class _SafeText(_OriginalText):\n"
            "    def __init__(self, *args, **kwargs):\n"
            "        super().__init__(*args, **kwargs)\n"
            "\n"
            "        # Leave one unit of margin on every side of the active frame.\n"
            "        max_width = max(config.frame_width - 1.0, 1.0)\n"
            "        max_height = max(config.frame_height - 1.0, 1.0)\n"
            "\n"
            "        if self.width > max_width:\n"
            "            self.scale_to_fit_width(max_width)\n"
            "\n"
            "        if self.height > max_height:\n"
            "            self.scale_to_fit_height(max_height)\n"
            "\n"
            "Text = _SafeText\n"
        )

        if "from manim import *" in clean:
            clean = clean.replace(
                "from manim import *",
                f"from manim import *\n\n{fallbacks}\n",
                1,
            )
        else:
            clean = f"from manim import *\n\n{fallbacks}\n\n{clean}"

        # 5. Detect the generated Scene class
        match = re.search(
            r"class\s+([A-Za-z0-9_]+)\s*\(\s*Scene\s*\):",
            clean,
        )

        if not match:
            print("\033[91mError:\033[0m Couldn't find a Scene class.")
            return

        scene_name = match.group(1)
        output_folder = os.path.abspath("videos")
        os.makedirs(output_folder, exist_ok=True)

        with tempfile.TemporaryDirectory() as tmp_dir:
            script_path = os.path.join(tmp_dir, "scene.py")
            media_path = os.path.join(tmp_dir, "media")

            with open(script_path, "w", encoding="utf-8") as file:
                file.write(clean)

            command = [
                "manim",
                f"-q{quality}",
                "--media_dir",
                media_path,
                script_path,
                scene_name,
            ]

            print(f"\033[94mRendering {scene_name}...\033[0m")

            result = standard_subprocess.run(
                command,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                error_output = result.stderr or result.stdout
                print(f"\033[91mManim render failed:\033[0m\n{error_output}")
                return

            temp_video = None

            for root, _, files in os.walk(media_path):
                for file_name in files:
                    if file_name.endswith(".mp4"):
                        temp_video = os.path.join(root, file_name)
                        break

                if temp_video:
                    break

            if not temp_video:
                print("\033[91mError:\033[0m No video file was generated.")
                return

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            target_name = f"{scene_name}_{timestamp}.mp4"
            saved_video_path = os.path.join(output_folder, target_name)

            shutil.copy2(temp_video, saved_video_path)

            print(f"\033[92mVideo saved to:\033[0m {saved_video_path}")

        print("\033[90mCleaned up intermediate build cache.\033[0m")

        if preview:
            print("\033[94mOpening video...\033[0m")
            os.startfile(saved_video_path)

    @staticmethod
    def extract_json_object(text):
        # Prefer a ```json ... ``` fenced block anywhere in the text
        fence_match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        if fence_match:
            return fence_match.group(1)
        fence_match = re.search(r"```\s*(\{.*?\})\s*```", text, re.DOTALL)
        if fence_match:
            return fence_match.group(1)
        # Fall back to the first { ... last } in the text
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start:end + 1]
        return text

    @staticmethod
    def see():
        #Write all the folders and PDFs inside the "information\\CSO" folder, at any depth
        for root, dirs, files in os.walk("information\\CSO"):
            for d in dirs:
                print(f"Folder: {d}")
            for f in files:
                if f.endswith(".pdf"):
                    print(f"PDF: {f}")
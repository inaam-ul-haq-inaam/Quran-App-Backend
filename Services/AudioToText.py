# import whisper
# import os
# import time 
# from Services.romanUrdu import WHISPER_PROMPT

# print("Loading Whisper Model...")
# model = whisper.load_model("small")
# print("Whisper Model Loaded!")

# def transcribe_audio(file_path: str) -> str:
#     try:
#             # ⏱️ START TIMER
#         start_time = time.time()
    
#         result = model.transcribe(
#             file_path,
#             fp16=False,     
#             language="en",  
#             initial_prompt=WHISPER_PROMPT
#         )
        
#         # 👇 1. Raw Text Nikalo
#         raw_text = result.get("text", "")

#         # 🛠️ FIX: Agar 'text' List hai (e.g. ['hello', 'world']), to usay String banao
#         if isinstance(raw_text, list):
#             raw_text = " ".join(str(x) for x in raw_text)

#         # ⏱️ END TIMER
#         end_time = time.time()
#         total_time = end_time - start_time
#    # 📊 Print Statistics
#         print(f"------------------------------------------------")
#         print(f"⚡ Process Time:  {total_time:.2f} seconds")
#         print(f"------------------------------------------------")

#         # 🛠️ FIX: Agar text None hai to empty string bana do
#         if not raw_text:
#             return ""

#         # Ab ye pakka String hai, to error nahi ayega
#         return str(raw_text).strip().lower()

#     except Exception as e:
#         print(f"❌ Whisper Error: {e}")
#         return ""

# # from faster_whisper import WhisperModel
# # import os
# # import time  # 👈 Import Time module
# # from Services.romanUrdu import WHISPER_PROMPT

# # # 🚀 CONFIGURATION
# # # device="cpu" aur compute_type="int8" ka matlab hai CPU par tez chalna.
# # print("Loading Faster Whisper Model (Tiny)...")
# # model = WhisperModel("tiny", device="cpu", compute_type="int8")
# # print("✅ Faster Whisper Model Loaded!")

# # def transcribe_audio(file_path: str) -> str:
# #     # ⏱️ START TIMER
# #     start_time = time.time()
    
# #     try:
# #         # ⚡ Transcribe Call
# #         segments, info = model.transcribe(
# #             file_path,
# #             beam_size=1,             
# #             language="en",           
# #             initial_prompt=WHISPER_PROMPT, 
# #             vad_filter=True          
# #         )

# #         # 👇 Asal processing yahan hoti hai jab hum segments par loop chalate hain
# #         text_list = [segment.text for segment in segments]
# #         final_text = " ".join(text_list)

# #         # ⏱️ END TIMER
# #         end_time = time.time()
# #         total_time = end_time - start_time
        
# #         # 📊 Print Statistics
# #         print(f"------------------------------------------------")
# #         print(f"🎵 Audio Length:  {info.duration:.2f} seconds")
# #         print(f"⚡ Process Time:  {total_time:.2f} seconds")
# #         print(f"🚀 Speed Factor:  {info.duration / total_time:.1f}x real-time")
# #         print(f"📝 Result:        '{final_text.strip()}'")
# #         print(f"------------------------------------------------")

# #         # 🛠️ FIX: Agar text khali hai
# #         if not final_text:
# #             return ""

# #         return final_text.strip().lower()

# #     except Exception as e:
# #         print(f"❌ Whisper Error: {e}")
# #         return ""

from faster_whisper import WhisperModel
import time
from Services.romanUrdu import WHISPER_PROMPT

# 🚀 CONFIGURATION UPDATED
# 1. 'int8' ki jagah 'int8_float32' use karein. Ye CPU k liye best hybrid mode hai.
#    Agar ye bhi slow ho to 'float32' try karein.
# 2. cpu_threads=4 set karein taake CPU choke na ho.

print("Loading Faster Whisper Model (Tiny)...")

# 👇 CHANGE HERE: compute_type="int8_float32" (More stable for Windows/CPU)
model = WhisperModel("tiny", device="cpu", compute_type="float32", cpu_threads=1)

print("✅ Faster Whisper Model Loaded!")

def transcribe_audio(file_path: str) -> str:
    # ⏱️ START TIMER
    start_time = time.time()
    
    try:
        # ⚡ Transcribe Call
        segments, info = model.transcribe(
            file_path,
            beam_size=1,             # Fastest Search
            language="en",           # Language Fixed
            initial_prompt=WHISPER_PROMPT, 
            vad_filter=False         # ⚠️ VAD ko False karein (Sometimes VAD takes 2-3 seconds extra)
        )

        # Process Segments
        text_list = [segment.text for segment in segments]
        final_text = " ".join(text_list)

        # ⏱️ END TIMER
        end_time = time.time()
        total_time = end_time - start_time
        
        # 📊 Print Statistics
        print(f"------------------------------------------------")
        print(f"🎵 Audio Length:  {info.duration:.2f} seconds")
        print(f"⚡ Process Time:  {total_time:.2f} seconds")  # Isay < 2s hona chahiye
        print(f"🚀 Speed Factor:  {info.duration / (total_time + 0.001):.1f}x real-time")
        print(f"📝 Result:        '{final_text.strip()}'")
        print(f"------------------------------------------------")

        if not final_text:
            return ""

        return final_text.strip().lower()

    except Exception as e:
        print(f"❌ Whisper Error: {e}")
        return ""
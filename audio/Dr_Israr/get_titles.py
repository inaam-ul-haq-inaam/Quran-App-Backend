import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3

path = '.'  # Agar script audio folder ke andar hai
files = [f for f in os.listdir(path) if f.endswith('.mp3')]

print("BayanID | Title | Filename")
print("-" * 50)

for index, file in enumerate(files, start=1):
    try:
        audio = ID3(file)
        # 'TIT2' ka matlab hota hai Title tag
        title = audio.get('TIT2').text[0] if audio.get('TIT2') else "No Title Found"
    except Exception:
        title = "Error Reading Tag"
    
    print(f"{index} | {title} | {file}")
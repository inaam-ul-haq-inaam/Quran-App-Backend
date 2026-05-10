# token_creator.py - Complete Voice Command Token Creator
# Features: 
#   1. Quran Play (Full Surah, Single Ayat, Range)
#   2. Chain Creation (Create, Select, Add, Save, etc.)
#   3. Chain Play
#   4. Bookmark (Surah, Ayat, Range)
#   5. Bayan Play (with First, Second, Third... support)
#   6. Player Controls (Play, Pause, Stop, Resume, Next, Previous)

import re
from typing import Any, Dict, Union, List

# Import from data.py (single source of truth)
from Services.data import (
    normalize_text,
    COMMANDS,
    BAYAN_INDEX_MAP,
    PLAYER_COMMANDS,
    SKIP_ACTIONS
)
from Services.spellCheck import find_surah_id 


def create_command_token(text: Union[str, List[str]]) -> Dict[str, Any]:
    """
    Main function to convert voice text to command token
    Returns a dictionary with player action and all necessary data
    """
    
    # ============================================================
    # 1️⃣ INPUT NORMALIZATION
    # ============================================================
    
    if isinstance(text, list):
        text = " ".join(str(x) for x in text)

    if not text:
        text = ""

    text = str(text).strip().lower()
    
    # Normalize text (handles spelling mistakes: aayat→ayat, bayaan→bayan, etc.)
    original_text = text
    text = normalize_text(text)
    
    if original_text != text:
        print(f"📝 Text normalized: '{original_text}' → '{text}'")

    # Response structure
    response: Dict[str, Any] = {
        "player": None,      # Action to perform (play, pause, etc.)
        "type": "surah",     # Type: surah, chain, bookmark, bayan
        "surah": None,       # Surah ID
        "from": None,        # Starting ayat (for range)
        "to": None,          # Ending ayat (for range)
        "isVoiceMode": True  # Voice command flag
    }


    # ============================================================
    # 2️⃣ CHAIN CREATION COMMANDS (Highest Priority)
    # ============================================================
    
    # 2.1 - Open chain builder screen
    if re.search(r"create\s+chain", text):
        response["player"] = "open_chain_builder"
        response["type"] = "chain"
        return response
    
    # 2.2 - Select surah for chain
    if re.search(r"select\s+surah", text):
        surah_match = re.search(r"surah\s+([a-z]+)", text)
        if surah_match:
            response["player"] = "select_surah"
            response["type"] = "chain"
            response["surahName"] = surah_match.group(1)
            return response
    
    # 2.3 - Select ayat for chain (SINGLE and RANGE)
    if re.search(r"select\s+ayat", text):
        # Check for RANGE first: "select ayat 1 to 8"
        range_match = re.search(r"select\s+ayat\s+(\d+)\s+(?:to|se)\s+(\d+)", text)
        if range_match:
            response["player"] = "select_ayat"
            response["type"] = "chain"
            response["fromAyat"] = int(range_match.group(1))
            response["toAyat"] = int(range_match.group(2))
            print(f"🎯 Range ayat matched: {response['fromAyat']} to {response['toAyat']}")
            return response
        
        # Then check for SINGLE: "select ayat 5"
        single_match = re.search(r"select\s+ayat\s+(\d+)", text)
        if single_match:
            response["player"] = "select_ayat"
            response["type"] = "chain"
            response["fromAyat"] = int(single_match.group(1))
            print(f"🎯 Single ayat matched: {response['fromAyat']}")
            return response
    
    # 2.4 - Add current selection to chain list
    if re.search(r"add\s+to\s+list", text) or re.search(r"add\s+kar", text):
        response["player"] = "add_to_list"
        response["type"] = "chain"
        return response
    
    # 2.5 - Set chain title
    title_match = re.search(r"(?:title|name|set title)\s+(.+?)(?:\s+chain)?$", text)
    if not title_match:
        title_match = re.search(r"naam\s+(.+)", text)
    
    if title_match:
        title = title_match.group(1).strip()
        title = re.sub(r'\s+chain$', '', title)
        if title:
            response["player"] = "set_title"
            response["type"] = "chain"
            response["title"] = title
            return response
    
    # 2.6 - Save chain
    if re.search(r"save\s+chain", text):
        response["player"] = "save_chain"
        response["type"] = "chain"
        return response
    
    # 2.7 - Remove last item from chain
    if re.search(r"remove\s+last", text) or re.search(r"last\s+hatayo", text):
        response["player"] = "remove_last"
        response["type"] = "chain"
        return response
    
    # 2.8 - Clear all items from chain
    if re.search(r"clear\s+all", text) or re.search(r"sab\s+hatayo", text):
        response["player"] = "clear_all"
        response["type"] = "chain"
        return response
    
    # 2.9 - Show current chain list
    if re.search(r"show\s+list", text) or re.search(r"list\s+dikhao", text):
        response["player"] = "show_list"
        response["type"] = "chain"
        return response
    
    # 2.10 - Cancel chain creation
    if re.search(r"cancel\s+chain", text) or re.search(r"chain\s+cancel", text):
        response["player"] = "cancel_chain"
        response["type"] = "chain"
        return response


    # ============================================================
    # 3️⃣ BOOKMARK COMMANDS
    # ============================================================
    
    # 3.1 - Bookmark full surah: "bookmark fatiha"
    surah_bookmark_match = re.search(r"bookmark\s+([a-z]+)(?:\s+ayat)?$", text)
    if surah_bookmark_match and "ayat" not in text:
        surah_name = surah_bookmark_match.group(1)
        response["player"] = "bookmark_surah"
        response["type"] = "bookmark"
        response["surahName"] = surah_name
        return response
    
    # 3.2 - Bookmark specific ayat: "bookmark fatiha ayat 5"
    ayat_bookmark_match = re.search(r"bookmark\s+([a-z]+)\s+ayat\s+(\d+)", text)
    if ayat_bookmark_match:
        surah_name = ayat_bookmark_match.group(1)
        ayat_num = int(ayat_bookmark_match.group(2))
        response["player"] = "bookmark_ayat"
        response["type"] = "bookmark"
        response["surahName"] = surah_name
        response["fromAyat"] = ayat_num
        return response
    
    # 3.3 - Bookmark range: "bookmark fatiha from ayat 1 to 3"
    range_bookmark_match = re.search(r"bookmark\s+([a-z]+)\s+from\s+ayat\s+(\d+)\s+to\s+ayat\s+(\d+)", text)
    if not range_bookmark_match:
        range_bookmark_match = re.search(r"bookmark\s+([a-z]+)\s+ayat\s+(\d+)\s+(?:to|se)\s+(\d+)", text)
    
    if range_bookmark_match:
        surah_name = range_bookmark_match.group(1)
        from_ayat = int(range_bookmark_match.group(2))
        to_ayat = int(range_bookmark_match.group(3))
        response["player"] = "bookmark_range"
        response["type"] = "bookmark"
        response["surahName"] = surah_name
        response["fromAyat"] = from_ayat
        response["toAyat"] = to_ayat
        return response
    
    # 3.4 - Bookmark with custom title: "bookmark fatiha as my favorite"
    title_bookmark = re.search(r"bookmark\s+([a-z]+)\s+as\s+(.+)", text)
    if title_bookmark:
        surah_name = title_bookmark.group(1)
        custom_title = title_bookmark.group(2).strip()
        response["player"] = "bookmark_with_title"
        response["type"] = "bookmark"
        response["surahName"] = surah_name
        response["title"] = custom_title
        return response
    
    # 3.5 - Show bookmarks list
    if re.search(r"(?:show|my)\s+bookmarks", text):
        response["player"] = "show_bookmarks"
        response["type"] = "bookmark"
        return response


    # ============================================================
    # 4️⃣ BAYAN COMMANDS (with First, Second, Third support)
    # ============================================================
    
    # 4.1 - Bayan with index: "play bayan baqarah first"
    bayan_with_index = re.search(r"(?:play|sunao|chalao)\s+bayan\s+([a-z]+)\s+(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|pehla|dosra|tesra|chautha|panchwa)", text)
    
    if not bayan_with_index:
        bayan_with_index = re.search(r"bayan\s+(?:play|sunao|chalao)\s+([a-z]+)\s+(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|pehla|dosra|tesra|chautha|panchwa)", text)
    
    if bayan_with_index:
        surah_name = bayan_with_index.group(1)
        index_word = bayan_with_index.group(2).lower()
        bayan_index = BAYAN_INDEX_MAP.get(index_word, 0)
        surah_id = find_surah_id(surah_name)
        
        if surah_id:
            response["player"] = "play"
            response["type"] = "bayan"
            response["surahId"] = surah_id
            response["bayanIndex"] = bayan_index
            print(f"🎤 Bayan with index: {surah_name} index {bayan_index}")
            return response
        else:
            print(f"❌ Surah not found: {surah_name}")
            return response
    
    # 4.2 - Simple bayan (first by default)
    bayan_match = re.search(r"(?:play|sunao|chalao)\s+bayan\s+([a-z]+)", text)
    if not bayan_match:
        bayan_match = re.search(r"bayan\s+(?:play|sunao|chalao)\s+([a-z]+)", text)
    
    if bayan_match:
        surah_name = bayan_match.group(1)
        surah_id = find_surah_id(surah_name)
        
        if surah_id:
            response["player"] = "play"
            response["type"] = "bayan"
            response["surahId"] = surah_id
            response["bayanIndex"] = 0
            print(f"🎤 Bayan (first/default): {surah_name}")
            return response
        else:
            print(f"❌ Surah not found: {surah_name}")
            return response
    
    # 4.3 - Introduction bayan
    if re.search(r"introduction\s+to\s+quran", text) or re.search(r"intro\s+bayan", text):
        response["player"] = "play"
        response["type"] = "bayan"
        response["surahId"] = 0
        response["bayanIndex"] = 0
        print("🎤 Introduction bayan")
        return response


    # ============================================================
    # 5️⃣ CHAIN PLAY COMMANDS
    # ============================================================
    
    # 5.1 - "play chain daily"
    play_chain_match = re.search(r"(?:play|sunao|chalao)\s+chain\s+(\w+(?:\s+\w+)?)", text)
    if play_chain_match:
        chain_name = play_chain_match.group(1).strip()
        response["player"] = "play_chain"
        response["type"] = "chain"
        response["chainName"] = chain_name
        return response
    
    # 5.2 - "daily chain play"
    alt_match = re.search(r"(\w+(?:\s+\w+)?)\s+chain\s+(?:play|sunao|chalao)", text)
    if alt_match:
        chain_name = alt_match.group(1).strip()
        response["player"] = "play_chain"
        response["type"] = "chain"
        response["chainName"] = chain_name
        return response


    # ============================================================
    # 6️⃣ QURAN PLAYBACK (Full Surah, Single Ayat, Range)
    # ============================================================
    
    # Pattern 1: "play fatiha from ayat 2" → Ayat 2 se end tak
    pattern1 = re.search(r"play\s+([a-z]+)\s+from\s+ayat\s+(\d+)", text)
    if pattern1:
        surah_name = pattern1.group(1)
        from_ayat = int(pattern1.group(2))
        surah_id = find_surah_id(surah_name)
        
        if surah_id:
            response["player"] = "play"
            response["type"] = "surah"
            response["surah"] = surah_id
            response["from"] = from_ayat
            response["to"] = None  # None means till end
            print(f"🎯 Quran Range: {surah_name} from ayat {from_ayat} to end")
            return response
    
    # Pattern 2: "play fatiha from ayat 1 to 5" → Specific range
    pattern2 = re.search(r"play\s+([a-z]+)\s+from\s+ayat\s+(\d+)\s+to\s+ayat\s+(\d+)", text)
    if not pattern2:
        pattern2 = re.search(r"play\s+([a-z]+)\s+ayat\s+(\d+)\s+to\s+(\d+)", text)
    
    if pattern2:
        surah_name = pattern2.group(1)
        from_ayat = int(pattern2.group(2))
        to_ayat = int(pattern2.group(3))
        surah_id = find_surah_id(surah_name)
        
        if surah_id:
            response["player"] = "play"
            response["type"] = "surah"
            response["surah"] = surah_id
            response["from"] = from_ayat
            response["to"] = to_ayat
            print(f"🎯 Quran Range: {surah_name} from ayat {from_ayat} to {to_ayat}")
            return response
    
    # Pattern 3: "play fatiha ayat 3" → Single ayat
    pattern3 = re.search(r"play\s+([a-z]+)\s+ayat\s+(\d+)", text)
    if pattern3:
        surah_name = pattern3.group(1)
        ayat_num = int(pattern3.group(2))
        surah_id = find_surah_id(surah_name)
        
        if surah_id:
            response["player"] = "play"
            response["type"] = "surah"
            response["surah"] = surah_id
            response["from"] = ayat_num
            response["to"] = ayat_num
            print(f"🎯 Quran Single Ayat: {surah_name} ayat {ayat_num}")
            return response
    
    # Pattern 4: "play fatiha to ayat 5" → Ayat 1 se 5 tak
    pattern4 = re.search(r"play\s+([a-z]+)\s+to\s+ayat\s+(\d+)", text)
    if not pattern4:
        pattern4 = re.search(r"play\s+([a-z]+)\s+tak\s+ayat\s+(\d+)", text)
    
    if pattern4:
        surah_name = pattern4.group(1)
        to_ayat = int(pattern4.group(2))
        surah_id = find_surah_id(surah_name)
        
        if surah_id:
            response["player"] = "play"
            response["type"] = "surah"
            response["surah"] = surah_id
            response["from"] = 1
            response["to"] = to_ayat
            print(f"🎯 Quran Range: {surah_name} from start to ayat {to_ayat}")
            return response
    
    # Pattern 5: "play fatiha" → Full surah
    pattern5 = re.search(r"play\s+([a-z]+)$", text)
    if pattern5:
        surah_name = pattern5.group(1)
        surah_id = find_surah_id(surah_name)
        
        if surah_id:
            response["player"] = "play"
            response["type"] = "surah"
            response["surah"] = surah_id
            response["from"] = 1
            response["to"] = None  # None means full surah
            print(f"🎯 Quran Full Surah: {surah_name}")
            return response


    # ============================================================
    # 7️⃣ STANDARD PLAYER CONTROLS
    # ============================================================

    if response["player"] is None:
        for action, keywords in COMMANDS.items():
            if action in PLAYER_COMMANDS:
                pattern = r"\b(" + "|".join(map(re.escape, keywords)) + r")\b"
                if re.search(pattern, text):
                    response["player"] = action
                    print(f"🎯 Matched command: {action}")
                    break


    # ============================================================
    # 8️⃣ SURAH DETECTION (Fallback)
    # ============================================================
    
    if response["player"] not in SKIP_ACTIONS and response["player"] is None:
        text_for_surah = text
        
        # Remove command words
        for action, keywords in COMMANDS.items():
            if action in PLAYER_COMMANDS:
                for word in keywords:
                    text_for_surah = re.sub(rf"\b{re.escape(word)}\b", "", text_for_surah)
        
        # Remove common words
        remove_words = ["bayan", "tafseer", "from", "to", "se", "tak", "ayat", "verse", "aayat", "ayah"]
        for word in remove_words:
            text_for_surah = re.sub(rf"\b{re.escape(word)}\b", "", text_for_surah)
        
        # Remove numbers
        text_for_surah = re.sub(r"\b\d+\b", "", text_for_surah)
        clean_text = text_for_surah.strip()

        if len(clean_text) >= 3:
            surah_id = find_surah_id(clean_text)
            if surah_id:
                response["player"] = "play"
                response["type"] = "surah"
                response["surah"] = surah_id
                response["from"] = 1
                response["to"] = None
                print(f"🎯 Quran detected via fallback: {clean_text}")


    # ============================================================
    # 9️⃣ NUMBERS EXTRACTION (for range)
    # ============================================================
    
    numbers = [int(n) for n in re.findall(r"\b\d+\b", text)]
    if response["player"] == "jump" and len(numbers) >= 1:
        response["ayatNumber"] = numbers[0]
    elif len(numbers) >= 1 and not response.get("from"):
        response["from"] = numbers[0]
    if len(numbers) >= 2 and not response.get("to"):
        response["to"] = numbers[1]


    # ============================================================
    # 🔟 FINAL RETURN
    # ============================================================
    
    return response
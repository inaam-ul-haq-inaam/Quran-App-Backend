# token_creator.py - COMPLETE WORKING CODE
# Features: Chain Creation, Chain Play, Bookmark, Range Playback, Next/Previous/Play/Pause/Stop/Resume

import re
from typing import Any, Dict, Union, List
from Services.spellCheck import find_surah_id

def create_command_token(text: Union[str, List[str]]) -> Dict[str, Any]:

    if isinstance(text, list):
        text = " ".join(str(x) for x in text)

    if not text:
        text = ""

    text = str(text).strip().lower()

    response: Dict[str, Any] = {
        "player": None,
        "type": "surah",
        "surah": None,
        "from": None,
        "to": None,
        "isVoiceMode": True
    }

    # ============================================================
    # SECTION 1: CHAIN CREATION COMMANDS (Highest Priority)
    # ============================================================
    
    # 1.1 - Open chain builder
    if re.search(r"create\s+chain", text):
        response["player"] = "open_chain_builder"
        response["type"] = "chain"
        return response
    
    # 1.2 - Select surah for chain
    if re.search(r"select\s+surah", text):
        surah_match = re.search(r"surah\s+([a-z]+)", text)
        if surah_match:
            response["player"] = "select_surah"
            response["type"] = "chain"
            response["surahName"] = surah_match.group(1)
            return response
    
    # 1.3 - Select ayat for chain (SINGLE and RANGE)
    if re.search(r"select\s+ayat", text):
        # First check for RANGE: "select ayat 1 to 8" or "select ayat 1 se 8"
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
    
    # 1.4 - Add to list
    if re.search(r"add\s+to\s+list", text) or re.search(r"add\s+kar", text):
        response["player"] = "add_to_list"
        response["type"] = "chain"
        return response
    
    # 1.5 - Set title
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
    
    # 1.6 - Save chain
    if re.search(r"save\s+chain", text):
        response["player"] = "save_chain"
        response["type"] = "chain"
        return response
    
    # 1.7 - Remove last
    if re.search(r"remove\s+last", text) or re.search(r"last\s+hatayo", text):
        response["player"] = "remove_last"
        response["type"] = "chain"
        return response
    
    # 1.8 - Clear all
    if re.search(r"clear\s+all", text) or re.search(r"sab\s+hatayo", text):
        response["player"] = "clear_all"
        response["type"] = "chain"
        return response
    
    # 1.9 - Show list
    if re.search(r"show\s+list", text) or re.search(r"list\s+dikhao", text):
        response["player"] = "show_list"
        response["type"] = "chain"
        return response
    
    # 1.10 - Cancel chain
    if re.search(r"cancel\s+chain", text) or re.search(r"chain\s+cancel", text):
        response["player"] = "cancel_chain"
        response["type"] = "chain"
        return response

    # ============================================================
    # SECTION 2: BOOKMARK COMMANDS
    # ============================================================
    
    # 2.1 - Bookmark full surah
    surah_bookmark_match = re.search(r"bookmark\s+([a-z]+)(?:\s+ayat)?$", text)
    if surah_bookmark_match and "ayat" not in text:
        surah_name = surah_bookmark_match.group(1)
        response["player"] = "bookmark_surah"
        response["type"] = "bookmark"
        response["surahName"] = surah_name
        return response
    
    # 2.2 - Bookmark specific ayat
    ayat_bookmark_match = re.search(r"bookmark\s+([a-z]+)\s+ayat\s+(\d+)", text)
    if ayat_bookmark_match:
        surah_name = ayat_bookmark_match.group(1)
        ayat_num = int(ayat_bookmark_match.group(2))
        response["player"] = "bookmark_ayat"
        response["type"] = "bookmark"
        response["surahName"] = surah_name
        response["fromAyat"] = ayat_num
        return response
    
    # 2.3 - Bookmark range
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
    
    # 2.4 - Bookmark with custom title
    title_bookmark = re.search(r"bookmark\s+([a-z]+)\s+as\s+(.+)", text)
    if title_bookmark:
        surah_name = title_bookmark.group(1)
        custom_title = title_bookmark.group(2).strip()
        response["player"] = "bookmark_with_title"
        response["type"] = "bookmark"
        response["surahName"] = surah_name
        response["title"] = custom_title
        return response
    
    # 2.5 - Show bookmarks list
    if re.search(r"(?:show|my)\s+bookmarks", text):
        response["player"] = "show_bookmarks"
        response["type"] = "bookmark"
        return response
    
        # ============================================================
    # SECTION 3: BAYAN DETECTION (FIXED - No variable error)
    # ============================================================
    
    # Pattern 1: "play bayan baqarah first" or "play bayan baqarah second"
    bayan_with_index = re.search(r"(?:play|sunao|chalao)\s+bayan\s+([a-z]+)\s+(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|pehla|dosra|tesra|chautha|panchwa)", text)
    
    if not bayan_with_index:
        bayan_with_index = re.search(r"bayan\s+(?:play|sunao|chalao)\s+([a-z]+)\s+(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|pehla|dosra|tesra|chautha|panchwa)", text)
    
    if bayan_with_index:
        surah_name = bayan_with_index.group(1)
        index_word = bayan_with_index.group(2).lower()
        
        # Index mapping
        index_map = {
            "first": 0, "pehla": 0,
            "second": 1, "dosra": 1,
            "third": 2, "tesra": 2,
            "fourth": 3, "chautha": 3,
            "fifth": 4, "panchwa": 4,
            "sixth": 5,
            "seventh": 6,
            "eighth": 7,
            "ninth": 8,
            "tenth": 9,
        }
        
        from Services.spellCheck import find_surah_id
        surah_id = find_surah_id(surah_name)
        bayan_index = index_map.get(index_word, 0)
        
        if surah_id:
            response["player"] = "play"
            response["type"] = "bayan"
            response["surahId"] = surah_id
            response["bayanIndex"] = bayan_index
            print(f"🎤 Bayan with index: {surah_name} index {bayan_index}")
            return response
        else:
            print(f"❌ Surah not found: {surah_name}")
            response["player"] = "play"
            response["type"] = "bayan"
            response["surahId"] = None
            return response
    
    # Pattern 2: Simple bayan "play bayan baqarah"
    bayan_match = re.search(r"(?:play|sunao|chalao)\s+bayan\s+([a-z]+)", text)
    if not bayan_match:
        bayan_match = re.search(r"bayan\s+(?:play|sunao|chalao)\s+([a-z]+)", text)
    
    if bayan_match:
        surah_name = bayan_match.group(1)
        from Services.spellCheck import find_surah_id
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
            response["player"] = "play"
            response["type"] = "bayan"
            response["surahId"] = None
            return response
    
    # Pattern 3: Introduction bayan
    if re.search(r"introduction\s+to\s+quran", text) or re.search(r"intro\s+bayan", text):
        response["player"] = "play"
        response["type"] = "bayan"
        response["surahId"] = 0
        response["bayanIndex"] = 0
        print("🎤 Introduction bayan")
        return response
    
    # ============================================================
    # SECTION 4: PLAY CHAIN (Explicit "chain" word required)
    # ============================================================
    
    # Pattern 1: "play chain daily", "play chain night"
    play_chain_match = re.search(r"(?:play|sunao|chalao)\s+chain\s+(\w+(?:\s+\w+)?)", text)
    if play_chain_match:
        chain_name = play_chain_match.group(1).strip()
        response["player"] = "play_chain"
        response["type"] = "chain"
        response["chainName"] = chain_name
        return response
    
    # Pattern 2: "daily chain play"
    alt_match = re.search(r"(\w+(?:\s+\w+)?)\s+chain\s+(?:play|sunao|chalao)", text)
    if alt_match:
        chain_name = alt_match.group(1).strip()
        response["player"] = "play_chain"
        response["type"] = "chain"
        response["chainName"] = chain_name
        return response

    # ============================================================
    # SECTION 5: RANGE PLAYBACK (4 PATTERNS)
    # ============================================================
    
    from Services.spellCheck import find_surah_id
    
    # Pattern 1: "play fatiha from ayat 2" → 2 se end tak
    pattern1 = re.search(r"play\s+([a-z]+)\s+from\s+ayat\s+(\d+)", text)
    if pattern1:
        surah_name = pattern1.group(1)
        from_ayat = int(pattern1.group(2))
        surah_id = find_surah_id(surah_name)
        
        if surah_id:
            response["player"] = "play_range"
            response["type"] = "surah"
            response["surah"] = surah_id
            response["from"] = from_ayat
            response["to"] = None
            return response
    
    # Pattern 2: "play fatiha from ayat 1 to 5" → specific range
    pattern2 = re.search(r"play\s+([a-z]+)\s+from\s+ayat\s+(\d+)\s+to\s+ayat\s+(\d+)", text)
    if not pattern2:
        pattern2 = re.search(r"play\s+([a-z]+)\s+ayat\s+(\d+)\s+to\s+(\d+)", text)
    
    if pattern2:
        surah_name = pattern2.group(1)
        from_ayat = int(pattern2.group(2))
        to_ayat = int(pattern2.group(3))
        surah_id = find_surah_id(surah_name)
        
        if surah_id:
            response["player"] = "play_range"
            response["type"] = "surah"
            response["surah"] = surah_id
            response["from"] = from_ayat
            response["to"] = to_ayat
            return response
    
    # Pattern 3: "play fatiha ayat 3" → single ayat
    pattern3 = re.search(r"play\s+([a-z]+)\s+ayat\s+(\d+)", text)
    if pattern3:
        surah_name = pattern3.group(1)
        ayat_num = int(pattern3.group(2))
        surah_id = find_surah_id(surah_name)
        
        if surah_id:
            response["player"] = "play_range"
            response["type"] = "surah"
            response["surah"] = surah_id
            response["from"] = ayat_num
            response["to"] = ayat_num
            return response
    
    # Pattern 4: "play fatiha to ayat 5" → 1 se 5 tak
    pattern4 = re.search(r"play\s+([a-z]+)\s+to\s+ayat\s+(\d+)", text)
    if not pattern4:
        pattern4 = re.search(r"play\s+([a-z]+)\s+tak\s+ayat\s+(\d+)", text)
    
    if pattern4:
        surah_name = pattern4.group(1)
        to_ayat = int(pattern4.group(2))
        surah_id = find_surah_id(surah_name)
        
        if surah_id:
            response["player"] = "play_range"
            response["type"] = "surah"
            response["surah"] = surah_id
            response["from"] = 1
            response["to"] = to_ayat
            return response

    # ============================================================
    # SECTION 6: STANDARD PLAYER COMMANDS (FIXED)
    # ============================================================
    
    COMMANDS = {
        "play": ["play", "chalao", "sunao", "laga", "start", "open"],
        "pause": ["pause", "ruko", "band", "wait", "thahro", "pass", "roko"],
        "stop": ["stop", "band kar", "rok do", "khatam", "close"],
        "resume": ["resume", "continue", "agey", "aage se", "phir se", "dobara"],
        "next": ["next", "agla", "age", "aage", "skip", "forward", "agla ayat", "next ayat"],
        "previous": ["previous", "pichla", "peeche", "back", "wapis", "return", "pichla ayat", "back ayat"],
        "jump": ["jump", "go to", "goto", "jao", "chalo"]
    }

    if response["player"] is None:
        for action, keywords in COMMANDS.items():
            pattern = r"\b(" + "|".join(map(re.escape, keywords)) + r")\b"
            if re.search(pattern, text):
                response["player"] = action
                print(f"🎯 Matched command: {action} for text: {text}")
                break

    # ============================================================
    # SECTION 7: SURAH DETECTION
    # ============================================================
    
    if response["player"] not in ["select_surah", "select_ayat", "add_to_list", "set_title", "save_chain", "remove_last", "clear_all", "show_list", "cancel_chain", "open_chain_builder", "bookmark_surah", "bookmark_ayat", "bookmark_range", "bookmark_with_title", "show_bookmarks", "play_range", "play_chain", "next", "previous", "pause", "resume", "stop", "jump"]:
        
        text_for_surah = text
        for keywords in COMMANDS.values():
            for word in keywords:
                text_for_surah = re.sub(rf"\b{re.escape(word)}\b", "", text_for_surah)
        
        for word in BAYAN_KEYWORDS:
            text_for_surah = re.sub(rf"\b{re.escape(word)}\b", "", text_for_surah)
        
        range_phrases = ["from", "to", "se", "tak", "ayat", "verse"]
        for phrase in range_phrases:
            text_for_surah = re.sub(rf"\b{re.escape(phrase)}\b", "", text_for_surah)
        
        text_for_surah = re.sub(r"\b\d+\b", "", text_for_surah)
        clean_text = text_for_surah.strip()

        if len(clean_text) >= 3:
            surah_id = find_surah_id(clean_text)
        else:
            surah_id = None

        if surah_id:
            response["surah"] = surah_id
            if response["player"] is None:
                response["player"] = "play"

    # ============================================================
    # SECTION 8: NUMBERS EXTRACTION
    # ============================================================
    
    numbers = [int(n) for n in re.findall(r"\b\d+\b", text)]
    if response["player"] == "jump" and len(numbers) >= 1:
        response["ayatNumber"] = numbers[0]
    elif len(numbers) >= 1 and not response.get("from"):
        response["from"] = numbers[0]
    if len(numbers) >= 2 and not response.get("to"):
        response["to"] = numbers[1]

    return response
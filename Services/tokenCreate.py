# ============================================================================
# token_creator.py - Complete Voice Command Token Creator
# ============================================================================
# Features:
#   1. Quran Play (Full Surah, Single Ayat, Range)
#   2. Chain Creation (Create, Select, Add, Save, Edit, Cancel)
#   3. Chain Play (explicit "chain" word)
#   4. Bookmark (Surah, Ayat, Range, Custom Title)
#   5. Bayan Play (with First, Second, Third… support)
#   6. Player Controls (Play, Pause, Stop, Resume, Next, Previous, Jump)
#   7. Next/Previous Surah Navigation
# ============================================================================

import re
from typing import Any, Dict, Union, List
from database import get_connection
from config import BASE_IP

# Import from data.py (single source of truth)
from Services.data import (
    normalize_text,
    COMMANDS,
    BAYAN_INDEX_MAP,
    PLAYER_COMMANDS,
    SKIP_ACTIONS
)
from Services.spellCheck import find_surah_id



# ============================================================
# HELPER: Get Surah Name from Database
# ============================================================
def _get_surah_name(surah_id: int) -> str:
    """Fetch surah name from database by surah ID"""
    if not surah_id:
        return None
    
    conn = get_connection()
    if conn is None:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT NameArabic FROM surah WHERE SurahID = ?", (surah_id,))
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        print(f"❌ Error fetching surah name: {e}")
        return None
    finally:
        conn.close()


def _add_surah_name(response: dict) -> dict:
    """Add surahName to response if type is 'surah'"""
    if response.get('type') == 'surah' and response.get('surah'):
        surah_name = _get_surah_name(response['surah'])
        if surah_name:
            response['surahName'] = surah_name
    return response


       # ============================================================
       # HELPER: Get Bayan Details by Surah ID and Index
       # ============================================================

def get_Bayan_By_Surah(surah_id: int):
    conn = get_connection()
    if conn is None:
        return {"Bayans": []}
    
    try:
        cursor = conn.cursor()
        
        query = """SELECT 
                    b.BayanID, 
                    b.Title, 
                    b.AudioURL, 
                    b.Duration, 
                    s.Name as ScholarName, 
                    su.NameEnglish as SurahName, 
                    b.StartAyatID, 
                    b.EndAyatID
                FROM Bayan b
                LEFT JOIN Scholar s ON b.ScholarID = s.ScholarID
                LEFT JOIN Surah su ON b.SurahID = su.SurahID
                WHERE b.SurahID = ?
                ORDER BY b.StartAyatID ASC"""
        
        cursor.execute(query, (surah_id,))
        rows = cursor.fetchall()
        
        bayan_list = []
        base_audio_url = f"{BASE_IP}/audio/Dr_Israr/" 

        for row in rows:
            bayan_list.append({
                "BayanID": row[0],
                "Title": row[1],
                "AudioUrl": f"{base_audio_url}{row[2]}",
                "Duration": row[3],
                "ScholarName": row[4],
                "SurahName": row[5],
                "StartAyatID": row[6],
                "EndAyatID": row[7]
            })
        
        return {"Bayans": bayan_list}
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"Bayans": []}
    
    finally:
        conn.close()
        
 
def _get_bayan_details(surah_id: int, bayan_index: int = 0) -> dict:
    """Fetch bayan title and URL by surah ID and index"""
    if not surah_id:
        return {"bayanTitle": None, "bayanUrl": None}
    
    try:
        bayan_data = get_Bayan_By_Surah(surah_id)
        
        if bayan_data and bayan_data.get("Bayans"):
            bayans = bayan_data["Bayans"]
            if bayan_index < len(bayans):
                bayan = bayans[bayan_index]
                return {
                    "bayanTitle": bayan.get("Title"),
                    "bayanUrl": bayan.get("AudioUrl")
                }
        
        return {"bayanTitle": None, "bayanUrl": None}
        
    except Exception as e:
        print(f"❌ Error fetching bayan details: {e}")
        return {"bayanTitle": None, "bayanUrl": None}


def _add_bayan_details(response: dict) -> dict:
    """Add bayanTitle and bayanUrl to response if type is 'bayan'"""
    if response.get('type') == 'bayan' and response.get('surahId'):
        bayan_details = _get_bayan_details(
            response['surahId'], 
            response.get('bayanIndex', 0)
        )
        response['bayanTitle'] = bayan_details.get('bayanTitle')
        response['bayanUrl'] = bayan_details.get('bayanUrl')
        print(f"🎤 Bayan Details: Title={response['bayanTitle']}, URL={response['bayanUrl']}")
    return response




def create_command_token(text: Union[str, List[str]]) -> Dict[str, Any]:
    """
    Main function to convert voice text to command token.
    Returns a dictionary with player action and all necessary data.
    """
    # ------------------------------------------------------------------------
    # 1. INPUT NORMALIZATION
    # ------------------------------------------------------------------------
    if isinstance(text, list):
        text = " ".join(str(x) for x in text)

    if not text:
        text = ""

    text = str(text).strip().lower()

    original_text = text
    text = normalize_text(text)                     # handles spelling, number words, etc.
    if original_text != text:
        print(f"📝 Text normalized: '{original_text}' → '{text}'")

    response: Dict[str, Any] = {
        "player": None,       # Action to perform
        "type": "surah",      # surah / chain / bookmark / bayan
        "surah": None,
        "surahName":None,
        "from": None,
        "to": None,
        "bayanTitle":None,
        "bayanUrl":None,
        "isVoiceMode": True
    }

    # ------------------------------------------------------------------------
    # 2. SELECT COMMANDS (HIGHEST PRIORITY – for chain building)
    # ------------------------------------------------------------------------
    # 2.1 "select surah ..."
    if re.search(r"select\s+surah", text) or re.search(r"surah\s+select", text):
        surah_match = re.search(r"(?:select\s+)?surah\s+([a-z]+)", text)
        if surah_match:
            response["player"] = "select_surah"
            response["type"] = "chain"
            response["surahName"] = surah_match.group(1)
            print(f"🎯 Select surah: {response['surahName']}")
            return response

    # 2.2 simple "select fatiha"
    simple_select_match = re.search(r"select\s+([a-z]+)$", text)
    if simple_select_match:
        surah_name = simple_select_match.group(1)
        if find_surah_id(surah_name):
            response["player"] = "select_surah"
            response["type"] = "chain"
            response["surahName"] = surah_name
            print(f"🎯 Select surah (simple): {surah_name}")
            return response

    # 2.3 select ayat (range or single)
    if re.search(r"select\s+ayat", text) or re.search(r"ayat\s+select", text):
        # range first
        range_match = re.search(r"(?:select\s+)?ayat\s+(\d+)\s+(?:to|se)\s+(\d+)", text)
        if range_match:
            response["player"] = "select_ayat"
            response["type"] = "chain"
            response["fromAyat"] = int(range_match.group(1))
            response["toAyat"] = int(range_match.group(2))
            print(f"🎯 Select range ayat: {response['fromAyat']} → {response['toAyat']}")
            return response

        # single ayat
        single_match = re.search(r"(?:select\s+)?ayat\s+(\d+)", text)
        if single_match:
            response["player"] = "select_ayat"
            response["type"] = "chain"
            response["fromAyat"] = int(single_match.group(1))
            print(f"🎯 Select single ayat: {response['fromAyat']}")
            return response

    # ------------------------------------------------------------------------
    # 3. CHAIN CREATION COMMANDS
    # ------------------------------------------------------------------------
    if re.search(r"create\s+chain", text):
        response["player"] = "open_chain_builder"
        response["type"] = "chain"
        return response

    if re.search(r"add\s+to\s+list", text) or re.search(r"add\s+kar", text):
        response["player"] = "add_to_list"
        response["type"] = "chain"
        return response

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

    if re.search(r"save\s+chain", text):
        response["player"] = "save_chain"
        response["type"] = "chain"
        return response

    if re.search(r"remove\s+last", text) or re.search(r"last\s+hatayo", text):
        response["player"] = "remove_last"
        response["type"] = "chain"
        return response

    if re.search(r"clear\s+all", text) or re.search(r"sab\s+hatayo", text):
        response["player"] = "clear_all"
        response["type"] = "chain"
        return response

    if re.search(r"show\s+list", text) or re.search(r"list\s+dikhao", text):
        response["player"] = "show_list"
        response["type"] = "chain"
        return response

    if re.search(r"cancel\s+chain", text) or re.search(r"chain\s+cancel", text):
        response["player"] = "cancel_chain"
        response["type"] = "chain"
        return response
        
        
        # SECTION: DELETE CHAIN COMMANDS
         # Pattern 1: "delete chain daily"
    delete_chain_match = re.search(r"(?:delete|remove|hatao)\s+chain\s+(\w+(?:\s+\w+)?)", text)
    if delete_chain_match:
        chain_name = delete_chain_match.group(1).strip()
        response["player"] = "delete_chain"
        response["type"] = "chain"
        response["chainName"] = chain_name
        return response

    # Pattern 2: "delete all chains"
    if re.search(r"delete\s+all\s+chains", text) or re.search(r"sab\s+chains\s+hatao", text):
        response["player"] = "delete_all_chains"
        response["type"] = "chain"
        return response

    # ------------------------------------------------------------------------
    # 4. BOOKMARK COMMANDS
    # ------------------------------------------------------------------------
    surah_bookmark_match = re.search(r"bookmark\s+([a-z]+)(?:\s+ayat)?$", text)
    if surah_bookmark_match and "ayat" not in text:
        response["player"] = "bookmark_surah"
        response["type"] = "bookmark"
        response["surahName"] = surah_bookmark_match.group(1)
        return response

    ayat_bookmark_match = re.search(r"bookmark\s+([a-z]+)\s+ayat\s+(\d+)", text)
    if ayat_bookmark_match:
        response["player"] = "bookmark_ayat"
        response["type"] = "bookmark"
        response["surahName"] = ayat_bookmark_match.group(1)
        response["fromAyat"] = int(ayat_bookmark_match.group(2))
        return response

    range_bookmark_match = re.search(
        r"bookmark\s+([a-z]+)\s+from\s+ayat\s+(\d+)\s+to\s+ayat\s+(\d+)", text
    )
    if not range_bookmark_match:
        range_bookmark_match = re.search(
            r"bookmark\s+([a-z]+)\s+ayat\s+(\d+)\s+(?:to|se)\s+(\d+)", text
        )
    if range_bookmark_match:
        response["player"] = "bookmark_range"
        response["type"] = "bookmark"
        response["surahName"] = range_bookmark_match.group(1)
        response["fromAyat"] = int(range_bookmark_match.group(2))
        response["toAyat"] = int(range_bookmark_match.group(3))
        return response

    title_bookmark = re.search(r"bookmark\s+([a-z]+)\s+as\s+(.+)", text)
    if title_bookmark:
        response["player"] = "bookmark_with_title"
        response["type"] = "bookmark"
        response["surahName"] = title_bookmark.group(1)
        response["title"] = title_bookmark.group(2).strip()
        return response

    if re.search(r"(?:show|my)\s+bookmarks", text):
        response["player"] = "show_bookmarks"
        response["type"] = "bookmark"
        return response

    # ------------------------------------------------------------------------
    # 5. BAYAN COMMANDS (with first/second/… index)
    # ------------------------------------------------------------------------
    BAYAN_KEYWORDS = ["bayan", "tafseer", "tafsir", "tarjuma", "explanation", "lecture"]

    # 5.1 bayan with explicit index
    bayan_with_index = re.search(
        r"(?:play|sunao|chalao)\s+bayan\s+([a-z]+)\s+"
        r"(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|"
        r"pehla|dosra|tesra|chautha|panchwa)", text
    )
    if not bayan_with_index:
        bayan_with_index = re.search(
            r"bayan\s+(?:play|sunao|chalao)\s+([a-z]+)\s+"
            r"(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|"
            r"pehla|dosra|tesra|chautha|panchwa)", text
        )
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
            print(f"🎤 Bayan with index: {surah_name} → index {bayan_index}")
            response = _add_bayan_details(response)
            return response
        else:
            print(f"❌ Surah not found: {surah_name}")
            return response

    # 5.2 simple bayan (first by default)
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
            response = _add_bayan_details(response)
            return response
        else:
            print(f"❌ Surah not found: {surah_name}")
            return response

    # 5.3 introduction bayan
    if re.search(r"introduction\s+to\s+quran", text) or re.search(r"intro\s+bayan", text):
        response["player"] = "play"
        response["type"] = "bayan"
        response["surahId"] = 0
        response["bayanIndex"] = 0
        print("🎤 Introduction bayan")
        response = _add_bayan_details(response)
        return response

    # ------------------------------------------------------------------------
    # 6. CHAIN PLAY (explicit "chain" word)
    # ------------------------------------------------------------------------
    play_chain_match = re.search(r"(?:play|sunao|chalao)\s+chain\s+(\w+(?:\s+\w+)?)", text)
    if play_chain_match:
        response["player"] = "play_chain"
        response["type"] = "chain"
        response["chainName"] = play_chain_match.group(1).strip()
        return response

    alt_match = re.search(r"(\w+(?:\s+\w+)?)\s+chain\s+(?:play|sunao|chalao)", text)
    if alt_match:
        response["player"] = "play_chain"
        response["type"] = "chain"
        response["chainName"] = alt_match.group(1).strip()
        return response

    # ------------------------------------------------------------------------
    # 7. QURAN PLAYBACK (full surah / single ayat / range – 5 patterns)
    # ------------------------------------------------------------------------
    # pattern 1: "play fatiha from ayat 2"  → from 2 to end
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
            response["to"] = None
            print(f"🎯 Quran: {surah_name} from ayat {from_ayat} to end")
            response = _add_surah_name(response)
            return response

    # pattern 2: "play fatiha from ayat 1 to 5"  → specific range
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
            print(f"🎯 Quran: {surah_name} from ayat {from_ayat} to {to_ayat}")
            response = _add_surah_name(response)
            return response

    # pattern 3: "play fatiha ayat 3"  → single ayat
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
            print(f"🎯 Quran single ayat: {surah_name} ayat {ayat_num}")
            response = _add_surah_name(response)
            return response

    # pattern 4: "play fatiha to ayat 5"  → from 1 to 5
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
            print(f"🎯 Quran: {surah_name} from start to ayat {to_ayat}")
            response = _add_surah_name(response)
            return response

    # pattern 5: "play fatiha"  → full surah
    pattern5 = re.search(r"play\s+([a-z]+)$", text)
    if pattern5:
        surah_name = pattern5.group(1)
        surah_id = find_surah_id(surah_name)
        if surah_id:
            response["player"] = "play"
            response["type"] = "surah"
            response["surah"] = surah_id
            response["from"] = 1
            response["to"] = None
            print(f"🎯 Quran full surah: {surah_name}")
            response = _add_surah_name(response)
            return response

    # ------------------------------------------------------------------------
    # 8. NEXT / PREVIOUS SURAH NAVIGATION
    # ------------------------------------------------------------------------
    if re.search(r"(?:next|agla|agli|aage)\s+surah", text) or re.search(r"surah\s+(?:next|agla)", text):
        response["player"] = "next_surah"
        response["type"] = "surah"
        print("🎯 Next surah command")
        return response

    if re.search(r"(?:previous|pichla|pichli|peeche)\s+surah", text) or re.search(r"surah\s+(?:previous|pichla)", text):
        response["player"] = "previous_surah"
        response["type"] = "surah"
        print("🎯 Previous surah command")
        return response

    # ------------------------------------------------------------------------
    # 9. STANDARD PLAYER CONTROLS (play, pause, stop, resume, next, previous, jump)
    # ------------------------------------------------------------------------
    if response["player"] is None:
        for action, keywords in COMMANDS.items():
            if action in PLAYER_COMMANDS:
                pattern = r"\b(" + "|".join(map(re.escape, keywords)) + r")\b"
                if re.search(pattern, text):
                    response["player"] = action
                    print(f"🎯 Matched command: {action}")
                    break

    # ------------------------------------------------------------------------
    # 10. FALLBACK SURAH DETECTION (if no explicit command)
    # ------------------------------------------------------------------------
    if response["player"] not in SKIP_ACTIONS and response["player"] is None:
        text_for_surah = text
        # remove command words
        for action, keywords in COMMANDS.items():
            if action in PLAYER_COMMANDS:
                for word in keywords:
                    text_for_surah = re.sub(rf"\b{re.escape(word)}\b", "", text_for_surah)
        # remove common noise words
        remove_words = ["bayan", "tafseer", "from", "to", "se", "tak", "ayat", "verse", "aayat", "ayah", "select"]
        for word in remove_words:
            text_for_surah = re.sub(rf"\b{re.escape(word)}\b", "", text_for_surah)
        text_for_surah = re.sub(r"\b\d+\b", "", text_for_surah).strip()

        if len(text_for_surah) >= 3:
            surah_id = find_surah_id(text_for_surah)
            if surah_id:
                response["player"] = "play"
                response["type"] = "surah"
                response["surah"] = surah_id
                response["from"] = 1
                response["to"] = None
                print(f"🎯 Quran detected via fallback: {text_for_surah}")

    # ------------------------------------------------------------------------
    # 11. NUMBERS EXTRACTION (for jump or range)
    # ------------------------------------------------------------------------
    numbers = [int(n) for n in re.findall(r"\b\d+\b", text)]
    if response["player"] == "jump" and len(numbers) >= 1:
        response["ayatNumber"] = numbers[0]
    elif len(numbers) >= 1 and not response.get("from"):
        response["from"] = numbers[0]
    if len(numbers) >= 2 and not response.get("to"):
        response["to"] = numbers[1]

    # ------------------------------------------------------------------------
    # 12. FINAL RETURN
    # ------------------------------------------------------------------------
    

    return response
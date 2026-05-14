# ============================================================================
# token_creator.py - Complete Voice Command Token Creator
# ============================================================================
# Features:
#   1. Quran Play (Full Surah, Single Ayat, Range)
#   2. Chain Creation (Create, Select, Add, Save, Edit, Cancel, Delete)
#   3. Chain Play (explicit "chain" word)
#   4. Bookmark (Surah, Ayat, Range, Custom Title)
#   5. Bayan Play (with First/Second/Third, and by Ayat Number)
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


# ============================================================================
# SECTION A: HELPER FUNCTIONS FOR SURAH
# ============================================================================

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


# ============================================================================
# SECTION B: HELPER FUNCTIONS FOR BAYAN
# ============================================================================

def _get_bayans_by_surah(surah_id: int) -> list:
    """Fetch all bayans for a surah directly from database"""
    if not surah_id:
        return []
    
    conn = get_connection()
    if conn is None:
        return []
    
    try:
        cursor = conn.cursor()
        
        # 🔥 FIX: Only include bayans with valid StartAyatID and EndAyatID
        query = """SELECT 
                    b.BayanID, 
                    b.Title, 
                    b.AudioURL, 
                    b.StartAyatID, 
                    b.EndAyatID
                FROM Bayan b
                WHERE b.SurahID = ?
                    AND b.StartAyatID IS NOT NULL
                    AND b.EndAyatID IS NOT NULL
                ORDER BY b.StartAyatID ASC"""
        
        cursor.execute(query, (surah_id,))
        rows = cursor.fetchall()
        
        bayans = []
        base_audio_url = f"{BASE_IP}/audio/Dr_Israr/"
        
        for row in rows:
            bayans.append({
                "bayanId": row[0],
                "title": row[1],
                "audioUrl": f"{base_audio_url}{row[2]}",
                "startAyat": row[3],
                "endAyat": row[4]
            })
        
        # Debug logs
        print(f"📖 Found {len(bayans)} bayans for surah {surah_id}")
        for idx, b in enumerate(bayans):
            print(f"   [{idx}] {b['title']}: Ayats {b['startAyat']}-{b['endAyat']}")
        
        return bayans
        
    except Exception as e:
        print(f"❌ Error fetching bayans: {e}")
        return []
    finally:
        conn.close()


def _find_bayan_by_ayat(surah_id: int, ayat_number: int) -> dict:
    """Find which bayan contains the given ayat number"""
    if not surah_id or not ayat_number:
        print(f"⚠️ Invalid input: surah_id={surah_id}, ayat_number={ayat_number}")
        return {"bayanIndex": None, "bayanTitle": None, "bayanUrl": None, "bayanId": None}
    
    print(f"🔍 Searching for ayat {ayat_number} in surah {surah_id}")
    
    bayans = _get_bayans_by_surah(surah_id)
    
    if not bayans:
        print(f"❌ No bayans found for surah {surah_id}")
        return {"bayanIndex": None, "bayanTitle": None, "bayanUrl": None, "bayanId": None}
    
    for idx, bayan in enumerate(bayans):
        start_ayat = bayan.get("startAyat")
        end_ayat = bayan.get("endAyat")
        
        print(f"   Checking bayan [{idx}]: {bayan.get('title')} -> Ayats {start_ayat}-{end_ayat}")
        
        # Check if ayat falls in this bayan's range
        if start_ayat and end_ayat:
            if start_ayat <= ayat_number <= end_ayat:
                print(f"   ✅ MATCH FOUND! Index {idx}")
                return {
                    "bayanIndex": idx,
                    "bayanTitle": bayan.get("title"),
                    "bayanUrl": bayan.get("audioUrl"),
                    "bayanId": bayan.get("bayanId"),
                    "startAyat": start_ayat,
                    "endAyat": end_ayat
                }
        else:
            print(f"   ⚠️ Invalid range: start={start_ayat}, end={end_ayat}")
    
    # If no range found, return first bayan as fallback
    print(f"⚠️ No bayan contains ayat {ayat_number}, returning first bayan (index 0) as fallback")
    return {
        "bayanIndex": 0,
        "bayanTitle": bayans[0].get("title"),
        "bayanUrl": bayans[0].get("audioUrl"),
        "bayanId": bayans[0].get("bayanId"),
        "startAyat": bayans[0].get("startAyat"),
        "endAyat": bayans[0].get("endAyat")
    }


def _get_bayan_by_index(surah_id: int, bayan_index: int = 0) -> dict:
    """Fetch bayan by surah ID and index"""
    bayans = _get_bayans_by_surah(surah_id)
    
    if bayans and bayan_index < len(bayans):
        bayan = bayans[bayan_index]
        print(f"📖 Getting bayan by index {bayan_index}: {bayan.get('title')}")
        return {
            "bayanTitle": bayan.get("title"),
            "bayanUrl": bayan.get("audioUrl"),
            "bayanId": bayan.get("bayanId")
        }
    
    print(f"⚠️ Bayan index {bayan_index} not found, total bayans: {len(bayans)}")
    return {"bayanTitle": None, "bayanUrl": None, "bayanId": None}


def _add_bayan_details(response: dict) -> dict:
    """Add bayanTitle and bayanUrl to response if type is 'bayan'"""
    if response.get('type') == 'bayan' and response.get('surahId'):
        print(f"🎤 Adding bayan details for surahId={response['surahId']}")
        
        # Check if we have specific ayat number
        if response.get('requestedAyat'):
            print(f"   Mode: By Ayat Number ({response['requestedAyat']})")
            bayan_info = _find_bayan_by_ayat(response['surahId'], response['requestedAyat'])
            response['bayanIndex'] = bayan_info.get('bayanIndex')
            response['bayanTitle'] = bayan_info.get('bayanTitle')
            response['bayanUrl'] = bayan_info.get('bayanUrl')
            response['bayanRange'] = f"{bayan_info.get('startAyat')}-{bayan_info.get('endAyat')}"
        else:
            # Normal bayan by index
            print(f"   Mode: By Index ({response.get('bayanIndex', 0)})")
            bayan_info = _get_bayan_by_index(response['surahId'], response.get('bayanIndex', 0))
            response['bayanTitle'] = bayan_info.get('bayanTitle')
            response['bayanUrl'] = bayan_info.get('bayanUrl')
        
        print(f"🎤 Bayan Details: Title={response.get('bayanTitle')}, URL={response.get('bayanUrl')}")
        print(f"🎤 Bayan Index: {response.get('bayanIndex')}, Range: {response.get('bayanRange')}")
    
    return response


# ============================================================================
# SECTION C: MAIN TOKEN CREATOR FUNCTION
# ============================================================================

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
    text = normalize_text(text)
    if original_text != text:
        print(f"📝 Text normalized: '{original_text}' → '{text}'")

    response: Dict[str, Any] = {
        "player": None,
        "type": "surah",
        "surah": None,
        "surahName": None,
        "from": None,
        "to": None,
        "bayanTitle": None,
        "bayanUrl": None,
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
    # range first: "select ayat 1 to 8" or "select ayat 1 sa 8"
        range_match = re.search(r"(?:select\s+)?ayat\s+(\d+)\s+(?:to|se|sa|sy|say)\s+(\d+)", text)
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
    
    # 3.1 Open chain builder
    if re.search(r"create\s+chain", text):
        response["player"] = "open_chain_builder"
        response["type"] = "chain"
        return response

    # 3.2 Add to list
    if re.search(r"add\s+to\s+list", text) or re.search(r"add\s+kar", text):
        response["player"] = "add_to_list"
        response["type"] = "chain"
        return response

    # 3.3 Set title
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

    # 3.4 Save chain
    if re.search(r"save\s+chain", text):
        response["player"] = "save_chain"
        response["type"] = "chain"
        return response

    # 3.5 Remove last
    if re.search(r"remove\s+last", text) or re.search(r"last\s+hatayo", text):
        response["player"] = "remove_last"
        response["type"] = "chain"
        return response

    # 3.6 Clear all
    if re.search(r"clear\s+all", text) or re.search(r"sab\s+hatayo", text):
        response["player"] = "clear_all"
        response["type"] = "chain"
        return response

    # 3.7 Show list
    if re.search(r"show\s+list", text) or re.search(r"list\s+dikhao", text):
        response["player"] = "show_list"
        response["type"] = "chain"
        return response

    # 3.8 Cancel chain
    if re.search(r"cancel\s+chain", text) or re.search(r"chain\s+cancel", text):
        response["player"] = "cancel_chain"
        response["type"] = "chain"
        return response
        
    # 3.9 Delete chain
    delete_chain_match = re.search(r"(?:delete|remove|hatao)\s+chain\s+(\w+(?:\s+\w+)?)", text)
    if delete_chain_match:
        chain_name = delete_chain_match.group(1).strip()
        response["player"] = "delete_chain"
        response["type"] = "chain"
        response["chainName"] = chain_name
        return response

    # 3.10 Delete all chains
    if re.search(r"delete\s+all\s+chains", text) or re.search(r"sab\s+chains\s+hatao", text):
        response["player"] = "delete_all_chains"
        response["type"] = "chain"
        return response


    # ------------------------------------------------------------------------
    # 4. BOOKMARK COMMANDS
    # ------------------------------------------------------------------------
    
    # 4.1 Bookmark full surah
    surah_bookmark_match = re.search(r"bookmark\s+([a-z]+)(?:\s+ayat)?$", text)
    if surah_bookmark_match and "ayat" not in text:
        response["player"] = "bookmark_surah"
        response["type"] = "bookmark"
        response["surahName"] = surah_bookmark_match.group(1)
        return response

    # 4.2 Bookmark specific ayat
    ayat_bookmark_match = re.search(r"bookmark\s+([a-z]+)\s+ayat\s+(\d+)", text)
    if ayat_bookmark_match:
        response["player"] = "bookmark_ayat"
        response["type"] = "bookmark"
        response["surahName"] = ayat_bookmark_match.group(1)
        response["fromAyat"] = int(ayat_bookmark_match.group(2))
        return response

    # 4.3 Bookmark range
    range_bookmark_match = re.search(
    r"bookmark\s+([a-z]+)\s+from\s+ayat\s+(\d+)\s+(?:to|se|sa|sy|say)\s+ayat\s+(\d+)", text
    )
    if not range_bookmark_match:
      range_bookmark_match = re.search(
         r"bookmark\s+([a-z]+)\s+ayat\s+(\d+)\s+(?:to|se|sa|sy|say)\s+(\d+)", text
      )
    if range_bookmark_match:
        response["player"] = "bookmark_range"
        response["type"] = "bookmark"
        response["surahName"] = range_bookmark_match.group(1)
        response["fromAyat"] = int(range_bookmark_match.group(2))
        response["toAyat"] = int(range_bookmark_match.group(3))
        return response

    # 4.4 Bookmark with custom title
    title_bookmark = re.search(r"bookmark\s+([a-z]+)\s+as\s+(.+)", text)
    if title_bookmark:
        response["player"] = "bookmark_with_title"
        response["type"] = "bookmark"
        response["surahName"] = title_bookmark.group(1)
        response["title"] = title_bookmark.group(2).strip()
        return response

    # 4.5 Show bookmarks list
    if re.search(r"(?:show|my)\s+bookmarks", text):
        response["player"] = "show_bookmarks"
        response["type"] = "bookmark"
        return response


    # ------------------------------------------------------------------------
    # 5. BAYAN COMMANDS
    # ------------------------------------------------------------------------
    
    BAYAN_KEYWORDS = ["bayan", "tafseer", "tafsir", "tarjuma", "explanation", "lecture"]

    # 5.0 Bayan by Ayat Number (Highest priority)
    bayan_by_ayat = re.search(
        r"(?:play|sunao|chalao)\s+bayan\s+([a-z]+)\s+ayat\s+(\d+)", 
        text
    )

    if bayan_by_ayat:
        surah_name = bayan_by_ayat.group(1)
        ayat_number = int(bayan_by_ayat.group(2))
        surah_id = find_surah_id(surah_name)
        
        print(f"🎤 Bayan by ayat detected: surah={surah_name}, ayat={ayat_number}, surah_id={surah_id}")
        
        if surah_id:
            response["player"] = "play"
            response["type"] = "bayan"
            response["surahId"] = surah_id
            response["requestedAyat"] = ayat_number
            response = _add_bayan_details(response)
            
            if response.get('bayanTitle'):
                print(f"🎤 Bayan by ayat: {surah_name} ayat {ayat_number} → {response['bayanTitle']} (Index {response.get('bayanIndex')})")
            else:
                print(f"❌ No bayan found for surah {surah_name} containing ayat {ayat_number}")
                
            return response
        else:
            print(f"❌ Surah not found: {surah_name}")
            return response

    # 5.1 Bayan with explicit index (first, second, third...)
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

    # 5.2 Simple bayan (first by default)
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

    # 5.3 Introduction bayan
    if re.search(r"introduction\s+to\s+quran", text) or re.search(r"intro\s+bayan", text):
        response["player"] = "play"
        response["type"] = "bayan"
        response["surahId"] = 0
        response["bayanIndex"] = 0
        response["bayanTitle"] = "Introduction to Quran"
        response["bayanUrl"] = f"{BASE_IP}/audio/Dr_Israr/intro.mp3"
        print("🎤 Introduction bayan")
        return response


    # ------------------------------------------------------------------------
    # 6. CHAIN PLAY (explicit "chain" word)
    # ------------------------------------------------------------------------
    
    # 6.1 "play chain daily"
    play_chain_match = re.search(r"(?:play|sunao|chalao)\s+chain\s+(\w+(?:\s+\w+)?)", text)
    if play_chain_match:
        response["player"] = "play_chain"
        response["type"] = "chain"
        response["chainName"] = play_chain_match.group(1).strip()
        return response

    # 6.2 "daily chain play"
    alt_match = re.search(r"(\w+(?:\s+\w+)?)\s+chain\s+(?:play|sunao|chalao)", text)
    if alt_match:
        response["player"] = "play_chain"
        response["type"] = "chain"
        response["chainName"] = alt_match.group(1).strip()
        return response


    # ------------------------------------------------------------------------
    # 7. QURAN PLAYBACK (Full Surah, Single Ayat, Range – 5 patterns)
    # ------------------------------------------------------------------------
    
    # Pattern 1: "play fatiha from ayat 2" → from 2 to end
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

    # Pattern 2: "play fatiha from ayat 1 to 5" → specific range
    pattern2 = re.search(r"play\s+([a-z]+)\s+from\s+ayat\s+(\d+)\s+(?:to|se|sa|sy|say)\s+ayat\s+(\d+)", text)
    if not pattern2:
       pattern2 = re.search(r"play\s+([a-z]+)\s+ayat\s+(\d+)\s+(?:to|se|sa|sy|say)\s+(\d+)", text)

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

    # Pattern 3: "play fatiha ayat 3" → single ayat
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

    # Pattern 4: "play fatiha to ayat 5" → from 1 to 5
    pattern4 = re.search(r"play\s+([a-z]+)\s+(?:to|se|sa|sy|say)\s+ayat\s+(\d+)", text)
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

    # Pattern 5: "play fatiha" → full surah
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
    
    # 8.1 Next surah
    if re.search(r"(?:next|agla|agli|aage)\s+surah", text) or re.search(r"surah\s+(?:next|agla)", text):
        response["player"] = "next_surah"
        response["type"] = "surah"
        print("🎯 Next surah command")
        return response

    # 8.2 Previous surah
    if re.search(r"(?:previous|pichla|pichli|peeche)\s+surah", text) or re.search(r"surah\s+(?:previous|pichla)", text):
        response["player"] = "previous_surah"
        response["type"] = "surah"
        print("🎯 Previous surah command")
        return response


    # ------------------------------------------------------------------------
    # 9. STANDARD PLAYER CONTROLS
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
    # 10. FALLBACK SURAH DETECTION
    # ------------------------------------------------------------------------
    
    if response["player"] not in SKIP_ACTIONS and response["player"] is None:
        text_for_surah = text
        
        # Remove command words
        for action, keywords in COMMANDS.items():
            if action in PLAYER_COMMANDS:
                for word in keywords:
                    text_for_surah = re.sub(rf"\b{re.escape(word)}\b", "", text_for_surah)
        
        # Remove common noise words
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
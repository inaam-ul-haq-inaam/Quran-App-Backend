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
#   8. Navigation Commands (Show Chains, Show Bookmarks)
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
    SKIP_ACTIONS,
    CHAIN_KEYWORDS,
    HISTORY_KEYWORDS,
    CREATE_ACTION_KEYWORDS,
    ADD_ACTION_KEYWORDS,
    TARGET_LIST_KEYWORDS,
    SELECT_ACTION_KEYWORDS,
    BAYAN_TRIGGER_WORDS,
    BAYAN_ACTION_VERBS,
    FROM_KEYWORDS,
    RANGE_CONNECTORS,
    END_KEYWORDS,
    AYAT_WORD,
)
from Services.spellCheck import find_surah_id, get_surah_name_from_id


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


def _get_resume_position(surah_id: int, profile_id: int = 1) -> int:
    """Fetch the latest resume position for a surah from play history"""
    if not surah_id:
        return 0
    
    conn = get_connection()
    if conn is None:
        return 0
    
    try:
        cursor = conn.cursor()
        query = """
            SELECT TOP 1 current_position
            FROM user_play_history
            WHERE profileId = ?
              AND content_type = 'surah'
              AND content_id = ?
              AND completed = 0
            ORDER BY played_at DESC
        """
        cursor.execute(query, (profile_id, surah_id))
        row = cursor.fetchone()
        return row[0] if row else 0
    except Exception as e:
        print(f"❌ Error fetching resume position: {e}")
        return 0
    finally:
        conn.close()

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
    """Find which bayan contains the given ayat number, with fallback to all surahs if needed"""
    if not surah_id or not ayat_number:
        return {"bayanIndex": None, "bayanTitle": None, "bayanUrl": None, "bayanId": None, "surahId": None}
    
    print(f"🔍 Searching for ayat {ayat_number} in surah {surah_id}")
    
    # 1. Try to find inside the requested surah first
    bayans = _get_bayans_by_surah(surah_id)
    if bayans:
        for idx, bayan in enumerate(bayans):
            start_ayat = bayan.get("startAyat")
            end_ayat = bayan.get("endAyat")
            
            print(f"   Checking bayan [{idx}]: {bayan.get('title')} -> Ayats {start_ayat}-{end_ayat}")
            
            if start_ayat and end_ayat:
                if start_ayat <= ayat_number <= end_ayat:
                    print(f"   ✅ MATCH FOUND inside requested surah! Index {idx}")
                    return {
                        "bayanIndex": idx,
                        "bayanTitle": bayan.get("title"),
                        "bayanUrl": bayan.get("audioUrl"),
                        "bayanId": bayan.get("bayanId"),
                        "startAyat": start_ayat,
                        "endAyat": end_ayat,
                        "surahId": surah_id
                    }
    
    # 2. If not found in the requested surah, search ALL surahs in the database
    print(f"⚠️ Ayat {ayat_number} not found in surah {surah_id}'s bayans. Searching all surahs...")
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
                SELECT b.BayanID, b.Title, b.AudioURL, b.StartAyatID, b.EndAyatID, b.SurahID
                FROM Bayan b
                WHERE b.StartAyatID <= ? AND b.EndAyatID >= ?
                ORDER BY b.SurahID ASC
            """
            cursor.execute(query, (ayat_number, ayat_number))
            rows = cursor.fetchall()
            
            if rows:
                print(f"   ℹ️ Found {len(rows)} matching bayans across all surahs for ayat {ayat_number}")
                
                requested_surah_name = get_surah_name_from_id(surah_id)
                best_row = None
                best_score = -1
                
                from thefuzz import fuzz
                
                for row in rows:
                    candidate_surah_id = row[5]
                    candidate_surah_name = get_surah_name_from_id(candidate_surah_id)
                    
                    if requested_surah_name and candidate_surah_name:
                        score = fuzz.token_set_ratio(requested_surah_name.lower(), candidate_surah_name.lower())
                        print(f"      Fuzzy matching '{requested_surah_name}' with candidate '{candidate_surah_name}' (ID: {candidate_surah_id}) -> Score: {score}")
                        if score > best_score:
                            best_score = score
                            best_row = row
                    else:
                        if best_row is None:
                            best_row = row
                
                if best_row:
                    matched_bayan_id = best_row[0]
                    matched_title = best_row[1]
                    matched_audio = best_row[2]
                    matched_start = best_row[3]
                    matched_end = best_row[4]
                    matched_surah_id = best_row[5]
                    
                    base_audio_url = f"{BASE_IP}/audio/Dr_Israr/"
                    full_audio_url = f"{base_audio_url}{matched_audio}"
                    
                    sibling_bayans = _get_bayans_by_surah(matched_surah_id)
                    matched_index = 0
                    for idx, sib in enumerate(sibling_bayans):
                        if sib.get("bayanId") == matched_bayan_id:
                            matched_index = idx
                            break
                    
                    print(f"   ✅ MATCH FOUND in surah {matched_surah_id} (bayan index {matched_index})! Title: {matched_title}")
                    return {
                        "bayanIndex": matched_index,
                        "bayanTitle": matched_title,
                        "bayanUrl": full_audio_url,
                        "bayanId": matched_bayan_id,
                        "startAyat": matched_start,
                        "endAyat": matched_end,
                        "surahId": matched_surah_id
                    }
        except Exception as e:
            print(f"❌ Error searching bayans across database: {e}")
        finally:
            conn.close()

    # 3. Fallback to first bayan of requested surah
    if bayans:
        print(f"⚠️ No bayan contains ayat {ayat_number} anywhere, returning first bayan of surah {surah_id}")
        return {
            "bayanIndex": 0,
            "bayanTitle": bayans[0].get("title"),
            "bayanUrl": bayans[0].get("audioUrl"),
            "bayanId": bayans[0].get("bayanId"),
            "startAyat": bayans[0].get("startAyat"),
            "endAyat": bayans[0].get("endAyat"),
            "surahId": surah_id
        }
    
    return {"bayanIndex": None, "bayanTitle": None, "bayanUrl": None, "bayanId": None, "surahId": None}


def _get_bayan_by_index(surah_id: int, bayan_index: int = 0) -> dict:
    """Fetch bayan by surah ID and index"""
    bayans = _get_bayans_by_surah(surah_id)
    
    if bayans and bayan_index < len(bayans):
        bayan = bayans[bayan_index]
        return {
            "bayanTitle": bayan.get("title"),
            "bayanUrl": bayan.get("audioUrl"),
            "bayanId": bayan.get("bayanId")
        }
    
    
    return {"bayanTitle": None, "bayanUrl": None, "bayanId": None}


def _add_bayan_details(response: dict) -> dict:
    if response.get('type') == 'bayan' and response.get('surahId'):
        if response.get('requestedAyat'):
            bayan_info = _find_bayan_by_ayat(response['surahId'], response['requestedAyat'])
            
            # 🔥 Update surahId if matched in a different surah
            if bayan_info.get('surahId') and bayan_info.get('surahId') != response['surahId']:
                print(f"🔄 Updating surahId in response from {response['surahId']} to {bayan_info.get('surahId')}")
                response['surahId'] = bayan_info.get('surahId')
            
            
            response['bayanIndex'] = bayan_info.get('bayanIndex')
            response['bayanTitle'] = bayan_info.get('bayanTitle')
            response['bayanUrl'] = bayan_info.get('bayanUrl')
            response['bayanId'] = bayan_info.get('bayanId')
            response['bayanRange'] = f"{bayan_info.get('startAyat')}-{bayan_info.get('endAyat')}"
        else:
            bayan_info = _get_bayan_by_index(response['surahId'], response.get('bayanIndex', 0))
            response['bayanTitle'] = bayan_info.get('bayanTitle')
            response['bayanUrl'] = bayan_info.get('bayanUrl')
            response['bayanId'] = bayan_info.get('bayanId')
            
        # Get raw list of bayans for final/updated surahId
        raw_bayans = _get_bayans_by_surah(response['surahId'])
        
        # Format the list specifically for the frontend player
        formatted_bayans = []
        for b in raw_bayans:
            formatted_bayans.append({
                "BayanID": b.get("bayanId"),
                "Title": b.get("title"),
                "AudioUrl": b.get("audioUrl"),
                "ScholarName": "Dr. Israr Ahmed",
                "StartAyatID": b.get("startAyat"),
                "EndAyatID": b.get("endAyat")
            })
            
        matched_index = response.get('bayanIndex', 0)
        if matched_index is None:
            matched_index = 0
            
        sliced_bayans = formatted_bayans[matched_index:]
        
        response['bayanList'] = sliced_bayans
        response['bayanIndex'] = 0
        
        if sliced_bayans:
            first_item = sliced_bayans[0]
            response['bayanTitle'] = first_item.get('Title')
            response['bayanUrl'] = first_item.get('AudioUrl')
            response['bayanId'] = first_item.get('BayanID')
            
            start = first_item.get('StartAyatID')
            end = first_item.get('EndAyatID')
            if start is not None and end is not None:
                response['bayanRange'] = f"{start}-{end}"
            else:
                response['bayanRange'] = None
                
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

    # ============================================================
    # SPECIAL HIGH-PRIORITY: DAILY QURAN VOICE COMMANDS
    # ============================================================
    # 1. Listen Quran Spelling & Typo Variations List
    listen_quran_variations = [
        "listen quran", "listn quran", "lisen quran", "lisn quran", "leson quran", "lesn quran", "lesten quran",
        "listen qur", "listn qur", "lisen qur", "lisn qur", "leson qur", "lesn qur",
        "listen to quran", "listen to qur", "listen to qurn", "listen to quraan",
        "play daily quran", "play daily qur", "play daily qurn", "play quran daily",
        "listen daily quran", "listen daily qur", "listen daily qurn",
        "quran listen", "qur listen", "qurn listen", "quran play"
    ]
    # 2. Save Quran Progress Spelling & Typo Variations List
    save_quran_variations = [
        "save quran progress", "save progress", "save quran", "sav quran progress", "sav progress", "sav quran",
        "save quran progres", "save progres", "sav progres", "seve progress", "seve progres", "saf progress", "saf progres",
        "seve quran", "saf quran", "save daily quran progress", "save daily quran", "save daily progress",
        "sav daily quran progress", "sav daily progress", "save daily quran", "seve daily progress", "seve daily quran",
        "saf daily progress", "saf daily quran", "save qurn progress", "save qurn progres", "save qurn",
        "sav qurn progress", "sav qurn", "seve qurn", "saf qurn"
    ]
    # 3. Continue Quran Spelling & Typo Variations List
    continue_quran_variations = [
        "continue quran", "continue daily quran", "resume quran", "resume daily quran", "continue qur", "continue", "resume",
        "rsume quran", "resme quran", "rasume quran", "resem quran", "resum quran", "rsume", "resme", "resum", "rasume",
        "continiue quran", "contine quran", "contnou quran", "contnue quran", "contnu quran", "contine", "contnue", "contnu",
        "continue daily qur", "resume daily qur", "rsume qur", "resme qur", "resum qur", "rasume qur",
        "continiue qur", "contine qur", "contnou qur", "contnue qur", "contnu qur",
        "continue qurn", "resume qurn", "rsume qurn", "resme qurn", "resum qurn", "rasume qurn",
        "continiue qurn", "contine qurn", "contnou qurn", "contnue qurn", "contnu qurn"
    ]

    is_listen_quran = (
        text in listen_quran_variations or
        any(v in text for v in ["listen quran", "listn quran", "listen qur", "listn qur"]) or
        re.search(r"\b(listen|listn|lisen|lisn|leson|lesn|lesten|lestn|play)\s+(?:to\s+)?(?:daily\s+)?(quran|qur|qurn|quraan)\b", text)
    )

    is_save_quran = (
        text in save_quran_variations or
        any(v in text for v in ["save quran", "sav quran", "save progress", "sav progress", "seve progress"]) or
        re.search(r"\b(save|sav|seve|saf|store|stor|stope|stop|paus|pause)\s+(?:daily\s+)?(?:quran\s+)?(progress|progres|prog|progrs)\b", text) or
        re.search(r"\b(save|sav|seve|saf)\s+daily\s+(quran|qur|qurn|quraan)\b", text) or
        re.search(r"\b(save|sav|seve|saf)\s+(quran|qur|qurn|quraan)\s+progress\b", text)
    )

    is_continue_quran = (
        text in continue_quran_variations or
        text == "continue" or
        text == "resume" or
        text == "rsume" or
        text == "resme" or
        text == "resum" or
        any(v in text for v in ["continue quran", "continue qur", "resume quran", "resume qur", "rsume quran", "resme quran"]) or
        re.search(r"\b(continue|contine|continiue|contnou|contnue|contnu|resume|rsume|resme|rasume|resem|resum)\s+(?:daily\s+)?(?:quran|qur|qurn|quraan)\b", text)
    )

    if is_listen_quran:
        print("🎙️ MATCHED DAILY QURAN: listen_quran")
        return {
            "player": "listen_quran",
            "type": "daily_quran",
            "isVoiceMode": True
        }

    if is_save_quran:
        print("🎙️ MATCHED DAILY QURAN: save_quran_progress")
        return {
            "player": "save_quran_progress",
            "type": "daily_quran",
            "isVoiceMode": True
        }

    if is_continue_quran:
        print("🎙️ MATCHED DAILY QURAN: continue_quran")
        return {
            "player": "continue_quran",
            "type": "daily_quran",
            "isVoiceMode": True
        }
    
    # ============================================================
    # SECTION: HISTORY / STATS COMMANDS (Show vs Play)
    # ============================================================

    # Helper to match keywords with word boundaries (avoid false positives)
    def _match_keyword(text, keywords):
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", text):
                return True
        return False

    # Helper to extract a numeric limit from text (supports digits and number words)
    def _extract_limit(text, default=4):
        # Try digits first
        num_match = re.search(r'(?:last|recent)\s+(\d+)', text)
        if num_match:
            return int(num_match.group(1))
        # Then number words
        number_words = {
            'one':1, 'two':2, 'three':3, 'four':4, 'five':5,
            'six':6, 'seven':7, 'eight':8, 'nine':9, 'ten':10
        }
        for word, val in number_words.items():
            if re.search(rf'\b{word}\b', text):
                return val
        return default

    # ============================================================
    # A. SHOW COMMANDS (only display – never play)
    # ============================================================

    # 1. Show last N items (mixed)
    if _match_keyword(text, HISTORY_KEYWORDS["last"]) and _match_keyword(text, HISTORY_KEYWORDS["items"]):
        limit = _extract_limit(text, 4)
        response["player"] = "show_last_played_items"
        response["type"] = "history"
        response["limit"] = limit
        response["content_type"] = None   # mixed
        return response

    # 2. Show last N surahs
    if _match_keyword(text, HISTORY_KEYWORDS["last"]) and _match_keyword(text, HISTORY_KEYWORDS["surahs"]):
        limit = _extract_limit(text, 4)
        response["player"] = "show_last_played_items"
        response["type"] = "history"
        response["limit"] = limit
        response["content_type"] = "surah"
        return response

    # 3. Show last N bayans
    if _match_keyword(text, HISTORY_KEYWORDS["last"]) and _match_keyword(text, HISTORY_KEYWORDS["bayans"]):
        limit = _extract_limit(text, 4)
        response["player"] = "show_last_played_items"
        response["type"] = "history"
        response["limit"] = limit
        response["content_type"] = "bayan"
        return response

    # 4. Show most played surah
    if _match_keyword(text, HISTORY_KEYWORDS["most_played"]) and _match_keyword(text, HISTORY_KEYWORDS["surahs"]):
        response["player"] = "show_most_played"
        response["type"] = "history"
        response["content_type"] = "surah"
        return response

    # 5. Show most played bayan
    if _match_keyword(text, HISTORY_KEYWORDS["most_played"]) and _match_keyword(text, HISTORY_KEYWORDS["bayans"]):
        response["player"] = "show_most_played"
        response["type"] = "history"
        response["content_type"] = "bayan"
        return response

    # 6. Show most played chain (optional)
    if _match_keyword(text, HISTORY_KEYWORDS["most_played"]) and _match_keyword(text, HISTORY_KEYWORDS["chains"]):
        response["player"] = "show_most_played"
        response["type"] = "history"
        response["content_type"] = "chain"
        return response

    # ============================================================
    # B. PLAY COMMANDS (direct playback – only for single items)
    # ============================================================

    # 7. Play most played surah
    if re.search(r"play\s+most\s+played\s+surah", text):
        response["player"] = "play_most_played"
        response["type"] = "history"
        response["content_type"] = "surah"
        return response

    # 8. Play most played bayan
    if re.search(r"play\s+most\s+played\s+bayan", text):
        response["player"] = "play_most_played"
        response["type"] = "history"
        response["content_type"] = "bayan"
        return response

    # 9. Play last played surah
    if re.search(r"play\s+last\s+played\s+surah", text):
        response["player"] = "play_last_played"
        response["type"] = "history"
        response["content_type"] = "surah"
        return response

    # 10. Play last played bayan
    if re.search(r"play\s+last\s+played\s+bayan", text):
        response["player"] = "play_last_played"
        response["type"] = "history"
        response["content_type"] = "bayan"
        return response

    # 11. Play last played chain
    if re.search(r"play\s+last\s+played\s+chain", text):
        response["player"] = "play_last_played"
        response["type"] = "history"
        response["content_type"] = "chain"
        return response


    # ============================================================
    # SECTION 1: BOOKMARK COMMANDS (HIGHEST PRIORITY)
    # ============================================================
    
    if "bookmark" in text:
        
        # 1.1 - Bookmark with custom title (contains "as")
        title_bookmark = re.search(r"bookmark\s+([a-z]+)(?:\s+ayat\s+(\d+))?(?:\s+(?:from\s+)?ayat\s+(\d+)\s+(?:to|se|sa|sy|say)\s+(\d+))?\s+as\s+(.+)", text)
        if title_bookmark:
            surah_name = title_bookmark.group(1)
            surah_id = find_surah_id(surah_name)
            
            if surah_id:
                response["player"] = "bookmark_with_title"
                response["type"] = "bookmark"
                response["surahId"] = surah_id
                response["surahName"] = surah_name
                response["title"] = title_bookmark.group(5).strip()
                
                if title_bookmark.group(2):
                    response["fromAyat"] = int(title_bookmark.group(2))
                    response["toAyat"] = int(title_bookmark.group(2))
                elif title_bookmark.group(3) and title_bookmark.group(4):
                    response["fromAyat"] = int(title_bookmark.group(3))
                    response["toAyat"] = int(title_bookmark.group(4))
                else:
                    response["fromAyat"] = 1
                    response["toAyat"] = None
                
                print(f"📖 Bookmark with title: {surah_name} → '{response['title']}'")
                return response
            else:
                print(f"❌ Surah not found: {surah_name}")
                return response
        
        # 1.2 - Bookmark range (only if no "as" word)
        if "as" not in text:
            range_match = re.search(r"bookmark\s+([a-z]+)\s+(?:from\s+)?ayat\s+(\d+)\s+(?:to|se|sa|sy|say)\s+(\d+)", text)
            if range_match:
                surah_name = range_match.group(1)
                surah_id = find_surah_id(surah_name)
                
                if surah_id:
                    response["player"] = "bookmark_range"
                    response["type"] = "bookmark"
                    response["surahId"] = surah_id
                    response["surahName"] = surah_name
                    response["fromAyat"] = int(range_match.group(2))
                    response["toAyat"] = int(range_match.group(3))
                    response["title"] = f"{surah_name.capitalize()} - Ayat {response['fromAyat']} to {response['toAyat']}"
                    print(f"📖 Bookmark range: {surah_name} ayats {response['fromAyat']}-{response['toAyat']}")
                    return response
        
        # 1.3 - Bookmark single ayat (only if no "as" word)
        if "as" not in text:
            ayat_match = re.search(r"bookmark\s+([a-z]+)\s+ayat\s+(\d+)", text)
            if ayat_match:
                surah_name = ayat_match.group(1)
                surah_id = find_surah_id(surah_name)
                
                if surah_id:
                    response["player"] = "bookmark_ayat"
                    response["type"] = "bookmark"
                    response["surahId"] = surah_id
                    response["surahName"] = surah_name
                    response["fromAyat"] = int(ayat_match.group(2))
                    response["toAyat"] = int(ayat_match.group(2))
                    response["title"] = f"{surah_name.capitalize()} - Ayat {response['fromAyat']}"
                    print(f"📖 Bookmark ayat: {surah_name} ayat {response['fromAyat']}")
                    return response
        
        # 1.4 - Bookmark full surah (only if no "as", no "ayat", and ends exactly)
        if "as" not in text and "ayat" not in text:
            surah_match = re.search(r"bookmark\s+([a-z]+)$", text)
            if surah_match:
                surah_name = surah_match.group(1)
                surah_id = find_surah_id(surah_name)
                
                if surah_id:
                    response["player"] = "bookmark_surah"
                    response["type"] = "bookmark"
                    response["surahId"] = surah_id
                    response["surahName"] = surah_name
                    response["fromAyat"] = 1
                    response["toAyat"] = None
                    response["title"] = f"{surah_name.capitalize()} (Full)"
                    print(f"📖 Bookmark full surah: {surah_name}")
                    return response


    # ============================================================
    # SECTION 2: SHOW BOOKMARKS / SHOW CHAINS
    # ============================================================
    
    # Build regex pattern from CHAIN_KEYWORDS (for "show chains" variants)
    chain_nav_pattern = "|".join(re.escape(kw) for kw in CHAIN_KEYWORDS)
    
    # Show Chains / Chain List (supports all keywords from data.py)
    if re.search(rf"show\s+(?:{chain_nav_pattern})", text):
        response["player"] = "show_chains"
        response["type"] = "navigation"
        print("📋 Show chains command matched")
        return response
    
    # Show Bookmarks / Quran Bookmarks
    if re.search(r"(?:show|my|open)\s+bookmarks?", text) or re.search(r"(?:quran|surah)\s+bookmarks?", text):
        response["player"] = "show_bookmarks"
        response["type"] = "navigation"
        print("📖 Show bookmarks command matched")
        return response


    # ============================================================
    # SECTION 3: SELECT COMMANDS (for chain building)
    # ============================================================

    # Helper to match any of the keywords (word boundaries)
    def _match_keyword2(text, keywords):
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", text):
                return True
        return False
    
    # ============================================================
    # 1. SELECT SURAH (with or without "surah" word)
    # ============================================================
    
    # Pattern: "select surah fatiha" or "select fatiha" (if surah name is recognized)
    if _match_keyword2(text, SELECT_ACTION_KEYWORDS):
        # First, try to match with explicit "surah" word
        surah_match = re.search(r"(?:select|choose)\s+surah\s+([a-z]+)", text, re.IGNORECASE)
        if surah_match:
            surah_name = surah_match.group(1)
            if find_surah_id(surah_name):
                response["player"] = "select_surah"
                response["type"] = "chain"
                response["surahName"] = surah_name
                print(f"🎯 Select surah: {surah_name}")
                return response
        
        # Then, try simple "select [surah_name]" at end of string (no extra words)
        simple_match = re.search(r"select\s+([a-z]+)$", text, re.IGNORECASE)
        if simple_match:
            surah_name = simple_match.group(1)
            if find_surah_id(surah_name):
                response["player"] = "select_surah"
                response["type"] = "chain"
                response["surahName"] = surah_name
                print(f"🎯 Select surah (simple): {surah_name}")
                return response
    
    # ============================================================
    # 2. SELECT AYAT (range or single) – numbers already normalized to digits
    # ============================================================
    
    # Since text is already normalized, "ayat" word is standard and numbers are digits.
    # So we can simply search for "select ayat" pattern.
    if re.search(r"select\s+ayat", text, re.IGNORECASE):
        # Check for range first: "select ayat 1 to 5" or "select ayat 1 se 5"
        range_match = re.search(r"select\s+ayat\s+(\d+)\s+(?:to|se|sa|sy|say)\s+(\d+)", text, re.IGNORECASE)
        if range_match:
            response["player"] = "select_ayat"
            response["type"] = "chain"
            response["fromAyat"] = int(range_match.group(1))
            response["toAyat"] = int(range_match.group(2))
            print(f"🎯 Select range ayat: {response['fromAyat']} → {response['toAyat']}")
            return response
        
        # Then single ayat: "select ayat 5"
        single_match = re.search(r"select\s+ayat\s+(\d+)", text, re.IGNORECASE)
        if single_match:
            response["player"] = "select_ayat"
            response["type"] = "chain"
            response["fromAyat"] = int(single_match.group(1))
            print(f"🎯 Select single ayat: {response['fromAyat']}")
            return response


    # ============================================================
    # SECTION 4: CHAIN CREATION COMMANDS
    # ============================================================
    
    # Build regex patterns from data.py
    create_pattern = "|".join(re.escape(kw) for kw in CREATE_ACTION_KEYWORDS)
    chain_obj_pattern = "|".join(re.escape(kw) for kw in CHAIN_KEYWORDS)
    add_pattern = "|".join(re.escape(kw) for kw in ADD_ACTION_KEYWORDS)
    list_target_pattern = "|".join(re.escape(kw) for kw in TARGET_LIST_KEYWORDS)
    
    # CREATE CHAIN
    if re.search(rf"(?:{create_pattern})\s+(?:{chain_obj_pattern})", text, re.IGNORECASE):
        response["player"] = "open_chain_builder"
        response["type"] = "chain"
        print("🎯 Create chain command")
        return response
    
    # ADD TO LIST
    if re.search(rf"(?:{add_pattern})\s+(?:to\s+)?(?:{list_target_pattern})", text, re.IGNORECASE):
        response["player"] = "add_to_list"
        response["type"] = "chain"
        print("🎯 Add to list command")
        return response
    
    # SET TITLE
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

    # SAVE CHAIN
    if re.search(r"save\s+chain", text):
        response["player"] = "save_chain"
        response["type"] = "chain"
        return response

    # REMOVE LAST
    if re.search(r"remove\s+last", text) or re.search(r"last\s+hatayo", text):
        response["player"] = "remove_last"
        response["type"] = "chain"
        return response

    # CLEAR ALL
    if re.search(r"clear\s+all", text) or re.search(r"sab\s+hatayo", text):
        response["player"] = "clear_all"
        response["type"] = "chain"
        return response

    # SHOW LIST
    if re.search(r"show\s+list", text) or re.search(r"list\s+dikhao", text):
        response["player"] = "show_list"
        response["type"] = "chain"
        return response

    # CANCEL CHAIN
    if re.search(r"cancel\s+chain", text) or re.search(r"chain\s+cancel", text):
        response["player"] = "cancel_chain"
        response["type"] = "chain"
        return response
        
    # DELETE CHAIN
    chain_keywords_pattern = "|".join(re.escape(kw) for kw in CHAIN_KEYWORDS)
    delete_chain_match = re.search(
        rf"(?:delete|remove|hatao)\s+(?:{chain_keywords_pattern})\s+(\w+(?:\s+\w+)?)",
        text, re.IGNORECASE
    )
    if delete_chain_match:
        response["player"] = "delete_chain"
        response["type"] = "chain"
        response["chainName"] = delete_chain_match.group(1).strip()
        print(f"🗑️ Delete chain matched: {response['chainName']}")
        return response

    # DELETE ALL CHAINS
    if re.search(r"delete\s+all\s+chains", text) or re.search(r"sab\s+chains\s+hatao", text):
        response["player"] = "delete_all_chains"
        response["type"] = "chain"
        return response


    # ============================================================
    # SECTION 5: BAYAN COMMANDS (connected to data.py)
    # ============================================================

    # Build dynamic regex parts from data.py
    bayan_trigger_pattern = "|".join(re.escape(w) for w in BAYAN_TRIGGER_WORDS)
    bayan_action_pattern = "|".join(re.escape(w) for w in BAYAN_ACTION_VERBS)
    bayan_index_keys = list(BAYAN_INDEX_MAP.keys())
    bayan_index_pattern = "|".join(re.escape(k) for k in bayan_index_keys)
    
    # 5.1 - Bayan by Ayat Number
    bayan_by_ayat = re.search(
        rf"(?:{bayan_action_pattern})\s+(?:{bayan_trigger_pattern})\s+([a-z]+)\s+ayat\s+(\d+)",
        text, re.IGNORECASE
    )
    if bayan_by_ayat:
        surah_name = bayan_by_ayat.group(1)
        ayat_number = int(bayan_by_ayat.group(2))
        surah_id = find_surah_id(surah_name)
        
        if surah_id:
            response["player"] = "play"
            response["type"] = "bayan"
            response["surahId"] = surah_id
            response["requestedAyat"] = ayat_number
            response = _add_bayan_details(response)
            print(f"🎤 Bayan by ayat: {surah_name} ayat {ayat_number}")
            return response
        else:
            print(f"❌ Surah not found: {surah_name}")
            return response
    
    # 5.2 - Bayan with index (first, second, ...)
    bayan_with_index = re.search(
        rf"(?:{bayan_action_pattern})\s+(?:{bayan_trigger_pattern})\s+([a-z]+)\s+({bayan_index_pattern})",
        text, re.IGNORECASE
    )
    if not bayan_with_index:
        # Alternative order: "bayan play fatiha first"
        bayan_with_index = re.search(
            rf"(?:{bayan_trigger_pattern})\s+(?:{bayan_action_pattern})\s+([a-z]+)\s+({bayan_index_pattern})",
            text, re.IGNORECASE
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
            response = _add_bayan_details(response)
            print(f"🎤 Bayan with index: {surah_name} → index {bayan_index}")
            return response
        else:
            print(f"❌ Surah not found: {surah_name}")
            return response
    
    # 5.3 - Simple bayan (no index, no ayat number)
    bayan_match = re.search(
        rf"(?:{bayan_action_pattern})\s+(?:{bayan_trigger_pattern})\s+([a-z]+)",
        text, re.IGNORECASE
    )
    if not bayan_match:
        bayan_match = re.search(
            rf"(?:{bayan_trigger_pattern})\s+(?:{bayan_action_pattern})\s+([a-z]+)",
            text, re.IGNORECASE
        )
    
    if bayan_match:
        surah_name = bayan_match.group(1)
        surah_id = find_surah_id(surah_name)
        if surah_id:
            response["player"] = "play"
            response["type"] = "bayan"
            response["surahId"] = surah_id
            response["bayanIndex"] = 0
            response = _add_bayan_details(response)
            print(f"🎤 Bayan (first/default): {surah_name}")
            return response
        else:
            print(f"❌ Surah not found: {surah_name}")
            return response
    
    # 5.4 - Introduction bayan
    if re.search(r"introduction\s+to\s+quran", text) or re.search(r"intro\s+bayan", text):
        response["player"] = "play"
        response["type"] = "bayan"
        response["surahId"] = 0
        response["bayanIndex"] = 0
        response["bayanTitle"] = "Introduction to Quran"
        response["bayanUrl"] = f"{BASE_IP}/audio/Dr_Israr/intro.mp3"
        print("🎤 Introduction bayan")
        return response


    # ============================================================
    # SECTION 6: CHAIN PLAY
    # ============================================================
    
    # Build regex from CHAIN_KEYWORDS
    chain_pattern = "|".join(re.escape(kw) for kw in CHAIN_KEYWORDS)
    play_chain_match = re.search(rf"(?:play|sunao|chalao)\s+(?:{chain_pattern})\s+(\w+(?:\s+\w+)?)", text)
    if play_chain_match:
        response["player"] = "play_chain"
        response["type"] = "chain"
        response["chainName"] = play_chain_match.group(1).strip()
        return response
    
    # Also for reverse pattern: "daily chain play"
    alt_match = re.search(r"(\w+(?:\s+\w+)?)\s+(?:{chain_pattern})\s+(?:play|sunao|chalao)", text)
    if alt_match:
        response["player"] = "play_chain"
        response["type"] = "chain"
        response["chainName"] = alt_match.group(1).strip()
        return response


    # ============================================================
    # SECTION 6.5: RESUME SPECIFIC CONTENT
    # ============================================================
    
    # 1. Resume Bayan -> Treat as Play Bayan
    bayan_trigger_pattern = "|".join(re.escape(w) for w in BAYAN_TRIGGER_WORDS)
    resume_bayan_match = re.search(rf"resume\s+(?:{bayan_trigger_pattern})\s+([a-z]+)", text, re.IGNORECASE)
    if resume_bayan_match:
        surah_name = resume_bayan_match.group(1)
        surah_id = find_surah_id(surah_name)
        if surah_id:
            response["player"] = "play"
            response["type"] = "bayan"
            response["surahId"] = surah_id
            response["bayanIndex"] = 0
            response = _add_bayan_details(response)
            print(f"🎤 Resume Bayan (treated as play): {surah_name}")
            return response

    # 2. Resume Chain -> Treat as Play Chain
    resume_chain_match = re.search(rf"resume\s+(?:{chain_pattern})\s+(\w+(?:\s+\w+)?)", text, re.IGNORECASE)
    if resume_chain_match:
        response["player"] = "play_chain"
        response["type"] = "chain"
        response["chainName"] = resume_chain_match.group(1).strip()
        print(f"🎤 Resume Chain (treated as play): {response['chainName']}")
        return response

    # 3. Resume Specific Surah
    resume_surah_match = re.search(r"resume\s+(?:surah\s+)?([a-z]+(?:\s+[a-z]+)?)", text, re.IGNORECASE)
    if resume_surah_match:
        target_name = resume_surah_match.group(1).strip()
        surah_id = find_surah_id(target_name)
        if surah_id:
            pos = _get_resume_position(surah_id)
            if pos > 0:
                response["player"] = "resume_surah"
                response["type"] = "surah"
                response["surah"] = surah_id
                response["resumeIndex"] = pos
                response = _add_surah_name(response)
                print(f"🎯 Resume Surah: {target_name} from index {pos}")
                return response
            else:
                response["player"] = "no_resume_found"
                response["surahName"] = target_name
                print(f"⚠️ No resume found for: {target_name}")
                return response

    # ============================================================
    # SECTION 7: QURAN PLAYBACK (5 patterns – fully data‑driven)
    # ============================================================
    
    # Build dynamic patterns from data.py
    play_keywords = "|".join(re.escape(kw) for kw in COMMANDS["play"])
    from_pattern = "|".join(re.escape(kw) for kw in FROM_KEYWORDS)
    range_pattern = "|".join(re.escape(kw) for kw in RANGE_CONNECTORS)
    end_pattern = "|".join(re.escape(kw) for kw in END_KEYWORDS)
    ayat_word = AYAT_WORD

    # Pattern 1: "play fatiha from ayat 2"  → from 2 to end
    pattern1 = re.search(
        rf"(?:{play_keywords})\s+([a-z]+)\s+(?:{from_pattern})\s+{ayat_word}\s+(\d+)",
        text, re.IGNORECASE
    )
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
            response = _add_surah_name(response)
            print(f"🎯 Quran: {surah_name} from ayat {from_ayat} to end")
            return response

    # Pattern 2: "play fatiha from ayat 1 to 5"  → specific range
    pattern2 = re.search(
        rf"(?:{play_keywords})\s+([a-z]+)\s+(?:{from_pattern})\s+{ayat_word}\s+(\d+)\s+(?:{range_pattern})\s+{ayat_word}\s+(\d+)",
        text, re.IGNORECASE
    )
    if not pattern2:
        pattern2 = re.search(
            rf"(?:{play_keywords})\s+([a-z]+)\s+{ayat_word}\s+(\d+)\s+(?:{range_pattern})\s+(\d+)",
            text, re.IGNORECASE
        )
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
            response = _add_surah_name(response)
            print(f"🎯 Quran: {surah_name} from ayat {from_ayat} to {to_ayat}")
            return response

    # Pattern 3: "play fatiha ayat 3"  → single ayat
    pattern3 = re.search(
        rf"(?:{play_keywords})\s+([a-z]+)\s+{ayat_word}\s+(\d+)",
        text, re.IGNORECASE
    )
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
            response = _add_surah_name(response)
            print(f"🎯 Quran single ayat: {surah_name} ayat {ayat_num}")
            return response

    # Pattern 4: "play fatiha to ayat 5"  → from 1 to 5
    pattern4 = re.search(
        rf"(?:{play_keywords})\s+([a-z]+)\s+(?:{range_pattern}|{end_pattern})\s+{ayat_word}\s+(\d+)",
        text, re.IGNORECASE
    )
    if not pattern4:
        pattern4 = re.search(
            rf"(?:{play_keywords})\s+([a-z]+)\s+tak\s+{ayat_word}\s+(\d+)",
            text, re.IGNORECASE
        )
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
            response = _add_surah_name(response)
            print(f"🎯 Quran: {surah_name} from start to ayat {to_ayat}")
            return response

    # Pattern 5: "play fatiha"  → full surah
    pattern5 = re.search(
        rf"(?:{play_keywords})\s+([a-z]+)$",
        text, re.IGNORECASE
    )
    if pattern5:
        surah_name = pattern5.group(1)
        surah_id = find_surah_id(surah_name)
        if surah_id:
            response["player"] = "play"
            response["type"] = "surah"
            response["surah"] = surah_id
            response["from"] = 1
            response["to"] = None
            response = _add_surah_name(response)
            print(f"🎯 Quran full surah: {surah_name}")
            return response


    # ============================================================
    # SECTION 8: NEXT/PREVIOUS SURAH NAVIGATION
    # ============================================================
    
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


    # ============================================================
    # SECTION 8.5: APP NAVIGATION (History, etc.)
    # ============================================================

    match = re.search(r"(?:show|open|display|dekhao|dikhao)\s+(?:(surah|bayan|chain)\s+)?(?:history|record)", text, re.IGNORECASE)
    if match:
        response["player"] = "show_history"
        filter_type = match.group(1)
        if filter_type:
            response["filter"] = filter_type.lower()
        print(f"🎯 Show History command (Filter: {response.get('filter', 'All')})")
        return response

    # ============================================================
    # SECTION 9: STANDARD PLAYER CONTROLS
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
    # SECTION 10: FALLBACK SURAH DETECTION
    # ============================================================
    
    if response["player"] not in SKIP_ACTIONS and response["player"] is None:
        text_for_surah = text
        
        for action, keywords in COMMANDS.items():
            if action in PLAYER_COMMANDS:
                for word in keywords:
                    text_for_surah = re.sub(rf"\b{re.escape(word)}\b", "", text_for_surah)
        
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


    # ============================================================
    # SECTION 11: NUMBERS EXTRACTION
    # ============================================================
    
    numbers = [int(n) for n in re.findall(r"\b\d+\b", text)]
    if response["player"] == "jump" and len(numbers) >= 1:
        response["ayatNumber"] = numbers[0]
    elif len(numbers) >= 1 and not response.get("from"):
        response["from"] = numbers[0]
    if len(numbers) >= 2 and not response.get("to"):
        response["to"] = numbers[1]


    # ============================================================
    # SECTION 12: FINAL RETURN
    # ============================================================
    
    return response
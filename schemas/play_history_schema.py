# schemas/play_history_schema.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# ============================================================
# 1. Request Schema for Tracking Play (UPDATED - Simple INSERT)
# ============================================================
class TrackPlaySchema(BaseModel):
    profileId: int
    content_type: str                     # 'surah', 'bayan', 'chain'
    content_id: int
    range_start: int = 1
    range_end: Optional[int] = None
    current_position: int = 0
    # REMOVED: increment field - ab zaroorat nahi
    # NEW FIELDS:
    voice_mode: int = 0                   # 1 = voice command, 0 = manual
    completed: int = 0                    # 1 = fully completed
    duration_seconds: int = 0             # listening duration


# ============================================================
# 2. Base Item Schema (UPDATED - for responses)
# ============================================================
class PlayHistoryItem(BaseModel):
    id: int
    profileId: int
    content_type: str
    content_id: int
    range_start: int
    range_end: Optional[int]
    current_position: int
    played_at: datetime
    # REMOVED: play_count field (ab query se COUNT karna hai)
    # NEW FIELDS:
    voice_mode: int = 0
    completed: int = 0
    duration_seconds: int = 0
    name: Optional[str] = None            # e.g., "Al-Fatihah"
    subtitle: Optional[str] = None        # e.g., "الفاتحة" or scholar name
    image: Optional[str] = None


# ============================================================
# 3. Response for Last Played Items (list) - UPDATED
# ============================================================
class LastPlayedItemsResponse(BaseModel):
    status: str
    items: List[PlayHistoryItem]


# ============================================================
# 4. Response for Resume Position - UPDATED
# ============================================================
class ResumePositionResponse(BaseModel):
    status: str
    position: int                         # current_position (ayat index or seconds)
    range_start: int
    range_end: Optional[int]
    last_played: Optional[str] = None     # NEW: when it was last played


# ============================================================
# 5. Response for Most Played Surah / Bayan / Chain - UPDATED
# ============================================================
class MostPlayedResponse(BaseModel):
    status: str
    content_id: int
    play_count: int                       # COUNT(*) from query
    name: str
    subtitle: Optional[str] = None


# ============================================================
# 6. Response for Last 4 Surahs Only (filtered by type)
# ============================================================
class LastPlayedByTypeResponse(BaseModel):
    status: str
    items: List[PlayHistoryItem]


# ============================================================
# 7. NEW: Response for Play Count (for individual item)
# ============================================================
class PlayCountResponse(BaseModel):
    status: str
    content_type: str
    content_id: int
    play_count: int                       # COUNT(*) from history
    last_played: Optional[str] = None
    total_duration: Optional[int] = 0     # sum of duration_seconds


# ============================================================
# 8. NEW: Request Schema for Date Range Query
# ============================================================
class DateRangeRequest(BaseModel):
    profileId: int
    content_type: Optional[str] = None
    content_id: Optional[int] = None
    start_date: Optional[str] = None      # '2024-01-01'
    end_date: Optional[str] = None        # '2024-12-31'


# ============================================================
# 9. NEW: Response for Analytics Summary
# ============================================================
class AnalyticsSummaryResponse(BaseModel):
    status: str
    profileId: int
    total_plays: int                      # Total number of plays
    total_surah_plays: int
    total_chain_plays: int
    total_bayan_plays: int
    total_voice_plays: int
    total_completed_plays: int
    total_duration_seconds: int
    most_played_surah: Optional[MostPlayedResponse] = None
    most_played_chain: Optional[MostPlayedResponse] = None
    most_played_bayan: Optional[MostPlayedResponse] = None
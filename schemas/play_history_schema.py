# schemas/play_history_schema.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# ============================================================
# 1. Request Schema for Tracking Play
# ============================================================
class TrackPlaySchema(BaseModel):
    profileId: int
    content_type: str                     # 'surah', 'bayan', 'chain'
    content_id: int
    range_start: int = 1
    range_end: Optional[int] = None
    current_position: int = 0
    increment: bool = True                # Increase play_count? True for new play, False for position update

# ============================================================
# 2. Base Item Schema (used in responses)
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
    play_count: int
    name: Optional[str] = None            # e.g., "Al-Fatihah"
    subtitle: Optional[str] = None        # e.g., "الفاتحة" or scholar name
    image: Optional[str] = None

# ============================================================
# 3. Response for Last Played Items (list)
# ============================================================
class LastPlayedItemsResponse(BaseModel):
    status: str
    items: List[PlayHistoryItem]

# ============================================================
# 4. Response for Resume Position
# ============================================================
class ResumePositionResponse(BaseModel):
    status: str
    position: int                         # current_position (ayat index or seconds)
    range_start: int
    range_end: Optional[int]

# ============================================================
# 5. Response for Most Played Surah / Bayan / Chain
# ============================================================
class MostPlayedResponse(BaseModel):
    status: str
    content_id: int
    play_count: int
    name: str
    subtitle: Optional[str] = None

# ============================================================
# 6. Response for Last 4 Surahs Only (filtered by type)
# ============================================================
class LastPlayedByTypeResponse(BaseModel):
    status: str
    items: List[PlayHistoryItem]
from typing import Literal, Optional, TypedDict


class AutoTagRule(TypedDict, total=False):
    key: str  # Full redis-like path
    values: list[str]  # List of accepted values
    prepend_string: Optional[str]
    append_string: Optional[str]
    bookmark_hierarchy: Optional[
        Literal["t1", "t2", "t3"]
    ]  # TODO(KERCH): Implement later. Fine for now.
    is_enabled: bool
    true_string: Optional[str]
    false_string: Optional[str]
    undefined_string: Optional[str]
    is_unique: bool


AUTO_TAG_CONFIG: list[AutoTagRule] = [
    {
        "key": "game:marvel_rivals:session:DEV_SESSION_ID:game_state:screen_statuses:current_screen_name",
        "is_enabled": True,
        "is_unique": True,
    },
    {
        "key": "game:marvel_rivals:session:DEV_SESSION_ID:game_state:map_battle_mode_statuses:team_objective_control_state",
        "is_enabled": True,
    },
    {
        "key": "game:marvel_rivals:session:DEV_SESSION_ID:game_state:map_battle_mode_statuses:battle_timeline_phase",
        "is_enabled": True,
    },
    {
        "key": "game:marvel_rivals:session:DEV_SESSION_ID:game_state:map_battle_mode_statuses:team_attack_or_defend",
        "is_enabled": True,
    },
    {
        "key": "game:marvel_rivals:session:DEV_SESSION_ID:game_state:map_battle_mode_statuses:game_mode_name",
        "is_enabled": True,
    },
    {
        "key": "game:marvel_rivals:session:DEV_SESSION_ID:game_state:map_battle_mode_statuses:map_battle_mode_name",
        "is_enabled": True,
    },
    {
        "key": "game:marvel_rivals:session:DEV_SESSION_ID:game_state:map_battle_mode_statuses:stage_name",
        "is_enabled": True,
    },
    {
        "key": "game:marvel_rivals:session:DEV_SESSION_ID:game_state:map_battle_mode_statuses:stage_location_name",
        "is_enabled": True,
    },
    {
        "key": "game:marvel_rivals:session:DEV_SESSION_ID:game_state:map_battle_mode_statuses:final_victory_or_defeat",
        "is_enabled": True,
        "true_string": "victory",
        "false_string": "defeat",
    },
]

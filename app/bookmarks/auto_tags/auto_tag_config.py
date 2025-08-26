from typing import Literal, NotRequired, TypedDict


class AutoTagRule(TypedDict):
    key: str  # Full redis-like path
    values: NotRequired[list[str]]
    prepend_string: NotRequired[str]
    append_string: NotRequired[str]
    bookmark_hierarchy: NotRequired[
        Literal["t1", "t2", "t3"]
    ]  # TODO(KERCH): Implement later. Fine for now.
    is_enabled: bool
    true_string: NotRequired[str]
    false_string: NotRequired[str]
    undefined_string: NotRequired[str]
    is_unique: NotRequired[bool]


AUTO_TAG_CONFIG: list[AutoTagRule] = [
    {
        "key": "game:marvel_rivals:session:DEV_SESSION_ID:game_state:screen_statuses:current_screen_name",
        "is_enabled": True,
        "is_unique": True,
    },
    {
        "key": "game:marvel_rivals:session:DEV_SESSION_ID:game_state:map_battle_mode_statuses:team_objective_control_state",
        "is_enabled": True,
        # "bookmark_hierarchy": "t2",
    },
    {
        "key": "game:marvel_rivals:session:DEV_SESSION_ID:game_state:map_battle_mode_statuses:battle_timeline_phase",
        "is_enabled": True,
        "bookmark_hierarchy": "t2",
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
        "true_string": "final_victory",
        "false_string": "final_defeat",
    },
]

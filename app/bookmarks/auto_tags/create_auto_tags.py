# app/bookmarks/auto_tags/create_auto_tags.py

from typing import List, Optional


def create_auto_tags(
    *,
    current_screen_name: Optional[str] = None,
    team_objective_control_state: Optional[str] = None,
    battle_timeline_phase: Optional[str] = None,
    team_attack_or_defend: Optional[str] = None,
    game_mode_name: Optional[str] = None,
    map_battle_mode_name: Optional[str] = None,
    stage_name: Optional[str] = None,
    stage_location_name: Optional[str] = None,
    final_victory_or_defeat: Optional[str] = None,
) -> List[str]:
    """
    Converts provided game state fields into a list of auto-tag strings,
    adding prefixes or suffixes as needed.
    """
    tags = []

    # Direct fields
    if current_screen_name:
        tags.append(current_screen_name)
    if team_objective_control_state:
        tags.append(team_objective_control_state)
    if battle_timeline_phase:
        tags.append(f"battle_phase_{battle_timeline_phase}")
    if team_attack_or_defend:
        tags.append(team_attack_or_defend)
    if game_mode_name:
        tags.append(game_mode_name)
    if map_battle_mode_name:
        tags.append(map_battle_mode_name)
    if stage_name:
        tags.append(stage_name)
    if stage_location_name:
        tags.append(stage_location_name)
    if final_victory_or_defeat:
        tags.append(f"final_{final_victory_or_defeat}")

    # (Optional: ensure tags are unique and alphabetized)
    tags = sorted(set(tags))
    return tags

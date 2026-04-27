MAIN_MENU = "main_menu"
SEARCH_MODE = "search_mode"

user_states: dict[int, str] = {}

def set_user_state(user_id: int, state: str) -> None:
    """
    Saves user's current bot state.
    """
    user_states[user_id] = state

def get_user_state(user_id: int) -> str:
    """
    Returns user's current bot state.
    Default state is main menu.
    """
    return user_states.get(user_id, MAIN_MENU)

def is_main_menu(user_id: int) -> bool:
    """
    Checks if user is currently in main menu.
    """
    return get_user_state(user_id) == MAIN_MENU
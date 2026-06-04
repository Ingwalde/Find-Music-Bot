from app.bot.constants import (
    ACTION_BACK_RESULTS,
    ACTION_SEARCH_AGAIN,
    CB_FAVORITE,
    CB_TRACK,
    CB_UNFAVORITE,
)
from app.bot.keyboards import (
    favorites_keyboard,
    genius_url_keyboard,
    history_keyboard,
    search_results_keyboard,
    track_actions_keyboard,
)


def flatten_buttons(markup):
    return [button for row in markup.keyboard for button in row]


def test_search_results_keyboard_has_track_buttons_and_pagination(sample_track):
    tracks = [
        sample_track | {"deezer_track_id": "1", "title": "Track 1"},
        sample_track | {"deezer_track_id": "2", "title": "Track 2"},
    ]

    markup = search_results_keyboard(tracks=tracks, page=0, total_pages=2)
    buttons = flatten_buttons(markup)

    assert buttons[0].callback_data == f"{CB_TRACK}:1"
    assert buttons[1].callback_data == f"{CB_TRACK}:2"
    assert any(button.text == "Next ➡️" for button in buttons)


def test_track_actions_keyboard_add_favorite_state(sample_track):
    markup = track_actions_keyboard(
        sample_track,
        is_favorite=False,
        show_back_to_results=True,
    )
    buttons = flatten_buttons(markup)

    assert any(button.text == "🎧 Deezer" for button in buttons)
    assert any(button.callback_data == ACTION_BACK_RESULTS for button in buttons)
    assert any(button.callback_data == f"{CB_FAVORITE}:671298" for button in buttons)
    assert any(button.callback_data == ACTION_SEARCH_AGAIN for button in buttons)


def test_track_actions_keyboard_remove_favorite_state(sample_track):
    markup = track_actions_keyboard(sample_track, is_favorite=True)
    buttons = flatten_buttons(markup)

    assert any(button.callback_data == f"{CB_UNFAVORITE}:671298" for button in buttons)


def test_favorites_keyboard_has_clear_button(sample_track):
    markup = favorites_keyboard([sample_track])
    buttons = flatten_buttons(markup)

    assert any(button.callback_data == "track:671298" for button in buttons)
    assert any(button.callback_data == "favorites_clear_request" for button in buttons)


def test_history_keyboard_has_clear_button():
    history = [{"id": 1, "query": "American Pie"}]

    markup = history_keyboard(history)
    buttons = flatten_buttons(markup)

    assert any(button.callback_data == "hist:1" for button in buttons)
    assert any(button.callback_data == "history_clear_request" for button in buttons)


def test_genius_url_keyboard_uses_language():
    markup = genius_url_keyboard("https://genius.com/test", language="uk")
    buttons = flatten_buttons(markup)

    assert buttons[0].text == "📖 Відкрити текст на Genius"
    assert buttons[0].url == "https://genius.com/test"

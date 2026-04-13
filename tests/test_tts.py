from unittest.mock import patch, MagicMock


def test_speak_falls_back_to_platform_fallback_on_edge_tts_failure():
    from jarvis_launcher import tts
    with patch("jarvis_launcher.tts._speak_edge_tts", side_effect=Exception("no internet")), \
         patch("jarvis_launcher.tts._speak_fallback") as mock_fallback:
        tts.speak("Hello sir")
        mock_fallback.assert_called_once_with("Hello sir")


def test_speak_edge_tts_is_called_first():
    from jarvis_launcher import tts
    with patch("jarvis_launcher.tts._speak_edge_tts") as mock_edge, \
         patch("jarvis_launcher.tts._speak_fallback") as mock_fallback:
        tts.speak("Hello sir", voice="en-GB-RyanNeural")
        mock_edge.assert_called_once_with("Hello sir", "en-GB-RyanNeural")
        mock_fallback.assert_not_called()

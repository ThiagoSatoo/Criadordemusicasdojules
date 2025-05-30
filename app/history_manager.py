import json
import os
from datetime import datetime

# Define the path for the history file.
# Using os.path.join for cross-platform compatibility.
# Storing in the 'instance' folder is common for user-specific data not part of the app's core code.
INSTANCE_FOLDER_PATH = os.path.join(os.path.dirname(__file__), '..', 'instance')
HISTORY_FILE_PATH = os.path.join(INSTANCE_FOLDER_PATH, 'generation_history.json')
MAX_HISTORY_ITEMS = 50 # Max number of entries to keep

def _ensure_instance_folder():
    """Ensures the instance folder exists."""
    if not os.path.exists(INSTANCE_FOLDER_PATH):
        try:
            os.makedirs(INSTANCE_FOLDER_PATH)
        except OSError as e:
            print(f"Error creating instance folder at {INSTANCE_FOLDER_PATH}: {e}")
            # Depending on the app's needs, you might raise this or handle it differently
            raise

def load_history():
    """
    Loads music generation history from the JSON file.

    Returns:
        A list of history entries (dictionaries), or an empty list if the file doesn't exist or is invalid.
    """
    _ensure_instance_folder() # Ensure the folder exists before trying to read
    if not os.path.exists(HISTORY_FILE_PATH):
        return []

    try:
        with open(HISTORY_FILE_PATH, 'r', encoding='utf-8') as f:
            history = json.load(f)
            if not isinstance(history, list): # Basic validation
                print("History file content is not a list. Starting fresh.")
                return []
            return history
    except json.JSONDecodeError:
        print(f"Error decoding JSON from {HISTORY_FILE_PATH}. File might be corrupted. Starting fresh.")
        return []
    except IOError as e:
        print(f"Error reading history file {HISTORY_FILE_PATH}: {e}")
        return []

def save_history_entry(original_prompt: str, voice: str, rhythm: str,
                       constructed_prompt: str, song_name: str, audio_url: str,
                       response_data: dict):
    """
    Adds a new entry to the music generation history and saves it.

    Args:
        original_prompt: The initial prompt from the user.
        voice: Selected voice.
        rhythm: Selected rhythm.
        constructed_prompt: The full prompt sent to the API.
        song_name: Name of the generated song (if available).
        audio_url: URL of the generated audio.
        response_data: The full JSON response from the API (for reference/debugging).
    """
    _ensure_instance_folder() # Ensure the folder exists before trying to write
    history = load_history()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_entry = {
        "id": timestamp + "_" + str(len(history) + 1), # Simple unique ID
        "timestamp": timestamp,
        "original_prompt": original_prompt,
        "voice": voice,
        "rhythm": rhythm,
        "constructed_prompt": constructed_prompt, # The prompt actually sent to API
        "song_name": song_name or "Não especificado",
        "audio_url": audio_url,
        "api_response_preview": { # Storing a preview, not the whole potentially massive response
            "model": response_data.get("model"),
            "id": response_data.get("id"),
            "usage": response_data.get("usage")
        }
        # Consider if you want to store more or less of response_data
    }

    history.insert(0, new_entry) # Add new entries to the beginning

    # Limit the number of history items
    if len(history) > MAX_HISTORY_ITEMS:
        history = history[:MAX_HISTORY_ITEMS]

    try:
        with open(HISTORY_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=4, ensure_ascii=False)
        print(f"Successfully saved history entry to {HISTORY_FILE_PATH}")
    except IOError as e:
        print(f"Error writing history file {HISTORY_FILE_PATH}: {e}")
    except TypeError as e:
        print(f"Error serializing history data to JSON: {e}")

if __name__ == '__main__':
    # Example usage (for testing the module directly)
    print("History Manager Module")
    print(f"Instance folder: {INSTANCE_FOLDER_PATH}")
    print(f"History file: {HISTORY_FILE_PATH}")

    # Test ensure_instance_folder
    _ensure_instance_folder()

    # Test saving an entry
    test_response = {"model": "meta-llama/llama-3-8b-instruct", "id": "test_id_123", "usage": {"prompt_tokens": 10, "completion_tokens": 20}}
    save_history_entry(
        original_prompt="A happy folk song about a river",
        voice="Feminina",
        rhythm="Pop",
        constructed_prompt="Crie uma música no ritmo Pop com voz Feminina sobre: A happy folk song about a river. A música deve ter no máximo 2 minutos de duração.",
        song_name="River's Joy",
        audio_url="http://example.com/music/rivers_joy.mp3",
        response_data=test_response
    )

    # Test loading history
    loaded_hist = load_history()
    print(f"\nLoaded {len(loaded_hist)} history entries.")
    if loaded_hist:
        print("Last entry:")
        print(json.dumps(loaded_hist[0], indent=2, ensure_ascii=False))

    # Example of how to clear history for testing (manual step)
    # if os.path.exists(HISTORY_FILE_PATH):
    #     os.remove(HISTORY_FILE_PATH)
    #     print("\nCleared history file for next test run.")

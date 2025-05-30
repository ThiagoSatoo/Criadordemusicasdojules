import requests
import json

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
LLAMA3_MODEL = "meta-llama/llama-3-8b-instruct" # Example Llama3 model

def generate_music_from_prompt(prompt: str, api_key: str):
    """
    Generates music data by sending a prompt to the OpenRouter API using the Llama3 model.

    Args:
        prompt: The user's text prompt for music generation.
        api_key: The user's OpenRouter API key.

    Returns:
        A dictionary containing the API response or an error message.
    """
    if not api_key:
        return {"error": "API key is missing."}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Constructing the payload for the Llama3 model.
    # This will likely need to be adjusted based on how Llama3 expects music generation prompts.
    # For now, using a standard chat completion structure.
    payload = {
        "model": LLAMA3_MODEL,
        "messages": [
            {"role": "user", "content": f"Generate music based on the following prompt: {prompt}"}
            # Potentially add system messages or more structured content if required by the model for music.
        ]
    }

    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, data=json.dumps(payload), timeout=30)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)

        # Assuming the response contains JSON data with the generated music or relevant info.
        # The actual structure of this response will depend on the OpenRouter API and Llama3's output for music.
        return response.json()

    except requests.exceptions.HTTPError as http_err:
        # Handle specific HTTP errors if needed (e.g., 401 for invalid API key)
        if response.status_code == 401:
            return {"error": "Invalid API key. Please check your credentials."}
        return {"error": f"HTTP error occurred: {http_err} - {response.text}"}
    except requests.exceptions.RequestException as req_err:
        # Handle other request errors (e.g., network issues)
        return {"error": f"Request error occurred: {req_err}"}
    except json.JSONDecodeError:
        return {"error": "Failed to decode API response. Response was not valid JSON."}

if __name__ == '__main__':
    # This is a simple test. Replace 'YOUR_API_KEY' with a real key and a prompt.
    # Note: Running this directly requires an API key.
    print("This script is intended to be used as a module.")
    # test_api_key = "YOUR_API_KEY"
    # test_prompt = "A melancholic piano piece in A minor."
    # if test_api_key == "YOUR_API_KEY":
    #     print("Please replace 'YOUR_API_KEY' with your actual OpenRouter API key to test.")
    # else:
    #     print(f"Testing with prompt: '{test_prompt}'")
    #     result = generate_music_from_prompt(test_prompt, test_api_key)
    #     print("API Response:")
    #     print(json.dumps(result, indent=2))

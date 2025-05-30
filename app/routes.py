from flask import render_template, request, flash, url_for, redirect
from app import app
import config
import os
from app.music_generator import generate_music_from_prompt
from app.history_manager import save_history_entry, load_history

# Helper function to update the config.py file
def update_config_file(key, value):
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.py')
    lines = []
    found = False
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            lines = f.readlines()
    with open(config_path, 'w') as f:
        for line in lines:
            if line.strip().startswith(key + " ="):
                f.write(f"{key} = '{value}'\n")
                found = True
            else:
                f.write(line)
        if not found:
            f.write(f"{key} = '{value}'\n")

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    prompt_text = ""
    response_data = None
    error_message = None
    audio_url = None
    song_name = None
    # Default selections for GET request
    voice_selection = "Instrumental"
    rhythm_selection = "Pop"
    music_duration_selection = 120 # Default duration for GET
    main_instrument_selection = "" # Default for GET

    if request.method == 'POST':
        original_prompt = request.form.get('prompt')
        voice_selection = request.form.get('voice_selection', 'Instrumental')
        rhythm_selection = request.form.get('rhythm_selection', 'Pop')
        main_instrument_selection = request.form.get('main_instrument', '').strip()

        try:
            music_duration_selection = int(request.form.get('music_duration', 120))
            if not (30 <= music_duration_selection <= 300):
                flash("Duração inválida. Usando 120 segundos.", "warning")
                music_duration_selection = 120
        except ValueError:
            flash("Valor de duração inválido. Usando 120 segundos.", "warning")
            music_duration_selection = 120

        # Store original prompt for re-rendering the form
        prompt_text = original_prompt

        api_key = getattr(config, 'API_KEY', None)

        if not api_key:
            error_message = "Chave da API não configurada. Por favor, defina-a na página de Configurações."
            flash(error_message, 'error')
            return redirect(url_for('settings'))

        if not original_prompt:
            error_message = "O prompt original não pode estar vazio."
        else:
            prompt_parts = []

            # 1. Tipo de música e voz + Ritmo
            if voice_selection == "Instrumental":
                prompt_parts.append(f"Crie uma música instrumental no ritmo {rhythm_selection}")
            elif voice_selection == "revezando":
                prompt_parts.append(f"Crie uma música com vozes masculina e feminina se revezando, no ritmo {rhythm_selection}")
            else: # Feminina, Masculina
                prompt_parts.append(f"Crie uma música com voz {voice_selection.lower()} no ritmo {rhythm_selection}")

            # 2. Tema
            # Using f-string for clarity and explicit quotes around original_prompt
            prompt_parts.append(f"sobre o tema: \"{original_prompt}\".")

            # 3. Instrumento Principal (Opcional)
            if main_instrument_selection:
                prompt_parts.append(f"Dê destaque ao instrumento {main_instrument_selection}, se possível.")

            # 4. Duração
            prompt_parts.append(f"A música deve ter uma duração aproximada de {music_duration_selection} segundos.")

            detailed_prompt = " ".join(prompt_parts)

            print(f"Constructed prompt: {detailed_prompt}") # For debugging

            # Call the music generation function with the detailed prompt
            response_data = generate_music_from_prompt(detailed_prompt, api_key)

            if 'error' in response_data:
                error_message = response_data['error']
                # Check for specific API key error to give a more targeted message
                if "invalid api key" in error_message.lower() or "unauthorized" in error_message.lower() or "401" in error_message.lower():
                    error_message = "Erro na Chave da API: Verifique se sua chave da API do OpenRouter é válida e tente novamente. Você pode atualizá-la na página de Configurações."
                    flash(error_message, 'error') # flash this specific common error
            else:
                # Attempt to extract audio_url and song_name from various possible locations
                # This is speculative and depends on the actual API response structure
                if isinstance(response_data, dict):
                    audio_url = response_data.get("url") or \
                                response_data.get("audio_url") or \
                                response_data.get("output", {}).get("audio_url")

                    # More complex extraction if nested, e.g. in 'choices'
                    if not audio_url and "choices" in response_data and isinstance(response_data["choices"], list) and response_data["choices"]:
                        first_choice = response_data["choices"][0]
                        if isinstance(first_choice, dict) and "message" in first_choice and isinstance(first_choice["message"], dict):
                             content = first_choice["message"].get("content")
                             if isinstance(content, dict): # If content itself is a dict
                                 audio_url = content.get("audio_url") or content.get("url")
                             elif isinstance(content, str) and content.startswith("http"): # If content is a direct URL string
                                 audio_url = content

                    song_name = response_data.get("name") or \
                                response_data.get("song_name") or \
                                response_data.get("title")

                    if not song_name and "choices" in response_data and isinstance(response_data["choices"], list) and response_data["choices"]:
                        first_choice = response_data["choices"][0]
                        if isinstance(first_choice, dict) and "message" in first_choice and isinstance(first_choice["message"], dict):
                            content = first_choice["message"].get("content")
                            if isinstance(content, dict):
                                song_name = content.get("song_name") or content.get("title")

                if not audio_url:
                    error_message = "Resposta da API recebida, mas nenhuma URL de áudio foi encontrada. Exibindo resposta completa abaixo."
                    # flash(error_message, 'warning') # This is a good place for a warning flash
                else:
                    # Successfully got an audio_url, save to history
                    save_history_entry(
                        original_prompt=original_prompt,
                        voice=voice_selection,
                        rhythm=rhythm_selection,
                        main_instrument=main_instrument_selection,
                        music_duration=music_duration_selection,
                        constructed_prompt=detailed_prompt,
                        song_name=song_name,
                        audio_url=audio_url,
                        response_data=response_data
                    )
                    pass

    return render_template('index.html',
                           prompt_text=prompt_text,  # This is the original user prompt
                           response_data=response_data,
                           error_message=error_message,
                           audio_url=audio_url,
                           song_name=song_name,
                           voice_selection=voice_selection,
                           rhythm_selection=rhythm_selection,
                           music_duration_selection=music_duration_selection,
                           main_instrument_selection=main_instrument_selection)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    current_api_key = getattr(config, 'API_KEY', '')
    if request.method == 'POST':
        api_key_from_form = request.form.get('api_key')
        if api_key_from_form:
            update_config_file('API_KEY', api_key_from_form)
            config.API_KEY = api_key_from_form # Update in current session
            flash('Chave da API salva com sucesso!', 'success')
            print(f"API Key saved: {api_key_from_form}")
            current_api_key = api_key_from_form # Ensure the form shows the newly saved key
        else:
            flash('O campo da Chave da API não pode estar vazio.', 'error')
        # Always render template for settings, passing the most current key
        return render_template('settings.html', api_key=current_api_key)

    # For GET request, load the current API key to display
    return render_template('settings.html', api_key=current_api_key)

@app.route('/history')
def history():
    history_items = load_history()
    return render_template('history.html', history_items=history_items)

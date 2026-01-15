from google.cloud import texttospeech as tts
from pathlib import Path
from utils.files import get_file_text

tts_client = tts.TextToSpeechClient()


def main(text: str):
    text = get_file_text('script.txt')
    synthesis_input = tts.SynthesisInput(text=text)

    voice = tts.VoiceSelectionParams(
        language_code='en-US', ssml_gender=tts.SsmlVoiceGender.MALE
    )

    audio_config = tts.AudioConfig(
        audio_encoding=tts.AudioEncoding.MP3
    )

    response = tts_client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    with open('output.mp3', 'wb') as out:
        out.write(response.audio_content)
        print('Audio content written to file "output.mp3"')

if __name__=='__main__':
    main()
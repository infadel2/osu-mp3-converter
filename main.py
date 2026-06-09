import eel
import shutil
import yt_dlp
import os
import eyed3
import ffmpeg
import base64
import argparse
import time
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.io import wavfile

eel.init('public')

# delete pre-existing temp-folder and make a new one
temp_folder = Path('./temp')
if temp_folder.is_dir():
    shutil.rmtree(temp_folder)
temp_folder.mkdir(parents=True, exist_ok=False)
        
def close_callback(route, websockets):
    if not websockets:
        while True:
            time.sleep(5)

@eel.expose
def taskGen(youtube_link, metadata, spek):
    add_youtube_metadata = metadata
    generate_spectrogram = spek
    print('I: Starting task', youtube_link, 'with options', metadata, spek)
    start = time.perf_counter()

    # yt-dlp section (self explanatory, we also save brain power and lines with the ffmpeg postprocessor)
    defaults = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': str(temp_folder) + '/final',
    }
    try:
        with yt_dlp.YoutubeDL(defaults) as ydl:
            #ydl.download([youtube_link])
            info_dict = ydl.extract_info(youtube_link, download=True)
            video_id = info_dict.get('id')
            video_title = info_dict.get('title')
            video_artist = info_dict.get('uploader')
    except Exception as e:
        eel.catchErrorMessage(f"{e}")
        return
    os.rename(str(temp_folder) + '/final.mp3', str(temp_folder) + '/' + video_id + '.mp3')

    # eyed3 section (we use eyed3 here because ffmpeg sucks at handling comment metadata for some reason)
    audiofile = eyed3.load(str(temp_folder) + '/' +  video_id + '.mp3')
    if add_youtube_metadata:
        # this is disabled by default because it almost always sucks due to how ppl upload music to youtube
        audiofile.tag.artist = video_artist
        audiofile.tag.title = video_title
    audiofile.tag.comments.set('https://github.com/infadel2/osu-mp3-converter')
    audiofile.tag.save(version=(2, 3, 0)) # apparently 2.4 breaks windows id3 compatibility

    # generate a spectrogram (if the user wants)
    if generate_spectrogram:
        (
            ffmpeg
            .input(str(temp_folder) + '/' + video_id + '.mp3')
            .output(str(temp_folder) + '/' + video_id + '-spek.wav')
            .run()
        )
        sample_rate, audio_data = wavfile.read(str(temp_folder) + '/' + video_id + '-spek.wav')
        if len(audio_data.shape) > 1:
            audio_data = audio_data[:, 0]
        plt.style.use('dark_background')
        plt.figure(figsize=(10, 6))
        plt.specgram(audio_data, Fs=sample_rate, cmap='gist_heat', NFFT=1024, noverlap=512, vmin=40, vmax=-40)
        plt.title('generated spectrogram for ' + video_id)
        plt.ylabel('Hz')
        plt.xlabel('Time (sec)')
        plt.colorbar(label='Gain (dB)')
        plt.savefig(str(temp_folder) + '/' + video_id + '-spek.png', bbox_inches='tight', dpi=300)
        os.remove(str(temp_folder) + '/' + video_id + '-spek.wav')
        with open(str(temp_folder) + '/' + video_id + '-spek.png', "rb") as file:
            spek_data = base64.b64encode(file.read()).decode("utf-8")
        eel.showSpectrogram(spek_data)
        os.remove(str(temp_folder) + '/' + video_id + '-spek.png')
    with open(str(temp_folder) + '/' + video_id + '.mp3', "rb") as mp3_file:
        base64_string = base64.b64encode(mp3_file.read()).decode("utf-8")
    eel.startDownload(base64_string, video_id)
    end = time.perf_counter()
    print(f'I: {youtube_link} was successfully converted in {(end - start):.3f} seconds')
    os.remove(str(temp_folder) + '/' + video_id + '.mp3')

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--port", type=int, default=4444, help="Port you want the server to serve to")
print('I: Server running on localhost:' + str(parser.parse_args().port))
eel.start('index.html', mode=None, block=True, host='localhost', port=parser.parse_args().port, close_callback=close_callback)
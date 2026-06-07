import eel
eel.init('public')
# delete pre-existing temp-folder and make a new one
from pathlib import Path
import shutil
temp_folder = Path('./temp')
if temp_folder.is_dir():
    shutil.rmtree(temp_folder)
temp_folder.mkdir(parents=True, exist_ok=False)
@eel.expose
def taskGen(youtube_link, md_serv, md_yt, spek):
    add_post_metadata = md_serv
    add_youtube_metadata = md_yt
    generate_spectrogram = spek
    print('I: Starting task', youtube_link, 'with options', md_serv, md_yt, spek)

    # yt-dlp section (self explanatory, we also save
    # brain power and lines with the ffmpeg postprocessor)
    import yt_dlp
    import os
    defaults = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': str(temp_folder) + '/final',
    }
    with yt_dlp.YoutubeDL(defaults) as ydl:
        #ydl.download([youtube_link])
        info_dict = ydl.extract_info(youtube_link, download=True)
        video_id = info_dict.get('id')
        video_title = info_dict.get('title')
        video_artist = info_dict.get('uploader')
    os.rename(str(temp_folder) + '/final.mp3', str(temp_folder) + '/' + video_id + '.mp3')

    # eyed3 section (we use eyed3 here because ffmpeg sucks
    # at handling comment metadata for some reason)
    if add_post_metadata:
        import eyed3
        audiofile = eyed3.load(str(temp_folder) + '/' +  video_id + '.mp3')
        if add_youtube_metadata:
            # this is disabled by default because it almost always
            # sucks due to how ppl upload music to youtube
            audiofile.tag.artist = video_artist
            audiofile.tag.title = video_title
            audiofile.tag.album = video_title
        audiofile.tag.comments.set('check out https://github.com/infadel2/osu-mp3-converter')
        audiofile.tag.save(version=(2, 3, 0)) # apparently 2.4 breaks windows id3 compatibility

    # generate a spectrogram (if the user wants)
    if generate_spectrogram:
        import ffmpeg
        import numpy as np
        import matplotlib.pyplot as plt
        from scipy.io import wavfile
        (
            ffmpeg
            .input(str(temp_folder) + '/' + video_id + '.mp3')
            .output(str(temp_folder) + '/' + video_id + '-spek.wav')
            .run()
        )
        sample_rate, audio_data = wavfile.read(str(temp_folder) + '/' + video_id + '-spek.wav')
        if len(audio_data.shape) > 1:
            audio_data = audio_data[:, 0]
        plt.figure(figsize=(10, 6))
        plt.specgram(audio_data, Fs=sample_rate, cmap='gist_heat', NFFT=1024, noverlap=512, vmin=40, vmax=-40)
        plt.title('generated spectrogram for ' + video_id)
        plt.ylabel('Hz')
        plt.xlabel('Time (sec)')
        plt.colorbar(label='Gain (dB)')
        plt.savefig(str(temp_folder) + '/' + video_id + '-spek.png', bbox_inches='tight', dpi=300)
        os.remove(str(temp_folder) + '/' + video_id + '-spek.wav')
        with open(str(temp_folder) + '/' + video_id + '-spek.png', "rb") as file:
            import base64
            spek_data = base64.b64encode(file.read()).decode("utf-8")
        eel.showSpectrogram(spek_data)
        os.remove(str(temp_folder) + '/' + video_id + '-spek.png')
    with open(str(temp_folder) + '/' + video_id + '.mp3', "rb") as mp3_file:
        import base64 # this is a bit stupid but like whatever
        base64_string = base64.b64encode(mp3_file.read()).decode("utf-8")
    eel.startDownload(base64_string, video_id)
    os.remove(str(temp_folder) + '/' + video_id + '.mp3')
import argparse
parser = argparse.ArgumentParser(description="A script that processes user data.")
parser.add_argument("-p", "--port", type=int, default=4444, help="Port you want the server to serve to")
print('I: Server running on localhost:' + str(parser.parse_args().port))
eel.start('index.html', mode=None, block=True, host='localhost', port=parser.parse_args().port)
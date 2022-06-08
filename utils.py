import datetime
import os
import subprocess
from pprint import pprint

import matplotlib.pyplot as plt
import numpy as np
import torchaudio
import validators
from bs4 import BeautifulSoup
from IPython.display import Audio, display
from pytube.extract import video_id


def download_youtube_wav(youtube_id, outfolder='./', overwrite=True):
    """
    Download the audio for a YouTube id/URL
    """
    if validators.url(youtube_id):
        youtube_id = video_id(youtube_id)

    os.makedirs(outfolder, exist_ok=True)

    outfile = os.path.join(outfolder, '{}.wav'.format(youtube_id))
    if not overwrite:
        if os.path.isfile(outfile):
            return outfile

    cmd = "youtube-dl --no-continue --extract-audio --audio-format wav -o '{}' {}".format(
        outfile, youtube_id)
    subprocess.Popen(cmd, shell=True).wait()

    assert os.path.isfile(outfile), "Couldn't find expected outfile, something went wrong"
    return outfile

def convert_wavfile(wavfile, outfile):
    """
    Converts file to 16khz single channel mono wav
    """
    cmd = "ffmpeg -y -i {} -acodec pcm_s16le -ar 16000 -ac 1 {}".format(
        wavfile, outfile)
    subprocess.Popen(cmd, shell=True).wait()
    return outfile

def check_wav_16khz_mono(wavfile):
    """
    Returns True if a wav file is 16khz and single channel
    """
    try:
        signal, fs = torchaudio.load(wavfile)

        mono = signal.shape[0] == 1
        freq = fs == 16000
        if mono and freq:
            return True
        else:
            return False
    except:
        return False

def waveplot_perspeaker(signal, fs, segments):
    for seg in segments:
        start = seg['start_sample']
        end = seg['end_sample']
        speech = signal[start:end]
        print('Speaker {} ({}s - {}s)'.format(seg['label'], seg['start'], seg['end']))
        if 'words' in seg:
            pprint(seg['words'])
        Audio(speech, rate=fs)
        type("Audio(speech, rate=fs) =======> {}".format(Audio(speech, rate=fs)))
        print('='*40 + '\n')

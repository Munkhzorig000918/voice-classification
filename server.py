import os
from fastapi import FastAPI, File, UploadFile
import requests 
import json
import shutil
import tempfile

import soundfile as sf
import utils
import model


app = FastAPI()

filename = 'destination.wav'
speech2TextUrl = 'https://ai.nubisoft.mn/speech' 
num_speaker = 2

class Type(object):
    def __init__(self, speaker, start, end, text):
        self.speaker = speaker
        self.start = start
        self.end = end
        self.text = text

@app.get("/url/")
async def read_item(youtube_id: str, num_speaker: int):
    fileOrder = 0
    startIndex = 0
    textList = []
    list = []

    with tempfile.TemporaryDirectory() as outdir:
        yt_file = utils.download_youtube_wav(youtube_id, outdir)

        wav_file = utils.convert_wavfile(yt_file, f"{outdir}/{youtube_id}_converted.wav")
        signal, fs = sf.read(wav_file)

        print(f"wav file: {wav_file}")

        diar = model.Diarizer(embed_model='ecapa', cluster_method='sc', window=1.5, period=0.75)

        segments = diar.diarize(wav_file, 
                            num_speakers=num_speaker,
                            outfile=f"{outdir}/{youtube_id}.rttm")

    utils.waveplot_perspeaker(signal, fs, segments)

    for seg in segments:
        start = seg['start_sample']
        end = seg['end_sample']
        speech = signal[start:end]
        print('Speaker {} ({}s - {}s'.format(seg['label'], seg['start'], seg['end']))
        sf.write('cluster{}.wav'.format(fileOrder), speech, samplerate=fs)
        fileOrder += 1

    for index in range(len(segments)):
        music_wav = open('cluster{}.wav'.format(index), 'rb') 
        data = {'file': ('test{}.wav'.format(index), music_wav, 'audio/mpeg')} 
        x = requests.post(speech2TextUrl, files=data)  

        os.remove('cluster{}.wav'.format(index))
        
        text = json.loads(x.text)
        textList.append(text['text'])

    for seg in segments:
        list.append(Type(str(seg['label']), seg['start'], seg['end'], textList[startIndex]))
        startIndex += 1

    return list

@app.post("/file/")
async def read_item(file: UploadFile = File(...)):
    fileOrder = 0
    
    with open(filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    with tempfile.TemporaryDirectory() as outdir:
        wav_file = filename
        signal, fs = sf.read(wav_file)

        print(f"wav file: {wav_file}")

        diar = model.Diarizer(embed_model='ecapa', cluster_method='sc')

        segments = diar.diarize(wav_file, 
                                num_speakers=num_speaker,
                                outfile=f"{outdir}.rttm")

    os.remove(filename)
    os.remove('destination_converted.wav')

    textList = []
    list = []
    startIndex = 0

    for seg in segments:
        start = seg['start_sample']
        end = seg['end_sample']
        speech = signal[start:end]
        print('Speaker {} ({}s - {}s'.format(seg['label'], seg['start'], seg['end']))
        sf.write('cluster{}.wav'.format(fileOrder), speech, samplerate=fs)
        fileOrder += 1

    for index in range(len(segments)):
        music_wav = open('cluster{}.wav'.format(index), 'rb') 
        data = {'file': ('output{}.wav'.format(index), music_wav, 'audio/mpeg')} 
        x = requests.post(speech2TextUrl, files=data)  

        os.remove('cluster{}.wav'.format(index))
        
        text = json.loads(x.text)
        textList.append(text['text'])

    for seg in segments:
        print(textList[startIndex])
        list.append(Type(str(seg['label']), seg['start'], seg['end'], textList[startIndex]))
        startIndex += 1

    return list
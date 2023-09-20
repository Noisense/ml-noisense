import os
import json
from fastapi import FastAPI, UploadFile, File
import numpy as np
import math
import seaborn as sns
import pandas as pd
import matplotlib.pylab as plt
import librosa.display
from scipy.io import wavfile
from itertools import cycle
from glob import glob

app = FastAPI()

sns.set_theme(style="white", palette=None)
color_pal = plt.rcParams["axes.prop_cycle"].by_key()["color"]
color_cycle = cycle(plt.rcParams["axes.prop_cycle"].by_key()["color"])

def calculate_leq(signal, sample_rate):
    squared_signal = signal**2
    mean_squared_signal = np.mean(squared_signal)
    leq = 10 * math.log10(mean_squared_signal)
    return leq

def calculate_nc(leq):
    nc = leq - 94
    return nc

def calculate_sil(leq):
    sil = leq - 10
    return sil

@app.get("/status")
def get_status():
    return {"status": "novin is running"}

@app.post("/analyze_audio")
async def analyze_audio(file: UploadFile = File(...)):
    file_path = f"{file.filename}"
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    sample_rate, audio_data = wavfile.read(file_path)

    audio_data_json = audio_data.tolist()


    if len(audio_data.shape) > 1:
        audio_data = np.mean(audio_data, axis=1)

    leq = calculate_leq(audio_data, sample_rate)

    nc = calculate_nc(leq)

    sil = calculate_sil(leq)

    os.remove(file_path)

    result = {
        "Level Kebisingan Equivalent (L_eq)": round(leq, 2),
        "Noise Criterion (NC)": round(nc, 2),
        "Speech Interference Level (SIL)": round(sil, 2),
        "Status Kebisingan": "",
        "df": audio_data_json
    }

    if leq <= 45:
        result["Status Kebisingan"] = "Tidak bising (Sesuai SNI 03-3958-2011)"
    elif leq <= 55:
        result["Status Kebisingan"] = "Bising ringan (Sesuai SNI 03-3958-2011)"
    elif leq <= 65:
        result["Status Kebisingan"] = "Bising sedang (Sesuai SNI 03-3958-2011)"
    elif leq <= 75:
        result["Status Kebisingan"] = "Bising berat (Sesuai SNI 03-3958-2011)"
    else:
        result["Status Kebisingan"] = "Bising sangat berat (Melebihi standar SNI 03-3958-2011)"

    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
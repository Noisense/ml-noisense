import os
import librosa
import pymysql
from moviepy.editor import *
from datetime import datetime, timedelta

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

db = pymysql.connect(
    host="localhost",
    user="root",
    passwd="noisense",
    database="noisense"
)

cursor = db.cursor()

start_date = datetime(2023, 11, 1)
end_date = datetime(2023, 11, 9)

input_dir_base = '../app/audio/'
output_dir_base = '../app/extract/wav/'

for single_date in daterange(start_date, end_date):
    folder_name = single_date.strftime("%d-%m-%Y")
    folder_path = os.path.join(input_dir_base, folder_name)

    if os.path.exists(folder_path):
        mp3_files = [file for file in os.listdir(folder_path) if file.endswith('.mp3')]

        if not mp3_files:
            print(f"Tidak ada file MP3 di folder {folder_name}, dilewati.")
            continue

        output_dir = os.path.join(output_dir_base, folder_name)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for mp3_file in mp3_files:
            file_id = os.path.splitext(mp3_file)[0]

            cursor.execute("SELECT EXISTS(SELECT 1 FROM extract_files WHERE file_id = %s)", (file_id))
            if cursor.fetchone()[0]:
                print(f"File ID {file_id} sudah ada di database, dilewati.")
                continue

            full_mp3_path = os.path.join(folder_path, mp3_file)
            output_wav_path = os.path.join(output_dir, os.path.splitext(mp3_file)[0] + '.wav')

            cursor.execute(
                           "SELECT audio_label FROM recordings JOIN recordings_files rf on recordings.audio_id = rf.audio_id WHERE rf.audio_id = %s",
                file_id
            )
            result = cursor.fetchone()
            if result:
                label = result[0]
            else:
                label = None

            audio_clip = AudioFileClip(full_mp3_path)
            audio_clip.write_audiofile(output_wav_path)
            audio_clip.close()

            y, sr = librosa.load(output_wav_path, sr=None)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
            mean_spectral_centroid = spectral_centroids.mean()
            zero_crossing_rate = librosa.feature.zero_crossing_rate(y)
            mean_zero_crossing_rate = zero_crossing_rate.mean()

            sql = """
            INSERT INTO extract_files 
            (file_id, filename, sample_rate, duration, file_path, date_recorded, tempo, mean_spectral_centroid, mean_zero_crossing_rate, label) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            val = (
                file_id, mp3_file, sr, librosa.get_duration(y=y, sr=sr), output_wav_path,
                single_date.date(), tempo, mean_spectral_centroid, mean_zero_crossing_rate, label
            )
            cursor.execute(sql, val)

        db.commit()

cursor.close()
db.close()

import os
import csv
import pickle
import configparser
import logging
from logging import FileHandler, StreamHandler, INFO, ERROR, Formatter
from pathlib import Path
from dotenv import load_dotenv
from pydub import AudioSegment
from pyannote.audio import Pipeline

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(INFO)
s_handler = StreamHandler()
s_handler.setLevel(ERROR)
f_handler = FileHandler("./app.log")
f_handler.setLevel(INFO)
formatter = Formatter("%(asctime)s - %(levelname)s : %(message)s (%(filename)s:%(lineno)d)")
s_handler.setFormatter(formatter)
f_handler.setFormatter(formatter)
logger.addHandler(s_handler)
logger.addHandler(f_handler)

load_dotenv()

config_ini = configparser.ConfigParser()
config_ini.read("config.ini",encoding="UTF-8")
file_path = config_ini["FILE"]["file_path"]
record_title = Path(file_path).stem

def main():
    if not is_diarization_necessary():
        shape_data_for_one_speaker_to_txt()
        return

    transform_audiofile_to_wav()
    number_of_speaker = speaker_diarization()
    shape_diarization_data_to_csv(number_of_speaker)
   

def is_diarization_necessary():
    if config_ini["SPEAKER_INFO"]["num_speakers"] == str(1):
        return False
    return True

def shape_data_for_one_speaker_to_txt():
    logger.info("話者の指定数が1人です。文字起こし結果を .txt で出力します")
    with open(f"./{record_title}_result/{record_title}_transcription.pickle", "rb") as f:
        result = pickle.load(f)
    with open(f"{record_title}_result/{record_title}.txt", "w") as f:
        f.write(result["text"])
    return

def transform_audiofile_to_wav():
    if Path(f"{record_title}_result/{record_title}.wav").exists():
        return
    sound = AudioSegment.from_file(file_path, format="mp3",encoding="UTF-8")
    sound.export(f"{record_title}_result/{record_title}.wav", format="wav",parameters=["-ar", str(sound.frame_rate)])
    logger.info("wav ファイルを作成しました")
    return


def speaker_diarization():
    def read_config(value):
        if value.lower() == "none":
            return None
        else:
            return int(value)

    num_speakers = read_config(config_ini["SPEAKER_INFO"]["num_speakers"])
    min_speakers = read_config(config_ini["SPEAKER_INFO"]["min_speakers"])
    max_speakers = read_config(config_ini["SPEAKER_INFO"]["max_speakers"])

    if num_speakers:
        number_of_speaker = f"{num_speakers}"
    elif min_speakers and max_speakers:
        number_of_speaker = f"{min_speakers}to{max_speakers}"
    elif not min_speakers and max_speakers:
        number_of_speaker = f"max{max_speakers}"
    elif min_speakers and not max_speakers:
        number_of_speaker = f"min{min_speakers}"
    else:
        number_of_speaker = f"unknown_"

    output_file = f"./{record_title}_result/{record_title}_diarization_{number_of_speaker}speakers.pickle"

    if Path(output_file).exists():
        logger.info("ファイルが既存のため話者分離をスキップします")
        return number_of_speaker

    logger.info("話者分離用の学習データの読み込みを開始")
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization@2.1",use_auth_token=os.environ["HF_AUTH_TOKEN"])
    logger.info("話者分離用の学習データの読み込みを終了")

    if num_speakers:
        min_speakers,max_speakers=None,None
    logger.info("音声データの話者分離を開始")
    try:
        diarization = pipeline(f"{record_title}_result/{record_title}.wav",
                                num_speakers=num_speakers,
                                min_speakers=min_speakers,
                                max_speakers=max_speakers,
                                )
    except:
        logger.exception("話者分離に失敗しました。config.ini のnum_speakers,min_speakers,max_speakersの値を変更して再度実行してください")
        raise Exception("Error")

    logger.info("音声データの話者分離を終了")
    with open(output_file, "wb") as f:
        pickle.dump(diarization, f)
    logger.info("話者分離結果の保存を終了")
    return number_of_speaker


def shape_diarization_data_to_csv(number_of_speaker):

    output_file = f"./{record_title}_result/result_{number_of_speaker}speaker_transcription.csv"

    def format_seconds_as_hhmmss(audio_seconds):
        audio_seconds = int(audio_seconds)
        hours = audio_seconds // 3600
        minutes = (audio_seconds % 3600) // 60
        seconds = audio_seconds % 60
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"


    with open(f"./{record_title}_result/{record_title}_transcription.pickle", "rb") as f:
        result = pickle.load(f)
    formed_result = [[d["start"],d["end"],d["text"]] for d in result["segments"]]
    logger.info("transcription pickleファイルを読み込み完了")

    with open(f"./{record_title}_result/{record_title}_diarization_{number_of_speaker}speakers.pickle", "rb") as f:
        diarization = pickle.load(f)
    speaker_list = [[turn.start, turn.end, speaker, ""]  for turn, _, speaker in diarization.itertracks(yield_label=True)]
    logger.info("diarization pickleファイルを読み込み完了")

    logger.info("データの整形を開始")
    for speaker in speaker_list:
        speaker_start = speaker[0]
        speaker_end = speaker[1]
        speaker_text = ""

        for res in formed_result:
            res_start = res[0]
            res_end = res[1]
            res_text = res[2]

            # speaker_listのstart,endの範囲にformed_resultのstart,endが含まれている場合
            if res_end > speaker_start and res_start < speaker_end:
                # textが speaker_list内に追加されていない場合のみ追加
                already_added = False
                for previous_speaker in speaker_list:
                    if res_text in previous_speaker[3]:
                        already_added = True
                        break
                
                if not already_added:
                    speaker_text += res_text

        #speaker 該当範囲のtextを追加
        speaker[3] = speaker_text.strip()

    # speaker_list から空の文字列行を除外
    speaker_list = [speaker for speaker in speaker_list if speaker[3].strip() != ""]

    for speaker in speaker_list:
        speaker[0] = format_seconds_as_hhmmss(speaker[0])
        speaker[1] = format_seconds_as_hhmmss(speaker[1])


    # speakerが連続する場合は統合する
    merged_speaker_list = []
    previous_speaker = None

    for speaker in speaker_list:
        if previous_speaker is None:
            previous_speaker = speaker
        elif previous_speaker[2] == speaker[2]:
            # 話者が同一の場合、終話時間をスライドさせる またtextを繋げる
            previous_speaker[1] = speaker[1]
            previous_speaker[3] += " " + speaker[3]
        else:
            merged_speaker_list.append(previous_speaker)
            previous_speaker = speaker

    # 最後のspeakerを追加
    if previous_speaker is not None:
        merged_speaker_list.append(previous_speaker)

    speaker_list = merged_speaker_list

    logger.info("データの整形を終了")

    # csvとして保存
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Start Time", "End Time", "Speaker", "Text"])
        for speaker in speaker_list:
            csv_writer.writerow(speaker)
    logger.info("csvデータの保存が完了")

    return



if __name__ == "__main__":
    main()

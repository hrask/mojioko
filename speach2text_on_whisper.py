import os
import sys
import pickle
import configparser
from pathlib import Path

import whisper

from logging import getLogger, FileHandler, INFO, Formatter
logger = getLogger(__name__)
logger.setLevel(INFO)
f_handler = FileHandler("./app.log")
f_handler.setLevel(INFO)
formatter = Formatter("%(asctime)s - %(levelname)s : %(message)s (%(filename)s:%(lineno)d)")
f_handler.setFormatter(formatter)
logger.addHandler(f_handler)


config_ini = configparser.ConfigParser()
config_ini.read("config.ini", encoding="UTF-8")
realtime_log = config_ini["DEFAULT"]["realtime_log"]
lang =         config_ini["DEFAULT"]["lang"]
model_size =   config_ini["DEFAULT"]["model_size"]
file_path =    config_ini["FILE"]["file_path"]
record_title = Path(file_path).stem
output_file = f"./{record_title}_result/{record_title}_transcription.pickle"


if Path(output_file).exists():
    logger.info("出力ファイルが存在するためスキップします")
    sys.exit()

model = whisper.load_model(model_size ,device="cpu")
### model高速化＆省メモリ化 ###
_ = model.half()
_ = model.cuda()

for m in model.modules():
    if isinstance(m, whisper.model.LayerNorm):
        m.float()

audio = whisper.load_audio(file_path)
result = model.transcribe(audio, verbose=realtime_log, language=lang,)

with open(output_file, 'wb') as f:
    pickle.dump(result, f)
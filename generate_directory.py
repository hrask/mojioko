import configparser
from pathlib import Path

from logging import getLogger, FileHandler, INFO, Formatter
logger = getLogger(__name__)
logger.setLevel(INFO)
f_handler = FileHandler("./app.log")
f_handler.setLevel(INFO)
formatter = Formatter("%(asctime)s - %(levelname)s : %(message)s (%(filename)s:%(lineno)d)")
f_handler.setFormatter(formatter)
logger.addHandler(f_handler)


config_ini = configparser.ConfigParser()
config_ini.read("config.ini",encoding="UTF-8")
file_path = config_ini["FILE"]["file_path"]
record_title = Path(file_path).stem

if not Path(file_path).exists():
    logger.info("音声ファイルが存在しません")
    raise FileNotFoundError("指定の音声ファイルが存在しません")

if not Path(f"./{record_title}_result").exists():
    Path(f"./{record_title}_result").mkdir()
    logger.info("ディレクトリを作成しました")

if not Path(f"/app.log"):
    Path(f"app.log").touch()
    logger.info("app.logを作成しました")
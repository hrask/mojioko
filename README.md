### プロジェクト概要
本プロジェクトでは以下の処理をローカル環境で行います：
1. [whisper](https://github.com/openai/whisper
)を用いた音声ファイルの文字起こし
2. [pyannote-audio](https://github.com/pyannote/pyannote-audio)を用いた話者分離（Speaker Diarization）
3. 話者ごとの文字起こしを整理・統合し、CSVファイルに出力


### ユースケース
- セキュリティ重視の環境で、データを外部に出さずに音声を分析
- 複数人の会話を話者ごとに整理したい場合


### 事前に必要なもの

1. Hugging Face pyannote.audioのAPIトークン
[こちら](https://huggingface.co/pyannote/speaker-diarization)からAPIトークンを取得し`.env`ファイルに記入してください

2. `ffmpeg`のインストール
[whisper](https://github.com/openai/whisper/tree/main)のリポジトリを参照してインストールしてください

3. 必要なライブラリのインストール
```bash
$ pip install -r requirement.txt
```

### 実行手順

1. 音声ファイルに合わせて`config.ini` を編集する
2. `app.bat`を実行する
3. 結果を確認する
結果は以下の形式で出力されます：  
`{音声ファイルの名前}_result/result_{話者情報}_transcription.csv`  
※start, end, speaker, text のカラムをで構成されます  
※1レコードは、「start から end までの時間でspeakerがtextの内容を発話した」ことを示しますが、文字起こしと話者分離を別々で処理する関係上時間が重なって表示されることがあります

---
#### `config.ini`の編集

###### [FILE]
`file_path` mp3ファイルのパス
###### [SPEAKER_INFO]
`num_speakers` 発言者の数がわかる場合に指定  
`min_speakers` 発言者の数が曖昧な場合の下限  
`max_speakers` 発言者の数が曖昧な場合の上限  
※`num_speakers`が指定された場合、`min_speakers`及び`max_speakers`は指定無しとして読み込まれる  
###### [DEFAULT]
`lang` 音声の言語  
`model_size` whisperで使用するモデルサイズ:[参照](https://github.com/openai/whisper/tree/main)  
`realtime_log` 文字起こしの内容表示のON/OFF  

---
#### 動作確認環境

**OS** : Windows10  
**GPU** : GTX 1660 Super  
**RAM** : 16GB  
Python 3.10.8
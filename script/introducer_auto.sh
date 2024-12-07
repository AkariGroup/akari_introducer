#!/bin/bash
# -*- coding: utf-8 -*-
## シェルオプション
set -e           # コマンド実行に失敗したらエラー
set -u           # 未定義の変数にアクセスしたらエラー
set -o pipefail  # パイプのコマンドが失敗したらエラー（bashのみ）

ip=$1

echo ${ip}

#第２引数でakari_motion_serverのパスが記載されていた場合は、そちらも起動する。
if [ "$#" -ge 2 ]; then
    (
    cd $2
    . venv/bin/activate
    gnome-terminal --title="motion_server" -- bash -ic "python3 server.py"
    )
fi


(
cd ../
 . venv/bin/activate

# gnome-terminal --title="voice_server" -- bash -ic "python3 lib/akari_rag_chatbot/lib/akari_chatgpt_bot/voicevox_server.py --voicevox_local --voice_host ${ip}"
 gnome-terminal --title="voice_server" -- bash -ic "python3 lib/akari_rag_chatbot/lib/akari_chatgpt_bot/aivis_server.py --voice_host ${ip}"
 gnome-terminal --title="introduce_gpt_publisher" -- bash -ic "python3 introduce_gpt_publisher.py --weaviate_host ${ip} --collections Akari"
 gnome-terminal --title="speech_publisher" -- bash -ic "python3 lib/akari_rag_chatbot/lib/akari_chatgpt_bot/speech_publisher.py --timeout 0.8 --auto"
 gnome-terminal --title="talk_controller" -- bash -ic "python3 lib/akari_rag_chatbot/lib/akari_chatgpt_bot/talk_controller_client.py"
 gnome-terminal --title="streamlit_server" -- bash -ic "streamlit run streamlit_server.py -- --display_pos left"
)

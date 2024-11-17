# app.py
import streamlit as st
import time
import grpc
import qrcode
from PIL import Image
import io
import threading
from streamlit.runtime.scriptrunner import add_script_run_ctx

# グローバル変数として現在のURLを保持
if "current_url" not in st.session_state:
    st.session_state.current_url = ""


def create_qr_code(url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    qr_image = qr.make_image(fill_color="black", back_color="white")

    byte_stream = io.BytesIO()
    qr_image.save(byte_stream, format="PNG")
    return byte_stream.getvalue()


def url_receiver():
    while True:
        try:
            # gRPCチャンネルの作成
            channel = grpc.insecure_channel("localhost:50051")
            #stub = url_service_pb2_grpc.URLServiceStub(channel)

            # URLの受信
            #for response in stub.ReceiveURL(url_service_pb2.Empty()):
            ##    st.session_state.current_url = response.url
            #    # Streamlitに再描画を要求
            #    st.rerun()

        except grpc.RpcError as e:
            print(f"gRPC error: {e}")
            time.sleep(5)  # 接続エラー時は5秒待機して再試行
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)


def main():
    st.set_page_config(layout="wide")

    # URLレシーバースレッドの開始（初回のみ）
    #if "receiver_started" not in st.session_state:
    #    receiver_thread = threading.Thread(target=url_receiver, daemon=True)
    #    add_script_run_ctx(receiver_thread)  # Streamlitのコンテキストを追加
    #    receiver_thread.start()
    #    st.session_state.receiver_started = True

    # 2列のレイアウトを作成
    left_col, right_col = st.columns([0.9, 0.1])
    st.session_state.current_url = st.text_input("URLを入力してください")
    with left_col:
        if st.session_state.current_url:
            if (
                "youtube.com" in st.session_state.current_url
                or "youtu.be" in st.session_state.current_url
            ):
                # YouTubeの場合
                if "watch?v=" in st.session_state.current_url:
                    video_id = st.session_state.current_url.split("watch?v=")[1].split(
                        "&"
                    )[0]
                elif "youtu.be/" in st.session_state.current_url:
                    video_id = st.session_state.current_url.split("youtu.be/")[1]
                else:
                    video_id = st.session_state.current_url

                embed_url = f"https://www.youtube.com/embed/{video_id}?autoplay=1"
                st.components.v1.iframe(embed_url, width=1440, height=810)
            else:
                # 通常のWebページの場合
                st.markdown(
                    f'<iframe src="{st.session_state.current_url}" '
                    f'style="width: 1440px; height: 810px; overflow: auto; display: block;"></iframe>',
                    unsafe_allow_html=True
                )

    with right_col:
        # QRコードを表示（上部）
        if st.session_state.current_url:
            qr_image = create_qr_code(st.session_state.current_url)
            st.image(qr_image,caption="QRコード")

        # 画像を表示（下部）
        try:
            image = Image.open("image/akari.jpg")
            st.image(image)
        except FileNotFoundError:
            st.error("image/image.jpg が見つかりません")


if __name__ == "__main__":
    main()

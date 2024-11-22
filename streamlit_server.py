# app.py
import copy
import streamlit as st
import grpc
import qrcode
import os
import sys
from concurrent import futures
from PIL import Image
import threading
from streamlit.runtime.scriptrunner import add_script_run_ctx

sys.path.append(os.path.join(os.path.dirname(__file__), "lib/grpc"))
import streamlit_server_pb2
import streamlit_server_pb2_grpc

DEFAULT_IMAGE = Image.open("image/talk.jpg")


def create_qr_code(url: str) -> Image:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    qr_image = qr.make_image(fill_color="black", back_color="white")
    return qr_image


def extract_video_id(url: str) -> str:
    if "watch?v=" in url:
        video_id = url.split("watch?v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1]
    else:
        video_id = url
    return video_id


class StreamlitServer(streamlit_server_pb2_grpc.StreamlitServerServiceServicer):
    """
    StreamlitにURLを送信するgRPCサーバ
    """

    def __init__(self, cur_url):
        self.cur_url = cur_url

    def SendUrl(
        self,
        request: streamlit_server_pb2.SendUrlRequest,
        context: grpc.ServicerContext,
    ) -> streamlit_server_pb2.SendUrlReply:
        self.cur_url[0] = request.url
        print(f"URL received: {self.cur_url}")
        return streamlit_server_pb2.SendUrlReply(success=True)


class Worker(threading.Thread):
    def __init__(self):
        super().__init__()
        self.cur_url = [""]

    def run(self):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        streamlit_server_pb2_grpc.add_StreamlitServerServiceServicer_to_server(
            StreamlitServer(self.cur_url), server
        )
        port = "10010"
        server.add_insecure_port("[::]:" + port)
        server.start()
        print(f"voice_server start. port: {port}")
        server.wait_for_termination()


def main():
    # URLレシーバースレッドの開始（初回のみ）
    if "worker" not in st.session_state:
        st.session_state.worker = Worker()
        st.session_state.worker.start()

    st.set_page_config(layout="wide")
    # 2列のレイアウトを作成
    left_col, right_col = st.columns([0.9, 0.1])
    left_placeholder = left_col.empty()  # 動的更新用のプレースホルダー
    right_placeholder = right_col.empty()  # 動的更新用のプレースホルダー
    prev_url = ""
    with right_placeholder:
        st.image(DEFAULT_IMAGE)
    while True:
        if st.session_state.worker.cur_url[0] != prev_url:
            prev_url = st.session_state.worker.cur_url[0]
            with left_placeholder:
                print("OK1")
                if "worker" in st.session_state:
                    if (
                        "youtube.com" in st.session_state.worker.cur_url[0]
                        or "youtu.be" in st.session_state.worker.cur_url[0]
                    ):
                        # YouTube埋め込みロジック
                        video_id = extract_video_id(
                            st.session_state.worker.cur_url[0]
                        )  # ビデオID抽出用関数に切り出す
                        embed_url = f"https://www.youtube.com/embed/{video_id}?autoplay=1&mute=1"
                        st.components.v1.iframe(embed_url, width=1440, height=810)
                    else:
                        # その他Webページの埋め込み
                        st.markdown(
                            f'<iframe src="{st.session_state.worker.cur_url[0]}" '
                            f'style="width: 1440px; height: 810px; overflow: auto; display: block;"></iframe>',
                            unsafe_allow_html=True,
                        )

            print("OK2")
            with right_placeholder:
                # QRコードを表示（上部）
                if "worker" in st.session_state and st.session_state.worker.cur_url[0]:
                    qr_image = create_qr_code(st.session_state.worker.cur_url[0])
                    qr_resized = qr_image.resize((500, 500))
                    overlay_image = copy.deepcopy(DEFAULT_IMAGE)
                    overlay_image.paste(qr_resized, (170, 1125))
                    st.image(overlay_image)
                    print("OK3")
                else:
                    st.image(DEFAULT_IMAGE)


if __name__ == "__main__":
    main()

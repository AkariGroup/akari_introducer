import argparse
import copy
import streamlit as st
import grpc
import qrcode
import os
import sys
import time
from typing import Optional
from concurrent import futures
from PIL import Image
import threading

sys.path.append(os.path.join(os.path.dirname(__file__), "lib/grpc"))
import streamlit_server_pb2
import streamlit_server_pb2_grpc

sys.path.append(
    os.path.join(
        os.path.dirname(__file__),
        "lib/akari_rag_chatbot/lib/akari_chatgpt_bot/lib/grpc",
    )
)
import motion_server_pb2
import motion_server_pb2_grpc


DEFAULT_IMAGE = Image.open("image/talk.jpg")


def create_qr_code(url: str) -> Image:
    """
    QRコードを生成する
    Args:
        url (str): QRコードに埋め込むURL

    Returns:
        Image: QRコード画像
    """
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
    """
    YouTubeのURLからビデオIDを抽出する
    Args:
        url (str): YouTubeのURL

    Returns:
        str: ビデオID
    """
    if "watch?v=" in url:
        video_id = url.split("watch?v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1]
    else:
        raise ValueError("Invalid URL")
    return video_id


class StreamlitServer(streamlit_server_pb2_grpc.StreamlitServerServiceServicer):
    """
    StreamlitにURLを送信するgRPCサーバ
    """

    def __init__(
        self,
        cur_url: list,
        display_pos: Optional[str] = None,
        motion_host: Optional[str] = "127.0.0.1",
        motion_port: Optional[str] = "50055",
    ):
        """コンストラクタ
        Args:
            cur_url (list): URLを格納するリスト
            display_pos (str, optional): AKARIから見たディスプレイの左右位置。この方向を向く。有効な値は"right"もしくは"left"。デフォルトはNone。
            motion_host (str, optional): モーションサーバーのホスト名。デフォルトは"127.0.0.1"。
            motion_port (str, optional): モーションサーバーのポート番号。デフォルトは"50055"。

        """
        self.cur_url = cur_url
        self.display_pos = display_pos
        print(f"display_pos: {self.display_pos}")
        motion_channel = grpc.insecure_channel(motion_host + ":" + motion_port)
        self.motion_stub = motion_server_pb2_grpc.MotionServerServiceStub(
            motion_channel
        )

    def SendUrl(
        self,
        request: streamlit_server_pb2.SendUrlRequest,
        context: grpc.ServicerContext,
    ) -> streamlit_server_pb2.SendUrlReply:
        """
        URLを受け取り、Streamlitに送信する
        Args:
            request (streamlit_server_pb2.SendUrlRequest): URLを格納したリクエスト
            context (grpc.ServicerContext): コンテキスト

        Returns:
            streamlit_server_pb2.SendUrlReply: レスポンス

        """
        self.cur_url[0] = request.url
        print(f"URL received: {self.cur_url}")
        motion = None
        if self.display_pos == "right":
            motion = "lookright"
        elif self.display_pos == "left":
            motion = "lookleft"
        if motion is not None:
            try:
                print(f"setMotion: {motion}")
                self.motion_stub.SetMotion(
                    motion_server_pb2.SetMotionRequest(
                        name=motion, priority=3, repeat=False, clear=True
                    )
                )
            except BaseException:
                print("setMotion error!")
                return False
        return streamlit_server_pb2.SendUrlReply(success=True)


class Worker(threading.Thread):
    def __init__(
        self,
        display_pos: Optional[str] = None,
        motion_host: Optional[str] = "127.0.0.1",
        motion_port: Optional[str] = "50055",
    ):
        """コンストラクタ
        Args:
            display_pos (str, optional): AKARIから見たディスプレイの左右位置。この方向を向く。有効な値は"right"もしくは"left"。デフォルトはNone。
            motion_host (str, optional): モーションサーバーのホスト名。デフォルトは"127.0.0.1"。
            motion_port (str, optional): モーションサーバーのポート番号。デフォルトは"50055"。

        """
        super().__init__()
        self.cur_url = [""]
        self.display_pos = display_pos
        self.motion_host = motion_host
        self.motion_port = motion_port

    def run(self):
        """
        gRPCサーバを起動する
        """
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        streamlit_server_pb2_grpc.add_StreamlitServerServiceServicer_to_server(
            StreamlitServer(
                cur_url=self.cur_url,
                display_pos=self.display_pos,
                motion_host=self.motion_host,
                motion_port=self.motion_port,
            ),
            server,
        )
        port = "10010"
        server.add_insecure_port("[::]:" + port)
        server.start()
        print(f"voice_server start. port: {port}")
        server.wait_for_termination()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--robot_ip", help="Robot ip address", default="127.0.0.1", type=str
    )
    parser.add_argument(
        "--robot_port", help="Robot port number", default="50055", type=str
    )
    parser.add_argument("--display_pos", help="Display position from AKARI", type=str)
    args = parser.parse_args()
    motion_host = args.robot_ip
    motion_port = args.robot_port
    display_pos = None
    if args.display_pos == "right" or args.display_pos == "left":
        display_pos = args.display_pos
        print(f"args display_pos: {display_pos}")
    # URLレシーバースレッドの開始（初回のみ）
    if "worker" not in st.session_state:
        st.session_state.worker = Worker(
            display_pos=display_pos, motion_host=motion_host, motion_port=motion_port
        )
        st.session_state.worker.start()

    st.set_page_config(layout="wide")
    # 2列のレイアウトを作成
    left_col, right_col = st.columns([0.9, 0.1])
    left_placeholder = left_col.empty()  # 動的更新用のプレースホルダー
    right_placeholder = right_col.empty()  # 動的更新用のプレースホルダー
    prev_url = ""
    last_updated_time = time.time()
    UPDATE_INTERVAL = 100
    DEFAULT_URL = "https://www.youtube.com/watch?v=hufXSDTFMVo&t=1s"
    st.session_state.worker.cur_url[0] = DEFAULT_URL
    with right_placeholder:
        st.image(DEFAULT_IMAGE)
    while True:
        if st.session_state.worker.cur_url[0] == "":
            st.session_state.worker.cur_url[0] = DEFAULT_URL
            last_updated_time = time.time()
        if time.time() - last_updated_time > UPDATE_INTERVAL:
            st.session_state.worker.cur_url[0] = ""
        if st.session_state.worker.cur_url[0] != prev_url:
            prev_url = st.session_state.worker.cur_url[0]
            last_updated_time = time.time()
            with left_placeholder:
                if "worker" in st.session_state:
                    play_youtube = False
                    # YouTube動画なら自動再生する。
                    if (
                        "youtube.com" in st.session_state.worker.cur_url[0]
                        or "youtu.be" in st.session_state.worker.cur_url[0]
                    ):
                        try:
                            video_id = extract_video_id(
                                st.session_state.worker.cur_url[0]
                            )  # ビデオID抽出用関数に切り出す
                            embed_url = f"https://www.youtube.com/embed/{video_id}?autoplay=1&mute=1"
                            st.components.v1.iframe(embed_url, width=1520, height=855)
                            play_youtube = True
                        except BaseException:
                            pass
                    # それ以外ならURLをそのまま表示
                    if not play_youtube:
                        st.markdown(
                            f'<iframe src="{st.session_state.worker.cur_url[0]}" '
                            f'style="width: 1520px; height: 855px; overflow: auto; display: block;"></iframe>',
                            unsafe_allow_html=True,
                        )
            with right_placeholder:
                # QRコードを表示（上部）
                if "worker" in st.session_state and st.session_state.worker.cur_url[0]:
                    qr_image = create_qr_code(st.session_state.worker.cur_url[0])
                    qr_resized = qr_image.resize((500, 500))
                    overlay_image = copy.deepcopy(DEFAULT_IMAGE)
                    overlay_image.paste(qr_resized, (170, 1125))
                    st.image(overlay_image)
                else:
                    st.image(DEFAULT_IMAGE)
        time.sleep(0.1)


if __name__ == "__main__":
    main()

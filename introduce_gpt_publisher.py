import argparse
import copy
import os
import sys
from concurrent import futures

import grpc
from lib.chat_akari_introducer import ChatStreamAkariIntroducer
from lib.prompt_creator import system_prompt_creator
from lib.akari_rag_chatbot.lib.weaviate_rag_controller import WeaviateRagController

sys.path.append(
    os.path.join(os.path.dirname(__file__), "lib/akari_chatgpt_bot/lib/grpc")
)
import gpt_server_pb2
import gpt_server_pb2_grpc
import voice_server_pb2
import voice_server_pb2_grpc


class GptServer(gpt_server_pb2_grpc.GptServerServiceServicer):
    """
    chatGPTにtextを送信し、返答をvoice_serverに送るgRPCサーバ
    """

    def __init__(
        self,
        collection_name: str,
        weaviate_host: str = "127.0.0.1",
        weaviate_port: int = 10080,
    ) -> None:
        """
        コンストラクタ
        Args:
            collection_name (str): 検索に使うWeaviateのコレクション名
        """
        self.chat_stream_akari_introducer = ChatStreamAkariIntroducer()
        self.messages = []
        self.messages = [
            self.chat_stream_akari_introducer.create_message("", role="system")
        ]
        voice_channel = grpc.insecure_channel("localhost:10002")
        self.stub = voice_server_pb2_grpc.VoiceServerServiceStub(voice_channel)
        self.weaviate_controller = WeaviateRagController(
            host=weaviate_host, port=weaviate_port
        )
        self.collections = collection_name

    def SetGpt(
        self, request: gpt_server_pb2.SetGptRequest(), context: grpc.ServicerContext
    ) -> gpt_server_pb2.SetGptReply:
        response = ""
        is_finish = True
        if request.HasField("is_finish"):
            is_finish = request.is_finish
        if len(request.text) < 2:
            return gpt_server_pb2.SetGptReply(success=True)
        print(f"Receive: {request.text}")
        content = f"{request.text}。"
        tmp_messages = copy.deepcopy(self.messages)
        tmp_messages.append(self.chat_stream_akari_introducer.create_message(content))
        if is_finish:
            self.messages = copy.deepcopy(tmp_messages)
        if is_finish:
            # 最終応答。高速生成するために、モデルはgpt-4o
            # テキストをWeaviateで検索
            weaviate_response = self.weaviate_controller.hybrid_search(
                collection_name=self.collections,
                text=content,
                limit=3,
                alpha=0.75,
                rerank=False,
            )
            contexts = ""
            for p in weaviate_response.objects:
                contexts += p.properties["content"]
            # system_promptをWeaviateの検索結果を含んだ文に変更
            system_prompt = system_prompt_creator(context=contexts)
            tmp_messages[0] = self.chat_stream_akari_introducer.create_message(
                system_prompt, role="system"
            )
            response = ""
            self.stub.StartHeadControl(voice_server_pb2.StartHeadControlRequest())
            for sentence in self.chat_stream_akari_introducer.chat_and_link(
                tmp_messages, model="gpt-4o"
            ):
                print(f"Send to voice server: {sentence}")
                self.stub.SetText(voice_server_pb2.SetTextRequest(text=sentence))
                response += sentence
            # Sentenceの終了を通知
            self.stub.SentenceEnd(voice_server_pb2.SentenceEndRequest())
            self.messages.append(
                self.chat_stream_akari_introducer.create_message(
                    response, role="assistant"
                )
            )
        else:
            # 途中での第一声とモーション準備。function_callingの確実性のため、モデルはgpt-4-turbo
            for sentence in self.chat_stream_akari_introducer.chat_and_motion(
                tmp_messages, model="gpt-4-turbo", short_response=True
            ):
                print(f"Send to voice server: {sentence}")
                self.stub.SetText(voice_server_pb2.SetTextRequest(text=sentence))
                response += sentence
                self.chat_stream_akari_introducer.send_reserved_motion()
        print("")
        return gpt_server_pb2.SetGptReply(success=True)

    def SendMotion(
        self, request: gpt_server_pb2.SendMotionRequest(), context: grpc.ServicerContext
    ) -> gpt_server_pb2.SendMotionReply:
        success = self.chat_stream_akari_introducer.send_reserved_motion()
        return gpt_server_pb2.SendMotionReply(success=success)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ip", help="Gpt server ip address", default="127.0.0.1", type=str
    )
    parser.add_argument(
        "--port", help="Gpt server port number", default="10001", type=str
    )
    parser.add_argument(
        "-c",
        "--collections",
        default="Test",
        type=str,
        help="Weaviate collection name",
    )
    parser.add_argument(
        "-w",
        "--weaviate_host",
        default="127.0.0.1",
        help="Weaviate host name",
    )
    parser.add_argument(
        "-p",
        "--weaviate_port",
        default=10080,
        type=int,
        help="Weaviate port number",
    )
    args = parser.parse_args()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    gpt_server_pb2_grpc.add_GptServerServiceServicer_to_server(
        GptServer(
            collection_name=args.collections,
            weaviate_host=args.weaviate_host,
            weaviate_port=args.weaviate_port,
        ),
        server,
    )
    server.add_insecure_port(args.ip + ":" + args.port)
    server.start()
    print(f"gpt_publisher start. port: {args.port}")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        exit()


if __name__ == "__main__":
    main()

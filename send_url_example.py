import json
import grpc
import os
import sys
from typing import Generator
import openai

sys.path.append(os.path.join(os.path.dirname(__file__), "lib/grpc"))
import streamlit_server_pb2
import streamlit_server_pb2_grpc

def main() -> None:
    streamlit_channel = grpc.insecure_channel("localhost:10010")
    stub = streamlit_server_pb2_grpc.StreamlitServerServiceStub(streamlit_channel)

    while True:
        print("リンクを入力後、Enterを押してください。")
        text = input("Link: ")
        try:
            stub.SendUrl(streamlit_server_pb2.SendUrlRequest(url=text))
        except grpc.RpcError as e:
            print(f"Error: {e}")
            continue

if __name__ == "__main__":
    main()

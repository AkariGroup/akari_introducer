import json
import os
import sys
from typing import Generator
import openai

from lib.akari_rag_chatbot.lib.akari_chatgpt_bot.lib.chat_akari_grpc import (
    ChatStreamAkariGrpc,
)
from gpt_stream_parser import force_parse_json

class ChatStreamAkariIntroducer(ChatStreamAkariGrpc):
    """ChatGPTやClaude3を使用して会話を行うためのクラス。"""

    def chat_and_link_gpt(
        self,
        messages: list,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        short_response: bool = False,
    ) -> Generator[str, None, None]:
        """ChatGPTを使用してチャットとモーションを処理するメソッド。

        Args:
            messages (list): チャットメッセージのリスト。
            model (str, optional): 使用するOpenAI GPTモデル。デフォルトは"gpt-4"。
            temperature (float, optional): サンプリング温度。デフォルトは0.7。
            short_response (bool, optional): 相槌などの短応答のみを返すか、通常の応答を返すか。

        Yields:
            str: チャット応答のジェネレータ。

        """
        functions = [
            {
                "name": "reply_with_link_",
                "description": "ユーザのメッセージに対する回答と、回答に関連するリンクがある場合は一つ選択します。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "talk": {
                            "type": "string",
                            "description": "回答",
                        },
                        "link": {
                            "type": "string",
                            "description": "関連するリンク",
                        },
                    },
                    "required": ["link", "talk"],
                },
            }
        ]
        result = openai.chat.completions.create(
            model=model,
            messages=messages,
            n=1,
            temperature=temperature,
            functions=functions,
            function_call={"name": "reply_with_link_"},
            stream=True,
            stop=None,
        )
        full_response = ""
        real_time_response = ""
        sentence_index = 0
        get_link = False
        for chunk in result:
            delta = chunk.choices[0].delta
            if delta.function_call is not None:
                if delta.function_call.arguments is not None:
                    full_response += chunk.choices[0].delta.function_call.arguments
                    try:
                        data_json = json.loads(full_response)
                        found_last_char = False
                        for char in self.last_char:
                            if real_time_response[-1].find(char) >= 0:
                                found_last_char = True
                        if not found_last_char:
                            data_json["talk"] = data_json["talk"] + "。"
                    except BaseException:
                        data_json = force_parse_json(full_response)
                    if data_json is not None:
                        if not get_link  and "link" in data_json:
                            real_time_link_response = str(data_json["link"])
                            print(real_time_link_response)
                            for char in self.last_char:
                                pos = real_time_link_response[sentence_index:].find(char)
                                if pos >= 0:
                                    link_sentence = real_time_link_response[
                                        sentence_index : sentence_index + pos + 1
                                    ]
                                    sentence_index += pos + 1
                                    if link_sentence != "":
                                        get_link = True
                                        print(link_sentence)
                                        yield link_sentence
                        real_time_response = str(data_json["talk"])
                        for char in self.last_char:
                            pos = real_time_response[sentence_index:].find(char)
                            if pos >= 0:
                                sentence = real_time_response[
                                    sentence_index : sentence_index + pos + 1
                                ]
                                sentence_index += pos + 1
                                if sentence != "":
                                    yield sentence
                                break

    def chat_and_link(
        self,
        messages: list,
        model: str = "gpt-4o",
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        """指定したモデルを使用して会話を行い、会話の内容に応じた動作も生成する

        Args:
            messages (list): 会話のメッセージ
            model (str): 使用するモデル名 (デフォルト: "gpt-4o")
            temperature (float): temperatureパラメータ (デフォルト: 0.7)
        Returns:
            Generator[str, None, None]): 返答を順次生成する

        """
        if model in self.openai_model_name:
            yield from self.chat_and_link_gpt(
                messages=messages,
                model=model,
                temperature=temperature,
            )
        else:
            print(f"Model name {model} can't use for this function")
            return

import argparse
import time

from lib.chat_akari_introducer import ChatStreamAkariIntroducer
from lib.prompt_creator import system_prompt_creator
from lib.akari_rag_chatbot.lib.weaviate_rag_controller import WeaviateRagController


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-m",
        "--model",
        nargs="+",
        type=str,
        default=["gpt-4o"],
        help="Model name list",
    )
    parser.add_argument(
        "-c",
        "--collection",
        default="Akari",
        type=str,
        help="Weaviate collection name",
    )
    parser.add_argument(
        "-s",
        "--show_search",
        action="store_true",
        help="Show search result",
    )
    args = parser.parse_args()
    chat_stream = ChatStreamAkariIntroducer()
    weaviate_controller = WeaviateRagController()
    messages_list = []
    if args.collection is None:
        print(
            "Collection name is not available. Please specify collection name with '-c {collection_name}'."
        )
        print(f"Current collections: {weaviate_controller.get_collections()}")
        return
    for i in range(0, len(args.model)):
        messages_list.append([""])
    while True:
        print("文章をキーボード入力後、Enterを押してください。")
        text = input("Input: ")
        rag_start = time.time()
        response = weaviate_controller.hybrid_search(
            text=text,
            limit=3,
            alpha=0.75,
            rerank=False,
            collection_name=args.collection,
        )
        print(f"search time: {time.time() - rag_start:.2f} [s]")
        contexts = ""
        for p in response.objects:
            if args.show_search:
                print(f"source: {p.properties['source']}")
                print(f"content: {p.properties['content']}")
            contexts += p.properties["content"]
        system_prompt = system_prompt_creator(context=contexts)
        for i, model in enumerate(args.model):
            messages_list[i][0] = chat_stream.create_message(
                system_prompt, role="system"
            )
            messages_list[i].append(chat_stream.create_message(text, role="user"))
            response = ""
            start = time.time()
            is_first = True
            output_delay = 0.0
            for sentence in chat_stream.chat_and_link(
                messages_list[i], model=model, temperature=0.2
            ):
                response += sentence
                print(sentence, end="", flush=True)
                if is_first:
                    output_delay = time.time() - start
                    is_first = False
            # chatGPTの返答をassistantメッセージとして追加
            messages_list[i].append(
                chat_stream.create_message(response, role="assistant")
            )
            interval = time.time() - start
            print("")
            print("-------------------------")
            print(f"delay: {output_delay:.2f} [s]  total_time: {interval:.2f} [s]")
            print("")


if __name__ == "__main__":
    main()

import argparse
import os
import urllib.parse

AKARI_DOC_URL = "https://akarigroup.github.io/docs/"


def convert_path_to_local_html(file_path):
    # _sources/ を削除し、拡張子を .html に変更
    new_path = file_path.replace("_sources/", "")
    new_path = urllib.parse.quote(new_path)
    new_path = new_path.replace("rst.txt", "html")
    return new_path


def convert_path_to_public_url(file_path):
    # _sources/ より前を削除し、拡張子を .html に変更
    new_path = file_path.split("_sources/", 1)[-1]
    new_path = urllib.parse.quote(new_path)
    new_path = new_path.replace("rst.txt", "html")
    new_path = new_path.replace("[", "html")
    return new_path


def convert_parmlink(title: str) -> str:
    print(f"Title: {title}")
    new_title = title.lower()
    new_title = urllib.parse.quote(new_title)
    return new_title


def replace_decorative_lines_for_local_html(path: str, text: str):
    lines = text.splitlines()
    result = []
    for i, line in enumerate(lines):
        # 特定の装飾記号のみの行を検出
        if (
            line.strip()
            in {
                "=" * len(line.strip()),
                "*" * len(line.strip()),
                "-" * len(line.strip()),
                "^" * len(line.strip()),
            }
            and len(line.strip()) > 0
        ):
            # 一つ前の行が存在し、かつ空行でない場合のみ置き換える
            if i > 0 and lines[i - 1].strip():
                result.append(
                    f"file://{convert_path_to_public_url(path)}#{convert_parmlink(lines[i - 1])}"
                )
            else:
                result.append(line)  # 置き換え条件を満たさない場合はそのまま追加
        else:
            result.append(line)
    return "\n".join(result)


def replace_decorative_lines_for_public_url(path: str, text: str):
    lines = text.splitlines()
    result = []
    for i, line in enumerate(lines):
        # 特定の装飾記号のみの行を検出
        if (
            line.strip()
            in {
                "=" * len(line.strip()),
                "*" * len(line.strip()),
                "-" * len(line.strip()),
                "^" * len(line.strip()),
            }
            and len(line.strip()) > 0
        ):
            # 一つ前の行が存在し、かつ空行でない場合のみ置き換える
            if i > 0 and lines[i - 1].strip():
                result.append(
                    f"{AKARI_DOC_URL}{convert_path_to_public_url(path)}#{convert_parmlink(lines[i - 1])}"
                )
            else:
                result.append(line)  # 置き換え条件を満たさない場合はそのまま追加
        else:
            result.append(line)
    return "\n".join(result)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", type=str, help="path to load text files")
    parser.add_argument("-s", "--save_path", type=str, help="path to save text files")
    args = parser.parse_args()
    file_paths = []
    if args.path is None:
        print("Path is not available")
        return
    if os.path.isdir(args.path):
        file_paths = [
            os.path.abspath(os.path.join(root, file))
            for root, dirs, files in os.walk(args.path)
            for file in files
        ]
    else:
        file_paths.append(args.path)
    for file_path in file_paths:
        print(f"Processing {file_path}")
        with open(file_path, "r", encoding="utf-8") as file:
            text = file.read()
            # 関数を呼び出して結果を出力
            output_text = replace_decorative_lines_for_public_url(
                path=file_path, text=text
            )
            if args.save_path:
                path = os.path.join(
                    args.save_path, os.path.relpath(file_path, args.path)
                )
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as save_file:
                    save_file.write(output_text)


if __name__ == "__main__":
    main()

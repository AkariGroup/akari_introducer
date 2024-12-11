import argparse
import os
from datetime import datetime
from typing import Any, List
from datetime import datetime, timezone

YOUTUBE_APIKEY = os.environ.get("YOUTUBE_API_KEY")
from googleapiclient.discovery import build


def get_channel_videos(channel_id: str) -> List[Any]:
    """YouTubeチャンネルのアップロード済み動画のリストを取得する。
    Args:
        channel_id (str): YouTubeチャンネルID
        date_after (datetime): この日付以降にアップロードされた動画のみ取得する

    Returns:
        list: Youtube動画のURL、タイトル、投稿日時のリスト
    """
    youtube = build("youtube", "v3", developerKey=YOUTUBE_APIKEY)

    videos = []
    next_page_token = None

    while True:
        # チャンネルのアップロード済みビデオプレイリストを取得
        channel_response = (
            youtube.channels().list(part="contentDetails", id=channel_id).execute()
        )

        playlist_id = channel_response["items"][0]["contentDetails"][
            "relatedPlaylists"
        ]["uploads"]

        # プレイリストの動画を取得
        playlist_response = (
            youtube.playlistItems()
            .list(
                part="snippet",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token,
            )
            .execute()
        )

        for item in playlist_response["items"]:
            video_id = item["snippet"]["resourceId"]["videoId"]
            video_title = item["snippet"]["title"]
            video_description = item["snippet"]["description"]
            published_at = datetime.fromisoformat(
                item["snippet"]["publishedAt"].replace("Z", "+00:00")
            )
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            videos.append((video_url, video_title, published_at, video_description))

        next_page_token = playlist_response.get("nextPageToken")
        if not next_page_token:
            break

    return videos


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--channel_id",
        type=str,
        help="Youtube channel ID",
        default="UCM7QPeFX99QHm9e825Ndu3w",
    )
    parser.add_argument("-s", "--save_path", type=str, help="path to save text files")
    args = parser.parse_args()
    video_list = get_channel_videos(args.channel_id)

    output_text = ""
    for url, title, date,description in video_list:
        output_text += f"Title: {title}\nURL: {url}\nDate: {date}\nDescription: {description}\n\n"
        output_text += "==============================\n"
    if args.save_path:
        path = f"{args.save_path}/youtube_videos.txt"
        with open(path, "w", encoding="utf-8") as save_file:
            save_file.write(output_text)


if __name__ == "__main__":
    main()

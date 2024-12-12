# akari_introducer

AKARIについての質問に対して、webブラウザ上にYoutubeやwebマニュアルのページなどを表示しながら回答する展示会用音声対話botアプリ。

## submoduleの更新
`git submodule update --init --recursive`  

## 仮想環境の作成
`python -m venv venv`  
`source venv/bin/activate`  
`pip install -r requirements.txt`  

## セットアップ方法
1. [akari_rag_chatbotのREADME](https://github.com/AkariGroup/akari_rag_chatbot/blob/main/README.md)のセットアップ手順に沿ってセットアップする。  
  **ただし、今回はWeaviateは音声合成と同じ外部PCで起動すること。外部PCはAKARIと同一のネットワーク内に存在する必要がある。また音声合成用にnvidia GPUの搭載されたものが望ましい**  
  **また、外部PCの音声合成としてはVOICEVOXを起動すること(Style-Bert-VITS2, Aivisも使用可能だが、script/内の起動スクリプトはVOICEVOX用になっています。)**  

2. 同様に[akari_rag_chatbot](https://github.com/AkariGroup/akari_rag_chatbot)を音声合成用の外部PCにcloneし、Weaviateをdockerで起動する。  
(外部PCで)  
`git clone https://github.com/AkariGroup/akari_rag_chatbot.git`  
`cd akari_rag_chatbot/weaviate/docker`  
`docker-compose up -d`  

3. AKARIにGoogle Chromeブラウザをインストールする。

4. Google Chromeブラウザに拡張機能[Ignore X-Frame headers](https://chrome.google.com/webstore/detail/ignore-x-frame-headers/gleekbfjekiniecknbkamfmkohkpodhe?pli=1)を追加する。(githubのリンクなどをiframeで表示するため)  

## Weaviateへのデータ追加
本アプリのRAGであるWeaviateに追加するデータは、  
・AKARIのwebマニュアルをbuildする際に生成されるsphinxベースのtxtファイルを加工したもの。  
・YouTubeのAKARIチャンネルの動画のタイトルと説明文を一覧にしたtxtファイル。  
の2種類がある。  
以下の2種類の方法でWeaviateにデータを追加することが出来る。  

### 既に加工済みのデータを用いる場合
本レポジトリ内に、加工済みのデータを含むrag_data.zipが格納されているため、そちらを用いてWeaviateにデータを追加することが出来る。
1. `akari_introducer/rag_data` 直下のrag_data.zipを展開する。  
  `cd akari_introducer/rag_data`  
  `unzip rag_data.zip`  

2. 展開されたtxtファイルをWeaviateに追加する。  
  `cd ../`  
  `source venv/bin/activate`  
  `python3 lib/akari_rag_chatbot/weaviate_uploader.py -c Akari --host {Weaviateを起動している外部PCのipアドレス} -p rag_data/`  

### 自分でデータ加工を行う場合
本レポジトリにsubmoduleとして含まれている[AKARIのwebマニュアルのリポジトリ](https://github.com/AkariGroup/docs.git)を用いて、データ加工を行うことが出来る。  
データの加工手順を知りたい方向け。  

1. docsを[READMEの手順](https://github.com/AkariGroup/docs/blob/main/README.md)に沿ってbuildする。  
  `cd akari_introducer/docs`  
  READMEの手順の2.以降を実行し、docsをbuildする。  

2. buildしたデータを加工する。  
  `cd ../../`  
  `python3 manual_converter.py -p docs/_build/html/_sources/source -s rag_data/`  
  `docs/_build/html/_sources/source`には、buildする際に生成される、sphinxのソースファイルを元にしたtxtファイルが格納されている。  
  manual_converter.pyは、このtxtファイルを加工し、表題の飾り文字部分をその表題へのリンクに変換している。  

3. YoutubeのAKARIチャンネルから動画情報を取得する。  
  `python3 youtube_info_abstractor.py -s rag_data/`  
  これにより、YouTubeのAKARIチャンネルの動画のタイトルと説明文を一覧にしたtxtファイルが生成され、`rag_data/youtube_videos.txt` に追加される。  

4. 作成されたtxtファイルをWeaviateに追加する。  
  `source venv/bin/activate`  
  `python3 lib/akari_rag_chatbot/weaviate_uploader.py -c Akari --host {Weaviateを起動している外部PCのipアドレス} -p rag_data/`

## 起動方法
### スクリプトを用いて起動する場合
`cd script`  
`./introducer_auto.sh {Weaviate、VOICEVOXを起動している外部PCのipアドレス} {akari_motion_serverのパス}`

実行すると、webブラウザのタブが自動で開きAKARI紹介のYoutube動画の再生が開始する。  
以降マイクに話しかけると、都度AKARIが回答し、同時にwebブラウザ上に回答に近しいYoutubeの動画、webマニュアルのページ、またはマニュアル内に含まれるリンク先(各部品の製品紹介ページや各レポジトリのGithubページなど)が表示される。  
100秒程度話しかけないと、AKARI紹介のYoutube動画の再生に戻る。  

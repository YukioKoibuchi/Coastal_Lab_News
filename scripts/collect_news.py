"""
海岸関係ニュース自動収集スクリプト（プロトタイプ）

直近の変更点（2026-07-29、ペイウォール除外・ジャンル分類）:
    1. 会員登録・ログインしないと読めない記事を除外するようにした。
       - 河北新報オンライン・北日本新聞（webun）はEXCLUDED_PUBLISHERSに追加し、
         直接の情報源（RSS_SOURCES）からは河北新報オンラインを外した。
       - それとは別に、check_link()でページ本文を実際に見て、「会員登録」
         「ログインして続きを読む」等の定型文言（PAYWALL_INDICATOR_PHRASES）が
         あればどの配信元の記事でも除外するようにした。ベストエフォートの判定で、
         JavaScriptで動的に表示されるペイウォールは見逃す可能性がある。
       - 除外件数は「会員登録が必要で除外: ◯件」としてコンソールに表示される。
    2. ホームページ表示時に同じ話題（例：地震直後の津波・港湾被害、夏の海水浴事故）が
       並んでしまう問題への対策として、記事にジャンル（genre）を付けるようにした
       （classify_genre()）。ジャンルは「地震・津波」「事故・安全」「高潮・気象」
       「侵食・保全工事」「港湾・インフラ」「環境・生態系・研究」「その他」の7種類。
       ジャンルが連続しないように並び替えるdiversify_by_genre()も用意した
       （ラウンドロビン方式。詳しくは関数のdocstring参照）。ホームページの
       トップ3件・詳細一覧ページのどちらでも使える想定。genreはdecisions.csv・
       news_auto.jsonにも記録される。

直近の変更点（2026-07-29、発行元の除外・優先順位）:
    1. 中身がほぼ無い配信元（au Webポータルなど）をEXCLUDED_PUBLISHERSで除外できるように
       した。タイトル末尾の「 - 発行元名」から発行元を判定する（extract_publisher()）。
       除外した件数は「除外対象の発行元: ◯件」としてコンソールに表示される。
    2. 同じニュースを複数のメディアが重複して報じていた場合、重複統合（dedupe_by_title）
       で「どれを残すか」の判断基準に発行元の優先順位（PUBLISHER_PRIORITY_TIERS）を
       追加した。NHK・全国紙・主要地方紙を最優先、共同通信等のニュース社を次点、
       それ以外は同列、FM局・ラジオ局は優先度を下げている。他に報じていたメディア名は
       代表記事の"other_sources"に記録され、decisions.csv・review_server.pyの画面
       にも表示される。どのメディアを採用したかはコンソールにも
       「[重複統合] 「タイトル」（採用メディア）を採用（他に報じたメディア: ...）」
       として表示される。
    優先順位の基準やau以外の除外対象は、実際の収集結果を見ながら
    EXCLUDED_PUBLISHERS / PUBLISHER_PRIORITY_TIERS / LOW_PRIORITY_PUBLISHER_KEYWORDS
    を編集して調整すること。

直近の変更点（2026-07-29、リンク切れ検知）:
    公開候補として残す直前に、そのURLへ実際にアクセスできるかを確認するようにした
    （is_link_alive()）。404・410など明確なリンク切れだけでなく、403や5xx、
    タイムアウトなど「壊れているとは限らないが今は確認できない」場合も、鮮度不明の
    記事を除外するのと同じ考え方で安全側に倒して除外する。除外した件数は
    「リンク切れで除外: ◯件」としてコンソールに表示され、除外した記事名もその場で
    1件ずつ表示される。ボット判定で正常なリンクまで除外してしまう可能性があるため、
    特定の情報源で除外が多発するようなら、この関数の判定基準を見直すこと。

直近の変更点（2026-07-29、収集範囲の拡大）:
    国交省プレスリリースに偏りすぎる（採用率が低い）問題を受けて、情報源とGoogle
    ニュースのクエリを広げた。
    1. Googleニュースのクエリを5本→17本に拡大。事故・安全系（離岸流、海水浴場 事故、
       サーフィン 事故、海岸 陥没、海岸 漂着）と環境・研究系（海洋ごみ、藻場、サンゴ礁、
       マングローブ、ウミガメ、海洋生態系 研究、サンゴ礁 白化）を追加した。
    2. CORE_KEYWORDSに上記に対応する語（離岸流、海水浴場、サーフィン、漂着、海洋ごみ、
       藻場、サンゴ礁、マングローブ、ウミガメ）を追加した。「陥没」は道路陥没など無関係な
       ニュースが多いため、単独ではキーワードに加えていない。
    3. 近畿地方整備局港湾空港部・九州地方整備局・環境省・水産庁をHTML一覧スクレイピングの
       情報源に追加した。
    4. 神奈川県庁（RSS）、河北新報・沖縄タイムス（地方紙RSS）をRSS_SOURCESに追加した。
       河北新報・沖縄タイムスはtrust="news"（Googleニュースと同じ、スコア2以上を要求）。
    5. 東北・中部地方整備局、北海道開発局は汎用的に使えるURL（年度で変わらないもの）を
       確認できなかったため見送った。静岡県など他の沿岸都道府県RSSも同様に未着手。
       いずれもこのセッションのネットワーク制限のため、追加した情報源が実際に正しく
       取得できるかは未検証（構造や文字コードが把握と違う可能性がある）。

直近の変更点（情報源の追加）:
    気象庁・海上保安庁を情報源に追加した。
    - 気象庁は通常のHTMLではなく press_list.js というJS配列ファイルで報道発表一覧を
      配信しているため、専用の解析関数 fetch_jma_press_list() を用意した。文字コードは
      utf-8 → euc-jp → shift_jis の順で自動判定を試みるが、実際の配信文字コードは
      このセッションのネットワーク制限のため確認できていない。タイトルが文字化けする
      場合は、この関数内のencodingリストの順序を入れ替えて試すこと。
    - 海上保安庁（kaiho.mlit.go.jp）は通常のHTML一覧なので既存のfetch_html_list()で
      対応できたが、記事一覧に日付が併記されていないため、published_atが空になり
      鮮度フィルタで除外されやすい（安全側の挙動だが、拾える件数は少ない見込み）。

第2版からの変更点:
    1. 鮮度フィルタを追加。published_atが取得日からRECENCY_DAYS（既定10日）を超えている
       記事、および日付が読み取れなかった記事は、自動公開の対象から外す。
       （実データで検証したところ、Googleニュース検索は2014年など古い記事も
         一致すればそのまま返してくるため、キーワードスコアとは別に必要だった）
    2. 実行のたびに data/news_auto_YYYYMMDD.json という日付つきファイルを保存し、
       過去分を上書きしないようにした（1週間分ためて後で振り返れるようにするため）。
       data/news_auto.json は「最新の実行結果」を指す形で毎回上書きする
       （news-preview.html はこちらを見にいく想定）。
    3. 新しく見つかった記事は data/decisions.csv に追記されるようにした。
       decision 列が空欄になっているので、日々の実行後にこのCSVを開いて
       「keep」（載せてよい）か「reject」（不要）を書き込んでいく。
       1週間ほどデータがたまったら analyze_feedback.py を実行すると、
       キーワードごとの採用率をもとに調整案を出す。

実行方法:
    pip install feedparser requests beautifulsoup4
    python collect_news.py

    ※ 実際にインターネットへ接続する。Cowork のサンドボックス環境からは
      外部ネットワークへ直接アクセスできないため、このセッション内では実行結果を
      確認できていない。お手元のPCで実行することを前提にしている。

自動実行（スケジュール）について:
    このスクリプト自体はCowork側からは自動実行できない（サンドボックスがネットワーク
    制限されているため）。お手元のMacで毎日自動実行したい場合は、README.mdに記載した
    cron の設定例を使って、ご自身のMac上でスケジュールしていただく必要がある。
"""

import ast
import csv
import difflib
import json
import re
import hashlib
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote

import feedparser
import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# 1. キーワード設定
# ---------------------------------------------------------------------------
CORE_KEYWORDS = [
    "海岸", "沿岸", "海浜", "砂浜", "養浜", "侵食", "海岸侵食", "海岸保全",
    "護岸", "防波堤", "離岸堤", "ヘッドランド", "高潮", "高波", "港湾",
    "海岸線", "海岸法", "海洋", "海難事故",
    # 事故・安全関連（2026-07-29追加）
    "離岸流", "海水浴場", "サーフィン", "漂着",
    # 環境・生態系・研究関連（2026-07-29追加、国交省中心だった情報源に環境省・水産庁を
    # 加えたことに合わせて、環境系ニュースも拾えるようにした）
    "海洋ごみ", "藻場", "サンゴ礁", "マングローブ", "ウミガメ",
    # 2026-08-01追加。津波はこれまでジャンル分類（GENRE_KEYWORDS）専用で、スコア判定には
    # 使っていなかった。検索キーワードとして採用する指示を受けて追加した。
    "津波",
]

# ホームページへの完全自動公開（人によるレビュー無し）を許可するキーワード
# （2026-08-05追加、2026-08-14更新）。CORE_KEYWORDSに載っているだけでは足りず、
# ここにも入っている必要がある。analyze_feedback.pyで「判定5件以上・却下率が高い
# フラグなし」を確認できたキーワードだけを手動でここに追加すること。
# 2026-08-14時点でのdecisions.csv 192件の分析結果に基づき、海難事故（93.8%、16件）・
# 高潮（86.7%、15件）・沿岸（91.7%、12件）・高波（81.8%、11件）・津波（83.3%、6件）を追加。
# 対象外（判定件数不足）: ヘッドランド（4件）、海岸線・養浜・サンゴ礁・海浜（各1件）
# 対象外（判定件数はあるが採用率が不安定・要観察）: マングローブ（42.9%、7件。
#   前回33.3%・6件から改善して40%ラインは超えたが、変動が大きくまだ様子見）
TRUSTED_KEYWORDS = [
    "海岸", "海洋", "離岸流", "港湾", "海洋ごみ", "海水浴場",
    "砂浜", "海岸保全", "侵食", "サーフィン", "海岸侵食", "ウミガメ", "漂着",
    "海難事故", "高潮", "沿岸", "高波", "津波",
]

ADJACENT_ONLY_KEYWORDS = [
    "土砂災害", "土石流", "砂防", "ダム", "河川", "下水道", "水道",
    "地下水", "水資源",
]

# 2026-07-29: 専門用語5本のみだと国交省プレスリリースに偏りやすいため、事故・安全系と
# 環境・研究系のクエリを追加して裾野を広げた。「海岸 陥没」はCORE_KEYWORDSに「陥没」を
# 加えていない（道路陥没など無関係なニュースが多く単独では誤検出リスクが高いため）。
# タイトルに「海岸」等が含まれていれば別の理由でスコアが付く想定。
GOOGLE_NEWS_QUERIES = [
    "海岸侵食", "養浜", "海岸保全", "高潮 海岸", "海難事故",
    # 事故・安全
    "離岸流", "海水浴場 事故", "サーフィン 事故", "海岸 陥没", "海岸 漂着",
    # 環境・研究
    "海洋ごみ", "藻場", "サンゴ礁", "マングローブ", "ウミガメ",
    "海洋生態系 研究", "サンゴ礁 白化",
    # 2026-08-01追加。「高潮 海岸」の組み合わせだけでなく、単独の「高潮」「津波」でも
    # 検索するよう指示を受けて追加。「海難事故」は既に単独クエリとして存在済み。
    "高潮", "津波",
]

MIN_SCORE_FOR_GOV = 1
MIN_SCORE_FOR_NEWS = 2

RECENCY_DAYS = 10  # これより古い記事（および日付不明の記事）は自動公開の対象から外す

# ---------------------------------------------------------------------------
# 2. 情報源リスト
# ---------------------------------------------------------------------------
RSS_SOURCES = [
    {"name": "国土交通省 プレスリリース", "url": "https://www.mlit.go.jp/pressrelease.rdf", "trust": "government"},
    {"name": "国土交通省 新着情報", "url": "https://www.mlit.go.jp/index.rdf", "trust": "government"},
    {"name": "国土交通省 災害情報", "url": "https://www.mlit.go.jp/saigai.rdf", "trust": "government"},
    # 2026-07-29追加。カテゴリ番号「10」の実際の中身（記者発表専用か新着全般か）は
    # このセッションのネットワーク制限のため未確認。他カテゴリの方が良ければ番号を調整すること。
    {"name": "神奈川県 新着情報", "url": "http://www.pref.kanagawa.jp/rss/10/list1.xml", "trust": "government"},
    # 2026-07-29追加。地方紙は全国紙より海岸侵食・養浜工事など地域密着ニュースを
    # 拾いやすい想定。trust="news"（Googleニュースと同じ扱い＝スコア2以上を要求）。
    # 河北新報オンラインは会員登録が無いと本文が読めないことが分かったため、直接の
    # 情報源からは外した（EXCLUDED_PUBLISHERSにも入れてあるので、Googleニュース経由で
    # 河北新報の記事が出てきた場合もあわせて除外される）。
    {"name": "沖縄タイムス", "url": "http://www.okinawatimes.co.jp/rss/index.xml", "trust": "news"},
] + [
    {
        "name": f"Googleニュース検索：{q}",
        "url": f"https://news.google.com/rss/search?q={quote(q)}&hl=ja&gl=JP&ceid=JP:ja",
        "trust": "news",
    }
    for q in GOOGLE_NEWS_QUERIES
]

HTML_LIST_SOURCES = [
    {"name": "北陸地方整備局 記者発表", "url": "https://www.hrr.mlit.go.jp/press/index.html", "trust": "government"},
    {"name": "中国地方整備局 記者発表", "url": "http://www.cgr.mlit.go.jp/kisya/index.html", "trust": "government"},
    {"name": "四国地方整備局 記者発表", "url": "https://www.skr.mlit.go.jp/pres/new/index.html", "trust": "government"},
    {"name": "海上保安庁 報道発表", "url": "https://www.kaiho.mlit.go.jp/info/kouhou/", "trust": "government"},
    # 2026-07-29追加。港湾空港部は近畿地方整備局の中でも海岸・港湾に直結する部署なので、
    # 整備局本体の一般ニュースより関連度が高いはず。
    {"name": "近畿地方整備局 港湾空港部 記者発表", "url": "https://www.pa.kkr.mlit.go.jp/general/press_release/index.html", "trust": "government"},
    {"name": "九州地方整備局 記者発表", "url": "http://www.qsr.mlit.go.jp/press_release/", "trust": "government"},
    # 2026-07-29追加。環境省・水産庁は国交省と違う切り口（海洋ごみ・サンゴ礁・藻場・
    # 漁港など）のニュースを拾うことを狙っている。ページ全体に海岸と無関係な話題も
    # 多いため、CORE_KEYWORDSでの絞り込みに依存する。
    {"name": "環境省 報道発表", "url": "https://www.env.go.jp/press/", "trust": "government"},
    {"name": "水産庁 報道発表", "url": "https://www.jfa.maff.go.jp/j/press/", "trust": "government"},
]
# 東北・中部地方整備局、北海道開発局は記者発表一覧のURLがその年度のPDF個別ページや
# ランダムなスラッグ（例: hkd.mlit.go.jp/.../slo5pa0000010y86.html）になっており、
# 汎用的に張り続けられるURLを確認できなかったため今回は見送った。必要なら該当局の
# サイトを直接確認してURLを追加すること。静岡県・千葉県・和歌山県など他の沿岸都道府県の
# 記者発表RSSも同様に、URLが確認でき次第RSS_SOURCESに追加できる。

# 気象庁の報道発表一覧は通常のHTMLではなく、press_list.jsというJS配列ファイルで
# 配信されている（ブラウザがJSを実行して一覧を組み立てる方式）。専用の解析関数
# fetch_jma_press_list() で読み込む。
JMA_SOURCES = [
    {"name": "気象庁 報道発表資料", "url": "https://www.jma.go.jp/jma/press_list.js", "trust": "government"},
]

DATE_PATTERN = re.compile(r"(20\d{2}[/\-年]\d{1,2}[/\-月]\d{1,2}日?|令和\d+年\d{1,2}月\d{1,2}日)")

REIWA_ERA_START_YEAR = 2019 - 1  # 令和1年 = 2019年

# ---------------------------------------------------------------------------
# 3. 発行元（メディア）の除外・優先順位（2026-07-29追加）
# ---------------------------------------------------------------------------
# 中身がほぼ無い配信元・会員登録しないと読めない配信元は、キーワードにマッチしても
# 候補から外す。Googleニュース・地方紙RSSのタイトルは末尾に " - 発行元名" が付くため、
# そこから発行元名を取り出して判定する（部分一致。例: "河北新報"は"河北新報オンライン"にも
# マッチする）。河北新報オンライン・北日本新聞（webun）は会員登録が無いと本文が読めない
# ため2026-07-29追加。ほかに気づいたら同様にここへ追加すること。
EXCLUDED_PUBLISHERS = ["au Webポータル", "河北新報", "北日本新聞", "webun"]

# 同じニュースを複数のメディアが重複して報じていた場合、重複統合でどれを残すかの
# 優先順位。数字が小さいほど優先度が高い（＝内容が詳しい・信頼できると想定）。
# ここに無い発行元（一般の地方紙・ネットニュースなど）はDEFAULT_PUBLISHER_TIER扱い。
# ラジオ局は記事が短い傾向があるため、既定よりさらに優先度を下げている。
# 過不足があれば、このリストを編集して調整すること。
PUBLISHER_PRIORITY_TIERS = [
    ["NHK", "朝日新聞", "読売新聞", "毎日新聞", "産経新聞", "日本経済新聞",
     "河北新報", "沖縄タイムス", "琉球新報"],
    ["共同通信", "時事通信", "47NEWS", "Yahoo!ニュース"],
]
DEFAULT_PUBLISHER_TIER = len(PUBLISHER_PRIORITY_TIERS)
LOW_PRIORITY_PUBLISHER_KEYWORDS = ["FM", "ラジオ", "コミュニティ放送"]
LOW_PRIORITY_PUBLISHER_TIER = DEFAULT_PUBLISHER_TIER + 1


def extract_publisher(title: str) -> str | None:
    """タイトル末尾の " - 発行元名" を取り出す（無ければNone）。
    発行元名自体にハイフンが含まれる場合は正しく分割できないことがある。"""
    if " - " not in title:
        return None
    return title.rsplit(" - ", 1)[-1].strip()


def is_excluded_publisher(title: str) -> bool:
    publisher = extract_publisher(title)
    if publisher is None:
        return False
    return any(name in publisher for name in EXCLUDED_PUBLISHERS)


def publisher_tier(title: str) -> int:
    """発行元の優先順位（数字が小さいほど優先）を返す。"""
    publisher = extract_publisher(title)
    if publisher is None:
        return DEFAULT_PUBLISHER_TIER
    for tier_index, names in enumerate(PUBLISHER_PRIORITY_TIERS):
        if any(name in publisher for name in names):
            return tier_index
    if any(kw in publisher for kw in LOW_PRIORITY_PUBLISHER_KEYWORDS):
        return LOW_PRIORITY_PUBLISHER_TIER
    return DEFAULT_PUBLISHER_TIER


def display_source_name(item: dict) -> str:
    """重複記録などで人に見せる用のメディア名。Googleニュース・地方紙RSS経由の記事は
    タイトル末尾の発行元名（例：NHK水戸ニュース）を使い、取れない場合は情報源の
    フィード名（source_name。例：国土交通省 プレスリリース）で代用する。"""
    return extract_publisher(item["title"]) or item["source_name"]


# ---------------------------------------------------------------------------
# 4. ジャンル分類（ホームページ表示時に同じ話題が並ぶのを防ぐため。2026-07-29追加）
# ---------------------------------------------------------------------------
# CORE_KEYWORDSとは別に、ジャンル分けだけのための語も含む（例:「地震」「津波」は
# スコアには使わないが、ジャンル分類には使う）。1記事が複数ジャンルの語を含む場合は
# GENRE_PRIORITYの順番（先に書いたジャンルほど優先）で1つに決める。
GENRE_KEYWORDS = {
    "地震・津波": ["地震", "津波"],
    "事故・安全": ["海難事故", "離岸流", "海水浴場", "サーフィン", "水難", "溺れ"],
    "高潮・気象": ["高潮", "高波", "台風", "暴風"],
    "侵食・保全工事": ["侵食", "海岸保全", "養浜", "護岸", "防波堤", "離岸堤", "ヘッドランド"],
    "港湾・インフラ": ["港湾"],
    "環境・生態系・研究": ["海洋ごみ", "藻場", "サンゴ礁", "マングローブ", "ウミガメ", "漂着", "生態系"],
}
GENRE_PRIORITY = [
    "地震・津波", "事故・安全", "高潮・気象", "侵食・保全工事", "港湾・インフラ", "環境・生態系・研究",
]
DEFAULT_GENRE = "その他"


def classify_genre(title: str) -> str:
    """タイトルの文言から記事のジャンルを1つ決める。ホームページのトップ表示や
    一覧ページで同じジャンルの記事が連続しないようにするための分類で、
    公開の可否（スコア）には影響しない。"""
    for genre in GENRE_PRIORITY:
        if any(kw in title for kw in GENRE_KEYWORDS[genre]):
            return genre
    return DEFAULT_GENRE


def diversify_by_genre(items: list[dict], count: int | None = None) -> list[dict]:
    """公開日の新しい順に並んだitemsを、ジャンルが連続しにくいように並び替える
    （2026-07-29追加）。地震の直後は地震・津波関連、夏は事故・安全関連の記事が
    同時多発しやすく、新着順のままだとホームページに同じ話題ばかり並んでしまう
    ことへの対策。

    やり方: ジャンルごとに新着順のまま束（バケツ）に分け、「その時点で一番新しい
    記事を持っているジャンル」から順に1件ずつ取り出すのを繰り返す（ラウンドロビン）。
    こうすると、結果として隣り合う記事のジャンルはできるだけ被らず、かつ全体としては
    おおむね新しい記事が前に来る。count を指定すると、ホームページ上部のような
    件数限定表示（例：3件）向けに、そこで打ち切って返す。

    どのジャンルの記事も他のジャンルより極端に多い場合（例：ある週は事故・安全の
    記事しか無い）は、他のジャンルが尽きた後は同じジャンルが連続することもある
    （避けられない）。
    """
    buckets: dict[str, list[dict]] = {}
    genre_order: list[str] = []  # ジャンルの初出順＝そのジャンルの一番新しい記事が出た順
    for item in items:
        genre = item.get("genre", DEFAULT_GENRE)
        if genre not in buckets:
            buckets[genre] = []
            genre_order.append(genre)
        buckets[genre].append(item)

    result: list[dict] = []
    while any(buckets[g] for g in genre_order):
        for g in genre_order:
            if buckets[g]:
                result.append(buckets[g].pop(0))
                if count is not None and len(result) >= count:
                    return result
    return result


def score_entry(title: str) -> tuple[int, list[str]]:
    matched = [kw for kw in CORE_KEYWORDS if kw in title]
    return len(matched), matched


def is_adjacent_false_positive(matched_core: list[str], title: str) -> bool:
    if matched_core:
        return False
    return any(kw in title for kw in ADJACENT_ONLY_KEYWORDS)


def min_score_for(trust: str) -> int:
    return MIN_SCORE_FOR_GOV if trust == "government" else MIN_SCORE_FOR_NEWS


def make_id(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]


def parse_published(raw: str):
    """様々な形式の日付文字列をdatetimeに変換する。読めなければNoneを返す。"""
    if not raw:
        return None
    raw = raw.strip()

    # RFC822形式（feedparserのpublished/updatedでよく出てくる）
    try:
        d = parsedate_to_datetime(raw)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d
    except (TypeError, ValueError):
        pass

    # 令和N年M月D日
    m = re.match(r"令和(\d+)年(\d{1,2})月(\d{1,2})日", raw)
    if m:
        year = REIWA_ERA_START_YEAR + int(m.group(1))
        try:
            return datetime(year, int(m.group(2)), int(m.group(3)), tzinfo=timezone.utc)
        except ValueError:
            return None

    # 2026-07-08 / 2026/07/08 / 2026年7月8日
    m = re.match(r"(20\d{2})[/\-年](\d{1,2})[/\-月](\d{1,2})", raw)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=timezone.utc)
        except ValueError:
            return None

    return None


def is_fresh(raw_published: str) -> bool:
    parsed = parse_published(raw_published)
    if parsed is None:
        return False  # 日付が読めない記事は「鮮度不明」として自動公開しない
    age = datetime.now(timezone.utc) - parsed
    return age <= timedelta(days=RECENCY_DAYS)


def sort_by_published(items: list[dict]) -> list[dict]:
    """日付表記が混在していても、実際の公開日時が新しい順に並べる。"""
    oldest = datetime.min.replace(tzinfo=timezone.utc)
    return sorted(
        items,
        key=lambda item: parse_published(item["published_at"]) or oldest,
        reverse=True,
    )


LINK_CHECK_TIMEOUT = 10
_LINK_CHECK_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# ページ本文にこれらの文言が含まれていたら、会員登録・ログインしないと読めない記事
# （ペイウォール）の可能性が高いと判断する（2026-07-29追加、ベストエフォート）。
PAYWALL_INDICATOR_PHRASES = [
    "会員登録", "会員限定", "有料会員", "ログインして続きを読む", "この続きを読むには",
    "続きを読むには会員", "無料会員登録", "定期購読",
]


def check_link(url: str) -> tuple[bool, bool]:
    """URLへ実際にアクセスして (生きているか, ペイウォールの可能性があるか) を返す
    （2026-07-29追加）。

    リンク切れやペイウォールの記事をホームページに載せてしまうと訪問者の期待を
    下げるため、公開候補に残す前に確かめる。ペイウォール判定には本文が必要なため、
    GETリクエストに統一している（以前はHEADで済ませていた）。

    生きているかどうかの判定:
        404・410など「明確に存在しない」場合はFalse。403や5xx、タイムアウトなど
        「壊れているとは限らないが今は確認できない」場合も、鮮度不明の記事を除外する
        のと同じ考え方で安全側に倒してFalseとして扱う。ボット判定で403を返すサイトを
        誤って除外してしまう可能性はあるため、特定の情報源で除外が多発するようなら、
        この関数の判定基準を見直すこと。

    ペイウォール判定:
        ページ本文にPAYWALL_INDICATOR_PHRASESの文言が含まれるかどうかで推定する
        ベストエフォートの判定。実際のペイウォールはJavaScriptで動的に表示される
        ことも多く、ここで使っているrequestsは静的HTMLしか取得できないため、
        見逃す（＝実際はペイウォールなのに検出できない）ことがある。確実に除外
        したい配信元は、EXCLUDED_PUBLISHERSに名前を直接追加すること。

    Googleニュース経由のURLはGoogle側のリダイレクトを挟むため、
    allow_redirects=Trueで最終的な記事ページの内容を見るようにしている
    （Google側のリダイレクト自体がボット判定でブロックされる可能性は
    このセッションのネットワーク制限のため未検証）。
    """
    try:
        resp = requests.get(
            url, timeout=LINK_CHECK_TIMEOUT, headers=_LINK_CHECK_HEADERS, allow_redirects=True
        )
    except requests.RequestException:
        return False, False

    if resp.status_code >= 400:
        return False, False

    is_paywalled = any(phrase in resp.text for phrase in PAYWALL_INDICATOR_PHRASES)
    return True, is_paywalled


def fetch_rss(source: dict) -> list[dict]:
    entries = []
    feed = feedparser.parse(source["url"])
    for e in feed.entries:
        title = e.get("title", "").strip()
        link = e.get("link", "").strip()
        if not title or not link:
            continue
        entries.append({
            "title": title,
            "url": link,
            "published_at": e.get("published", e.get("updated", "")),
        })
    return entries


def fetch_html_list(source: dict) -> list[dict]:
    entries = []
    try:
        resp = requests.get(source["url"], timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.encoding = resp.apparent_encoding
    except requests.RequestException:
        return entries

    soup = BeautifulSoup(resp.text, "html.parser")
    for a in soup.find_all("a"):
        title = a.get_text(strip=True)
        href = a.get("href", "")
        if not title or len(title) < 8 or not href:
            continue
        if not re.search(r"(press|kisha|houdou|\.pdf|\.html)", href, re.IGNORECASE):
            continue
        full_url = href if href.startswith("http") else requests.compat.urljoin(source["url"], href)
        prev_text = a.find_previous(string=True) or ""
        date_match = DATE_PATTERN.search(str(prev_text)) or DATE_PATTERN.search(title)
        entries.append({
            "title": title,
            "url": full_url,
            "published_at": date_match.group(0) if date_match else "",
        })
    return entries


def fetch_jma_press_list(source: dict) -> list[dict]:
    """気象庁の報道発表資料一覧は、通常のHTMLではなく press_list.js という
    JS配列ファイル（`array[num++] = ['1','/jma/press/...html','8','7','9','タイトル'];`
    という形式）で配信されている。ブラウザがこれを実行して一覧を組み立てているため、
    ここでは正規表現でJS配列の中身を抜き出し、Python側で解釈する。

    文字コードがContent-Typeヘッダーで正しく宣言されていないことがあるため、
    utf-8で読めなければeuc-jp、shift_jisの順で試す（実際の配信文字コードは
    このセッションのネットワーク制限のため確認できていない。文字化けする場合は
    このencodings のリストの順序を入れ替えて試すこと）。
    """
    entries = []
    try:
        resp = requests.get(source["url"], timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    except requests.RequestException:
        return entries

    text = None
    for encoding in ("utf-8", "euc-jp", "shift_jis"):
        try:
            text = resp.content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        text = resp.content.decode("utf-8", errors="replace")

    for m in re.finditer(r"array\[num\+\+\]\s*=\s*(\[.*?\])\s*;?\s*$", text, re.MULTILINE):
        try:
            row = ast.literal_eval(m.group(1))
        except (ValueError, SyntaxError):
            continue
        if len(row) < 6:
            continue

        _flag, path, era_year, month, day, title = row[0], row[1], row[2], row[3], row[4], row[5]
        try:
            year = REIWA_ERA_START_YEAR + int(era_year)
            published_at = f"{year:04d}-{int(month):02d}-{int(day):02d}"
        except (ValueError, TypeError):
            published_at = ""

        url = path if str(path).startswith("http") else "https://www.jma.go.jp" + path
        entries.append({"title": title, "url": url, "published_at": published_at})

    return entries


def normalize_title(title: str) -> str:
    """同じニュースの表記ゆれ（【画像】接頭辞、末尾の発行元名、1/2ページ番号、
    「（2026年7月10日掲載）」のような日付スタンプなど）を取り除き、重複判定用のキーにする"""
    t = title
    t = re.sub(r"^【[^】]*】", "", t)                          # 先頭の【画像】などを除去
    t = re.sub(r"[（(][^）)]*掲載[）)]\s*$", "", t)              # 末尾の「（2026年7月10日掲載）」を除去
    t = re.sub(r"\s*-\s*[^-]+$", "", t)                        # 末尾の " - 発行元名" を除去
    t = re.sub(r"[\s　]*\d+\s*/\s*\d+\s*$", "", t)              # 末尾の "1/2" ページ番号を除去
    t = re.sub(r"[\s　]+", "", t)                               # 空白除去
    return t


def _titles_are_same_story(key_a: str, key_b: str) -> bool:
    """完全一致だけでなく、表記ゆれで少しだけ違う見出しも同じニュースとして扱う"""
    if key_a == key_b:
        return True
    if key_a in key_b or key_b in key_a:
        return True
    return difflib.SequenceMatcher(None, key_a, key_b).ratio() >= 0.85


def dedupe_by_title(results: list[dict]) -> list[dict]:
    """同じニュースが複数のメディア・情報源から重複して拾われた場合、発行元の優先順位
    （publisher_tier、数字が小さいほど優先）をまず基準にし、同ティアなら公開日が新しい
    もの、それも同じならスコアが高いものを残す。他に報じていたメディア名は代表記事の
    "other_sources" に記録し、どれを採用したかをコンソールにも表示する
    （2026-07-29追加。例：同じ茨城のニュースをNHK・地元紙・FM局が報じていた場合、
    NHKや新聞を優先し、FM局の記事名は"other_sources"に残す）"""
    fallback = datetime.min.replace(tzinfo=timezone.utc)
    groups: list[dict] = []  # [{"key": 正規化タイトル, "item": 代表記事, "members": [記事,...]}]

    for item in results:
        key = normalize_title(item["title"])
        match = next((g for g in groups if _titles_are_same_story(key, g["key"])), None)

        if match is None:
            groups.append({"key": key, "item": item, "members": [item]})
            continue

        match["members"].append(item)
        existing = match["item"]

        existing_tier = publisher_tier(existing["title"])
        item_tier = publisher_tier(item["title"])
        existing_dt = parse_published(existing["published_at"]) or fallback
        item_dt = parse_published(item["published_at"]) or fallback

        if item_tier < existing_tier:
            is_better = True
        elif item_tier > existing_tier:
            is_better = False
        elif item_dt > existing_dt:
            is_better = True
        elif item_dt == existing_dt and item["score"] > existing["score"]:
            is_better = True
        else:
            is_better = False

        if is_better:
            match["item"] = item
            match["key"] = key

    final = []
    for g in groups:
        chosen = g["item"]
        if len(g["members"]) > 1:
            other_names = [display_source_name(m) for m in g["members"] if m is not chosen]
            chosen["other_sources"] = "・".join(dict.fromkeys(other_names))  # 順序を保ったまま重複除去
            print(
                f"[重複統合] 「{chosen['title']}」（{display_source_name(chosen)}）を採用"
                f"（他に報じたメディア: {chosen['other_sources']}）"
            )
        else:
            chosen.setdefault("other_sources", "")
        final.append(chosen)

    return final


def collect() -> tuple[list[dict], int, int, int, int, int]:
    """公開対象リストと、鮮度不足／リンク切れ／ペイウォール／除外発行元で除外した件数、
    重複統合で除外した件数を返す"""
    results = []
    seen_urls = set()
    skipped_stale = 0
    skipped_dead_link = 0
    skipped_paywall = 0
    skipped_excluded_publisher = 0

    all_sources = (
        [(s, fetch_rss) for s in RSS_SOURCES]
        + [(s, fetch_html_list) for s in HTML_LIST_SOURCES]
        + [(s, fetch_jma_press_list) for s in JMA_SOURCES]
    )

    for source, fetcher in all_sources:
        try:
            raw_entries = fetcher(source)
        except Exception as exc:
            print(f"[警告] {source['name']} の取得に失敗: {exc}")
            continue

        for entry in raw_entries:
            title, link = entry["title"], entry["url"]
            if link in seen_urls:
                continue
            if is_excluded_publisher(title):
                skipped_excluded_publisher += 1
                continue

            score, matched = score_entry(title)
            if score < min_score_for(source["trust"]):
                continue
            if is_adjacent_false_positive(matched, title):
                continue
            if not is_fresh(entry["published_at"]):
                skipped_stale += 1
                continue
            is_alive, is_paywalled = check_link(link)
            if not is_alive:
                skipped_dead_link += 1
                print(f"[除外] リンク切れの可能性: {title} ({link})")
                continue
            if is_paywalled:
                skipped_paywall += 1
                print(f"[除外] 会員登録が必要な可能性: {title} ({link})")
                continue

            seen_urls.add(link)
            results.append({
                "id": make_id(link),
                "title": title,
                "url": link,
                "source_name": source["name"],
                "source_trust": source["trust"],
                "published_at": entry["published_at"],
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "matched_keywords": matched,
                "score": score,
                "genre": classify_genre(title),
                "status": "published",
            })

    before_dedupe = len(results)
    results = dedupe_by_title(results)
    duplicates_removed = before_dedupe - len(results)

    results = sort_by_published(results)
    return (
        results, skipped_stale, skipped_dead_link, skipped_paywall,
        skipped_excluded_publisher, duplicates_removed,
    )


DECISIONS_FIELDS = ["id", "date_collected", "title", "url", "published_at", "score",
                    "source_trust", "matched_keywords", "source_name", "other_sources",
                    "genre", "decision", "locked"]


def update_decisions_csv(data: list[dict], decisions_path: Path):
    """新しく見つかったIDだけをdecisions.csvに追記する（decision列は空欄のまま）"""
    existing_ids = set()
    rows = []
    if decisions_path.exists():
        with decisions_path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                existing_ids.add(row["id"])
                # 旧バージョン（url/published_at列が無いdecisions.csv）を読み込んだ場合の後方互換
                rows.append({field: row.get(field, "") for field in DECISIONS_FIELDS})

    today = datetime.now().strftime("%Y-%m-%d")
    added = 0
    for item in data:
        if item["id"] in existing_ids:
            continue
        rows.append({
            "id": item["id"],
            "date_collected": today,
            "title": item["title"],
            "url": item["url"],
            "published_at": item["published_at"],
            "score": item["score"],
            "source_trust": item["source_trust"],
            "matched_keywords": "・".join(item["matched_keywords"]),
            "source_name": item["source_name"],
            "other_sources": item.get("other_sources", ""),  # 同じニュースを報じていた他のメディア（重複統合時のみ）
            "genre": item.get("genre", DEFAULT_GENRE),
            "decision": "",  # ここに keep / reject を書き込んでください（review_server.pyから操作しても良い）
            "locked": "",    # review_server.pyで「完了」を押すとdoneになり、一覧から外れる
        })
        added += 1

    with decisions_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=DECISIONS_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    return added


def main():
    (
        data, skipped_stale, skipped_dead_link, skipped_paywall,
        skipped_excluded_publisher, duplicates_removed,
    ) = collect()

    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)

    dated_path = data_dir / f"news_auto_{datetime.now().strftime('%Y%m%d')}.json"
    latest_path = data_dir / "news_auto.json"
    for path in (dated_path, latest_path):
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    added = update_decisions_csv(data, data_dir / "decisions.csv")

    print(
        f"{len(data)} 件を検出"
        f"（鮮度不足で除外: {skipped_stale}件 / リンク切れで除外: {skipped_dead_link}件"
        f" / 会員登録が必要で除外: {skipped_paywall}件"
        f" / 除外対象の発行元: {skipped_excluded_publisher}件"
        f" / 重複統合で除外: {duplicates_removed}件）。"
    )
    print(f"{dated_path.name} / news_auto.json に保存した。")
    print(f"decisions.csv に新規 {added} 件を追記した（decision列にkeep/rejectを記入してください）。")
    for item in data:
        print(f"  [{item['score']}/{item['source_trust']}/{item['genre']}] {item['title']} ({item['source_name']})")


if __name__ == "__main__":
    main()

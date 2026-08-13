"""
coastal-news-data リポジトリ用の news.json 生成スクリプト（news-prototype/generate_site_news.py
のコピーを、このリポジトリの構成に合わせて調整したもの。2026-08-14作成）。

news-prototype版との違い:
    出力先が「このリポジトリのルート直下の data/news.json」になっている点だけが違う
    （scripts/ フォルダの1つ上）。ロジック自体（TRUSTED_KEYWORDSによる絞り込み、
    diversify_by_genre()によるジャンル分散）はnews-prototype版と同じ。

    ローカル（news-prototype）でのキーワード調整結果をこちらに反映する場合は、
    collect_news.py（TRUSTED_KEYWORDS等を含む）をこのリポジトリの scripts/collect_news.py
    に上書きコピーすること。README.md「ローカルでの調整結果を本番へ反映する」も参照。

なぜNetlifyと連携させないこのリポジトリに置くのか:
    以前、Coast_Lab_Homepage本体のリポジトリにnews.jsonを直接コミットしていたところ、
    毎日のコミットのたびにNetlifyの本番デプロイが発生し、クレジット消費が急増した
    （Production deploysが主因と判明）。このリポジトリはNetlifyと一切連携させないため、
    ここへの日次コミットはNetlifyのデプロイを一切発生させない。Coast_Lab_Homepage側は
    ビルド時にこのJSONを埋め込むのではなく、表示時（クライアント側）にこのリポジトリの
    news.jsonをfetchして読み込む（サンプル実装は
    news-prototype/coast_lab_homepage_news_fetch_sample.jsx を参照）。
"""

import json
from pathlib import Path

import collect_news as cn

MAX_ITEMS = 30


def build_site_items(candidates: list[dict]) -> tuple[list[dict], int]:
    trusted = []
    held_back = 0
    for item in candidates:
        if any(kw in cn.TRUSTED_KEYWORDS for kw in item["matched_keywords"]):
            trusted.append(item)
        else:
            held_back += 1

    diversified = cn.diversify_by_genre(trusted)
    return diversified, held_back


def to_site_format(item: dict) -> dict:
    return {
        "id": item["id"],
        "title": item["title"],
        "url": item["url"],
        "source": cn.display_source_name(item),
        "published_at": item["published_at"],
        "genre": item.get("genre", cn.DEFAULT_GENRE),
    }


def main():
    (
        candidates, skipped_stale, skipped_dead_link, skipped_paywall,
        skipped_excluded_publisher, duplicates_removed,
    ) = cn.collect()

    site_items, held_back = build_site_items(candidates)
    site_items = site_items[:MAX_ITEMS]

    # このリポジトリのルート直下の data/news.json に書き出す（scripts/の1つ上）
    out_path = Path(__file__).parent.parent / "data" / "news.json"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(
        json.dumps([to_site_format(i) for i in site_items], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(
        f"{len(candidates)} 件の候補のうち、{len(site_items)} 件を{out_path}に出力した"
        f"（様子見キーワードのみで見送り: {held_back}件 / 鮮度不足: {skipped_stale}件"
        f" / リンク切れ: {skipped_dead_link}件 / 会員登録が必要: {skipped_paywall}件"
        f" / 除外対象の発行元: {skipped_excluded_publisher}件 / 重複統合: {duplicates_removed}件）。"
    )


if __name__ == "__main__":
    main()

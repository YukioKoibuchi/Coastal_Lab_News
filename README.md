# coastal-news-data（テンプレート）

Coast_Lab_Homepageの「全国海岸関係ニュース」欄に表示するnews.jsonを、毎日自動生成・コミットするための**専用リポジトリ**のテンプレート。このフォルダの中身をそのまま新しいGitHubリポジトリにコピーして使う想定。

## なぜ専用リポジトリなのか

以前、Coast_Lab_Homepage本体のリポジトリにnews.jsonを直接コミットしていたところ、毎日のコミットのたびにNetlifyが本番デプロイを実行し、Netlifyのクレジット消費が急増した（使用量ダッシュボードでProduction deploysが主因と確認済み。ビルド時間自体は短いが、デプロイの発生回数自体に課金される仕組みのため、月数回→毎日30回に増えたことが直撃した）。

このリポジトリは**Netlifyと一切連携させない**。ここへの日次コミットはNetlifyから見えないため、デプロイは発生しない。Coast_Lab_Homepage側は、ビルド時にnews.jsonを埋め込むのではなく、ページ表示時（クライアント側のJavaScript）でこのリポジトリのnews.jsonをfetchして読み込む方式に変える（サンプル実装: `news-prototype/coast_lab_homepage_news_fetch_sample.jsx`）。これにより、ニュース更新とNetlifyのデプロイが完全に切り離される。

## セットアップ手順

1. GitHubで新しいリポジトリを作成する（例: `coastal-news-data`）。**Public**にする（raw.githubusercontent.com・jsDelivr経由でホームページ側から読み込むため、認証無しでアクセスできる必要がある）。
2. このフォルダ（`coastal-news-data-repo-template/`）の中身一式を、新しいリポジトリの直下にコピーしてコミット・プッシュする。
3. リポジトリのSettings → Actions → General で、Workflow permissionsが「Read and write permissions」になっていることを確認する（`update-news.yml`側にも`permissions: contents: write`を明記済みだが、リポジトリ全体のデフォルト設定が read-only の場合は書き込みが失敗することがある）。
4. このリポジトリをNetlifyと連携させていないことを確認する（Netlifyのサイト一覧にこのリポジトリが出てこないこと）。
5. `Actions`タブから`Update Coastal News Data`ワークフローを`workflow_dispatch`（手動実行）で一度試し、`data/news.json`が正しく更新されるか確認する。
6. Coast_Lab_Homepage側のニュース欄コンポーネントを、このリポジトリのnews.jsonをfetchする方式に変更する（`coast_lab_homepage_news_fetch_sample.jsx`参照）。

## ローカル（news-prototype）との関係

- `scripts/collect_news.py`・`scripts/generate_site_news.py`は、`news-prototype/`にある同名ファイルのコピー（generate_site_news.pyのみ出力先パスを調整）。
- ローカルでの日々のレビュー（`review_server.py`・`analyze_feedback.py`）で`TRUSTED_KEYWORDS`などのルールを更新したら、更新後の`collect_news.py`をこのリポジトリの`scripts/collect_news.py`に上書きコピーし、コミット・プッシュする。詳しい手順は`news-prototype/README.md`の「ローカルでの調整結果を本番へ反映する」を参照。
- `decisions.csv`（Keep/Rejectの個別履歴）はローカルのチューニング作業専用のデータであり、このリポジトリには含めない。

## 未検証の点

- このテンプレートはnews-prototype側で作成したものであり、実際にGitHubリポジトリとして動かして検証はできていない（このセッションはネットワーク制限のため）。特にGitHub Actionsの`permissions`まわりの挙動は、リポジトリ・Organizationの設定によって変わることがあるので、初回は`workflow_dispatch`で手動実行して動作を確認すること。
- raw.githubusercontent.com / jsDelivr経由のfetchが、実際のCoast_Lab_Homepageのビルド・ホスティング環境（CSP設定等）で問題なく動くかも未確認。

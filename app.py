import streamlit as st
import os
import time
import urllib.parse
import requests
import shutil
import tempfile
from bs4 import BeautifulSoup

# --- 画面のタイトル（変更しました） ---
st.title("PDF一括ダウンローダー")
st.write("指定したURLから、条件に合うPDFをまとめてZIPでダウンロードします。")

# --- ユーザー入力欄 ---
# デフォルト値は福岡市の例を入れています
default_url = "https://www.city.fukuoka.lg.jp/kankyo/sanhai/hp/sangyouhaikibutu/haisyutujigyousya/taryoukouhyou.html"
target_url = st.text_input("対象のURL", default_url)
keyword = st.text_input("ファイル名に含む文字 (空欄ならすべて)", "06")

# --- 実行ボタン ---
if st.button("ダウンロードを開始"):
    # 進捗バーの表示
    progress_bar = st.progress(0)
    status_text = st.empty()

    # 一時フォルダを作成（処理が終わったら自動で消えるようにする）
    with tempfile.TemporaryDirectory() as temp_dir:
        save_dir = os.path.join(temp_dir, "pdfs")
        os.makedirs(save_dir, exist_ok=True)

        status_text.text("サイトの情報を取得中...")

        try:
            # 【重要】ブラウザからのアクセスだと思わせるための「名刺」のようなもの（User-Agent）
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(target_url, headers=headers)
            response.raise_for_status() # エラーがあればここで止まる

            soup = BeautifulSoup(response.content, "html.parser")
            links = soup.find_all("a")

            # ダウンロード対象のリストを作る
            download_targets = []
            for link in links:
                href = link.get("href")
                if href and href.lower().endswith(".pdf"):
                    # 【重要】相対パス（例: ../a.pdf）を絶対パス（http://.../a.pdf）に変換
                    full_url = urllib.parse.urljoin(target_url, href)
                    
                    # ファイル名を取得（URLの最後の部分）
                    # 日本語ファイル名などがURLエンコードされている場合に対応
                    filename = os.path.basename(urllib.parse.urlparse(full_url).path)
                    try:
                        filename = urllib.parse.unquote(filename)
                    except:
                        pass # 変換できなければそのまま
                    
                    # キーワード絞り込み
                    if not keyword or keyword in filename:
                        download_targets.append((filename, full_url))

            # 重複を除去（同じファイルへのリンクが複数ある場合など）
            download_targets = list(set(download_targets))

            if not download_targets:
                status_text.warning(f"「{keyword}」を含むPDFは見つかりませんでした。\n（取得できたリンク数: {len(links)}件）")
                progress_bar.empty()
            else:
                status_text.text(f"{len(download_targets)} 件のPDFが見つかりました。ダウンロード中...")
                
                # ダウンロード実行
                for i, (filename, url) in enumerate(download_targets):
                    try:
                        file_res = requests.get(url, headers=headers)
                        # ファイル名が被らないように工夫しても良いが、今回はシンプルに保存
                        file_path = os.path.join(save_dir, filename)
                        
                        with open(file_path, "wb") as f:
                            f.write(file_res.content)
                        
                        # 進捗バー更新
                        progress_bar.progress((i + 1) / len(download_targets))
                        time.sleep(0.1) # サーバー負荷軽減のため少し待つ
                    except Exception as e:
                        st.write(f"エラー: {filename} の取得に失敗しました ({e})")

                # ZIPに圧縮
                status_text.text("ZIPファイルを作成中...")
                shutil.make_archive(os.path.join(temp_dir, "download_files"), 'zip', save_dir)
                zip_path = os.path.join(temp_dir, "download_files.zip")

                # ダウンロードボタンを表示
                with open(zip_path, "rb") as f:
                    st.download_button(
                        label="📦 ZIPファイルをダウンロード",
                        data=f,
                        file_name="downloaded_pdfs.zip",
                        mime="application/zip"
                    )
                
                status_text.success("処理が完了しました！上のボタンからダウンロードしてください。")

        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

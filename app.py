import streamlit as st
import os
import time
import urllib.parse
import requests
import shutil
import tempfile
from bs4 import BeautifulSoup

# --- 画面のタイトル ---
st.title("福岡市産廃PDF 一括ダウンローダー")
st.write("指定したURLから、条件に合うPDFをまとめてZIPでダウンロードします。")

# --- ユーザー入力欄 ---
target_url = st.text_input("対象のURL", "https://www.city.fukuoka.lg.jp/kankyo/sanhai/hp/sangyouhaikibutu/haisyutujigyousya/taryoukouhyoua.html")
keyword = st.text_input("ファイル名に含む文字（空欄ならすべて）", "06")

# --- 実行ボタン ---
if st.button("ダウンロードを開始"):
    # 進捗バーの表示
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 一時フォルダを作成（処理が終わったら自動で消えるようにする）
    with tempfile.TemporaryDirectory() as temp_dir:
        save_dir = os.path.join(temp_dir, "pdfs")
        os.makedirs(save_dir)
        
        status_text.text("サイトの情報を取得中...")
        
        try:
            response = requests.get(target_url)
            response.encoding = response.apparent_encoding
            soup = BeautifulSoup(response.text, "html.parser")
            
            links = soup.find_all("a")
            pdf_links = [l for l in links if l.get("href") and l.get("href").lower().endswith(".pdf")]
            
            total_links = len(pdf_links)
            count = 0
            
            for i, link in enumerate(pdf_links):
                href = link.get("href")
                pdf_url = urllib.parse.urljoin(target_url, href)
                filename = os.path.basename(pdf_url)
                
                # キーワード判定
                if keyword in filename:
                    status_text.text(f"ダウンロード中: {filename}")
                    
                    try:
                        pdf_data = requests.get(pdf_url)
                        save_path = os.path.join(save_dir, filename)
                        with open(save_path, "wb") as f:
                            f.write(pdf_data.content)
                        count += 1
                        time.sleep(1) # マナーとして待機
                    except Exception as e:
                        st.error(f"エラー: {filename} - {e}")
                
                # 進捗バーの更新
                progress_bar.progress((i + 1) / total_links)

            if count > 0:
                status_text.text("ZIPファイルを作成中...")
                # ZIPファイルの作成
                zip_path = os.path.join(temp_dir, "download_files")
                shutil.make_archive(zip_path, 'zip', root_dir=save_dir)
                
                # ダウンロードボタンの表示
                with open(zip_path + ".zip", "rb") as f:
                    st.download_button(
                        label="📦 ZIPファイルをダウンロード",
                        data=f,
                        file_name="fukuoka_pdfs.zip",
                        mime="application/zip"
                    )
                st.success(f"完了しました！ {count} 個のファイルをまとめました。")
            else:
                st.warning(f"「{keyword}」を含むPDFは見つかりませんでした。")
                
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

import streamlit as st
import re

# 必要なライブラリのインストール指示（コメント）
# 実行方法:
# pip install streamlit pdfplumber
# streamlit run app.py

# --- ページ設定 ---
st.set_page_config(
    page_title="PDF買い物チェックリスト",
    page_icon="🛒",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- カスタムCSS（スマホ表示対応・大フォント・チェック時装飾） ---
st.markdown("""
<style>
    /* 全体フォントサイズ調整 */
    html, body, [class*="css"] {
        font-size: 18px;
    }
    
    /* 大タイトル */
    .main-title {
        font-size: 32px !important;
        font-weight: bold;
        text-align: center;
        margin-bottom: 25px;
        color: #1E3A8A;
    }

    /* スマホ向けボタンの大型化 */
    div.stButton > button {
        font-size: 20px !important;
        padding: 15px 30px !important;
        width: 100%;
        border-radius: 12px !important;
        background-color: #3B82F6 !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
        box-shadow: 0 4px 6px rgba(59, 130, 246, 0.2);
    }
    div.stButton > button:hover {
        background-color: #2563EB !important;
    }

    /* チェックリスト行のスタイル（未チェック） */
    .checklist-row-unchecked {
        background-color: #FFFFFF;
        padding: 16px;
        border-radius: 12px;
        border: 2px solid #E5E7EB;
        margin-bottom: 12px;
        font-size: 20px;
        color: #1F2937;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        display: flex;
        flex-direction: column;
        gap: 4px;
        transition: all 0.2s ease;
    }

    /* チェックリスト行のスタイル（チェック済み：グレー背景＆取り消し線） */
    .checklist-row-checked {
        background-color: #F3F4F6 !important;
        text-decoration: line-through !important;
        color: #9CA3AF !important;
        padding: 16px;
        border-radius: 12px;
        border: 2px solid #E5E7EB;
        margin-bottom: 12px;
        font-size: 20px;
        box-shadow: none;
        display: flex;
        flex-direction: column;
        gap: 4px;
        transition: all 0.2s ease;
    }

    /* バッジ（数量・店舗用） */
    .badge-qty {
        background-color: #DBEAFE;
        color: #1E40AF;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 14px;
        font-weight: bold;
        display: inline-block;
        margin-right: 8px;
    }
    .badge-store {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 14px;
        font-weight: bold;
        display: inline-block;
    }
    .badge-qty-checked {
        background-color: #E5E7EB;
        color: #9CA3AF;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 14px;
        display: inline-block;
        margin-right: 8px;
    }
    .badge-store-checked {
        background-color: #E5E7EB;
        color: #9CA3AF;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 14px;
        display: inline-block;
    }

    /* ストリームリット標準チェックボックスの大型化 */
    [data-testid="stCheckbox"] {
        transform: scale(1.4);
        margin-left: 10px;
        margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)

# --- セッションステートの初期化 ---
if "checklist_items" not in st.session_state:
    st.session_state.checklist_items = []
if "checked_states" not in st.session_state:
    st.session_state.checked_states = {}

# --- タイトル ---
st.markdown('<div class="main-title">🛒 PDF買い物チェックリスト</div>', unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #6B7280; font-size: 16px; margin-bottom: 30px;'>PDFファイルをドラッグ＆ドロップして、商品リストを自動で作成・管理できます。</p>", unsafe_allow_html=True)

# --- PDFデータのパース関数 ---
def extract_data_from_pdf(uploaded_file):
    extracted_items = []
    try:
        import pdfplumber
        with pdfplumber.open(uploaded_file) as pdf:
            text = ""
            # 全ページのテキストを抽出
            for page in pdf.pages:
                text += page.extract_text() or ""
                
                # 表データ（Table）の抽出を試みる
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        # 2列または3列以上のデータを想定してフィルタ
                        non_empty = [cell for cell in row if cell]
                        if len(non_empty) >= 2:
                            # 簡易的なヘッダー行スキップ
                            if any(x in str(non_empty[0]) for x in ["商品", "品名", "数量", "店"]):
                                continue
                            name = str(non_empty[0]).strip()
                            qty = str(non_empty[1]).strip() if len(non_empty) > 1 else "1"
                            store = str(non_empty[2]).strip() if len(non_empty) > 2 else ""
                            extracted_items.append({"name": name, "quantity": qty, "store": store})
            
            # 表がうまく抽出できなかった場合のテキスト正規表現パース
            if not extracted_items and text:
                # 行ごとにパース
                lines = text.split("\n")
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    # 簡易的な「商品名 数量 店舗」のスペース区切りや、個数表記などを検出
                    # 例: "リンゴ 3個 スーパー" や "牛乳 1本"
                    parts = re.split(r'\s+', line)
                    if len(parts) >= 1:
                        name = parts[0]
                        # ヘッダーと思われる単語はスキップ
                        if name in ["商品名", "品名", "商品", "No", "番号", "合計"]:
                            continue
                        
                        qty = "1"
                        store = ""
                        
                        # 残りのパーツから数量や店舗を探す
                        for p in parts[1:]:
                            if re.search(r'\d+(個|つ|本|袋|枚|kg|g|ml|L|p|缶|パック|足)?$', p):
                                qty = p
                            else:
                                store = p
                        
                        extracted_items.append({"name": name, "quantity": qty, "store": store})
                        
    except ImportError:
        # pdfplumberがインストールされていない場合の簡易モックパース (デモやローカル環境配慮)
        st.warning("⚠️ pdfplumberがインストールされていないため、サンプルデータを生成します。 (pip install pdfplumber でPDFの解析が可能になります)")
        extracted_items = [
            {"name": "牛乳", "quantity": "1本", "store": "スーパーA"},
            {"name": "食パン(6枚切)", "quantity": "1袋", "store": "スーパーA"},
            {"name": "たまご(10個入)", "quantity": "1パック", "store": "スーパーA"},
            {"name": "ティッシュペーパー", "quantity": "5箱組", "store": "ドラッグストアB"},
            {"name": "ノート(B5)", "quantity": "3冊", "store": "100円ショップC"},
        ]
    except Exception as e:
        st.error(f"PDFの読み込み中にエラーが発生しました: {e}")
        
    return extracted_items

# --- ファイルアップローダー (ドラッグ＆ドロップ対応) ---
uploaded_file = st.file_uploader(
    "PDFファイル（買い物リストや発注書）をドラッグ＆ドロップ",
    type=["pdf"],
    help="PDFから商品名、数量、店舗を抽出します。"
)

# アップロードされた場合の処理
if uploaded_file is not None:
    # 新しいファイルがアップロードされた場合のみパース
    file_id = f"{uploaded_file.name}_{uploaded_file.size}"
    if st.session_state.get("last_uploaded_file_id") != file_id:
        with st.spinner("PDFから表データを抽出しています..."):
            items = extract_data_from_pdf(uploaded_file)
            if items:
                st.session_state.checklist_items = items
                # チェック状態を初期化
                st.session_state.checked_states = {i: False for i in range(len(items))}
                st.session_state.last_uploaded_file_id = file_id
                st.success(f"🎉 {len(items)}件の商品を抽出しました！")
            else:
                st.warning("PDFから商品データを抽出できませんでした。手動で入力するか、別のPDFでお試しください。")

# リセットボタン
if st.session_state.checklist_items:
    col_reset, col_empty = st.columns([1, 2])
    with col_reset:
        if st.button("リストをクリア"):
            st.session_state.checklist_items = []
            st.session_state.checked_states = {}
            st.session_state.last_uploaded_file_id = None
            st.rerun()

# --- チェックリストの表示 ---
if st.session_state.checklist_items:
    st.markdown("### 📋 買い物チェックリスト")
    st.write("タップして完了にチェックを入れられます。")
    
    # 進行状況のプログレスバー
    total_items = len(st.session_state.checklist_items)
    checked_count = sum(1 for v in st.session_state.checked_states.values() if v)
    progress_val = checked_count / total_items if total_items > 0 else 0.0
    
    st.progress(progress_val)
    st.write(f"進捗率: {checked_count} / {total_items} 件完了 ({int(progress_val*100)}%)")
    st.markdown("---")

    for idx, item in enumerate(st.session_state.checklist_items):
        # チェックボックスと表示行を横並びにする
        col1, col2 = st.columns([1, 8])
        
        with col1:
            # セッションステートとバインドされたチェックボックス
            is_checked = st.checkbox(
                "",
                value=st.session_state.checked_states.get(idx, False),
                key=f"check_{idx}"
            )
            # 状態を保存
            st.session_state.checked_states[idx] = is_checked

        with col2:
            name = item.get("name", "")
            qty = item.get("quantity", "")
            store = item.get("store", "")
            
            # CSSクラスの決定
            row_class = "checklist-row-checked" if is_checked else "checklist-row-unchecked"
            badge_qty_class = "badge-qty-checked" if is_checked else "badge-qty"
            badge_store_class = "badge-store-checked" if is_checked else "badge-store"
            
            # 数量・店舗バッジのHTML
            qty_html = f'<span class="{badge_qty_class}">数量: {qty}</span>' if qty else ""
            store_html = f'<span class="{badge_store_class}">店舗: {store}</span>' if store else ""
            
            # カスタムHTMLの描画
            st.markdown(f"""
            <div class="{row_class}">
                <div style="font-weight: bold; margin-bottom: 6px;">🛒 {name}</div>
                <div>
                    {qty_html}
                    {store_html}
                </div>
            </div>
            """, unsafe_allow_html=True)
else:
    # リストが空の場合のプレースホルダー
    st.info("💡 PDFファイルをドラッグ＆ドロップして読み込ませるか、以下の「デモ用サンプルを読み込む」ボタンをクリックして体験してください。")
    
    if st.button("デモ用サンプルデータを読み込む"):
        demo_items = [
            {"name": "牛乳(低脂肪)", "quantity": "1本", "store": "ライフスーパー"},
            {"name": "レタス", "quantity": "1個", "store": "ライフスーパー"},
            {"name": "鶏もも肉", "quantity": "500g", "store": "ライフスーパー"},
            {"name": "目薬", "quantity": "1箱", "store": "マツモトキヨシ"},
            {"name": "電池(単3)", "quantity": "4本パック", "store": "セリア"},
        ]
        st.session_state.checklist_items = demo_items
        st.session_state.checked_states = {i: False for i in range(len(demo_items))}
        st.rerun()

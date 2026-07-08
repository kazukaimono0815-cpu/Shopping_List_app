import streamlit as st
import re

# 必要なライブラリのインストール指示
# 実行方法:
# pip install streamlit pdfplumber
# streamlit run app.py

# --- ページ設定 ---
st.set_page_config(
    page_title="PDF買い物チェックリスト",
    page_icon="🛒",
    layout="wide", # テーブルを横幅いっぱいに綺麗に表示
    initial_sidebar_state="collapsed"
)

# --- カスタムCSS（スマホ表示対応・コンパクトなテーブル表示・チェック時装飾） ---
st.markdown("""
<style>
    /* 全体フォントサイズ調整 */
    html, body, [class*="css"] {
        font-size: 14px;
    }
    
    /* 大タイトル */
    .main-title {
        font-size: 26px !important;
        font-weight: bold;
        text-align: center;
        margin-bottom: 15px;
        color: #1E3A8A;
    }

    /* ボタンの大型化（スマホ・PC両対応） */
    div.stButton > button {
        font-size: 16px !important;
        padding: 10px 20px !important;
        width: 100%;
        border-radius: 10px !important;
        background-color: #3B82F6 !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
        box-shadow: 0 4px 6px rgba(59, 130, 246, 0.15);
    }
    div.stButton > button:hover {
        background-color: #2563EB !important;
    }

    /* 表（テーブル）全体のコンテナ制限（スクロール低減・1画面収まり用） */
    .table-container {
        max-height: 480px;
        overflow-y: auto;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        background: white;
        padding: 4px;
        margin-bottom: 20px;
    }

    /* 各行のスタイル（未チェック） */
    .row-unchecked {
        background-color: #FFFFFF;
        border-bottom: 1px solid #E5E7EB;
        transition: background-color 0.2s ease;
    }
    .row-unchecked:hover {
        background-color: #F9FAFB;
    }

    /* 各行のスタイル（チェック済み：グレー背景＆取り消し線） */
    .row-checked {
        background-color: #F3F4F6 !important;
        color: #9CA3AF !important;
        border-bottom: 1px solid #E5E7EB;
    }

    /* チェックボックス要素の大型化 */
    [data-testid="stCheckbox"] {
        transform: scale(1.2);
        margin-top: 2px;
    }

    /* テーブル内の商品名ボタンのスタイル調整（テキスト風リンク） */
    .table-container button {
        background-color: transparent !important;
        border: none !important;
        color: #1E3A8A !important;
        font-weight: bold !important;
        font-size: 13px !important;
        text-align: left !important;
        padding: 2px 0px !important;
        box-shadow: none !important;
        width: 100% !important;
        cursor: pointer;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        display: block !important;
    }
    .table-container button:hover {
        color: #3B82F6 !important;
        text-decoration: underline !important;
    }
    
    /* 1行スマホ最適化 */
    [data-testid="column"] {
        padding: 1px 2px !important;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# --- セッションステートの初期化（複数ファイル対応・状態保持） ---
if "documents" not in st.session_state:
    st.session_state.documents = {}
if "revealed_codes" not in st.session_state:
    st.session_state.revealed_codes = {}

# デモ用サンプルデータの定義（1: 購入先、2: 商品コード、3: 商品名、4: 数量）
DEMO_ITEMS = [
    {"store": "ライフ スーパー", "code": "4901301236543", "name": "北海道産 特選牛乳 (1000ml)", "quantity": "1本", "checked": False},
    {"store": "ライフ スーパー", "code": "4901301236544", "name": "完熟バナナ (フィリピン産)", "quantity": "1袋", "checked": False},
    {"store": "ライフ スーパー", "code": "4901301236545", "name": "国産 鶏もも肉 (特大パック)", "quantity": "500g", "checked": False},
    {"store": "マツモトキヨシ", "code": "4987067223502", "name": "鼻炎カプセルS (24カプセル)", "quantity": "1箱", "checked": False},
    {"store": "セリア", "code": "4510019120034", "name": "単3形乾電池 (4本パック)", "quantity": "1つ", "checked": False}
]

# デモデータが未登録なら登録
if "デモ用サンプル" not in st.session_state.documents:
    st.session_state.documents["デモ用サンプル"] = DEMO_ITEMS.copy()

# --- タイトル ---
st.markdown('<div class="main-title">🛒 PDF買い物テーブル・チェックリスト</div>', unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #6B7280; font-size: 14px; margin-bottom: 20px;'>複数PDFを同時に取り込み、元の表フォーマット（1:購入先、2:商品コード、3:商品名、4:数量）を保ったまま消込が行えます。<br>商品名をタップすると商品コードを表示できます。</p>", unsafe_allow_html=True)

# --- PDFデータのパース関数 ---
def extract_table_from_pdf(uploaded_file):
    extracted_items = []
    try:
        import pdfplumber
        with pdfplumber.open(uploaded_file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        # 4列以上のデータ抽出
                        if len(row) >= 2:
                            # ヘッダー行などのスキップ判定
                            if any(x in str(row[0]) for x in ["購入先", "店舗", "店", "No"]):
                                continue
                            
                            store = str(row[0]).strip() if len(row) > 0 and row[0] else ""
                            code = str(row[1]).strip() if len(row) > 1 and row[1] else ""
                            name = str(row[2]).strip() if len(row) > 2 and row[2] else ""
                            qty = str(row[3]).strip() if len(row) > 3 and row[3] else "1"
                            
                            # 商品名が空で、コードだけある場合は補完
                            if not name and code:
                                name = f"商品 {code}"
                                
                            if name or store:
                                extracted_items.append({
                                    "store": store,
                                    "code": code,
                                    "name": name,
                                    "quantity": qty,
                                    "checked": False
                                })
            
            # 表が抽出できなかった場合のテキスト正規表現パース
            if not extracted_items and text:
                lines = text.split("\n")
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    parts = re.split(r'\s+', line)
                    if len(parts) >= 3:
                        store = parts[0]
                        code = parts[1]
                        name = parts[2]
                        qty = parts[3] if len(parts) > 3 else "1"
                        if name in ["商品名", "品名", "商品", "No", "番号", "合計"]:
                            continue
                        extracted_items.append({
                            "store": store,
                            "code": code,
                            "name": name,
                            "quantity": qty,
                            "checked": False
                        })
    except ImportError:
        # フォールバック
        extracted_items = [
            {"store": "スーパーA", "code": "4901234567890", "name": f"【解析サンプル】{uploaded_file.name}の商品A", "quantity": "2個", "checked": False},
            {"store": "ドラッグストアB", "code": "4909876543210", "name": f"【解析サンプル】{uploaded_file.name}の商品B", "quantity": "1袋", "checked": False},
        ]
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
    return extracted_items

# --- 複数ファイルアップローダー ---
uploaded_files = st.file_uploader(
    "PDFファイル（複数アップロード対応）",
    type=["pdf"],
    accept_multiple_files=True,
    help="複数のPDFからそれぞれ独立したチェックリストテーブルを作成します。"
)

# 新しいファイルの取り込み処理
if uploaded_files:
    for f in uploaded_files:
        if f.name not in st.session_state.documents:
            with st.spinner(f"{f.name} を解析中..."):
                parsed_items = extract_table_from_pdf(f)
                if parsed_items:
                    st.session_state.documents[f.name] = parsed_items

# --- ドキュメント別タブ表示 ---
if st.session_state.documents:
    doc_names = list(st.session_state.documents.keys())
    tabs = st.tabs(doc_names)
    
    for i, tab_name in enumerate(doc_names):
        with tabs[i]:
            items = st.session_state.documents[tab_name]
            
            if not items:
                st.info("このファイルのデータは空です。")
                continue
            
            # --- リアルタイム進捗率の計算 ---
            total = len(items)
            checked_count = sum(1 for item in items if item["checked"])
            progress_ratio = checked_count / total if total > 0 else 0.0
            
            # 進捗表示
            col_prog_bar, col_prog_text = st.columns([4, 1])
            with col_prog_bar:
                st.progress(progress_ratio)
            with col_prog_text:
                st.write(f"消込: {checked_count}/{total} ({int(progress_ratio*100)}%)")
            
            # 操作パネル
            col_actions, col_space = st.columns([2, 3])
            with col_actions:
                if st.button(f"全チェック解除 ({tab_name[:10]}...)", key=f"reset_{tab_name}"):
                    for item in items:
                        item["checked"] = False
                    st.rerun()
            
            # --- 表形式表示（1画面に収まるコンパクト設計） ---
            st.markdown('<div class="table-container">', unsafe_allow_html=True)
            
            # テーブルヘッダーの描画（1列目:購入先、2列目:商品名、3列目:数量）
            c_chk, c_store, c_name, c_qty = st.columns([0.8, 2.5, 5.5, 1.2])
            c_chk.markdown("<span style='font-size: 11px; font-weight: bold; color: #4B5563;'>消込</span>", unsafe_allow_html=True)
            c_store.markdown("<span style='font-size: 11px; font-weight: bold; color: #4B5563;'>購入先</span>", unsafe_allow_html=True)
            c_name.markdown("<span style='font-size: 11px; font-weight: bold; color: #4B5563;'>商品名 (タップでコード表示)</span>", unsafe_allow_html=True)
            c_qty.markdown("<span style='font-size: 11px; font-weight: bold; color: #4B5563; display: block; text-align: right;'>数量</span>", unsafe_allow_html=True)
            st.markdown("<hr style='margin: 4px 0; border-color: #E5E7EB;' />", unsafe_allow_html=True)
            
            # 各行の描画
            for idx, item in enumerate(items):
                c_chk, c_store, c_name, c_qty = st.columns([0.8, 2.5, 5.5, 1.2])
                
                # 1. 消込（チェックボックス）
                chk_key = f"chk_{tab_name}_{idx}"
                new_val = c_chk.checkbox("", value=item["checked"], key=chk_key)
                if new_val != item["checked"]:
                    item["checked"] = new_val
                    st.rerun()
                
                # 2. 購入先 (1列目)
                store_val = item.get("store", "") or "-"
                if item["checked"]:
                    c_store.markdown(f'<span style="color: #9CA3AF; text-decoration: line-through; font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block;">{store_val}</span>', unsafe_allow_html=True)
                else:
                    c_store.markdown(f'<span style="color: #4B5563; font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block;">{store_val}</span>', unsafe_allow_html=True)
                
                # 3. 商品名 (2列目) - 未チェック時はタップでコード表示切り替え
                name_val = item["name"]
                code_val = item.get("code", "") or "-"
                is_revealed = st.session_state.revealed_codes.get(f"{tab_name}_{idx}", False)
                if item["checked"]:
                    c_name.markdown(f'<span style="color: #9CA3AF; text-decoration: line-through; font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block;">🛒 {name_val}</span>', unsafe_allow_html=True)
                else:
                    if c_name.button(f"🛒 {name_val}", key=f"btn_name_{tab_name}_{idx}"):
                        st.session_state.revealed_codes[f"{tab_name}_{idx}"] = not is_revealed
                        st.rerun()
                    if is_revealed and code_val and code_val != "-":
                        c_name.markdown(f'<span style="color: #2563EB; font-weight: bold; font-family: monospace; font-size: 11px; background-color: #EFF6FF; padding: 1px 4px; border-radius: 4px; display: inline-block; margin-top: 2px;">コード: {code_val}</span>', unsafe_allow_html=True)
                
                # 4. 数量 (3列目)
                qty_val = item["quantity"]
                if item["checked"]:
                    c_qty.markdown(f'<span style="color: #9CA3AF; text-decoration: line-through; font-size: 12px; display: block; text-align: right; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{qty_val}</span>', unsafe_allow_html=True)
                else:
                    c_qty.markdown(f'<span style="color: #1F2937; font-weight: bold; font-size: 12px; display: block; text-align: right; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{qty_val}</span>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

            # 手動追加機能（誤消去防止のため個別削除ボタンは除去）
            with st.expander("➕ 商品をテーブルに手動追加"):
                col_add_s, col_add_c, col_add_n, col_add_q = st.columns([2, 2.5, 4, 1.5])
                add_store = col_add_s.text_input("購入先（1列目）", key=f"add_s_{tab_name}")
                add_code = col_add_c.text_input("商品コード（2列目）", key=f"add_c_{tab_name}")
                add_name = col_add_n.text_input("商品名（3列目）", key=f"add_n_{tab_name}")
                add_qty = col_add_q.text_input("数量（4列目）", key=f"add_q_{tab_name}", value="1")
                
                if st.button("テーブルに追加する", key=f"btn_add_{tab_name}"):
                    if add_name or add_store:
                        st.session_state.documents[tab_name].append({
                            "store": add_store,
                            "code": add_code,
                            "name": add_name,
                            "quantity": add_qty,
                            "checked": False
                        })
                        st.success(f"「{add_name or add_store}」を追加しました！")
                        st.rerun()

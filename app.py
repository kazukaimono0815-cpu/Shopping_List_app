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
        background-color: #0F172A;
        color: #F1F5F9;
    }
    
    /* 大タイトル */
    .main-title {
        font-size: 26px !important;
        font-weight: bold;
        text-align: center;
        margin-bottom: 15px;
        color: #3B82F6;
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
        border: 1px solid #334155;
        border-radius: 12px;
        background: #0F172A;
        padding: 8px;
        margin-bottom: 20px;
    }

    /* チェックボックス要素の大型化 */
    [data-testid="stCheckbox"] {
        transform: scale(1.3);
        margin-top: 2px;
    }

    /* テーブル内の商品名ボタンのスタイル調整（テキスト風リンク） */
    .table-container button {
        background-color: transparent !important;
        border: none !important;
        color: #F1F5F9 !important;
        font-weight: bold !important;
        font-size: 14px !important;
        text-align: left !important;
        padding: 2px 0px !important;
        box-shadow: none !important;
        width: 100% !important;
        cursor: pointer;
        white-space: normal !important;
        display: block !important;
    }
    .table-container button:hover {
        color: #60A5FA !important;
        text-decoration: underline !important;
    }
    
    /* 1行スマホ最適化 */
    [data-testid="column"] {
        padding: 2px 4px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- セッションステートの初期化（複数ファイル対応・状態保持） ---
if "documents" not in st.session_state:
    st.session_state.documents = {}
if "revealed_codes" not in st.session_state:
    st.session_state.revealed_codes = {}

# デモ用サンプルデータの定義
DEMO_ITEMS = [
    {"store": "ライフ スーパー", "code": "4901301236543", "name": "北海道産 特選牛乳 (1000ml)", "quantity": "1本", "checked": False},
    {"store": "ライフ スーパー", "code": "4901301236544", "name": "完熟バナナ (フィリピン産)", "quantity": "1袋", "checked": False},
    {"store": "ライフ スーパー", "code": "4901301236545", "name": "国産 鶏もも肉 (特大パック)", "quantity": "500g", "checked": False},
    {"store": "", "code": "", "name": "---EMPTY_ROW---", "quantity": "", "checked": False},
    {"store": "マツモトキヨシ", "code": "4987067223502", "name": "鼻炎カプセルS (24カプセル)", "quantity": "1箱", "checked": False},
    {"store": "マツモトキヨシ", "code": "4901301324221", "name": "BOXティッシュ (5箱パック)", "quantity": "1袋", "checked": False},
    {"store": "", "code": "", "name": "---EMPTY_ROW---", "quantity": "", "checked": False},
    {"store": "セリア", "code": "4510019120034", "name": "単3形乾電池 (4本パック)", "quantity": "1つ", "checked": False}
]

# デモデータが未登録なら登録
if "デモ用サンプル" not in st.session_state.documents:
    st.session_state.documents["デモ用サンプル"] = DEMO_ITEMS.copy()

# --- タイトル ---
st.markdown('<div class="main-title">🛒 PDF買い物テーブル・チェックリスト</div>', unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94A3B8; font-size: 14px; margin-bottom: 20px;'>複数PDFから空白行ごとの店舗ブロックに分けて表示します。<br>商品名をタップすると商品コードが表示され、チェックで消込が行えます。</p>", unsafe_allow_html=True)

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
                        if len(row) >= 2:
                            if any(x in str(row[0]) for x in ["購入先", "店舗", "店", "No"]):
                                continue
                            
                            store = str(row[0]).strip() if len(row) > 0 and row[0] else ""
                            code = str(row[1]).strip() if len(row) > 1 and row[1] else ""
                            name = str(row[2]).strip() if len(row) > 2 and row[2] else ""
                            qty = str(row[3]).strip() if len(row) > 3 and row[3] else "1"
                            
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
            
            # フォールバック テキストパース
            if not extracted_items and text:
                lines = text.split("\n")
                for line in lines:
                    line = line.strip()
                    if not line:
                        extracted_items.append({
                            "store": "",
                            "code": "",
                            "name": "---EMPTY_ROW---",
                            "quantity": "",
                            "checked": False
                        })
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
    except Exception as e:
        st.error(f"エラー: {e}")
    return extracted_items

# --- 複数ファイルアップローダー ---
uploaded_files = st.file_uploader(
    "PDFファイル（複数アップロード対応）",
    type=["pdf"],
    accept_multiple_files=True
)

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
                st.info("データが空です。")
                continue
            
            # 空白行によるブロック化
            blocks = []
            current_block_items = []
            for item in items:
                is_empty_row = (
                    item.get("name") == "---EMPTY_ROW---" or
                    (not item.get("name") and not item.get("store") and not item.get("code") and not item.get("quantity"))
                )
                if is_empty_row:
                    if current_block_items:
                        first_store = current_block_items[0].get("store") or "その他"
                        blocks.append({
                            "title": first_store,
                            "items": current_block_items
                        })
                        current_block_items = []
                else:
                    current_block_items.append(item)
            
            if current_block_items:
                first_store = current_block_items[0].get("store") or "その他"
                blocks.append({
                    "title": first_store,
                    "items": current_block_items
                })
            
            if not blocks:
                blocks = [{"title": "その他", "items": []}]

            # 全体進捗の計算 (空行マーカー除外)
            valid_items = [item for item in items if item.get("name") != "---EMPTY_ROW---"]
            total = len(valid_items)
            checked_count = sum(1 for item in valid_items if item["checked"])
            progress_ratio = checked_count / total if total > 0 else 0.0
            
            st.write(f"📊 **全体の進捗率: {checked_count}/{total} 件 ({int(progress_ratio*100)}%)**")
            st.progress(progress_ratio)
            
            # 操作パネル
            if st.button("全チェックを解除する", key=f"reset_{tab_name}"):
                for item in items:
                    item["checked"] = False
                st.rerun()
                
            # ブロック(店舗)タブ
            block_tabs = st.tabs([f"🛒 {b['title']}" for b in blocks])
            for b_idx, block_tab in enumerate(block_tabs):
                with block_tab:
                    b_items = blocks[b_idx]["items"]
                    
                    st.markdown('<div class="table-container">', unsafe_allow_html=True)
                    
                    # テーブルヘッダー
                    c_chk, c_name, c_qty = st.columns([1, 7, 2])
                    c_chk.markdown("<span style='font-size: 11px; font-weight: bold; color: #94A3B8;'>消込</span>", unsafe_allow_html=True)
                    c_name.markdown("<span style='font-size: 11px; font-weight: bold; color: #94A3B8;'>商品名 (タップでコード)</span>", unsafe_allow_html=True)
                    c_qty.markdown("<span style='font-size: 11px; font-weight: bold; color: #94A3B8; display: block; text-align: right;'>数量</span>", unsafe_allow_html=True)
                    st.markdown("<hr style='margin: 4px 0; border-color: #334155;' />", unsafe_allow_html=True)
                    
                    # 未チェックを上にしてループ表示
                    sorted_b_items = sorted(b_items, key=lambda x: x["checked"])
                    for idx, item in enumerate(sorted_b_items):
                        c_chk, c_name, c_qty = st.columns([1, 7, 2])
                        
                        # 1. チェックボックス
                        global_idx = items.index(item)
                        chk_key = f"chk_{tab_name}_{b_idx}_{global_idx}"
                        new_val = c_chk.checkbox("", value=item["checked"], key=chk_key)
                        if new_val != item["checked"]:
                            item["checked"] = new_val
                            st.rerun()
                        
                        # 2. 商品名とコード
                        name_val = item["name"]
                        code_val = item.get("code") or ""
                        is_revealed = st.session_state.revealed_codes.get(f"{tab_name}_{global_idx}", False)
                        
                        if item["checked"]:
                            c_name.markdown(f'<span style="color: #64748B; text-decoration: line-through; font-size: 13px; display: block; padding-top: 4px;">🛒 {name_val}</span>', unsafe_allow_html=True)
                        else:
                            if c_name.button(f"🛒 {name_val}", key=f"btn_name_{tab_name}_{b_idx}_{global_idx}"):
                                st.session_state.revealed_codes[f"{tab_name}_{global_idx}"] = not is_revealed
                                st.rerun()
                            
                            if is_revealed and code_val:
                                c_name.markdown(f'<span style="color: #60A5FA; font-weight: bold; font-family: monospace; font-size: 11px; background-color: #1E293B; padding: 2px 6px; border-radius: 4px; margin-left: 24px; display: inline-block;">コード: {code_val}</span>', unsafe_allow_html=True)
                        
                        # 3. 数量
                        qty_val = item["quantity"]
                        if item["checked"]:
                            c_qty.markdown(f'<span style="color: #64748B; text-decoration: line-through; font-size: 13px; display: block; text-align: right; padding-top: 4px;">{qty_val}</span>', unsafe_allow_html=True)
                        else:
                            c_qty.markdown(f'<div style="text-align: right; padding-top: 2px;"><span style="color: #F59E0B; background-color: #78350F; padding: 3px 10px; border-radius: 8px; font-weight: 800; font-size: 12px; border: 1px solid #B45309;">{qty_val}</span></div>', unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)

            # 手動追加
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
                        st.success(f"追加しました！")
                        st.rerun()

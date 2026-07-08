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
        font-size: 16px;
    }
    
    /* 大タイトル */
    .main-title {
        font-size: 28px !important;
        font-weight: bold;
        text-align: center;
        margin-bottom: 15px;
        color: #1E3A8A;
    }

    /* ボタンの大型化（スマホ・PC両対応） */
    div.stButton > button {
        font-size: 18px !important;
        padding: 12px 24px !important;
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
        max-height: 450px;
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
        transform: scale(1.3);
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# --- セッションステートの初期化（複数ファイル対応・状態保持） ---
if "documents" not in st.session_state:
    st.session_state.documents = {}

# デモ用サンプルデータの定義
DEMO_ITEMS = [
    {"name": "北海道産 特選牛乳 (1000ml)", "quantity": "1本", "store": "ライフ スーパー", "checked": False},
    {"name": "完熟バナナ (フィリピン産)", "quantity": "1袋", "store": "ライフ スーパー", "checked": False},
    {"name": "国産 鶏もも肉 (特大パック)", "quantity": "500g", "store": "ライフ スーパー", "checked": False},
    {"name": "鼻炎カプセルS (24カプセル)", "quantity": "1箱", "store": "マツモトキヨシ", "checked": False},
    {"name": "単3形乾電池 (4本パック)", "quantity": "1つ", "store": "セリア", "checked": False}
]

# デモデータが未登録なら登録
if "デモ用サンプル" not in st.session_state.documents:
    st.session_state.documents["デモ用サンプル"] = DEMO_ITEMS.copy()

# --- タイトル ---
st.markdown('<div class="main-title">🛒 PDF買い物テーブル・チェックリスト</div>', unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #6B7280; font-size: 15px; margin-bottom: 20px;'>複数PDFを同時に取り込み、元の表フォーマットを保ったまま快適に消込（チェック）が行えます。</p>", unsafe_allow_html=True)

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
                        non_empty = [cell for cell in row if cell]
                        if len(non_empty) >= 2:
                            if any(x in str(non_empty[0]) for x in ["商品", "品名", "数量", "店", "No"]):
                                continue
                            name = str(non_empty[0]).strip()
                            qty = str(non_empty[1]).strip() if len(non_empty) > 1 else "1"
                            store = str(non_empty[2]).strip() if len(non_empty) > 2 else ""
                            extracted_items.append({
                                "name": name,
                                "quantity": qty,
                                "store": store,
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
                    if len(parts) >= 1:
                        name = parts[0]
                        if name in ["商品名", "品名", "商品", "No", "番号", "合計"]:
                            continue
                        qty = "1"
                        store = ""
                        for p in parts[1:]:
                            if re.search(r'\d+(個|つ|本|袋|枚|kg|g|ml|L|p|缶|パック|足)?$', p):
                                qty = p
                            else:
                                store = p
                        extracted_items.append({
                            "name": name,
                            "quantity": qty,
                            "store": store,
                            "checked": False
                        })
    except ImportError:
        # フォールバック
        extracted_items = [
            {"name": f"【解析サンプル】{uploaded_file.name}の商品A", "quantity": "2個", "store": "スーパーA", "checked": False},
            {"name": f"【解析サンプル】{uploaded_file.name}の商品B", "quantity": "1袋", "store": "ドラッグストアB", "checked": False},
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
                st.write(f"消込完了: {checked_count}/{total} ({int(progress_ratio*100)}%)")
            
            # 操作パネル
            col_actions, col_space = st.columns([2, 3])
            with col_actions:
                if st.button(f"全チェック解除 ({tab_name[:10]}...)", key=f"reset_{tab_name}"):
                    for item in items:
                        item["checked"] = False
                    st.rerun()
            
            # --- 表形式表示（1画面に収まるコンパクト設計） ---
            st.markdown('<div class="table-container">', unsafe_allow_html=True)
            
            # テーブルヘッダーの描画
            col_chk, col_name, col_qty, col_store, col_del = st.columns([1, 4, 2, 2, 1])
            col_chk.markdown("**消込**")
            col_name.markdown("**商品名**")
            col_qty.markdown("**数量**")
            col_store.markdown("**店舗/備考**")
            col_del.markdown("**操作**")
            st.markdown("<hr style='margin: 4px 0;' />", unsafe_allow_html=True)
            
            # 各行の描画
            # コピーを作ってイテレートするかインデックス管理
            # Pythonのリストpop時のインデックス破綻を防ぐためにenumerateしたキーに対して操作
            to_delete = None
            for idx, item in enumerate(items):
                # StreamlitのColumnsを使ってインタラクティブかつ綺麗に配置
                c_chk, c_name, c_qty, c_store, c_del = st.columns([1, 4, 2, 2, 1])
                
                # 1. 消込（チェックボックス）
                chk_key = f"chk_{tab_name}_{idx}"
                new_val = c_chk.checkbox("", value=item["checked"], key=chk_key)
                if new_val != item["checked"]:
                    item["checked"] = new_val
                    st.rerun()
                
                # 2. 商品名・数量・店舗（消込時は打消し線）
                if item["checked"]:
                    c_name.markdown(f'<span style="color: #9CA3AF; text-decoration: line-through; font-size: 18px;">🛒 {item["name"]}</span>', unsafe_allow_html=True)
                    c_qty.markdown(f'<span style="color: #9CA3AF; text-decoration: line-through;">{item["quantity"]}</span>', unsafe_allow_html=True)
                    c_store.markdown(f'<span style="color: #9CA3AF; text-decoration: line-through;">{item["store"]}</span>', unsafe_allow_html=True)
                else:
                    c_name.markdown(f'<span style="font-weight: bold; font-size: 18px; color: #1F2937;">🛒 {item["name"]}</span>', unsafe_allow_html=True)
                    c_qty.markdown(f'<span style="color: #4B5563; font-weight: 500;">{item["quantity"]}</span>', unsafe_allow_html=True)
                    c_store.markdown(f'<span style="color: #4B5563;">{item["store"]}</span>', unsafe_allow_html=True)
                
                # 5. 個別削除ボタン
                if c_del.button("❌", key=f"del_{tab_name}_{idx}"):
                    to_delete = idx
            
            if to_delete is not None:
                items.pop(to_delete)
                st.session_state.documents[tab_name] = items
                st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)

            # 手動追加機能
            with st.expander("➕ 商品をテーブルに手動追加"):
                col_add_n, col_add_q, col_add_s = st.columns([4, 2, 2])
                add_name = col_add_n.text_input("商品名", key=f"add_n_{tab_name}")
                add_qty = col_add_q.text_input("数量", key=f"add_q_{tab_name}", value="1")
                add_store = col_add_s.text_input("店舗/備考", key=f"add_s_{tab_name}")
                
                if st.button("テーブルに追加する", key=f"btn_add_{tab_name}"):
                    if add_name:
                        st.session_state.documents[tab_name].append({
                            "name": add_name,
                            "quantity": add_qty,
                            "store": add_store,
                            "checked": False
                        })
                        st.success(f"「{add_name}」を追加しました！")
                        st.rerun()

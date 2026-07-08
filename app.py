# -*- coding: utf-8 -*-
import streamlit as st
import re

# --- Page Config ---
st.set_page_config(
    page_title="PDF買い物チェックリスト",
    page_icon="clipboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS for mobile compatibility and compact table styling ---
st.markdown("""
<style>
    /* Overall font size adjustment */
    html, body, [class*="css"] {
        font-size: 14px;
        background-color: #0F172A;
        color: #F1F5F9;
    }
    
    /* Main title */
    .main-title {
        font-size: 26px !important;
        font-weight: bold;
        text-align: center;
        margin-bottom: 15px;
        color: #3B82F6;
    }

    /* Button enlargement for mobile and PC */
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

    /* Table container constraints */
    .table-container {
        max-height: 480px;
        overflow-y: auto;
        border: 1px solid #334155;
        border-radius: 12px;
        background: #0F172A;
        padding: 8px;
        margin-bottom: 20px;
    }

    /* Checkbox enlargement */
    [data-testid="stCheckbox"] {
        transform: scale(1.3);
        margin-top: 2px;
    }

    /* Button link style for item names */
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
    
    /* Mobile column optimization */
    [data-testid="column"] {
        padding: 2px 4px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Initialize session state ---
if "documents" not in st.session_state:
    st.session_state.documents = {}
if "revealed_codes" not in st.session_state:
    st.session_state.revealed_codes = {}

# Demo items definition
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

# Register demo items if not present
if "デモ用サンプル" not in st.session_state.documents:
    st.session_state.documents["デモ用サンプル"] = DEMO_ITEMS.copy()

# --- Main Title ---
st.markdown('<div class="main-title">PDF買い物テーブル・チェックリスト</div>', unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94A3B8; font-size: 14px; margin-bottom: 20px;'>複数PDFから空白行ごとの店舗ブロックに分けて表示します。<br>商品名をタップすると商品コードが表示され、チェックで消込が行えます。</p>", unsafe_allow_html=True)

# --- PDF Parsing Function ---
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
                            
                            # Detect empty row
                            if not name and not store and not code:
                                extracted_items.append({
                                    "store": "",
                                    "code": "",
                                    "name": "---EMPTY_ROW---",
                                    "quantity": "",
                                    "checked": False
                                })
                                continue
                            
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
            
            # Fallback text parser
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

# --- Multiple File Uploader ---
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

# --- Document Tabs Display ---
if st.session_state.documents:
    doc_names = list(st.session_state.documents.keys())
    tabs = st.tabs(doc_names)
    
    for i, tab_name in enumerate(doc_names):
        with tabs[i]:
            items = st.session_state.documents[tab_name]
            
            if not items:
                st.info("データが空です。")
                continue
            
            # Grouping by empty rows or store changes
            blocks = []
            current_block_items = []
            last_store = ""
            for item in items:
                is_empty_row = (
                    item.get("name") == "---EMPTY_ROW---" or
                    (not item.get("name") and not item.get("store") and not item.get("code") and not item.get("quantity"))
                )
                
                item_store = item.get("store", "")
                is_store_change = item_store and last_store and item_store != last_store
                
                if is_empty_row or is_store_change:
                    if current_block_items:
                        first_store = current_block_items[0].get("store") or "その他"
                        blocks.append({
                            "title": first_store,
                            "items": current_block_items
                        })
                        current_block_items = []
                
                if not is_empty_row:
                    current_block_items.append(item)
                    if item_store:
                        last_store = item_store
            
            if current_block_items:
                first_store = current_block_items[0].get("store") or "その他"
                blocks.append({
                    "title": first_store,
                    "items": current_block_items
                })
            
            if not blocks:
                blocks = [{"title": "その他", "items": []}]

            # Progress calculation
            valid_items = [item for item in items if item.get("name") != "---EMPTY_ROW---"]
            total = len(valid_items)
            checked_count = sum(1 for item in valid_items if item["checked"])
            progress_ratio = checked_count / total if total > 0 else 0.0
            
            st.write(f"全体の進捗率: {checked_count}/{total} 件 ({int(progress_ratio*100)}%)")
            st.progress(progress_ratio)
            
            # Operation panel
            if st.button("全チェックを解除する", key=f"reset_{tab_name}"):
                for item in items:
                    item["checked"] = False
                st.rerun()
                
            # --- Block Selection UI (Column and Card style instead of tabs) ---
            block_key = f"active_block_{tab_name}"
            if block_key not in st.session_state:
                st.session_state[block_key] = 0
                
            active_b_idx = st.session_state[block_key]
            if active_b_idx >= len(blocks):
                active_b_idx = 0
                st.session_state[block_key] = 0

            st.markdown("<p style='font-size: 11px; font-weight: bold; color: #94A3B8; margin-top: 15px; margin-bottom: 5px;'>店舗・グループ（空白行で区切られたブロック）</p>", unsafe_allow_html=True)
            
            # Render indicators
            cols = st.columns(max(len(blocks), 1))
            for b_idx, block in enumerate(blocks):
                is_active = (b_idx == active_b_idx)
                unchecked_count = sum(1 for item in block["items"] if not item["checked"])
                
                # Select indicator text depending on store name
                icon_char = "[店]"
                title_lower = block["title"].lower()
                if any(x in title_lower for x in ["マツモト", "ドラッグ", "薬", "ココカラ"]):
                    icon_char = "[薬]"
                elif any(x in title_lower for x in ["セリア", "ダイソー", "100", "キャンドゥ"]):
                    icon_char = "[雑]"
                elif any(x in title_lower for x in ["ライフ", "スーパー", "イオン", "業務"]):
                    icon_char = "[食]"
                
                badge_str = f"未:{unchecked_count}" if unchecked_count > 0 else "済"
                button_label = f"{icon_char} {block['title']}\n({badge_str})"
                
                with cols[b_idx]:
                    # Custom CSS border for active selection
                    border_style = "border: 2px solid #3B82F6; background-color: rgba(59, 130, 246, 0.15);" if is_active else "border: 1px solid #334155; background-color: #0F172A;"
                    st.markdown(f"<div style='{border_style} border-radius: 12px; padding: 4px; text-align: center; margin-bottom: 10px;'>", unsafe_allow_html=True)
                    if st.button(button_label, key=f"block_btn_{tab_name}_{b_idx}"):
                        st.session_state[block_key] = b_idx
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

            # Render item list for active block
            active_block = blocks[active_b_idx]
            b_items = active_block["items"]
            
            st.markdown('<div class="table-container">', unsafe_allow_html=True)
            
            # Table header
            c_chk, c_name, c_qty = st.columns([1, 7, 2])
            c_chk.markdown("<span style='font-size: 11px; font-weight: bold; color: #94A3B8;'>消込</span>", unsafe_allow_html=True)
            c_name.markdown("<span style='font-size: 11px; font-weight: bold; color: #94A3B8;'>商品名 (タップでコード)</span>", unsafe_allow_html=True)
            c_qty.markdown("<span style='font-size: 11px; font-weight: bold; color: #94A3B8; display: block; text-align: right;'>数量</span>", unsafe_allow_html=True)
            st.markdown("<hr style='margin: 4px 0; border-color: #334155;' />", unsafe_allow_html=True)
            
            # Loop with unchecked items first
            sorted_b_items = sorted(b_items, key=lambda x: x["checked"])
            for idx, item in enumerate(sorted_b_items):
                c_chk, c_name, c_qty = st.columns([1, 7, 2])
                
                # 1. Checkbox
                global_idx = items.index(item)
                chk_key = f"chk_{tab_name}_{active_b_idx}_{global_idx}"
                new_val = c_chk.checkbox("", value=item["checked"], key=chk_key)
                if new_val != item["checked"]:
                    item["checked"] = new_val
                    st.rerun()
                
                # 2. Item name and code
                name_val = item["name"]
                code_val = item.get("code") or ""
                is_revealed = st.session_state.revealed_codes.get(f"{tab_name}_{global_idx}", False)
                
                if item["checked"]:
                    c_name.markdown(f'<span style="color: #64748B; text-decoration: line-through; font-size: 13px; display: block; padding-top: 4px;"> {name_val}</span>', unsafe_allow_html=True)
                else:
                    if c_name.button(f" {name_val}", key=f"btn_name_{tab_name}_{active_b_idx}_{global_idx}"):
                        st.session_state.revealed_codes[f"{tab_name}_{global_idx}"] = not is_revealed
                        st.rerun()
                    
                    if is_revealed and code_val:
                        c_name.markdown(f'<span style="color: #60A5FA; font-weight: bold; font-family: monospace; font-size: 11px; background-color: #1E293B; padding: 2px 6px; border-radius: 4px; margin-left: 24px; display: inline-block;">コード: {code_val}</span>', unsafe_allow_html=True)
                
                # 3. Quantity
                qty_val = item["quantity"]
                if item["checked"]:
                    c_qty.markdown(f'<span style="color: #64748B; text-decoration: line-through; font-size: 13px; display: block; text-align: right; padding-top: 4px;">{qty_val}</span>', unsafe_allow_html=True)
                else:
                    c_qty.markdown(f'<div style="text-align: right; padding-top: 2px;"><span style="color: #F59E0B; background-color: #78350F; padding: 3px 10px; border-radius: 8px; font-weight: 800; font-size: 12px; border: 1px solid #B45309;">{qty_val}</span></div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

            # Manual Addition Form
            with st.expander("商品をテーブルに手動追加"):
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

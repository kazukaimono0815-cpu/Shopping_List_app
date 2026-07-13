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
        font-size: 24px !important;
        font-weight: bold;
        text-align: center;
        margin-bottom: 10px;
        color: #3B82F6;
    }

    /* Expander / Accordion Styling */
    .streamlit-expanderHeader {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        padding: 10px !important;
    }
    
    /* Checkbox layout helper */
    [data-testid="stCheckbox"] {
        transform: scale(1.2);
        margin-top: 2px;
    }

    /* Table Container inside expander */
    .table-container {
        border: 1px solid #334155;
        border-radius: 12px;
        background: #0F172A;
        padding: 12px;
        margin-bottom: 12px;
    }

    /* Styled Badges */
    .qty-badge {
        color: #F59E0B;
        background-color: #78350F;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 800;
        font-size: 11px;
        border: 1px solid #B45309;
        display: inline-block;
    }
    .qty-badge-checked {
        color: #64748B;
        background-color: #1E293B;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 500;
        font-size: 11px;
        border: 1px solid #334155;
        text-decoration: line-through;
        display: inline-block;
    }
    .store-badge {
        background-color: rgba(59, 130, 246, 0.15);
        border: 1px solid rgba(59, 130, 246, 0.3);
        color: #60A5FA;
        font-weight: bold;
        font-size: 10px;
        border-radius: 4px;
        padding: 2px 6px;
        display: inline-block;
    }
    .code-badge {
        color: #60A5FA;
        font-weight: bold;
        font-family: monospace;
        font-size: 11px;
        background-color: #1E293B;
        padding: 2px 6px;
        border-radius: 4px;
        display: inline-block;
        border: 1px solid #334155;
    }
</style>
""", unsafe_allow_html=True)

# --- Initialize session state ---
if "documents" not in st.session_state:
    st.session_state.documents = {}
if "revealed_codes" not in st.session_state:
    st.session_state.revealed_codes = {}

# --- Main Title ---
st.markdown('<div class="main-title">PDF買い物テーブル・チェックリスト</div>', unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94A3B8; font-size: 13px; margin-bottom: 15px;'>複数PDFに対応したスマホ最適化チェックリストです。<br>商品名をタップすると商品コードが表示され、チェックボックスで消込を行えます。</p>", unsafe_allow_html=True)

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
    "PDFファイル（複数アップロード・表消込対応）",
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

# --- No Document Fallback ---
if not st.session_state.documents:
    st.info("💡 PDFファイルをアップロードするか、下のボタンから空の買い物リストを作成してください。")
    if st.button("➕ 新しい空の買い物リストを作成する"):
        st.session_state.documents["新規買い物リスト.pdf"] = []
        st.rerun()

# --- Document Tabs Display ---
if st.session_state.documents:
    doc_names = list(st.session_state.documents.keys())
    
    # Simple active document selection (tabs or selectbox)
    if len(doc_names) > 1:
        active_doc_name = st.selectbox("表示するリストを選択", doc_names)
    else:
        active_doc_name = doc_names[0]
        
    st.subheader(f"📄 {active_doc_name}")
    
    # Remove file button
    if st.button("🗑️ このリストを削除する", key=f"del_doc_{active_doc_name}"):
        del st.session_state.documents[active_doc_name]
        st.rerun()

    items = st.session_state.documents.get(active_doc_name, [])
    
    if not items and items != []:
        st.info("データがありません。")
    else:
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
        col_ctrl1, col_ctrl2 = st.columns([2, 2])
        with col_ctrl1:
            if st.button("🔄 全消込を解除する", key=f"reset_{active_doc_name}"):
                for item in items:
                    item["checked"] = False
                st.rerun()
        
        # --- View Mode Selector ---
        view_mode = st.radio(
            "表示モードを選択",
            ["🏪 店舗別アコーディオン", "📊 購入状態別一括表示"],
            horizontal=True,
            key=f"view_mode_{active_doc_name}"
        )

        if "🏪 店舗別アコーディオン" in view_mode:
            # ==================== 🏪 店舗別アコーディオン ====================
            st.write("👉 グループをタップすると、すぐ下に商品リストが表示されます。")
            
            for b_idx, block in enumerate(blocks):
                block_title = block["title"]
                b_items = block["items"]
                
                # Filter out empty rows from count
                actual_items = [it for it in b_items if it.get("name") != "---EMPTY_ROW---"]
                unchecked_in_block = sum(1 for it in actual_items if not it["checked"])
                total_in_block = len(actual_items)
                
                # Choose indicator icon depending on store name
                icon_char = "🏪"
                title_lower = block_title.lower()
                if any(x in title_lower for x in ["マツモト", "ドラッグ", "薬", "ココカラ"]):
                    icon_char = "💊"
                elif any(x in title_lower for x in ["セリア", "ダイソー", "100", "キャンドゥ"]):
                    icon_char = "🧸"
                elif any(x in title_lower for x in ["ライフ", "スーパー", "イオン", "業務"]):
                    icon_char = "🥬"
                
                badge_str = f"残り: {unchecked_in_block}件" if unchecked_in_block > 0 else "✅ 完了！"
                expander_label = f"{icon_char} {block_title} ({badge_str} / 合計: {total_in_block}件)"
                
                # Using st.expander as Accordion: "グループをタップしたらすぐ下に商品が表示される"
                # By default, expand the first block, and specify a unique key to persist open/closed state on rerun
                is_first = (b_idx == 0)
                expander_key = f"exp_{active_doc_name}_{block_title}_{b_idx}"
                with st.expander(expander_label, expanded=is_first, key=expander_key):
                    if not b_items:
                        st.info("この店舗に登録されている商品はありません。")
                    else:
                        st.markdown('<div class="table-container">', unsafe_allow_html=True)
                        
                        # Sorted items (unchecked first)
                        sorted_items = sorted(b_items, key=lambda x: x["checked"])
                        for item in sorted_items:
                            # Unique key calculation
                            global_idx = items.index(item)
                            
                            c_chk, c_name, c_qty = st.columns([1.5, 6.5, 2])
                            
                            # 1. Checkbox
                            chk_key = f"chk_ac_{active_doc_name}_{b_idx}_{global_idx}"
                            new_val = c_chk.checkbox("", value=item["checked"], key=chk_key, label_visibility="collapsed")
                            if new_val != item["checked"]:
                                item["checked"] = new_val
                                st.rerun()
                                
                            # 2. Item Name & Code Reveal on Tap
                            name_val = item["name"]
                            code_val = item.get("code") or ""
                            is_revealed = st.session_state.revealed_codes.get(f"{active_doc_name}_{global_idx}", False)
                            
                            if item["checked"]:
                                c_name.markdown(f'<span style="color: #64748B; text-decoration: line-through; font-size: 13.5px; display: block; padding-top: 4px;">🛒 {name_val}</span>', unsafe_allow_html=True)
                            else:
                                if c_name.button(f"🛒 {name_val}", key=f"btn_name_ac_{active_doc_name}_{b_idx}_{global_idx}"):
                                    st.session_state.revealed_codes[f"{active_doc_name}_{global_idx}"] = not is_revealed
                                    st.rerun()
                                
                                if is_revealed and code_val:
                                    c_name.markdown(f'<div class="code-badge">コード: {code_val}</div>', unsafe_allow_html=True)
                                    
                            # 3. Quantity Badge
                            qty_val = item["quantity"]
                            if item["checked"]:
                                c_qty.markdown(f'<div style="text-align: right; padding-top: 4px;"><span class="qty-badge-checked">{qty_val}</span></div>', unsafe_allow_html=True)
                            else:
                                c_qty.markdown(f'<div style="text-align: right; padding-top: 4px;"><span class="qty-badge">{qty_val}</span></div>', unsafe_allow_html=True)
                                
                        st.markdown('</div>', unsafe_allow_html=True)

        else:
            # ==================== 📊 購入状態別一括表示 ====================
            # "購入されているものと未購入のものが一目でわかるページを作ってください"
            st.write("📋 すべての店舗から、購入状態に合わせて一括整理して表示します。")
            
            uncompleted_items = [it for it in valid_items if not it["checked"]]
            completed_items = [it for it in valid_items if it["checked"]]
            
            c_uncomp, c_comp = st.columns(2)
            
            with c_uncomp:
                st.markdown(f"### ⚠️ 未購入の商品 ({len(uncompleted_items)}件)")
                if not uncompleted_items:
                    st.success("🎉 すべて購入済みです！買い物お疲れ様でした！")
                else:
                    for item in uncompleted_items:
                        global_idx = items.index(item)
                        # Box style container
                        st.markdown(f'<div class="table-container">', unsafe_allow_html=True)
                        
                        c_chk, c_info, c_qty = st.columns([1.5, 6.5, 2])
                        # 1. Checkbox
                        chk_key = f"chk_status_un_{active_doc_name}_{global_idx}"
                        new_val = c_chk.checkbox("", value=False, key=chk_key, label_visibility="collapsed")
                        if new_val:
                            item["checked"] = True
                            st.rerun()
                            
                        # 2. Name, Store, and Code
                        name_val = item["name"]
                        store_val = item.get("store") or "その他"
                        code_val = item.get("code") or ""
                        is_revealed = st.session_state.revealed_codes.get(f"{active_doc_name}_{global_idx}", False)
                        
                        # Info block
                        with c_info:
                            st.markdown(f'<span class="store-badge">🏪 {store_val}</span>', unsafe_allow_html=True)
                            if st.button(f"🛒 {name_val}", key=f"btn_name_status_un_{active_doc_name}_{global_idx}"):
                                st.session_state.revealed_codes[f"{active_doc_name}_{global_idx}"] = not is_revealed
                                st.rerun()
                            if is_revealed and code_val:
                                st.markdown(f'<div class="code-badge">コード: {code_val}</div>', unsafe_allow_html=True)
                                
                        # 3. Quantity
                        c_qty.markdown(f'<div style="text-align: right; padding-top: 15px;"><span class="qty-badge">{item["quantity"]}</span></div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                        
            with c_comp:
                st.markdown(f"### ✅ 購入済みの商品 ({len(completed_items)}件)")
                if not completed_items:
                    st.info("チェックされた商品はまだありません。")
                else:
                    for item in completed_items:
                        global_idx = items.index(item)
                        # Box style container (muted border/background)
                        st.markdown(f'<div class="table-container" style="border-color: #1E293B; opacity: 0.65;">', unsafe_allow_html=True)
                        
                        c_chk, c_info, c_qty = st.columns([1.5, 6.5, 2])
                        # 1. Checkbox (can uncheck)
                        chk_key = f"chk_status_comp_{active_doc_name}_{global_idx}"
                        new_val = c_chk.checkbox("", value=True, key=chk_key, label_visibility="collapsed")
                        if not new_val:
                            item["checked"] = False
                            st.rerun()
                            
                        # 2. Name & Store
                        with c_info:
                            st.markdown(f'<span class="store-badge" style="background-color: #1E293B; color: #64748B; border-color: #334155;">🏪 {item.get("store") or "その他"}</span>', unsafe_allow_html=True)
                            st.markdown(f'<span style="color: #64748B; text-decoration: line-through; font-size: 13.5px; display: block; font-weight: bold; padding-top: 4px;">🛒 {item["name"]}</span>', unsafe_allow_html=True)
                            
                        # 3. Quantity
                        c_qty.markdown(f'<div style="text-align: right; padding-top: 15px;"><span class="qty-badge-checked">{item["quantity"]}</span></div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)



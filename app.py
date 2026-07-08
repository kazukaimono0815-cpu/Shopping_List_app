import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  UploadCloud,
  CheckCircle,
  FileText,
  Trash2,
  Plus,
  RefreshCw,
  Copy,
  Download,
  Check,
  AlertCircle,
  Sparkles,
  ShoppingBag,
  Store,
  Grid,
  FileSpreadsheet,
  ChevronRight,
  Info,
  Layers,
  CheckSquare
} from "lucide-react";

// Types
interface ChecklistItem {
  id: string;
  name: string;
  quantity: string;
  store: string;
  code: string;
  checked: boolean;
}

interface DocumentData {
  id: string;
  name: string;
  items: ChecklistItem[];
}

const STREAMLIT_CODE = `import streamlit as st
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
                            
                            # 空白行（すべての値がほぼ空）を検知
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
            
            # フォールバック テキストパース
            if not extracted_items and text:
                lines = text.split("\\n")
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
                    parts = re.split(r'\\s+', line)
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
            
            # 空白行または店舗名の変更によるブロック化
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
                
            # --- アイコン式のブロック選択 (タブの代わりにカラム+カードで実装) ---
            block_key = f"active_block_{tab_name}"
            if block_key not in st.session_state:
                st.session_state[block_key] = 0
                
            active_b_idx = st.session_state[block_key]
            if active_b_idx >= len(blocks):
                active_b_idx = 0
                st.session_state[block_key] = 0

            st.markdown("<p style='font-size: 11px; font-weight: bold; color: #94A3B8; margin-top: 15px; margin-bottom: 5px;'>🛒 店舗・グループ（空白行で区切られたブロック）</p>", unsafe_allow_html=True)
            
            # アイコンボタンを横並びに配置
            cols = st.columns(max(len(blocks), 1))
            for b_idx, block in enumerate(blocks):
                is_active = (b_idx == active_b_idx)
                unchecked_count = sum(1 for item in block["items"] if not item["checked"])
                
                # 店舗名に応じた絵文字アイコンの選択
                icon_char = "🏪"
                title_lower = block["title"].lower()
                if any(x in title_lower for x in ["マツモト", "ドラッグ", "薬", "ココカラ"]):
                    icon_char = "💊"
                elif any(x in title_lower for x in ["セリア", "ダイソー", "100", "キャンドゥ"]):
                    icon_char = "🧸"
                elif any(x in title_lower for x in ["ライフ", "スーパー", "イオン", "業務"]):
                    icon_char = "🛒"
                
                badge_str = f"🔴 {unchecked_count}" if unchecked_count > 0 else "✅"
                button_label = f"{icon_char} {block['title']}\\n({badge_str})"
                
                with cols[b_idx]:
                    # アクティブなアイコンには青い枠線と背景を付けるカスタムCSS
                    border_style = "border: 2px solid #3B82F6; background-color: rgba(59, 130, 246, 0.15);" if is_active else "border: 1px solid #334155; background-color: #0F172A;"
                    st.markdown(f"<div style='{border_style} border-radius: 12px; padding: 4px; text-align: center; margin-bottom: 10px;'>", unsafe_allow_html=True)
                    if st.button(button_label, key=f"block_btn_{tab_name}_{b_idx}"):
                        st.session_state[block_key] = b_idx
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

            # 選択されたブロック of アイテムリストを描画
            active_block = blocks[active_b_idx]
            b_items = active_block["items"]
            
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
                chk_key = f"chk_{tab_name}_{active_b_idx}_{global_idx}"
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
                    if c_name.button(f"🛒 {name_val}", key=f"btn_name_{tab_name}_{active_b_idx}_{global_idx}"):
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
`;

interface Block {
  id: string;
  title: string;
  items: ChecklistItem[];
}

function getBlocksFromItems(items: ChecklistItem[]): Block[] {
  const blocks: Block[] = [];
  let currentBlockItems: ChecklistItem[] = [];
  let blockIndex = 0;
  let lastStore = "";

  for (const item of items) {
    const isEmptyRow =
      item.name === "---EMPTY_ROW---" ||
      (!item.name && !item.store && !item.code && !item.quantity);

    const isStoreChange = item.store && lastStore && item.store !== lastStore;

    if (isEmptyRow || isStoreChange) {
      if (currentBlockItems.length > 0) {
        const firstStore = currentBlockItems[0].store || "その他";
        blocks.push({
          id: `block-${blockIndex++}`,
          title: firstStore,
          items: currentBlockItems
        });
        currentBlockItems = [];
      }
    }

    if (!isEmptyRow) {
      currentBlockItems.push(item);
      if (item.store) {
        lastStore = item.store;
      }
    }
  }

  if (currentBlockItems.length > 0) {
    const firstStore = currentBlockItems[0].store || "その他";
    blocks.push({
      id: `block-${blockIndex++}`,
      title: firstStore,
      items: currentBlockItems
    });
  }

  if (blocks.length === 0) {
    blocks.push({
      id: "block-empty",
      title: "その他",
      items: []
    });
  }

  return blocks;
}

export default function App() {
  const [activeTab, setActiveTab] = useState<"demo" | "streamlit">("demo");
  const [documents, setDocuments] = useState<DocumentData[]>([]);
  const [activeDocId, setActiveDocId] = useState<string>("demo-doc");
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Manual addition inputs
  const [addStore, setAddStore] = useState("");
  const [addCode, setAddCode] = useState("");
  const [addName, setAddName] = useState("");
  const [addQty, setAddQty] = useState("");
  const [revealedCodes, setRevealedCodes] = useState<Record<string, boolean>>({});
  const [activeBlockId, setActiveBlockId] = useState<string | null>(null);

  // Load and initialize
  useEffect(() => {
    const cached = localStorage.getItem("pdf_docs_store");
    if (cached) {
      try {
        const parsed = JSON.parse(cached);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setDocuments(parsed);
          setActiveDocId(parsed[0].id);
          return;
        }
      } catch (e) {
        console.error("Failed to parse cached docs", e);
      }
    }

    // Set fallback default mock document with empty rows (marker ---EMPTY_ROW---) to demonstrate blocks
    const defaultDoc: DocumentData = {
      id: "demo-doc",
      name: "デモ用サンプル買い物リスト.pdf",
      items: [
        { id: "d1", store: "ライフ スーパー", code: "4901301236543", name: "北海道産 特選牛乳 (1000ml)", quantity: "1本", checked: false },
        { id: "d2", store: "ライフ スーパー", code: "4901301236544", name: "完熟バナナ (フィリピン産)", quantity: "1袋", checked: false },
        { id: "d3", store: "ライフ スーパー", code: "4901301236545", name: "国産 鶏もも肉 (特大パック)", quantity: "500g", checked: false },
        { id: "e1", store: "", code: "", name: "---EMPTY_ROW---", quantity: "", checked: false },
        { id: "d4", store: "マツモトキヨシ", code: "4987067223502", name: "鼻炎カプセルS (24カプセル)", quantity: "1箱", checked: false },
        { id: "d6", store: "マツモトキヨシ", code: "4901301324221", name: "BOXティッシュ (5箱パック)", quantity: "1袋", checked: false },
        { id: "e2", store: "", code: "", name: "---EMPTY_ROW---", quantity: "", checked: false },
        { id: "d5", store: "セリア", code: "4510019120034", name: "単3形乾電池 (4本パック)", quantity: "1つ", checked: false }
      ]
    };
    setDocuments([defaultDoc]);
    setActiveDocId("demo-doc");
  }, []);

  // Synchronize activeBlockId when activeDocId or documents change
  useEffect(() => {
    const activeDoc = documents.find(d => d.id === activeDocId);
    if (activeDoc) {
      const docBlocks = getBlocksFromItems(activeDoc.items);
      if (docBlocks.length > 0) {
        const exists = docBlocks.some(b => b.id === activeBlockId);
        if (!exists) {
          setActiveBlockId(docBlocks[0].id);
        }
      } else {
        setActiveBlockId(null);
      }
    } else {
      setActiveBlockId(null);
    }
  }, [activeDocId, documents, activeBlockId]);

  const saveDocs = (newDocs: DocumentData[]) => {
    setDocuments(newDocs);
    localStorage.setItem("pdf_docs_store", JSON.stringify(newDocs));
  };

  // Process a PDF upload
  const handleProcessPdf = async (file: File) => {
    if (file.type !== "application/pdf" && !file.name.endsWith(".pdf")) {
      setErrorMsg("PDFファイルのみ選択できます。");
      return;
    }

    setLoading(true);
    setErrorMsg(null);

    try {
      const reader = new FileReader();
      reader.onload = async (e) => {
        const dataUrl = e.target?.result as string;
        const base64 = dataUrl.split(",")[1];

        // API extraction call
        const response = await fetch("/api/extract", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ pdfBase64: base64 })
        });

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.error || "PDFの解析に失敗しました。");
        }

        const data = await response.json();
        if (data && Array.isArray(data.items)) {
          const newItems: ChecklistItem[] = data.items.map((item: any, idx: number) => ({
            id: `ext-${Date.now()}-${idx}`,
            name: item.name || "不明な商品",
            quantity: item.quantity || "1",
            store: item.store || "",
            code: item.code || "",
            checked: false
          }));

          const newDoc: DocumentData = {
            id: `doc-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`,
            name: file.name,
            items: newItems
          };

          const updatedDocs = [...documents.filter(d => d.id !== "demo-doc"), newDoc];
          saveDocs(updatedDocs);
          setActiveDocId(newDoc.id);
        } else {
          throw new Error("有効な表形式の商品データを抽出できませんでした。");
        }
      };
      reader.readAsDataURL(file);
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.message || "PDFの解析中にエラーが発生しました。");
    } finally {
      setLoading(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      for (let i = 0; i < files.length; i++) {
        const file = files.item(i);
        if (file) {
          handleProcessPdf(file);
        }
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      for (let i = 0; i < files.length; i++) {
        const file = files.item(i);
        if (file) {
          handleProcessPdf(file);
        }
      }
    }
  };

  // Delete a document/tab
  const handleDeleteDoc = (docId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const updated = documents.filter(d => d.id !== docId);
    saveDocs(updated);
    if (activeDocId === docId && updated.length > 0) {
      setActiveDocId(updated[0].id);
    }
  };

  // Clear/Reset all check states of active document
  const handleResetActiveDocChecks = () => {
    const updated = documents.map(doc => {
      if (doc.id === activeDocId) {
        return {
          ...doc,
          items: doc.items.map(item => ({ ...item, checked: false }))
        };
      }
      return doc;
    });
    saveDocs(updated);
  };

  // Toggle individual check (消込)
  const handleToggleCheck = (itemId: string) => {
    const updated = documents.map(doc => {
      if (doc.id === activeDocId) {
        return {
          ...doc,
          items: doc.items.map(item =>
            item.id === itemId ? { ...item, checked: !item.checked } : item
          )
        };
      }
      return doc;
    });
    saveDocs(updated);
  };

  // Delete individual item from active document (消去 / 削除)
  const handleDeleteItem = (itemId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const updated = documents.map(doc => {
      if (doc.id === activeDocId) {
        return {
          ...doc,
          items: doc.items.filter(item => item.id !== itemId)
        };
      }
      return doc;
    });
    saveDocs(updated);
  };

  // Add individual item to active document
  const handleAddItemToActive = (e: React.FormEvent) => {
    e.preventDefault();
    if (!addName.trim() && !addStore.trim()) return;

    const activeDocObj = documents.find(d => d.id === activeDocId);
    const docBlocks = activeDocObj ? getBlocksFromItems(activeDocObj.items) : [];
    const currentBlockObj = docBlocks.find(b => b.id === activeBlockId) || docBlocks[0];
    const defaultStore = currentBlockObj ? currentBlockObj.title : "";

    const newItem: ChecklistItem = {
      id: `man-${Date.now()}`,
      store: addStore.trim() || defaultStore || "その他",
      code: addCode.trim() || "",
      name: addName.trim() || "手動追加の商品",
      quantity: addQty.trim() || "1",
      checked: false
    };

    const updated = documents.map(doc => {
      if (doc.id === activeDocId) {
        return {
          ...doc,
          items: [...doc.items, newItem]
        };
      }
      return doc;
    });

    saveDocs(updated);
    setAddStore("");
    setAddCode("");
    setAddName("");
    setAddQty("");
  };

  // Load standard Demo Document
  const handleResetToDemo = () => {
    const demoDoc: DocumentData = {
      id: "demo-doc",
      name: "デモ用サンプル買い物リスト.pdf",
      items: [
        { id: "d1", store: "ライフ スーパー", code: "4901301236543", name: "北海道産 特選牛乳 (1000ml)", quantity: "1本", checked: false },
        { id: "d2", store: "ライフ スーパー", code: "4901301236544", name: "完熟バナナ (フィリピン産)", quantity: "1袋", checked: false },
        { id: "d3", store: "ライフ スーパー", code: "4901301236545", name: "国産 鶏もも肉 (特大パック)", quantity: "500g", checked: false },
        { id: "e1", store: "", code: "", name: "---EMPTY_ROW---", quantity: "", checked: false },
        { id: "d4", store: "マツモトキヨシ", code: "4987067223502", name: "鼻炎カプセルS (24カプセル)", quantity: "1箱", checked: false },
        { id: "d6", store: "マツモトキヨシ", code: "4901301324221", name: "BOXティッシュ (5箱パック)", quantity: "1袋", checked: false },
        { id: "e2", store: "", code: "", name: "---EMPTY_ROW---", quantity: "", checked: false },
        { id: "d5", store: "セリア", code: "4510019120034", name: "単3形乾電池 (4本パック)", quantity: "1つ", checked: false }
      ]
    };
    saveDocs([demoDoc]);
    setActiveDocId("demo-doc");
  };

  // Calculate current active document statistics (excluding empty marker rows)
  const activeDoc = documents.find(d => d.id === activeDocId) || documents[0];
  const totalItems = activeDoc?.items.filter(item => item.name !== "---EMPTY_ROW---").length || 0;
  const checkedItems = activeDoc?.items.filter(item => item.name !== "---EMPTY_ROW---" && item.checked).length || 0;
  const progressPercent = totalItems > 0 ? Math.round((checkedItems / totalItems) * 100) : 0;

  const blocks = activeDoc ? getBlocksFromItems(activeDoc.items) : [];
  const currentBlock = blocks.find(b => b.id === activeBlockId) || blocks[0];

  // Clipboard copies
  const handleCopyCode = () => {
    navigator.clipboard.writeText(STREAMLIT_CODE);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadCode = () => {
    const blob = new Blob([STREAMLIT_CODE], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "app.py";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col antialiased">
      {/* Dynamic Header */}
      <header className="border-b border-slate-800 bg-slate-950/90 backdrop-blur-md sticky top-0 z-50 py-3 px-4 sm:px-6">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="bg-gradient-to-tr from-blue-600 to-indigo-500 p-2 rounded-xl shadow-lg shadow-blue-500/10">
              <ShoppingBag className="h-5 w-5 text-white animate-pulse" />
            </div>
            <div>
              <h1 id="app-title" className="text-lg sm:text-xl font-extrabold tracking-tight bg-gradient-to-r from-blue-400 to-indigo-200 bg-clip-text text-transparent">
                PDF 買い物チェックリスト作成器
              </h1>
              <p className="text-[11px] text-slate-400 font-medium">複数PDF同時アップロード対応・表形式そのまま消込仕様</p>
            </div>
          </div>

          <div className="flex bg-slate-900 p-1 rounded-xl border border-slate-800">
            <button
              id="tab-demo"
              onClick={() => setActiveTab("demo")}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
                activeTab === "demo"
                  ? "bg-blue-600 text-white shadow"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <CheckSquare className="h-3.5 w-3.5" />
              <span>チェックリスト表示</span>
            </button>
            <button
              id="tab-streamlit"
              onClick={() => setActiveTab("streamlit")}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
                activeTab === "streamlit"
                  ? "bg-indigo-600 text-white shadow"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <FileText className="h-3.5 w-3.5" />
              <span>Streamlit app.py</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-6xl w-full mx-auto p-3 sm:p-5 flex flex-col gap-4">
        
        {/* Compact Notice */}
        <div className="bg-gradient-to-r from-blue-950/30 to-indigo-950/20 border border-blue-900/40 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-sm">
          <div className="flex items-start gap-2.5">
            <Sparkles className="h-5 w-5 text-blue-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-xs sm:text-sm text-slate-200 font-bold">
                複数ファイルの同時アップロード・表形式消込仕様をサポートしました
              </p>
              <p className="text-[11px] text-slate-400 mt-0.5">
                PDF内の表データをそっくりそのまま表示。スマホでタップしやすい大型チェックボックスで、消し込んだアイテムは瞬時に進捗率へ反映されます。
              </p>
            </div>
          </div>
          {documents.length === 0 && (
            <button
              onClick={handleResetToDemo}
              className="text-xs font-bold text-blue-400 hover:text-blue-300 bg-blue-500/10 hover:bg-blue-500/20 px-3 py-1.5 rounded-lg border border-blue-500/20 transition-all self-start sm:self-auto"
            >
              デモ用サンプルを読込
            </button>
          )}
        </div>

        <AnimatePresence mode="wait">
          {activeTab === "demo" ? (
            <motion.div
              key="demo-view"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-stretch"
            >
              {/* Left sidebar: PDF Upload and File Tabs list */}
              <div className="lg:col-span-4 flex flex-col gap-4">
                
                {/* PDF Drag and Drop Uploader */}
                <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 shadow-md flex flex-col gap-3">
                  <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                    <UploadCloud className="h-4 w-4 text-blue-400" />
                    <span>PDFファイルのインポート</span>
                  </h2>

                  <div
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                    className={`border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-all flex flex-col items-center justify-center gap-2 ${
                      isDragging
                        ? "border-blue-500 bg-blue-600/10"
                        : "border-slate-800 hover:border-slate-700 bg-slate-900/30 hover:bg-slate-900/60"
                    }`}
                  >
                    <input
                      type="file"
                      ref={fileInputRef}
                      onChange={handleFileChange}
                      accept="application/pdf"
                      multiple
                      className="hidden"
                    />
                    <UploadCloud className="h-6 w-6 text-slate-400" />
                    <div>
                      <p className="text-xs font-bold text-slate-300">ファイルをドラッグ＆ドロップ</p>
                      <p className="text-[10px] text-slate-500 mt-0.5">またはここをクリック（複数選択可）</p>
                    </div>
                  </div>

                  {loading && (
                    <div className="bg-blue-950/40 border border-blue-900/30 rounded-lg p-3 text-center flex items-center justify-center gap-2">
                      <RefreshCw className="h-4 w-4 text-blue-400 animate-spin" />
                      <span className="text-xs text-slate-300">Gemini 3.5 AIがPDFの表データを抽出中...</span>
                    </div>
                  )}

                  {errorMsg && (
                    <div className="bg-red-500/10 border border-red-500/20 p-3 rounded-lg text-red-400 text-xs flex items-start gap-2">
                      <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                      <span className="leading-tight">{errorMsg}</span>
                    </div>
                  )}
                </div>

                {/* File list / Tabs */}
                <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 shadow-md flex flex-col gap-3 flex-1 min-h-[160px]">
                  <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                    <Layers className="h-4 w-4 text-indigo-400" />
                    <span>読み込み済みのPDFリスト</span>
                  </h2>

                  {documents.length > 0 ? (
                    <div className="flex flex-col gap-2 max-h-[220px] overflow-y-auto pr-1">
                      {documents.map((doc) => {
                        const checked = doc.items.filter(i => i.checked).length;
                        const total = doc.items.length;
                        const pct = total > 0 ? Math.round((checked / total) * 100) : 0;
                        const isActive = doc.id === activeDocId;

                        return (
                          <div
                            key={doc.id}
                            onClick={() => setActiveDocId(doc.id)}
                            className={`flex items-center justify-between p-3 rounded-xl border cursor-pointer transition-all select-none ${
                              isActive
                                ? "bg-blue-600/10 border-blue-500/60 text-white"
                                : "bg-slate-900/50 border-slate-800 hover:border-slate-700 text-slate-400 hover:text-slate-200"
                            }`}
                          >
                            <div className="flex items-center gap-2.5 min-w-0">
                              <FileSpreadsheet className={`h-4.5 w-4.5 flex-shrink-0 ${isActive ? "text-blue-400" : "text-slate-500"}`} />
                              <div className="min-w-0">
                                <p className="text-xs font-bold truncate max-w-[170px]">{doc.name}</p>
                                <p className="text-[10px] text-slate-500 font-medium mt-0.5">
                                  進捗: {checked}/{total} 品 ({pct}%)
                                </p>
                              </div>
                            </div>
                            <button
                              onClick={(e) => handleDeleteDoc(doc.id, e)}
                              className="p-1 rounded hover:bg-red-500/20 text-slate-500 hover:text-red-400 transition-colors"
                              title="リストを削除"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </button>
                          </div>
                        )
                      })}
                    </div>
                  ) : (
                    <div className="text-center py-6 text-slate-600 text-xs">
                      インポートされたPDFがありません。上のパネルからアップロードしてください。
                    </div>
                  )}
                </div>

              </div>

              {/* Right panel: Active Table and 消込 Sheet */}
              <div className="lg:col-span-8 flex flex-col gap-4">
                
                {/* Compact Table View Container */}
                <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 shadow-md flex flex-col flex-1">
                  
                  {/* Table Control Header */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3 mb-3">
                    <div>
                      <h3 className="text-sm font-bold text-white flex items-center gap-2">
                        <FileSpreadsheet className="h-4.5 w-4.5 text-blue-400" />
                        <span>{activeDoc?.name || "シート表示"}</span>
                      </h3>
                      <p className="text-[11px] text-slate-500 font-medium mt-0.5">
                        空白行ごとのブロック（店舗）タブに分けて表示。右にスワイプ（スライド）またはタップで消し込めます。
                      </p>
                    </div>

                    {totalItems > 0 && (
                      <button
                        onClick={handleResetActiveDocChecks}
                        className="text-[10px] font-bold text-amber-400 hover:text-amber-300 bg-amber-500/10 hover:bg-amber-500/20 px-2.5 py-1.5 rounded-lg border border-amber-500/20 transition-all self-start sm:self-auto"
                      >
                        全消込を解除する
                      </button>
                    )}
                  </div>

                  {/* Realtime Progress Card */}
                  {totalItems > 0 && (
                    <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-3 mb-3 flex flex-col gap-2">
                      <div className="flex items-center justify-between text-xs font-bold text-slate-300">
                        <span className="flex items-center gap-1.5">
                          <CheckCircle className="h-4 w-4 text-emerald-400" />
                          <span>リスト全体の消込進捗率</span>
                        </span>
                        <span className="text-blue-400 text-xs font-mono bg-blue-500/10 px-2 py-0.5 rounded">
                          {checkedItems} / {totalItems} 件完了 ({progressPercent}%)
                        </span>
                      </div>
                      <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${progressPercent}%` }}
                          transition={{ duration: 0.2 }}
                          className="bg-gradient-to-r from-blue-500 to-indigo-500 h-full rounded-full"
                        />
                      </div>
                    </div>
                  )}

                  {/* Blocks / Custom Icon-Style Selector (空白行ごとのアイコン式店舗選択) */}
                  {blocks.length > 0 && (
                    <div className="flex flex-col gap-1.5 mb-4">
                      <span className="text-[10px] font-extrabold text-slate-500 uppercase tracking-wider block">
                        店舗・エリア（空白行グループ）
                      </span>
                      <div className="flex gap-4 pb-2 mb-1 overflow-x-auto scrollbar-none py-1 px-0.5">
                        {blocks.map((block, idx) => {
                          const isBlockActive = block.id === activeBlockId;
                          const uncheckedInBlock = block.items.filter((item) => !item.checked).length;

                          // Determine specific icons and style colors per shop
                          let BlockIcon = Store;
                          let activeColors = "bg-blue-500/20 ring-2 ring-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.3)] text-blue-400";
                          let hoverGlow = "from-blue-500 to-cyan-500";

                          const titleLower = block.title.toLowerCase();
                          if (
                            titleLower.includes("マツモト") ||
                            titleLower.includes("ドラッグ") ||
                            titleLower.includes("薬") ||
                            titleLower.includes("ココカラ")
                          ) {
                            BlockIcon = CheckSquare;
                            activeColors = "bg-emerald-500/20 ring-2 ring-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.3)] text-emerald-400";
                            hoverGlow = "from-emerald-500 to-teal-500";
                          } else if (
                            titleLower.includes("セリア") ||
                            titleLower.includes("ダイソー") ||
                            titleLower.includes("100") ||
                            titleLower.includes("キャンドゥ")
                          ) {
                            BlockIcon = Grid;
                            activeColors = "bg-purple-500/20 ring-2 ring-purple-500 shadow-[0_0_15px_rgba(168,85,247,0.3)] text-purple-400";
                            hoverGlow = "from-purple-500 to-pink-500";
                          } else if (
                            titleLower.includes("ライフ") ||
                            titleLower.includes("スーパー") ||
                            titleLower.includes("イオン") ||
                            titleLower.includes("業務")
                          ) {
                            BlockIcon = ShoppingBag;
                            activeColors = "bg-amber-500/20 ring-2 ring-amber-500 shadow-[0_0_15px_rgba(245,158,11,0.3)] text-amber-400";
                            hoverGlow = "from-amber-500 to-orange-500";
                          } else if (idx === 0) {
                            BlockIcon = Store;
                            activeColors = "bg-blue-500/20 ring-2 ring-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.3)] text-blue-400";
                            hoverGlow = "from-blue-500 to-indigo-500";
                          } else {
                            BlockIcon = Store;
                            activeColors = "bg-slate-700/30 ring-2 ring-slate-400 shadow-[0_0_15px_rgba(148,163,184,0.3)] text-slate-300";
                            hoverGlow = "from-slate-500 to-slate-400";
                          }

                          return (
                            <button
                              key={block.id}
                              type="button"
                              onClick={() => setActiveBlockId(block.id)}
                              className="flex flex-col items-center gap-1.5 focus:outline-none transition-all select-none cursor-pointer flex-shrink-0 group"
                            >
                              {/* Icon Wrapper */}
                              <div
                                className={`w-14 h-14 rounded-2xl border flex items-center justify-center relative transition-all ${
                                  isBlockActive
                                    ? `${activeColors} border-transparent scale-105`
                                    : "bg-slate-900/80 border-slate-800 hover:border-slate-700 hover:scale-102"
                                }`}
                              >
                                {/* Gentle hover glow */}
                                <div
                                  className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${hoverGlow} opacity-0 group-hover:opacity-10 transition-opacity`}
                                />

                                <BlockIcon
                                  className={`h-6 w-6 relative z-10 transition-colors ${
                                    isBlockActive ? "text-white" : "text-slate-400 group-hover:text-slate-200"
                                  }`}
                                />

                                {/* Badges */}
                                {uncheckedInBlock > 0 ? (
                                  <span className="absolute -top-1.5 -right-1.5 bg-rose-600 text-white font-mono text-[9px] px-1.5 py-0.5 rounded-full font-extrabold min-w-[18px] text-center shadow-[0_2px_5px_rgba(225,29,72,0.4)] border border-rose-500">
                                    {uncheckedInBlock}
                                  </span>
                                ) : (
                                  <span className="absolute -top-1.5 -right-1.5 bg-emerald-600 p-0.5 rounded-full shadow-[0_2px_5px_rgba(5,150,105,0.4)] border border-emerald-500 flex items-center justify-center">
                                    <Check className="h-2.5 w-2.5 text-white stroke-[3.5px]" />
                                  </span>
                                )}
                              </div>

                              {/* Shop Name Label */}
                              <span
                                className={`text-[11px] font-bold max-w-[70px] truncate transition-colors text-center ${
                                  isBlockActive
                                    ? "text-slate-100 font-extrabold"
                                    : "text-slate-400 group-hover:text-slate-200"
                                }`}
                              >
                                {block.title}
                              </span>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Excel-like Compact Sheet Grid with Swipe support (using div-based responsive design) */}
                  <div className="flex-1 min-h-[250px] max-h-[350px] overflow-y-auto overflow-x-hidden border border-slate-800 rounded-lg bg-slate-950/60 flex flex-col">
                    {currentBlock && currentBlock.items.length > 0 ? (
                      [...currentBlock.items]
                        .sort((a, b) => {
                          if (a.checked === b.checked) return 0;
                          return a.checked ? 1 : -1; // 未チェックを上にソート
                        })
                        .map((item) => (
                          <div
                            key={item.id}
                            className="relative overflow-hidden border-b border-slate-800/60 select-none"
                          >
                            {/* Slide-Reveal Green Swipe Backdrop */}
                            <div className="absolute inset-0 bg-emerald-600/20 flex items-center justify-between px-5 pointer-events-none z-0">
                              <div className="flex items-center gap-1.5 text-emerald-400 font-bold text-xs">
                                <CheckCircle className="h-4 w-4" />
                                <span>消込トグル</span>
                              </div>
                              <div className="flex items-center gap-1.5 text-emerald-400 font-bold text-xs">
                                <span>スワイプしてトグル</span>
                                <CheckCircle className="h-4 w-4" />
                              </div>
                            </div>

                            {/* Swipeable Foreground content */}
                            <motion.div
                              drag="x"
                              dragDirectionLock
                              dragConstraints={{ left: 0, right: 0 }}
                              dragElastic={0.6}
                              style={{ touchAction: "pan-y" }}
                              animate={{ x: 0 }}
                              transition={{ type: "spring", stiffness: 450, damping: 40 }}
                              onDragEnd={(event, info) => {
                                if (Math.abs(info.offset.x) > 50) {
                                  handleToggleCheck(item.id);
                                }
                              }}
                              className={`relative z-10 flex items-center justify-between p-3.5 transition-colors cursor-grab active:cursor-grabbing ${
                                item.checked
                                  ? "bg-slate-900/40 opacity-40"
                                  : "bg-slate-950 hover:bg-slate-900/30"
                              }`}
                            >
                              {/* Large Checkbox Tap Target */}
                              <div
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleToggleCheck(item.id);
                                }}
                                className="flex items-center justify-center p-1 cursor-pointer flex-shrink-0"
                              >
                                <div
                                  className={`w-6.5 h-6.5 rounded-lg border-2 flex items-center justify-center transition-all ${
                                    item.checked
                                      ? "bg-emerald-500 border-emerald-500 text-slate-950"
                                      : "border-slate-600 hover:border-slate-400 bg-slate-900"
                                  }`}
                                >
                                  {item.checked && <Check className="h-4 w-4 stroke-[3px] text-white" />}
                                </div>
                              </div>

                              {/* Item Description & Interactive Code Toggle */}
                              <div
                                className="flex-1 min-w-0 px-3.5 cursor-pointer"
                                onClick={() => {
                                  setRevealedCodes((prev) => ({ ...prev, [item.id]: !prev[item.id] }));
                                }}
                              >
                                <div className="flex flex-col">
                                  <span
                                    className={`text-xs sm:text-sm font-bold leading-tight ${
                                      item.checked
                                        ? "text-slate-600 line-through decoration-slate-600/60"
                                        : "text-slate-100"
                                    }`}
                                  >
                                    🛒 {item.name}
                                  </span>
                                  
                                  {/* Code toggler */}
                                  {!item.checked && revealedCodes[item.id] && item.code && (
                                    <span className="text-blue-400 font-bold font-mono text-[9px] sm:text-[10px] bg-blue-950/40 px-1.5 py-0.5 rounded border border-blue-900/30 mt-1 self-start select-text">
                                      コード: {item.code}
                                    </span>
                                  )}
                                </div>
                              </div>

                              {/* High Visibility Stylized Quantity Badge */}
                              <div className="flex-shrink-0 text-right pr-1">
                                {item.checked ? (
                                  <span className="inline-block bg-slate-800 text-slate-500 border border-slate-700/50 px-2 py-0.5 rounded-md font-medium text-[11px] line-through">
                                    {item.quantity}
                                  </span>
                                ) : (
                                  <span className="inline-block bg-gradient-to-r from-amber-500/20 to-orange-500/20 text-amber-400 border border-amber-500/30 px-3 py-1 rounded-lg font-extrabold text-xs sm:text-sm font-mono shadow-[0_0_8px_rgba(245,158,11,0.15)]">
                                    {item.quantity}
                                  </span>
                                )}
                              </div>
                            </motion.div>
                          </div>
                        ))
                    ) : (
                      <div className="py-12 text-center text-slate-500 text-xs">
                        表示可能なテーブルデータがありません。
                      </div>
                    )}
                  </div>

                  {/* Add Row inside Active Sheet Form */}
                  {activeDoc && (
                    <form onSubmit={handleAddItemToActive} className="mt-3.5 bg-slate-900/80 p-3 rounded-xl border border-slate-800 flex flex-col sm:flex-row gap-2.5 items-end">
                      <div className="w-full sm:w-[22%]">
                        <label className="text-[10px] font-bold text-slate-400 block mb-1">購入先（1列目）</label>
                        <input
                          type="text"
                          value={addStore}
                          onChange={(e) => setAddStore(e.target.value)}
                          placeholder="例: ライフ"
                          className="w-full bg-slate-950 border border-slate-800 focus:border-blue-500 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 placeholder-slate-700 focus:outline-none"
                        />
                      </div>
                      <div className="w-full sm:w-[23%]">
                        <label className="text-[10px] font-bold text-slate-400 block mb-1">商品コード（2列目）</label>
                        <input
                          type="text"
                          value={addCode}
                          onChange={(e) => setAddCode(e.target.value)}
                          placeholder="例: 4901301..."
                          className="w-full bg-slate-950 border border-slate-800 focus:border-blue-500 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 placeholder-slate-700 focus:outline-none"
                        />
                      </div>
                      <div className="flex-1 w-full">
                        <label className="text-[10px] font-bold text-slate-400 block mb-1">商品名（3列目）</label>
                        <input
                          type="text"
                          required
                          value={addName}
                          onChange={(e) => setAddName(e.target.value)}
                          placeholder="例: 有機キャベツ"
                          className="w-full bg-slate-950 border border-slate-800 focus:border-blue-500 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 placeholder-slate-700 focus:outline-none"
                        />
                      </div>
                      <div className="w-full sm:w-[12%]">
                        <label className="text-[10px] font-bold text-slate-400 block mb-1">数量（4列目）</label>
                        <input
                          type="text"
                          value={addQty}
                          onChange={(e) => setAddQty(e.target.value)}
                          placeholder="1本"
                          className="w-full bg-slate-950 border border-slate-800 focus:border-blue-500 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 placeholder-slate-700 focus:outline-none"
                        />
                      </div>
                      <button
                        type="submit"
                        className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-3 py-1.5 rounded-lg text-xs flex items-center justify-center gap-1 transition-all h-[32px] w-full sm:w-auto flex-shrink-0"
                      >
                        <Plus className="h-4.5 w-4.5" />
                        <span>行追加</span>
                      </button>
                    </form>
                  )}

                </div>

              </div>
            </motion.div>
          ) : (
            <motion.div
              key="streamlit-view"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="flex flex-col gap-4"
            >
              <div className="bg-slate-950 rounded-2xl border border-slate-800 p-5 shadow-lg">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4 mb-4">
                  <div>
                    <h3 className="text-base font-bold text-white flex items-center gap-1.5">
                      <Sparkles className="h-5 w-5 text-indigo-400" />
                      <span>複数ファイル・表消込対応 Streamlit (app.py) コード</span>
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">
                      ご要望である複数ファイルのタブ切替、および元の表形式のまま美しく表示・消込・進捗集計するプロ仕様コードです。
                    </p>
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={handleCopyCode}
                      className="bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 px-3 py-2 rounded-xl text-xs font-bold text-slate-200 transition-all flex items-center gap-1.5 shadow"
                    >
                      {copied ? (
                        <>
                          <Check className="h-4 w-4 text-emerald-400" />
                          <span className="text-emerald-400 font-bold">コピー完了</span>
                        </>
                      ) : (
                        <>
                          <Copy className="h-4 w-4 text-slate-400" />
                          <span>コードをコピー</span>
                        </>
                      )}
                    </button>
                    <button
                      onClick={handleDownloadCode}
                      className="bg-blue-600 hover:bg-blue-500 px-3 py-2 rounded-xl text-xs font-bold text-white transition-all flex items-center gap-1.5 shadow"
                    >
                      <Download className="h-4 w-4" />
                      <span>app.py を保存</span>
                    </button>
                  </div>
                </div>

                {/* Local run manual */}
                <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800 text-xs text-slate-300 flex flex-col gap-2 mb-4">
                  <span className="font-bold text-blue-400 block">⚡ ローカルの起動コマンド</span>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-1">
                    <div className="bg-slate-950 p-2.5 rounded border border-slate-850 font-mono">
                      <p className="text-slate-500"># ライブラリのセットアップ</p>
                      <p className="text-amber-300">pip install streamlit pdfplumber</p>
                    </div>
                    <div className="bg-slate-950 p-2.5 rounded border border-slate-850 font-mono">
                      <p className="text-slate-500"># アプリの起動</p>
                      <p className="text-emerald-400">streamlit run app.py</p>
                    </div>
                  </div>
                </div>

                {/* Main scrollable code pre */}
                <div className="relative">
                  <div className="absolute top-3 right-3 bg-slate-900/90 text-[10px] text-indigo-400 font-mono px-2 py-0.5 rounded border border-slate-800">
                    python
                  </div>
                  <pre className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-xs text-slate-300 overflow-x-auto max-h-[450px] font-mono leading-relaxed select-text">
                    <code>{STREAMLIT_CODE}</code>
                  </pre>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Aesthetic Footer */}
      <footer className="mt-auto border-t border-slate-800 bg-slate-950/40 py-4 text-center text-slate-500 text-[10px]">
        <div className="max-w-6xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <p>© 2026 PDF買い物チェックリスト. Created with Streamlit & AI Studio Build Pro.</p>
          <div className="flex gap-3">
            <span>ファイル別セッションステート永続化</span>
            <span>•</span>
            <span>表形式1画面レイアウト</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

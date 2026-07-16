import sys

IS_WINDOWS = sys.platform == "win32"

# ── cppcheck MISRA addon yolu ──────────────────────────────────────────────────
# Windows'ta cppcheck installer addons'u Program Files altına kurar.
# Linux'ta kaynaktan derlenince /usr/local/share/Cppcheck/addons/ altına gider.
MISRA_ADDON_PATH = (
    r"C:\Program Files\Cppcheck\addons\misra.py"
    if IS_WINDOWS else
    "/usr/local/share/Cppcheck/addons/misra.py"
)

# ── MISRA kural metni yolu ────────────────────────────────────────────────────
# Aşağıdaki yolları kendi ortamına göre güncelle.
MISRA_RULE_TEXT_PATH = (
    r".githooks\misra_c_2023__headlines_for_cppcheck.txt"
    if IS_WINDOWS else
    ".githooks/misra_c_2023__headlines_for_cppcheck.txt"
)

# ── Python binary adı ─────────────────────────────────────────────────────────
# Windows'ta PATH'teki python komutu kullanılır (python3.9 çalışmaz).
# Linux'ta tam versiyon adı tercih edilir.
PYTHON_BIN = "python" if IS_WINDOWS else "python3.9"

# ── Webhook URL'leri ──────────────────────────────────────────────────────────
WEBHOOK_URL        = "http://localhost:5678/webhook/commit-review"
REPORT_WEBHOOK_URL = "http://localhost:5678/webhook/bypass-report"

# ── Rapor çıktı klasörü ───────────────────────────────────────────────────────
OUTPUT_DIR = "./git_commit_docs"
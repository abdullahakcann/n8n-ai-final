import re
import sys
import subprocess
import os

IS_WINDOWS = sys.platform == "win32"

############################ REGEX ############################ 

FUNC_SIGNATURE_RE = re.compile(r'^[A-Za-z_][\w\s\*]*\b\w+\s*\([^;{}]*\)\s*$')
STATIC_LINE_RE = re.compile(r'^(?P<file>[^:]+):(?P<line>\d+): (?P<severity>\w+): (?P<message>.+)$')
MISRA_LINE_RE  = re.compile(r'^\[(?P<file>.+?):(?P<line>\d+)\]')


############################ HELPERS ############################

def run_git_cmd(args):
    try:
        return subprocess.check_output(args, stderr=subprocess.DEVNULL).decode("utf-8").strip()
    except subprocess.CalledProcessError:
        return ""

def parse_jira_issue_key(commit_msg: str = None):
    _jira_match  = re.match(r'^([A-Z]+-\d+)', commit_msg)
    jira_key     = _jira_match.group(1) if _jira_match else None
    return jira_key

def ask_user(prompt):
    """Git hook'ları stdin'i terminale bağlamadığı için doğrudan terminal cihazından okur."""
    candidates = ["CON"] if IS_WINDOWS else ["/dev/tty"]
    # Git Bash bazen /dev/tty'yi de destekler, fallback olarak dene
    if IS_WINDOWS:
        candidates.append("/dev/tty")

    for tty_path in candidates:
        try:
            with open(tty_path, 'r') as tty:
                print(prompt, end='', flush=True)
                return tty.readline().strip()
        except (OSError, FileNotFoundError):
            continue

    print("\nEtkileşimli terminal bulunamadı, otomatik olarak reddediliyor.")
    return "n"

def find_function_ranges(filepath):
    """
    Dosyadaki fonksiyon gövdelerinin (başlangıç, bitiş) satır numaralarını bulur.
    Brace-depth takibi + fonksiyon imzası sezgisiyle çalışır.
    Struct/union/enum gibi top-level blokları fonksiyon sanmamak için
    açılan '{' öncesindeki metnin fonksiyon imzasına benzeyip benzemediğine bakılır.
    """
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except OSError:
        return []

    ranges = []
    depth = 0
    pending_sig_lines = []
    func_start_line = None

    for idx, line in enumerate(lines, start=1):
        open_count  = line.count("{")
        close_count = line.count("}")

        if depth == 0 and open_count > 0:
            pending_sig_lines.append(line)
            signature_text  = " ".join(s.strip() for s in pending_sig_lines)
            sig_before_brace = signature_text.split("{", 1)[0].strip()

            is_function_sig = bool(FUNC_SIGNATURE_RE.match(sig_before_brace)) and "(" in sig_before_brace

            if is_function_sig:
                func_start_line = idx if func_start_line is None else func_start_line
            pending_sig_lines = []

        elif depth == 0 and open_count == 0 and close_count == 0:
            stripped = line.strip()
            if stripped and not stripped.startswith(("//", "/*", "*")):
                pending_sig_lines.append(line)
                if len(pending_sig_lines) > 10:
                    pending_sig_lines = pending_sig_lines[-10:]

        elif depth == 0:
            pending_sig_lines = []

        depth += open_count - close_count

        if depth == 0 and func_start_line is not None and close_count > 0:
            ranges.append((func_start_line, idx))
            func_start_line = None

    return ranges


def expand_lines_to_functions(filepath, line_numbers):
    """
    Verilen satır numaralarını, bulundukları fonksiyonun tüm satır aralığına genişletir.
    Fonksiyon dışı (global scope) satırlar olduğu gibi kalır.
    """
    if not line_numbers:
        return set()

    ranges = find_function_ranges(filepath)
    expanded = set()

    for ln in line_numbers:
        matched = False
        for start, end in ranges:
            if start <= ln <= end:
                expanded.update(range(start, end + 1))
                matched = True
                break
        if not matched:
            expanded.add(ln)

    return expanded

def get_changed_lines(files):
    """
    'git diff --cached -U0' çıktısından değişen satırları bulur,
    sonra her satırı bulunduğu fonksiyonun tüm aralığına genişletir.
    """
    changed_lines = {}

    diff_output = run_git_cmd(["git", "diff", "--cached", "-U0", "--"] + files)
    if not diff_output:
        return changed_lines

    current_file = None
    for line in diff_output.splitlines():
        if line.startswith("+++ "):
            path = line[4:].strip()
            if path == "/dev/null":
                current_file = None
            else:
                current_file = path.split("/", 1)[1] if path.startswith(("a/", "b/")) else path
                changed_lines.setdefault(current_file, set())
            continue

        if line.startswith("@@") and current_file is not None:
            match = re.search(r'\+(\d+)(?:,(\d+))?', line)
            if match:
                start_line = int(match.group(1))
                line_count = int(match.group(2)) if match.group(2) is not None else 1
                for ln in range(start_line, start_line + line_count):
                    changed_lines[current_file].add(ln)

    # ── Değişen satırları fonksiyon sınırlarına genişlet ──────────────────────
    expanded_changed_lines = {}
    for filename, lines in changed_lines.items():
        if os.path.exists(filename):
            expanded_changed_lines[filename] = expand_lines_to_functions(filename, lines)
        else:
            expanded_changed_lines[filename] = lines

    return expanded_changed_lines


def _normalize_path(p):
    return os.path.normpath(p).replace("\\", "/")


def _is_line_relevant(filename, lineno, changed_lines):
    filename_norm = _normalize_path(filename)
    for f, lines in changed_lines.items():
        if _normalize_path(f) == filename_norm:
            return lineno in lines
    return False



def filter_static_output(raw_output, changed_lines):
    """Sadece değişen satırlarla ilgili statik analiz satırlarını tutar."""
    relevant = []
    for line in raw_output.splitlines():
        m = STATIC_LINE_RE.match(line)
        if not m:
            continue  # 'Active checkers' gibi özet satırları atla
        if _is_line_relevant(m.group("file"), int(m.group("line")), changed_lines):
            relevant.append(line)
    return relevant


def filter_misra_lines(lines_list, changed_lines):
    """Sadece değişen satırlarla ilgili MISRA ihlallerini tutar."""
    relevant = []
    for line in lines_list:
        m = MISRA_LINE_RE.match(line)
        if not m:
            continue
        if _is_line_relevant(m.group("file"), int(m.group("line")), changed_lines):
            relevant.append(line)
    return relevant
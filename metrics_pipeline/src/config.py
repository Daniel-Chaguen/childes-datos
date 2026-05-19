from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "prepared_bi"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

CSV_OUTPUT = OUTPUT_DIR / "metrics_by_file.csv"
XLSX_OUTPUT = OUTPUT_DIR / "metrics_by_file.xlsx"

GROUP_DIRS = {
    "control": DATA_DIR / "control",
    "experimental": DATA_DIR / "experimental",
}

DISORDER_CODES = {
    "TD": "typically_developed",
    "DS": "down_syndrome",
    "LT": "late_talker",
    "HL": "hearing_limited",
    "SLI": "specific_language_impairment",
}

SPACY_MODEL = "en_core_web_sm"

MATTR_WINDOW = 50
COMMON_WORD_MIN_DOC_FREQ_RATIO = 0.05
COMMON_WORD_MIN_CORPUS_FREQ = 20

POS_TAGS = [
    "ADJ",
    "ADP",
    "ADV",
    "AUX",
    "CCONJ",
    "DET",
    "INTJ",
    "NOUN",
    "NUM",
    "PART",
    "PRON",
    "PROPN",
    "SCONJ",
    "VERB",
]

"""Deterministic discipline checklist tool.

For each discipline it checks the user's brief for the inputs that discipline needs.
An input that is not mentioned is reported as MISSING. Nothing is guessed:
the tool never invents a dimension, a load, or a requirement.
"""
import re
from typing import Any

_DIGITS = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')

# (label, pattern that proves the input was given, what is missing when absent)
REQUIREMENTS: dict[str, list[tuple[str, str]]] = {
    'architecture': [
        ('ابعاد زمین یا بنا', r'\d+(?:\.\d+)?\s*(?:متر)?\s*[×xX*]\s*\d+'),
        ('فهرست فضاها', r'فروشگاه|انبار|اتاق|دفتر|کانتر|سالن|آشپزخانه|سرویس'),
        ('ورودی و بارگیری', r'ورودی|بارگیری|درب|تخلیه'),
    ],
    'interior': [
        ('فهرست فضاها', r'فروشگاه|انبار|اتاق|دفتر|کانتر|سالن|آشپزخانه|سرویس'),
        ('سبک و متریال', r'سبک|متریال|رنگ|مدرن|کلاسیک|چوب|سنگ'),
        ('هویت بصری / لوگو', r'لوگو|برند|هویت'),
    ],
    'structure': [
        ('ابعاد دهانه و کف', r'\d+(?:\.\d+)?\s*(?:متر)?\s*[×xX*]\s*\d+'),
        ('ارتفاع', r'ارتفاع'),
        ('گزارش خاک', r'خاک|ژئوتکنیک'),
        ('سیستم سازه', r'فولاد|بتن|اسکلت|سازه'),
    ],
    'mechanical': [
        ('تعداد نفرات یا بار حرارتی', r'\d+\s*نفر|کارمند|کارکنان|بار حرارتی'),
        ('سرمایش / گرمایش / تهویه', r'سرمایش|گرمایش|تهویه|تهیه\s*مطبوع|هوای تازه'),
        ('سرویس‌های آب و فاضلاب', r'آب|فاضلاب|سرویس بهداشتی|تخلیه'),
    ],
    'electrical': [
        ('فهرست تجهیزات برقی', r'برق|تجهیزات|دستگاه|کامپیوتر|پوز|شبکه|دوربین'),
        ('روشنایی', r'روشنایی|لامپ|نورپردازی|نور'),
        ('برق اضطراری / تابلو', r'اضطراری|تابلو|ژنراتور|یو‌پی‌اس|یوپی‌اس'),
    ],
    'fire_safety': [
        ('کاربری و جمعیت', r'فروشگاه|انبار|کاربری|نفر|جمعیت'),
        ('مسیر خروج', r'خروج'),
        ('مواد قابل اشتعال', r'روغن|سوخت|مواد قابل اشتعال|مواد شیمیایی|باتری'),
    ],
    'cost': [
        ('ابعاد برای متره', r'\d+(?:\.\d+)?\s*(?:متر)?\s*[×xX*]\s*\d+'),
        ('ارتفاع برای دیوار', r'ارتفاع'),
        ('بودجه یا سطح کیفیت', r'بودجه|سطح کیفیت|میلیون|میلیارد|تومان|دلار'),
    ],
    'compliance': [
        ('شهر / موقعیت', r'تهران|شهر|کشور|استان|منطقه'),
        ('مدارک مالکیت یا مجوز', r'مالک|مجوز|سند|پروانه'),
        ('ضوابط شهرسازی', r'ضوابط|تراکم|عقب‌نشینی|عقب نشینی|کاربری مجاز'),
    ],
}

def _normalize(text: str) -> str:
    return (text or '').translate(_DIGITS).lower()

def checklist_for(discipline: str, brief: str) -> dict[str, Any]:
    """Return the inputs found and missing for a discipline. Unknown discipline raises KeyError."""
    if discipline not in REQUIREMENTS:
        raise KeyError(f'unknown discipline: {discipline}')
    text = _normalize(brief)
    present, missing = [], []
    for label, pattern in REQUIREMENTS[discipline]:
        (present if re.search(pattern, text) else missing).append(label)
    total = len(REQUIREMENTS[discipline])
    return {
        'tool': 'discipline_checklist',
        'discipline': discipline,
        'present': present,
        'missing': missing,
        'completeness': round(len(present) / total, 2) if total else None,
        'note': 'بررسی واژگانی ساده؛ نبودِ یک واژه به معنی نبودِ اطلاعات نیست و تأیید مهندسی نیست.',
    }

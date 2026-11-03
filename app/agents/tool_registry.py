"""Small, explicit local tool registry. Tools are deterministic and do not perform external writes."""
from dataclasses import dataclass
from typing import Callable, Any
import re

@dataclass(frozen=True)
class ToolSpec:
    id: str
    name: str
    description: str
    local_or_online: str
    requires_approval: bool = False

TOOLS = {
    'document_reader': ToolSpec('document_reader','خواندن سند','استخراج متن از PDF, DOCX, XLSX, PPTX و متن‌های رایج','local'),
    'area_calculator': ToolSpec('area_calculator','محاسبه‌گر مساحت','محاسبه‌ی ساده‌ی مساحت از عرض و طول واردشده؛ بدون محاسبه‌ی سازه','local'),
    'quantity_takeoff': ToolSpec('quantity_takeoff','متره‌ی هندسی','محاسبه‌ی کف، محیط و سطح دیوار از ابعاد و ارتفاع؛ بدون قیمت و بدون کسر بازشوها','local'),
    'concept_svg': ToolSpec('concept_svg','دیاگرام SVG','ساخت دیاگرام شماتیک مفهومی از ابعاد و فضاهای ورودی','local'),
    'discipline_checklist': ToolSpec('discipline_checklist','چک‌لیست رشته‌ای','ساخت فهرست اطلاعات و ملاحظات برای رشته‌ی تخصصی','local'),
    'online_model': ToolSpec('online_model','مدل زبانی آنلاین','ارسال درخواست به API سازگار انتخاب‌شده توسط کاربر','online'),
    'workflow_monitor': ToolSpec('workflow_monitor','پایش گردش کار','نمایش وضعیت ایجنت‌ها و مسیر رخدادها','local'),
}
AGENT_TOOLS = {
    'architecture':['document_reader','area_calculator','concept_svg','online_model','workflow_monitor'],
    'interior':['document_reader','concept_svg','online_model','workflow_monitor'],
    'structure':['document_reader','discipline_checklist','online_model','workflow_monitor'],
    'mechanical':['document_reader','discipline_checklist','online_model','workflow_monitor'],
    'electrical':['document_reader','discipline_checklist','online_model','workflow_monitor'],
    'fire_safety':['document_reader','discipline_checklist','online_model','workflow_monitor'],
    'cost':['document_reader','area_calculator','quantity_takeoff','discipline_checklist','online_model','workflow_monitor'],
    'compliance':['document_reader','discipline_checklist','online_model','workflow_monitor'],
}

def catalog(agents):
    return [{
        'id': agent_id,
        'name': agent.info.name,
        'discipline': agent.info.discipline,
        'description': agent.info.description,
        'status_scope': 'مفهومی؛ بازبینی متخصص لازم است',
        'tools': [TOOLS[tool_id].__dict__ for tool_id in AGENT_TOOLS.get(agent_id, [])]
    } for agent_id, agent in agents.items()]

def normalize_digits(text: str) -> str:
    return text.translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩','01234567890123456789'))

def area_tool_from_text(text: str) -> dict[str, Any] | None:
    """Extract explicit LxW values and calculate area only when units/intent are clear."""
    normalized=normalize_digits(text.lower())
    if not any(word in normalized for word in ['متر','area','مساحت','ابعاد']):
        return None
    match=re.search(r'(?<!\d)(\d+(?:\.\d+)?)\s*(?:متر)?\s*[×xX*]\s*(\d+(?:\.\d+)?)\s*(?:متر)?', normalized)
    if not match:
        return None
    a,b=float(match.group(1)),float(match.group(2))
    if a<=0 or b<=0 or a>10000 or b>10000:
        return None
    return {'tool':'area_calculator','width_or_side_a_m':a,'length_or_side_b_m':b,'area_m2':a*b,'note':'مساحت مستطیلی ساده؛ بدون لحاظ بازشوها یا محدودیت‌های طراحی.'}

def takeoff_from_text(text: str) -> dict[str, Any] | None:
    """Geometric quantity takeoff from explicit width x length (and optional height). No prices, no openings."""
    normalized = normalize_digits(text.lower())
    if not any(word in normalized for word in ['متره','برآورد','دیوار','کف','ارتفاع','هزینه']):
        return None
    match = re.search(r'(?<!\d)(\d+(?:\.\d+)?)\s*(?:متر)?\s*[×xX*]\s*(\d+(?:\.\d+)?)\s*(?:متر)?', normalized)
    if not match:
        return None
    width, length = float(match.group(1)), float(match.group(2))
    if not (0 < width <= 10000 and 0 < length <= 10000):
        return None
    result: dict[str, Any] = {'tool': 'quantity_takeoff', 'floor_area_m2': round(width * length, 2), 'perimeter_m': round(2 * (width + length), 2)}
    height_match = re.search(r'ارتفاع\D{0,20}?(\d+(?:\.\d+)?)', normalized)
    if height_match:
        height = float(height_match.group(1))
        if 0 < height <= 100:
            result['height_m'] = height
            result['wall_area_m2'] = round(result['perimeter_m'] * height, 2)
            result['ceiling_area_m2'] = result['floor_area_m2']
    result['note'] = 'تخمین هندسی ساده؛ بازشوها، ستون‌ها، کسری‌ها و قیمت لحاظ نشده‌اند.'
    return result

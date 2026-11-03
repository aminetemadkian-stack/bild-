from app.agents.base import DesignAgent
from app.models.schemas import AgentInfo, Project, AgentResult
from app.core.config import settings
from app.agents.llm_client import generate_agent_result

DISCLAIMER = "خروجی مفهومی و نیازمند بازبینی متخصص دارای صلاحیت است؛ برای ساخت، مجوز یا محاسبه‌ی مهندسی استفاده نشود."

class ConceptAgent(DesignAgent):
    def __init__(self, info: AgentInfo, summary_fn):
        self.info, self.summary_fn = info, summary_fn
    def run(self, project: Project) -> AgentResult:
        if settings.llm_provider.lower() in {"openai_compatible", "openai-compatible"}:
            return generate_agent_result(project, self.info)
        if settings.llm_provider.lower() != "demo":
            raise RuntimeError("Unsupported LLM_PROVIDER. Use demo or openai_compatible.")
        summary, findings, assumptions = self.summary_fn(project)
        return AgentResult(agent_id=self.info.id, status="completed", summary=summary, findings=findings, assumptions=assumptions, needs_professional_review=True)

def area_text(p: Project) -> str:
    if p.site.width_m and p.site.length_m:
        return f"ابعاد ثبت‌شده {p.site.width_m:g}×{p.site.length_m:g} متر، مساحت مستطیلی تقریبی {p.site.width_m*p.site.length_m:g} مترمربع"
    return f"مساحت اعلامی {p.site.area_m2:g} مترمربع" if p.site.area_m2 else "ابعاد زمین هنوز ثبت نشده"

def architecture(p):
    spaces = "، ".join(p.spaces) if p.spaces else "برنامه‌ی فضایی هنوز کامل نشده"
    return ("پیشنهاد جانمایی مفهومی بر اساس نوع پروژه و نیازهای ثبت‌شده.", [area_text(p), f"فضاهای درخواستی: {spaces}"], ["ابعاد زمین، جهت، ورودی‌ها و ضوابط شهرسازی تأیید نشده‌اند."])
def interior(p):
    spaces = "، ".join(p.spaces) if p.spaces else "فضاهای داخلی باید با کارفرما تعیین شوند"
    return ("چارچوب اولیه‌ی طراحی داخلی و تجربه‌ی کاربر.", [f"فضاهای لحاظ‌شده: {spaces}", "متریال، نور، مبلمان و دسترس‌پذیری باید در مرحله‌ی طراحی توسعه یابند."], ["سلیقه‌ی بصری، بودجه، نمونه‌ی متریال و نیازهای بهره‌برداری دریافت نشده‌اند."])
def structure(p):
    return ("هماهنگی اولیه‌ی رشته‌ی سازه؛ محاسبه یا انتخاب سیستم سازه انجام نشده است.", ["برای طراحی، گزارش خاک، شبکه‌ی ستون، بارها، مصالح و الزامات محل لازم است."], ["هیچ ابعاد یا عضو سازه‌ای از این خروجی قابل برداشت نیست."])
def mechanical(p):
    return ("فهرست اولیه‌ی هماهنگی مکانیک ساختمان.", ["نیاز سرمایش/گرمایش، تهویه، هوای تازه، آب، فاضلاب و تخلیه باید مشخص شود."], ["ظرفیت‌گذاری و مسیرگذاری تأسیسات انجام نشده است."])
def electrical(p):
    return ("فهرست اولیه‌ی هماهنگی برق و جریان ضعیف.", ["روشنایی، پریز، تابلو، ارت، شبکه، امنیت و برق اضطراری باید با کاربری هماهنگ شوند."], ["بار، مدار، کابل و تجهیزات محاسبه نشده‌اند."])
def fire(p):
    return ("نقاط نیازمند بررسی ایمنی حریق و خروج.", ["کاربری، جمعیت، بار حریق، مسیرهای خروج، اعلام و اطفا باید طبق ضوابط مرجع محلی بررسی شوند."], ["این ماژول تأییدیه‌ی آتش‌نشانی یا طراحی سیستم اطفا صادر نمی‌کند."])
def cost(p):
    return ("چارچوب متره و برآورد؛ قیمت یا مقدار ساخت محاسبه نشده است.", ["برای برآورد باید نقشه‌های مصوب، مشخصات مصالح، مقادیر و قیمت روز تهیه شود."], ["بودجه، سطح کیفیت و بازار محلی مشخص نشده‌اند."])
def compliance(p):
    return ("چک‌لیست ضوابط برای پیگیری توسط تیم پروژه.", [f"موقعیت اعلامی: {p.location}", "کاربری، مجوزها، دسترسی، انرژی، ایمنی و ضوابط محلی باید از مراجع رسمی بررسی شوند."], ["این سرویس به‌روزرسانی یا تأیید خودکار قوانین محلی ندارد."])

AGENT_DEFS = [
 ("architecture", "ایجنت معماری", "معماری", "برنامه‌ریزی فضا و جانمایی مفهومی", "طرح مفهومی، نه نقشه‌ی اجرایی", architecture),
 ("interior", "ایجنت طراحی داخلی", "طراحی داخلی", "تجربه‌ی فضا، متریال، نور و مبلمان", "مفهوم داخلی، نه دیتیل ساخت", interior),
 ("structure", "ایجنت هماهنگی سازه", "سازه", "جمع‌آوری ورودی‌های لازم برای تیم سازه", "چک‌لیست؛ بدون محاسبات", structure),
 ("mechanical", "ایجنت مکانیک", "تأسیسات مکانیکی", "هماهنگی نیازهای تهویه و لوله‌کشی", "چک‌لیست مفهومی؛ بدون سایزینگ", mechanical),
 ("electrical", "ایجنت برق", "برق و جریان ضعیف", "هماهنگی روشنایی، برق و فناوری", "چک‌لیست مفهومی؛ بدون محاسبه", electrical),
 ("fire_safety", "ایجنت حریق و ایمنی", "ایمنی", "ثبت موضوعات نیازمند بررسی حریق و خروج", "یادآور؛ نه تأییدیه یا طراحی حریق", fire),
 ("cost", "ایجنت متره و برآورد", "هزینه", "تعریف ورودی‌های لازم برای برآورد", "چارچوب؛ بدون قیمت قطعی", cost),
 ("compliance", "ایجنت کنترل الزامات", "ضوابط", "چک‌لیست بررسی محلی", "چک‌لیست؛ نه تفسیر حقوقی یا تأیید", compliance),
]
AGENTS = {aid: ConceptAgent(AgentInfo(id=aid,name=name,discipline=disc,description=desc,output_scope=scope), fn) for aid,name,disc,desc,scope,fn in AGENT_DEFS}

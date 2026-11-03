from app.agents.concept_agents import AGENTS

def test_agents_are_registered():
    assert {"architecture", "interior", "structure", "mechanical", "electrical", "fire_safety", "cost", "compliance"} <= set(AGENTS)

def test_agent_tool_catalog_has_tools_for_every_agent():
    from app.agents.tool_registry import AGENT_TOOLS, TOOLS
    assert set(AGENTS) <= set(AGENT_TOOLS)
    assert all(tool_id in TOOLS for tool_ids in AGENT_TOOLS.values() for tool_id in tool_ids)

def test_area_tool_reads_persian_dimensions():
    from app.agents.tool_registry import area_tool_from_text
    result = area_tool_from_text("مساحت سوله با ابعاد ۲۵×۶۰ متر را حساب کن")
    assert result["area_m2"] == 1500
    assert result["tool"] == "area_calculator"

def test_area_tool_does_not_guess_without_dimensions():
    from app.agents.tool_registry import area_tool_from_text
    assert area_tool_from_text("برای فروشگاه برنامه فضا بده") is None

def test_takeoff_computes_floor_perimeter_and_walls():
    from app.agents.tool_registry import takeoff_from_text
    result = takeoff_from_text("متره دیوار سوله ۲۵×۶۰ متر با ارتفاع ۳ متر")
    assert result["floor_area_m2"] == 1500
    assert result["perimeter_m"] == 170
    assert result["wall_area_m2"] == 510

def test_takeoff_does_not_guess_without_dimensions():
    from app.agents.tool_registry import takeoff_from_text
    assert takeoff_from_text("برآورد هزینه ساخت کلی بده") is None

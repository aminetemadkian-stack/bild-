"""Minimal stdlib DXF (R12) writer for concept plans. Labels are ASCII to avoid codepage issues in CAD."""

def _pair(code, value):
    return f"{code}\n{value}\n"

def _line(x1, y1, x2, y2, layer):
    return "".join([_pair(0,"LINE"),_pair(8,layer),_pair(10,f"{x1:.3f}"),_pair(20,f"{y1:.3f}"),_pair(30,"0.0"),_pair(11,f"{x2:.3f}"),_pair(21,f"{y2:.3f}"),_pair(31,"0.0")])

def _text(x, y, height, value, layer):
    safe = "".join(ch for ch in str(value) if 32 <= ord(ch) < 127)
    return "".join([_pair(0,"TEXT"),_pair(8,layer),_pair(10,f"{x:.3f}"),_pair(20,f"{y:.3f}"),_pair(30,"0.0"),_pair(40,f"{height:.3f}"),_pair(1,safe)])

def concept_dxf(width: float, length: float, height: float, store_depth: float, name: str = "CONCEPT") -> str:
    shelf_count = 3 if width > 10 and length > 12 else 0
    body = []
    body.append(_line(0,0,width,0,"WALLS")); body.append(_line(width,0,width,length,"WALLS"))
    body.append(_line(width,length,0,length,"WALLS")); body.append(_line(0,length,0,0,"WALLS"))
    body.append(_line(0,store_depth,width,store_depth,"WALLS"))
    for i in range(shelf_count):
        x = width * (0.27 + i * 0.23)
        body.append(_line(x, store_depth + 2, x, length - 2, "SHELVES"))
    body.append(_text(width/2, store_depth/2, 0.6, "FRONT / PUBLIC ZONE", "TEXT"))
    body.append(_text(width/2, store_depth + (length-store_depth)/2, 0.6, "STORAGE / WORK ZONE", "TEXT"))
    body.append(_text(0, -2.0, 0.5, f"{name} | {width:g} x {length:g} m | clear height {height:g} m", "TEXT"))
    body.append(_text(0, -3.0, 0.5, "CONCEPT ONLY - NOT FOR PERMIT OR CONSTRUCTION", "TEXT"))
    header = _pair(0,"SECTION") + _pair(2,"HEADER") + _pair(9,"$ACADVER") + _pair(1,"AC1009") + _pair(0,"ENDSEC")
    entities = _pair(0,"SECTION") + _pair(2,"ENTITIES") + "".join(body) + _pair(0,"ENDSEC")
    return header + entities + _pair(0,"EOF")

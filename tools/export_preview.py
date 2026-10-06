"""Render the actual Lua panel layout as HTML, without claiming native engine QA."""
from pathlib import Path
from html import escape
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / '.test-tools'))
from lupa.lua51 import LuaRuntime

lua = LuaRuntime(unpack_returned_tuples=True)
lua.globals().mod_path = (root / 'Memorial Ledger').as_posix()
lua.execute("package.path = mod_path .. '/?.lua;' .. package.path")
for name in ('mock_openmw.lua', 'mock_player.lua'):
    lua.execute((root / 'tests' / name).read_text(encoding='utf-8'))
lua.execute("""
    panel = require('scripts.memorial_ledger.player'); panel.interface.open()
    local token = globalEvents[#globalEvents].data.token
    local names = {'Fallen adventurer', 'Ashlander scout', 'Bandit', 'Temple pilgrim', 'Smuggler', 'Dunmer traveler', 'Imperial soldier'}
    local statuses = {'Observed', 'Observed', 'Observed', 'Unavailable', 'Removed', 'Revived', 'Observed'}
    local places = {'Balmora', 'Ashlands [3, 8]', 'Addamasartus', 'Molag Mar', 'Bitter Coast [-2, -5]', 'West Gash [0, 2]', 'Seyda Neen'}
    previewRows = {}
    for i=1,7 do previewRows[i]={id=i,name=names[i],location=places[i],status=statuses[i],note='',observedAt=118800} end
    panel.eventHandlers.MemorialLedgerSnapshot({rows=previewRows,total=31,matches=31,page=1,pages=5,token=token})
""")


def bounds(node):
    props = node['props']
    size = props['size'] if props else None
    if size:
        return size['x'], size['y']
    width = height = 0
    if node['content']:
        for _, child in node['content'].items():
            child_width, child_height = bounds(child)
            pos = child['props']['position'] if child['props'] else None
            width = max(width, child_width + (pos['x'] if pos else 0))
            height = max(height, child_height + (pos['y'] if pos else 0))
    return width, height


def render(node, is_root=False):
    props = node['props']
    kind = node['type'] or ''
    css = ['position:absolute', 'box-sizing:border-box']
    if props:
        pos, size = props['position'], props['size']
        if pos:
            css += [f'left:{pos["x"]}px', f'top:{pos["y"]}px']
        if size:
            css += [f'width:{size["x"]}px', f'height:{size["y"]}px']
        if props['textAlignH'] == 'Center':
            css += ['text-align:center', 'line-height:28px']
        if props['textSize']:
            css += [f'font-size:{props["textSize"]}px']
    classes = [kind.lower()]
    if kind == 'Container' and not is_root:
        classes += ['border']
        if not props or not props['size']:
            width, height = bounds(node)
            css += [f'width:{width + 4}px', f'height:{height + 4}px']
    if is_root:
        width, height = bounds(node)
        css += ['position:relative', f'width:{width}px', f'height:{height}px']
    value = props['text'] if props else None
    content = escape(str(value)).replace('\n', '<br>') if value is not None else ''
    children = node['content']
    if children:
        content += ''.join(render(child) for _, child in children.items())
    return f'<div class="{" ".join(classes)}" style="{";".join(css)}">{content}</div>'


HTML_START = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Memorial Ledger | Lua Layout Preview</title><style>
body{margin:0;background:#101412;color:#dbd5ba;font-family:Georgia,serif;display:grid;place-items:center;min-height:100vh}
.container{background:#000}.border{border:1px solid #827659;background:#000}
.text{overflow:hidden;white-space:normal;font-size:16px;line-height:22px}
.textedit{background:#000;padding:3px;overflow:hidden}
.image{background:#827659}
.widget{background:transparent}.container>.widget{border:1px solid #827659}
</style><body>'''


def write_preview(name):
    target = root / 'reports' / f'{name}.html'
    target.write_text(HTML_START + render(lua.globals().uiState.element.layout, True) + '</body></html>', encoding='utf-8')
    print(target)


def show_detail():
    lua.execute("""
        uiState.element.layout.content[1].content[4].events.mouseClick()
        local token = globalEvents[#globalEvents].data.token
        panel.eventHandlers.MemorialLedgerSnapshot({rows=previewRows,selected=previewRows[1],total=31,matches=31,page=1,pages=5,token=token})
    """)


write_preview('memorial-ledger-panel')
show_detail()
write_preview('memorial-ledger-detail')
lua.execute("""
    panel.interface.open(); uiState.width,uiState.height = 640,480; panel.interface.open()
    local rows = {}; for i=1,4 do rows[i] = previewRows[i] end
    panel.eventHandlers.MemorialLedgerSnapshot({rows=rows,total=31,matches=31,page=1,pages=8,token=globalEvents[#globalEvents].data.token})
""")
write_preview('memorial-ledger-panel-compact')
show_detail()
write_preview('memorial-ledger-detail-compact')
lua.execute("uiState.width,uiState.height = 1920,1080; settingsPanel = require('scripts.memorial_ledger.menu')")
write_preview('memorial-ledger-settings')
lua.execute("uiState.width,uiState.height = 640,480; settingsPanel.engineHandlers.onFrame()")
write_preview('memorial-ledger-settings-compact')

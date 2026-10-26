"""Render a layout proposal only; does not change firmware or existing previews."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'tools/make_ui_preview.py'
code=source.read_text(encoding='utf8').split('\noverview=',1)[0]
code=code.replace(" text(8,4,title,'#49d2ff',2);text(260,5,mode,'#f7b84b' if 'RX:' in mode else '#9cb4be')", """ d.rectangle((4,0,235,21),fill='#101b20',outline='#49d2ff')
 d.rectangle((244,0,475,21),fill='#101b20',outline='#49d2ff')
 text(12,7,title,'#49d2ff',1);text(220,7,'>','#49d2ff')
 text(260,7,mode,'#f7b84b' if 'RX:' in mode else '#ffffff')
 text(460,7,'>','#49d2ff')""")
ns={'__file__':str(source)}
exec(compile(code,str(source),'exec'),ns)
rows=json.loads((ROOT/'docs/overview.json').read_text(encoding='utf8'))
rows=[(r['id'],r['label'],r['sample']) for r in rows]
for name,mode in [('display_modell_entwurf.png','AUTO / AKTIV'),('display_modell_rx_entwurf.png','AUTO / RX: LISTEN ONLY')]:
 ns['image_page'](name,rows,'Uebersicht',0,len(rows),mode)
print('Model header proposal: 6x8 font; 20 rows; no firmware changes')

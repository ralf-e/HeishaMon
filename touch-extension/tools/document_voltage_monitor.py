"""Generate the Rev07 connection sheet from the verified design, no PCB edits."""
from pathlib import Path
import collections,html,json
from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,TableStyle,Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A3,landscape
R=Path(__file__).resolve().parents[1];H=R/'hardware/Rev07'
d=json.loads((H/'netlist_design.json').read_text());v=json.loads((H/'validation_summary.json').read_text())
assert v['drc_violations']==v['erc_violations']==v['unconnected_items']==0
nets=collections.defaultdict(list)
for c in d['components']:
 for pin,net in c['nets'].items():
  if net:nets[net].append(c['ref']+'.'+pin)
md=['# Rev.0.7 - Verbindungsmatrix','', 'J6/J7 sind externe W5500-Gegenkontakte, keine zusätzlichen PCB-Bauteile.','', '| Netz | Alle verbundenen Kontakte |','| --- | --- |']
md += ['| '+n+' | '+', '.join(sorted(pins))+' |' for n,pins in sorted(nets.items())]
(H/'connection_matrix.md').write_text('\n'.join(md)+'\n',encoding='utf8')
body=ParagraphStyle('body',fontName='Helvetica',fontSize=8.5,leading=11)
small=ParagraphStyle('small',fontName='Helvetica',fontSize=10,leading=14,spaceAfter=8)
title=ParagraphStyle('title',fontName='Helvetica-Bold',fontSize=18,leading=24,spaceAfter=12)
rows=[[Paragraph('Netz',body),Paragraph('Alle elektrisch verbundenen Kontakte (Bauteil.Pin)',body)]]
rows += [[Paragraph(html.escape(n),body),Paragraph(', '.join(sorted(pins)),body)] for n,pins in sorted(nets.items())]
table=Table(rows,colWidths=[180,930],repeatRows=1)
table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dcecf2')),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#a8bac5')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3)]))
story=[Paragraph('HeishaMon V6 Touch Rev.0.7 - Gesamtverdrahtung',title),Paragraph('23 x 41 mm, 2 Lagen. ERC 0 / DRC 0 / 0 offene Verbindungen. Hardwaretest und Fertigungsfreigabe ausstehend.',small),table,Spacer(1,10),
 Paragraph('AIN0 = 3V3_V6 vor R0; AIN1 = 3V3_EXT nach R0; AIN2 = 5V_V6; AIN3 = TP5, externe 12-V-Messleitung (0..18 V positiv). Bei gemeinsamer V6-/Adaptermasse ist nur diese eine zusaetzliche Leitung noetig; GND besteht bereits ueber die Steckkontakte. TP6 ist ein optionaler GND-Loet-/Pruefpunkt, keine zusaetzlich erforderliche Masseleitung. TP5 ist kein Versorgungseingang.',small),
 Paragraph('U1: MCP23008-E/SS, SSOP-20. U2: ADS1115IDGSR, Adresse 0x48. U3: TMUX1511PWR. U4: TLV809EA29DCKR. ADC_ENABLE an MCP-GP0: Low bedeutet ungueltige Messung / Unterspannung.',small),
 Paragraph('Alle gleichnamigen Netze sind verbunden. J1/J2/J3/J4 und die Einbaulage entsprechen Rev.0.6. V6-Kontakte vor Anschluss am realen Board messen. Die Firmware dev.7 enthaelt noch keine ADC-Auswertung.',small)]
SimpleDocTemplate(str(H/'Gesamtverdrahtung_rev07.pdf'),pagesize=landscape(A3),leftMargin=40,rightMargin=40,topMargin=30,bottomMargin=30).build(story)
print('Rev07 connection matrix and PDF generated')

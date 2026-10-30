"""Rev.0.7 component extension; executed by design_adapter.py --voltage.

All four ADS inputs are divided and isolated by TMUX1511 when EXT power is off.
TLV809EA29DCKR keeps switches open below its 2.93-V threshold.
Datasheet pin assignments are deliberately explicit.
"""

def custom_symbol(name, pins, footprint):
 sym=['symbol',Q(name),['pin_names',['offset',0.508]],['in_bom','yes'],['on_board','yes']]
 half_height=5.08 if len(pins)==3 else 12.7
 for prop,val in [('Reference','U'),('Value',name),('Footprint',footprint)]:
  ay=half_height+5.08 if prop=='Reference' else half_height+2.54 if prop=='Value' else 0
  sym.append(['property',Q(prop),Q(val),['at',0,ay,0],effects(1.27,hide=prop=='Footprint')])
 body=['symbol',Q(name+'_0_1'),['rectangle',['start',-5.08,half_height],['end',5.08,-half_height],['stroke',['width',.254],['type','default']],['fill',['type','background']]]]
 sym.append(body)
 unit=['symbol',Q(name+'_1_1')]
 for i,(num,label,typ) in enumerate(pins):
  side=0 if i<(len(pins)+1)//2 else 1
  row=i if side==0 else i-(len(pins)+1)//2
  unit.append(['pin',typ,'line',['at',-10.16 if side==0 else 10.16,(2.54 if len(pins)==3 else 10.16)-row*2.54,0 if side==0 else 180],['length',5.08],
   ['name',Q(label),effects(1.0)],['number',Q(str(num)),effects(1.0)]])
 sym.append(unit);cache['HMX_Power:'+name]=sym
 comps.append(dict(ref={'TMUX1511PWR':'U3','TLV809EA29DCKR':'U4'}[name],lib_id='HMX_Power:'+name,symbol=copy.deepcopy(sym),value=name,footprint=footprint,nets={},at=(450,100),boardat=(110.16,120),rot=0,schrot=0,uuid=uid()))
 return comps[-1]

adc_nets={1:'GND',2:None,3:'GND',4:'ADC_A0',5:'ADC_A1',6:'ADC_A2',7:'ADC_A3',8:'+3V3_EXT',9:'I2C_SDA',10:'I2C_SCL'}
add('U2','Analog_ADC','ADS1115IDGS','ADS1115IDGSR','Package_SO:TSSOP-10_3x3mm_P0.5mm',adc_nets,(448.31,76.2),(110.16,114.3))
comps[-1]['schrot']=0
sw=custom_symbol('TMUX1511PWR',[(1,'SEL1','input'),(2,'S1','passive'),(3,'D1','passive'),(4,'SEL2','input'),(5,'S2','passive'),(6,'D2','passive'),(7,'GND','power_in'),(8,'D3','passive'),(9,'S3','passive'),(10,'SEL3','input'),(11,'D4','passive'),(12,'S4','passive'),(13,'SEL4','input'),(14,'VDD','power_in')],'Package_SO:TSSOP-14_4.4x5mm_P0.65mm')
sw.update(at=(447.04,142.24),boardat=(110.16,121.2))
sw['nets']={'1':'ADC_ENABLE','4':'ADC_ENABLE','10':'ADC_ENABLE','13':'ADC_ENABLE','7':'GND','14':'+3V3_EXT'}
for ch,(s_pin,d_pin) in enumerate([(2,3),(5,6),(9,8),(12,11)]):sw['nets'].update({str(s_pin):'DIV'+str(ch),str(d_pin):'ISO'+str(ch)})
supervisor=custom_symbol('TLV809EA29DCKR',[(1,'GND','power_in'),(2,'~{RESET}','output'),(3,'VDD','power_in')],'Package_TO_SOT_SMD:SOT-323_SC-70')
supervisor.update(at=(537.21,76.2),boardat=(118.1,119.1),nets={'1':'GND','2':'ADC_ENABLE','3':'+3V3_EXT'})
u1=next(c for c in comps if c['ref']=='U1')
old_by_name={pin['name']:u1['nets'][pin['number']] for pin in getpins(u1['symbol']) if pin['name']!='NC'}
old_by_name['GP0']='ADC_ENABLE'
u1['lib_id'],u1['symbol']=symbol('Interface_Expansion','MCP23008-xSS')
u1['value']='MCP23008-E/SS';u1['footprint']='Package_SO:SSOP-20_5.3x7.2mm_P0.65mm'
u1['nets']={pin['number']:old_by_name.get(pin['name']) for pin in getpins(u1['symbol'])}

for ch,(rail,top,maximum) in enumerate([('+3V3_V6',10000,3.6),('+3V3_EXT',10000,3.6),('+5V_V6',20000,5.5),('+12V_SENSE',68000,18.0)]):
 x=105.7+3*ch
 # The source divider remains connected when the isolation switch is open.
 defs=[(12+ch*4,top,rail,'DIV'+str(ch)),(13+ch*4,10000,'DIV'+str(ch),'GND'),
       (14+ch*4,1000,'ISO'+str(ch),'ADC_A'+str(ch)),(15+ch*4,100000,'ADC_A'+str(ch),'GND')]
 for row,(n,r,a,b) in enumerate(defs):
  add('R'+str(n),'Device','R',str(r)+' 0.1%','Resistor_SMD:R_0603_1608Metric',{1:a,2:b},(69.85+ch*100.33,292.1+row*25.4),(x,126+row*1.7))
  comps[-1]['schrot']=0
 add('C'+str(7+ch),'Device','C','100n 25V','Capacitor_SMD:C_0603_1608Metric',{1:'DIV'+str(ch),2:'GND'},(69.85+ch*100.33,393.7),(x,132.8))
 comps[-1]['schrot']=0

for ref,pos,at in [('C4',(114.3,112.4),(448.31,226.06)),('C5',(114.5,119.2),(481.33,226.06)),('C6',(118,120.5),(537.21,226.06))]:
 add(ref,'Device','C','100n 16V','Capacitor_SMD:C_0603_1608Metric',{1:'+3V3_EXT',2:'GND'},at,pos)
 comps[-1]['schrot']=0

# Existing connector positions and board outline are intentionally unchanged.
placement={
 'R1':(105.5,114.3),'R2':(105.5,118.5),'R3':(105.5,122.7),
 'R5':(114.8,114.3),'R6':(114.8,118.5),'R7':(114.8,122.7),
 'R10':(118.1,116.2),'R11':(118.1,111.4),'C2':(118.1,124),'C3':(118.1,113.8),
}
for c in comps:
 if c['ref'] in placement:
  c['boardat']=placement[c['ref']]
  if c['ref'].startswith('R') and c['ref'] not in ['R10','R11']:c['rot']=90

for ref,net,x in [('TP5','+12V_SENSE',114.3),('TP6','GND',116.8)]:
 add(ref,'Connector','TestPoint',net,'TestPoint:TestPoint_THTPad_D1.5mm_Drill0.7mm',{1:net},(514.35 if ref=='TP5' else 552.45,269.24),(x,134.7))
 comps[-1]['schrot']=0

# Native project library for the two parts missing from the stock KiCad library.
local=['kicad_symbol_lib',['version',20241209],['generator',Q('eeschema')]]
for key in ['HMX_Power:TMUX1511PWR','HMX_Power:TLV809EA29DCKR']:
 sym=copy.deepcopy(cache[key]);sym[1]=Q(key.split(':')[1]);local.append(sym)
(OUT/'HMX_Power.kicad_sym').write_text(emit(local)+'\n',encoding='utf8')
(OUT/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "HMX_Power") (type "KiCad") (uri "${KIPRJMOD}/HMX_Power.kicad_sym") (options "") (descr "HMX voltage monitor")))\n')

measurement_spec=dict(adc='ADS1115IDGSR',address='0x48',supply='+3V3_EXT',switch='TMUX1511PWR',supervisor='TLV809EA29DCKR',supervisor_threshold_v=2.93,validity_input='MCP23008 GP0: high = measurement enabled; low = undervoltage / invalid',
 channels=[dict(channel=i,rail=rail,r_top_ohm=top,r_bottom_ohm=10000,r_series_ohm=1000,r_pulldown_ohm=100000,max_source_v=maximum) for i,(rail,top,maximum) in enumerate([('+3V3_V6',10000,3.6),('+3V3_EXT',10000,3.6),('+5V_V6',20000,5.5),('+12V_SENSE',68000,18)])],
 external_input='TP5 +12V_SENSE: one extra measurement wire when V6/adapter share connector GND; TP6 optional GND solder/test point; not a power input',hardware_tested=False,firmware_support=False)
(OUT/'voltage_monitor.json').write_text(json.dumps(measurement_spec,indent=2)+'\n')
placement_file=OUT/'component_placement.json'
if placement_file.exists():
 placements=json.loads(placement_file.read_text())
 for c in comps:
  if c['ref'] in placements:
   c['boardat']=placements[c['ref']]['xy'];c['rot']=placements[c['ref']]['rotation']

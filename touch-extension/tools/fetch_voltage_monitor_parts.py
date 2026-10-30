"""Read public supplier facts for Rev07; no upload, account action or order.

Run with ordinary Python and network access. Persist selected public fields only;
temporary signed datasheet URLs and account-related fields are never saved.
"""
from pathlib import Path
from datetime import datetime, timezone
import json
import urllib.request

R = Path(__file__).resolve().parents[1]
H = R / 'hardware/Rev07'
parts = json.loads((H / 'parts_catalogue.json').read_text())['parts']

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'HeishaMon-Rev07-design-review/1.0'})
    with urllib.request.urlopen(req, timeout=45) as response:
        return json.load(response)

stocks, packages = [], []
for part in parts:
    code = part['code']
    url = 'https://jlcpcb.com/api/overseas-pcb-order/v1/smtComponentShopCart/getComponentDetail?componentCode=' + code
    reply = get(url)
    assert reply['code'] == 200, (code, reply.get('message'))
    d = reply['data']
    assert d['componentCode'] == code and d['componentModelEn'] == part['mpn'], (code, d['componentModelEn'])
    stocks.append(dict(code=code, mpn=d['componentModelEn'], refs=part['refs'],
                       package=d['componentSpecificationEn'], description=d['describe'],
                       warehouse_stock=d['stockCount'], available_order_quantity=d['canPresaleNumber'],
                       component_status=d['componentStatus'], assembly_process=d['assemblyProcess'],
                       minimum_purchase=d['minPurchaseNum'], attrition_quantity=d['lossNumber'],
                       checked_at=datetime.now(timezone.utc).isoformat(), source_url=url))
    if part['refs'][0] in ['U1', 'U2', 'U3', 'U4', 'J4']:
        url = 'https://easyeda.com/api/products/' + code + '/components'
        e = get(url)
        assert e['success']
        package = e['result']['packageDetail']
        data = package['dataStr']
        if isinstance(data, str):
            data = json.loads(data)
        head = data['head']
        pads = []
        for shape in data['shape']:
            f = shape.split('~')
            if f[0] == 'PAD':
                # EasyEDA standard internal length unit: 10 mil = 0.254 mm.
                pads.append(dict(number=f[8], x_mm=round((float(f[2])-float(head['x']))*.254, 6),
                                 y_mm=round((float(f[3])-float(head['y']))*.254, 6)))
        packages.append(dict(code=code, ref=part['refs'][0], package=package['title'],
                             package_uuid=package['uuid'], pads=pads, source_url=url,
                             checked_at=datetime.now(timezone.utc).isoformat()))
    print(code, stocks[-1]['available_order_quantity'], flush=True)

(H / 'stock_snapshot.json').write_text(json.dumps(dict(
    source='JLCPCB public parts API', reservation=False, quantity_per_board_only=True,
    note='Snapshot; assembly attrition and order quantity must be rechecked in quotation.',
    parts=stocks), indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
(H / 'supplier_package_facts.json').write_text(json.dumps(dict(
    source='JLCEDA/EasyEDA Official Library',
    homepages=['https://lceda.cn/', 'https://easyeda.com/'],
    note='Selected pad coordinates for independent orientation comparison; not an assembly-preview confirmation.',
    packages=packages), indent=2)+'\n', encoding='utf-8')

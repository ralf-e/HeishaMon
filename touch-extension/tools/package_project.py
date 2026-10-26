from pathlib import Path
import json,hashlib,difflib,zipfile,re
R=Path(__file__).resolve().parents[1];O=R/'output';O.mkdir(exist_ok=True)
version=re.search(r'HMX_VERSION "([^"]+)"',(R/'extension/hmx_config.h').read_text())[1]
suffix='dev'+version.rsplit('.',1)[1]+'_Rev06'
tree=json.loads((R/'upstream-reference/tree.json').read_text());changed=[]
for item in tree['files']:
 p=R/'firmware'/item['path'];data=p.read_bytes();sha=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
 if sha!=item['sha']:changed.append(item['path'])
assert set(changed)=={'HeishaMon/HeishaMon.ino','HeishaMon/gpio.cpp'},changed
patch=[]
for name in ['HeishaMon.ino','gpio.cpp']:
 a=(R/'upstream-reference'/name).read_text().splitlines(keepends=True);b=(R/'firmware/HeishaMon'/name).read_text().splitlines(keepends=True)
 patch.extend(difflib.unified_diff(a,b,fromfile='a/HeishaMon/'+name,tofile='b/HeishaMon/'+name))
(R/'docs/upstream_integration.patch').write_text(''.join(patch),encoding='utf8')
status=dict(extension=version,upstream=tree['commit'],original_files=len(tree['files']),modified_upstream_files=changed,integration_tests='6 passed',preview_navigation='passed: Node VM DOM simulation, touch persistence/restart/storage failure',policy_cpp='clangd constexpr assertions: 0 errors',esp32_full_build='NOT COMPLETED for current extension; previous dev.6 user build succeeded',hardware_design=json.loads((R/'hardware/validation_summary.json').read_text()),jlcpcb_export=json.loads((R/'manufacturing/JLCPCB/Rev06/export_validation.json').read_text()),hardware_tests='NOT PERFORMED',flashable_binary_included=False)
binary_manifest=O/'firmware/firmware_manifest.json'
firmware_items=[]
if binary_manifest.exists() and json.loads(binary_manifest.read_text(encoding='utf-8-sig')).get('extension')==version:
 manifest=json.loads(binary_manifest.read_text())
 image=O/'firmware'/manifest['image']
 assert image.is_file() and hashlib.sha256(image.read_bytes()).hexdigest()==manifest['sha256']
 assert manifest['extension']==version
 for path,sha in manifest.get('installed_sha256',{}).items():
  assert hashlib.sha256((R/'firmware'/path).read_bytes()).hexdigest()==sha, 'BIN source mismatch: '+path
 status['esp32_full_build']='SUCCESS: packaged application with matching extension version; hardware untested'
 status['flashable_binary_included']=True
 status['firmware_manifest']=manifest
 firmware_items=[image,binary_manifest]
(R/'docs/validation_status.json').write_text(json.dumps(status,indent=2)+'\n')
def archive(target,items):
 items=list(dict.fromkeys(items))
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
  hashes=[]
  for p,name in items:
   z.write(p,name);hashes.append(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+name)
  z.writestr('SHA256SUMS.txt','\n'.join(hashes)+'\n')
 return target.stat().st_size

def files(folder):return [p for p in (R/folder).rglob('*') if p.is_file() and 'build' not in p.relative_to(R).parts and '__pycache__' not in p.parts and p.suffix not in ['.pyc','.kicad_prl'] and not any(part.endswith('-backups') for part in p.parts)]
pdf=O/('HeishaMon_V6_Touch_Anleitung_'+suffix+'.pdf')
assert pdf.exists()
# Standalone JLC upload files, independently downloadable.
import shutil
standalone=[]
for src,dst in [('BOM_JLCPCB.csv','BOM_HeishaMon_V6_Rev06.csv'),('CPL_JLCPCB.csv','CPL_HeishaMon_V6_Rev06.csv'),('Gerber_HeishaMon_V6_Rev06.zip','Gerber_HeishaMon_V6_Rev06.zip')]:
 shutil.copyfile(R/'manufacturing/JLCPCB/Rev06'/src,O/dst);standalone.append(dst)
schematic_pdf=O/'HeishaMon_V6_Schaltplan_Rev06.pdf';shutil.copyfile(R/'hardware/Gesamtschaltplan_rev06.pdf',schematic_pdf);standalone.append(schematic_pdf.name)
current=[]
for folder in ['firmware/HeishaMon','extension','upstream-reference','vendor','docs','hardware','manufacturing','validation']:
 current.extend((p,p.relative_to(R).as_posix()) for p in files(folder))
current.extend((p,p.relative_to(R).as_posix()) for folder in ['tools','tests'] for p in files(folder) if p.name!='compile_commands.json')
current.extend((R/name,name) for name in ['LICENSE','LICENSING.md'])
current += [(R/'README.md','README.md'),(R/'.gitignore','.gitignore'),(R/'firmware/hmx-installed.json','firmware/hmx-installed.json'),(pdf,'output/'+pdf.name)]
current.extend((p,p.relative_to(R).as_posix()) for p in firmware_items)
project=O/('HeishaMon_V6_Touch_Projekt_'+suffix+'.zip');archive(project,current)
kicad=O/'HeishaMon_V6_KiCad_Rev06.zip';archive(kicad,[(p,'HeishaMon_V6_Touch_Adapter/'+p.relative_to(R/'hardware').as_posix()) for p in files('hardware')])
jlc=O/'HeishaMon_V6_JLCPCB_Rev06.zip';archive(jlc,[(p,'JLCPCB_Rev06/'+p.relative_to(R/'manufacturing/JLCPCB/Rev06').as_posix()) for p in files('manufacturing/JLCPCB/Rev06')])
release=dict(software=version,hardware='0.6',files=[pdf.name,pdf.with_suffix('.md').name,project.name,kicad.name,jlc.name]+standalone+[p.relative_to(O).as_posix() for p in firmware_items])
(O/'current-release.json').write_text(json.dumps(release,indent=2))
print(json.dumps(dict(files=release['files'],project_bytes=project.stat().st_size,project_entries=len(current),smd_placements=status['jlcpcb_export']['smd_placements'],manual_headers_excluded=True),indent=2))

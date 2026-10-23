"""Render the project's small Markdown manual as standalone HTML, including offline images."""
from pathlib import Path
import base64,html,re
from project_config import VERSION,DISPLAY_NAME
B=Path(__file__).resolve().parents[1]
def inline(s):
 s=html.escape(s)
 s=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',s)
 return re.sub(r'`([^`]+)`',r'<code>\1</code>',s)
rows=[];paragraph=[];in_list=False
def flush():
 if paragraph:rows.append('<p>'+inline(' '.join(paragraph))+'</p>');paragraph.clear()
for line in (B/'docs/USER-MANUAL.md').read_text(encoding='utf-8').splitlines():
 image=re.fullmatch(r'!\[(.*?)\]\((.*?)\)',line)
 heading=re.match(r'^(#{1,3}) (.*)',line)
 if not line or heading or image or line.startswith('- '):
  flush()
  if in_list and not line.startswith('- '):rows.append('</ul>');in_list=False
  if heading:
   n=len(heading[1]);rows.append(f'<h{n}>'+inline(heading[2])+f'</h{n}>')
  elif image:
   path=(B/'docs'/image[2]).resolve();path.relative_to(B.resolve())
   encoded=base64.b64encode(path.read_bytes()).decode()
   rows.append('<figure><img alt="'+html.escape(image[1],quote=True)+'" src="data:image/png;base64,'+encoded+'"><figcaption>'+inline(image[1])+'</figcaption></figure>')
  elif line.startswith('- '):
   if not in_list:rows.append('<ul>');in_list=True
   rows.append('<li>'+inline(line[2:])+'</li>')
 else:paragraph.append(line)
flush()
if in_list:rows.append('</ul>')
css='body{font:17px/1.6 system-ui,sans-serif;max-width:1000px;margin:36px auto;padding:0 24px;color:#20242a}h1,h2,h3{line-height:1.25}h2{margin-top:2em;border-bottom:2px solid #b92d38;padding-bottom:8px}figure{margin:24px 0}img{max-width:100%;height:auto}figcaption{color:#555;font-style:italic;font-size:14px}code{overflow-wrap:anywhere}@media print{body{font-size:11pt;margin:0}h2,h3{break-after:avoid}figure{break-inside:avoid}}'
(B/'docs/USER-MANUAL.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(DISPLAY_NAME+' '+VERSION)+' — User Manual</title><style>'+css+'</style><body>'+'\n'.join(rows)+'</body></html>',encoding='utf-8')
print('Standalone manual generated with embedded offline previews')

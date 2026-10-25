"""Generate five native MPC pages for the sixteen-lane sequencer."""
from pathlib import Path
import json,zipfile,copy,hashlib,math,shutil,sys,re
from functools import lru_cache
from PIL import Image,ImageDraw,ImageFont
from project_config import FOLDER, SKIN_IDENTIFIER, VERSION
from provenance import inputs,tree,timestamp
B=Path(__file__).resolve().parents[1];P=json.loads((B/'params.json').read_text());I={p['key']:i for i,p in enumerate(P)}
OUT=B/'build/skin'/FOLDER;A=OUT/'Plugin Skins'
if OUT.exists():shutil.rmtree(OUT)
A.mkdir(parents=True)
z=zipfile.ZipFile(B/'reference/skin-base.zip');assert hashlib.sha256((B/'reference/skin-base.zip').read_bytes()).hexdigest()==(B/'reference/skin-base.zip.sha256').read_text().split()[0]
J=json.loads(z.read('Plugin Skins/TUI.json'));D=J['pageData'];D['componentDefinitions']['localComponentDefinitions']=[];defs=D['componentDefinitions']['localComponentDefinitions']
C={'bg':'#171a1e','panel':'#252b31','oled':'#111b18','text':'#e8e5d0','muted':'#b4bcba','red':'#f2474d','amber_bg':'#342e22','amber_text':'#c5ac78','amber_edge':'#8b7854'}
READ_ONLY_TEXT='#6b756f'
@lru_cache(maxsize=32)
def font(n):return ImageFont.truetype(str(B/'reference/fonts/TitilliumWeb-Regular.ttf'),n)
def text(d,xy,t,n=23,c=None,anchor=None):d.text(xy,t,font=font(n),fill=c or C['text'],anchor=anchor)
def image(w,h,bg=None):im=Image.new('RGB',(w,h),bg or C['bg']);return im,ImageDraw.Draw(im)
def save(name,im):im.save(A/name)
def bounds(x,y,w,h,extra=None):return dict(version=2,acceptsHWFocus='Yes',showWhenDataModelInvalid='Hide',whenVisible='Always',boundsType='Absolute',bounds=f'{x} {y} {w} {h}',additionalInvalidatingHandles=extra or [])
def child(kind,data,x,y,w,h,name='Control'):
 return {'version':2,'componentData':{'version':1,'name':name,'type':kind,'data':data},'handle remapping':{'version':1,'map':[]},'bounds':bounds(x,y,w,h)}
def action(handler):return {'version':2,'onAction':'Mouse Down','handler':handler,'handleName':'Data','additionalData':'','handle remapping':{'version':1,'map':[]}}
def local(name,children,actions=None,focus=False):
 clear={'version':1,'colour':'0','image':''};v=dict(version=4,actions=actions or [],backgroundData=dict(version=1,focussed=clear,unfocussed=clear),ignoreMousePresses=not bool(actions),disableCoarseDataWheel=False,repeats=1,hideQLinkBounds=True,componentsData=children)
 if focus:
  boxes=[list(map(int,c['bounds']['bounds'].split())) for c in children];w=max(x+cw for x,y,cw,ch in boxes);h=max(y+ch for x,y,cw,ch in boxes)
  c=child('Focus',dict(version=1,backgroundColour='00000000',outlineColour='ffffffff',backgroundInset=2.,outlineThickness=2.),0,0,w,h);c['bounds']['whenVisible']='WhenFocussed';c['bounds']['acceptsHWFocus']='No';children.append(c)
 defs.append({'key':name,'value':v});return name
def placed(kind,key,x,y,w,h,extra=None,maps=None):
 c=child(kind,dict(version=1,handleName='Data'),x,y,w,h,key);c['handle remapping']['map']=[{'key':'Data','value':f'Parameter {I[key]}'}]+(maps or []);c['bounds']['additionalInvalidatingHandles']=extra or [];return c
def gate(key,val,n):return f'IndexedEnabling/{val}/{n}/Parameter {I[key]}'
def art(name,x,y,w,h):
 c=child('Image',dict(version=2,imageType='Regular',colour='0',image=name),x,y,w,h);c['bounds']['acceptsHWFocus']='No';return c
def label(x,y,w,h,n=24,handle='Data',kind='Value',colour='ffe8e5d0'):
 c=child('Label',dict(version=1,textStyle=dict(version=1,font=dict(version=1,name='Titillium Web',style='Regular',height=float(n)),colour=colour,justification='left verticallyCentred',case='Original'),type=kind,handleName=handle),x,y,w,h);c['bounds']['acceptsHWFocus']='No';return c
def readout(key,x,y,w,h,n=24):
 k=local(f'read_{key}_{x}_{y}',[label(0,0,w,h,n)]);c=placed(k,key,x,y,w,h);c['bounds']['acceptsHWFocus']='No';return c
def button(key,title,x,y,w,h,momentary=True,id=1,count=2,extra=None,tag=None,native_touch=False):
 tag=tag or f'btn_{key}_{x}_{y}_{id}'
 for state in [0,1]:
  im,d=image(w,h,C['amber_bg'] if state else C['panel']);d.rounded_rectangle((1,1,w-2,h-2),radius=3,outline=C['amber_edge'] if state else '#727d81');text(d,(w//2,h//2),title,21,C['amber_text'] if state else C['text'],'mm');save(tag+f'_{state}.png',im)
 if native_touch:
  # A single touch owner, matching the working step-pad triggers. A nested
  # Momentary Button can retain its pressed gesture until focus moves away.
  # The wrapper already sends the trigger's release; artwork follows Data.
  children=[]
  for state in [0,1]:
   c=art(tag+f'_{state}.png',0,0,w,h)
   c['bounds']['additionalInvalidatingHandles']=[gate(key,state,2)]
   children.append(c)
  k=local(tag,children,[action('Toggle Switch'),dict(action('Toggle Switch'),onAction='Enter Pressed')],focus=True)
 else:
  k=local(tag,[child('Button',dict(version=2,onImage=tag+'_1.png',offImage=tag+'_0.png',buttonId=id,numButtonsInGroup=count,handleName='Data',gestureBehaviour='Momentary' if momentary else 'Instant'),0,0,w,h)],[action('Q-Link'),dict(action('Toggle Switch'),onAction='Enter Pressed')],focus=True)
 if not momentary:
  for element in defs[-1]['value']['componentsData']:
   if element['componentData']['type']=='Focus':element['bounds']['additionalInvalidatingHandles']=[gate(key,id,count)]
 return placed(k,key,x,y,w,h,extra)
def toggle(key,title,x,y,w,h):
 # One native Toggle Switch owns touch/Enter and binds the actual state.
 # No momentary proxy and no child Button that could toggle a second time.
 children=[]
 for current in [0,1]:
  tag=f'toggle_{key}_{x}_{y}_{current}'
  im,d=image(w,h,C['amber_bg'] if current else C['panel']);d.rounded_rectangle((1,1,w-2,h-2),radius=3,outline=C['amber_edge'] if current else '#727d81')
  caption=('HOLD' if current else 'GATE') if key.endswith('_hold') else title+(' ON' if current else ' OFF') if key=='auto_rotate' else title
  text(d,(w//2,h//2),caption,21,C['amber_text'] if current else C['text'],'mm');save(tag+'.png',im)
  c=art(tag+'.png',0,0,w,h);c['bounds']['additionalInvalidatingHandles']=[gate(key,current,2)];children.append(c)
 actions=[action('Toggle Switch'),dict(action('Toggle Switch'),onAction='Enter Pressed')]
 return [placed(local(f'toggle_native_{key}_{x}_{y}',children,actions,focus=True),key,x,y,w,h)]
def field(key,x,y,w,h,n=26):
 tag=f'field_{w}_{h}';fn=tag+'.png'
 if not (A/fn).exists():
  im=Image.new('RGB',(w,h*128),C['panel']);dr=ImageDraw.Draw(im)
  for f in range(128):dr.rectangle((1,f*h+1,w-2,(f+1)*h-2),outline='#727d81')
  save(fn,im)
 parts=[child('Knob',dict(version=5,knobType='FilmStrip',filmStrip=fn,numFrames=127,invert=False,dragOrientation='Vertical',handleName='Data'),0,0,w,h),label(12,0,w-24,h,n)]
 k=local(f'field_{key}',parts,[action('Q-Link')],focus=True);return placed(k,key,x,y,w,h)
def rand_button(x,y,w,h):
 children=[]
 for armed in [0,1]:
  im,d=image(w,h,'#1a3324' if armed else C['panel'])
  d.rounded_rectangle((1,1,w-2,h-2),radius=3,outline='#65bc7b' if armed else '#727d81')
  if armed:
   # Shear the glyph mask to italic without requiring an additional font file.
   mask=Image.new('RGBA',(80,30),(0,0,0,0));md=ImageDraw.Draw(mask)
   text(md,(8,0),'RAND',21,'#a0d8ad')
   mask=mask.transform(mask.size,Image.Transform.AFFINE,(1,-.18,4,0,1,0),resample=Image.Resampling.BICUBIC)
   im.paste(mask,((w-80)//2,(h-30)//2),mask)
   d.rectangle((w-13,5,w-7,11),fill='#ffffff')
  else:text(d,(w//2,h//2),'RAND',21,C['text'],'mm')
  fn=f'rand_mode{armed}.png';save(fn,im)
  c=art(fn,0,0,w,h);c['bounds']['additionalInvalidatingHandles']=[gate('rand_mode',armed,2)];children.append(c)
 actions=[action('Toggle Switch'),dict(action('Toggle Switch'),onAction='Enter Pressed')]
 return placed(local('rand_two_stage',children,actions,focus=True),'randomize',x,y,w,h)
# Shared knob filmstrip, exact image/control geometry.
im=Image.new('RGB',(58,58*128),C['oled']);dr=ImageDraw.Draw(im)
for v in range(128):
 y=v*58;dr.ellipse((4,y+4,54,y+54),outline=C['text'],width=2);a=math.radians(-135+270*v/127);dr.line((29,y+29,29+math.sin(a)*20,y+29-math.cos(a)*20),fill=C['text'],width=3)
save('dial.png',im)
# Read-only reference strip: same frames/geometry, attenuated foreground only.
reference=Image.new('RGB',im.size,C['oled'])
reference=Image.blend(reference,im,.35)
save('dial_read_only.png',reference)
# Native 1280 x 628 content: MPC owns the header and bottom tabs.
im,dr=image(1280,628);save('pattern.png',im)
parts=[art('pattern.png',0,0,1280,628)]
for i in range(16):
 x=20+(i%8)*156;w=148;h=46;tag=f'lane_select_{i}';children=[]
 # Exactly one native selection owner is visible per lane. Explicit Mute
 # overrides activity immediately; Solo exclusions retain the usual artwork.
 for muted,flash in [(0,0),(0,1),(1,0)]:
  for selected in [0,1]:
   bg=('#2b2529' if selected else '#1b2023') if muted else '#203c49' if flash else '#352329' if selected else C['panel']
   ink=('#ad747b' if selected else '#858d91') if muted else '#91c9df' if flash else C['red'] if selected else C['text']
   edge='#ffffff' if selected else '#333b40' if muted else '#5b9cb7' if flash else '#485057'
   im,d=image(w,h,bg);d.rectangle((1,1,w-2,h-2),outline=edge,width=2 if selected else 1)
   text(d,(w//2,h//2),f'A{i+1:02}',24,ink,'mm');save(tag+f'_m{muted}_f{flash}_{selected}.png',im)
  native=child('Button',dict(version=2,onImage=tag+f'_m{muted}_f{flash}_1.png',offImage=tag+f'_m{muted}_f{flash}_0.png',buttonId=i,numButtonsInGroup=16,handleName='Data',gestureBehaviour='Instant'),0,0,w,h)
  conditions=[gate(f'l{i}_mute',muted,2)]
  if not muted:conditions.append(gate(f'lane_flash{i}',flash,2))
  native['bounds']['acceptsHWFocus']='No';native['bounds']['additionalInvalidatingHandles']=conditions;children.append(native)
 kind=local(tag,children,[action('Q-Link')]);parts.append(placed(kind,'line_select16',x,12+(i//8)*52,w,h))
parts += [button('edit_view','LINE',20,394,148,46,False,0,2),button('edit_view','EDIT',176,394,148,46,False,1,2)]
parts += [*toggle('sel_mute','MUTE',488,394,148,46),*toggle('sel_solo','SOLO',644,394,148,46)]
for control in [button('half','1/2',800,394,148,46),button('double','x2',956,394,148,46),rand_button(1112,394,148,46)]:
 control['bounds']['additionalInvalidatingHandles'].append(gate('edit_view',0,2))
 parts.append(control)
parts += [button('edit_tool','SELECT',800,394,148,46,False,0,2,extra=[gate('edit_view',1,2)]),button('edit_tool','DRAW',956,394,148,46,False,1,2,extra=[gate('edit_view',1,2)]),button('erase_values','ERASE',1112,394,148,46,extra=[gate('edit_view',1,2)])]
# Opaque display artwork, headers and four controls per scope.
im,dr=image(1240,264,C['oled']);dr.rectangle((1,1,1238,262),outline='#68736a',width=2);dr.line((8,131,1230,131),fill='#68736a',width=1);save('scopes.png',im);parts.append(art('scopes.png',20,120,1240,264))
im,d=image(299,94,C['oled']);d.rectangle((1,1,297,92),outline='#68736a');save('parameter_box.png',im)
im,d=image(299,94,C['oled']);d.rectangle((1,1,297,92),outline='#303f36');save('parameter_box_read_only.png',im)
for view,keys in [(0,['sel_'+k for k in ['velocity','prob','humanize','gate','steps','hits','rotate','division']]),(1,['sel_velocity','sel_prob','sel_humanize','sel_gate','step_velocity','step_prob','step_ratchet','step_decay'])]:
 for title,y in [('LINE',120),('STEP' if view else 'STEPS',252)]:
  im,d=image(720,26,C['oled']);text(d,(0,0),title,20,READ_ONLY_TEXT if view and y==120 else C['text']);fn=f'scope_v{view}_{y}.png';save(fn,im);c=art(fn,34,y+4,720,26);c['bounds']['additionalInvalidatingHandles']=[gate('edit_view',view,2)];parts.append(c)
 for n,key in enumerate(keys):
  x=30+(n%4)*309;y=151+(n//4)*132
  read_only=bool(view and n<4)
  colour='ff'+READ_ONLY_TEXT[1:] if read_only else 'ffe8e5d0'
  children=[art('parameter_box_read_only.png' if read_only else 'parameter_box.png',0,0,299,94),child('Knob',dict(version=5,knobType='FilmStrip',filmStrip='dial_read_only.png' if read_only else 'dial.png',numFrames=127,invert=False,dragOrientation='Vertical',handleName='Data'),9,19,58,58),label(82,0,210,27,20,kind='Name',colour=colour),label(82,27,200,40,34,colour=colour)]
  if read_only:
   for component in children:component['bounds']['acceptsHWFocus']='No'
  kind=local(f'knob_v{view}_{n}',children,None if read_only else [action('Q-Link')],focus=not read_only)
  conditions=[gate('edit_view',view,2)]+([gate('rand_mode',0,2)] if not view else [])
  component=placed(kind,key,x,y,299,94,conditions)
  if read_only:component['bounds']['acceptsHWFocus']='No'
  parts.append(component)
  if not view:
   # Mutually exclusive sibling: exactly one touch owner at any given time.
   picked=[]
   for chosen in [0,1]:
    im,d=image(299,94,'#1a3324' if chosen else C['oled'])
    d.rectangle((1,1,297,92),outline='#65bc7b' if chosen else '#68736a',width=2 if chosen else 1)
    fn=f'rand_pick_box{chosen}.png';save(fn,im)
    c=art(fn,0,0,299,94);c['bounds']['additionalInvalidatingHandles']=[gate(f'rand_pick{n}',chosen,2)];picked.append(c)
   # Static dial: selecting a target never edits its value or turns a knob.
   # Opaque dial uses the same surface as its enclosing state.
   for chosen in [0,1]:
    im,d=image(58,58,'#1a3324' if chosen else C['oled']);d.ellipse((4,4,54,54),outline='#a0d8ad' if chosen else C['text']);d.line((29,29,39,12),fill='#a0d8ad' if chosen else C['text'],width=2)
    fn=f'rand_dial{chosen}.png';save(fn,im);c=art(fn,9,19,58,58);c['bounds']['additionalInvalidatingHandles']=[gate(f'rand_pick{n}',chosen,2)];picked.append(c)
   picked += [label(82,0,210,27,20,handle='Value',kind='Name'),label(82,27,200,40,34,handle='Value')]
   actions=[action('Toggle Switch'),dict(action('Toggle Switch'),onAction='Enter Pressed')]
   k=local(f'rand_target{n}',picked,actions,focus=True)
   parts.append(placed(k,f'rand_toggle{n}',x,y,299,94,[gate('edit_view',0,2),gate('rand_mode',1,2)],maps=[{'key':'Value','value':f'Parameter {I[key]}'}]))
  if view and n>=4:
   im,d=image(10,10,C['text']);fn='custom_square.png';save(fn,im);c=art(fn,x+282,y+6,10,10);c['bounds']['additionalInvalidatingHandles']=[gate('edit_view',1,2),gate(f'step_custom{n-4}',1,2)];parts.append(c)
# Each pad has ONE native touch owner containing its passive state artwork.
# A sibling display above a separate Button can intercept physical touch on MPC.
for i in range(32):
 x=20+(i%16)*78;y=470+(i//16)*64;w=70;h=54
 states=[]
 for state in range(18):
  outside=state>=16;active=not outside and state&1;selected=(not outside and state&2) or state==17;head=not outside and state&4;custom=not outside and state&8
  bg='#432449' if custom else '#352329' if active else C['panel'];ink='#d780e0' if custom else C['red'] if active else '#555e62' if outside else '#a5adaa'
  im,d=image(w,h,bg);d.rectangle((1,1,w-2,h-2),outline='#ffffff' if selected else '#88518e' if custom else '#485057',width=2 if selected else 1)
  if head:d.rectangle((4,4,w-5,h-5),outline=C['red'],width=3)
  if custom:d.rectangle((w-12,5,w-7,10),fill=C['text'])
  text(d,(w//2,h//2),f'{i+1:02}',24,ink,'mm');fn=f'step{i}_state{state}.png';save(fn,im)
  c=art(fn,0,0,w,h);c['bounds']['additionalInvalidatingHandles']=[gate(f'editcell{i}',state,18)];
  states.append(c)
 # Native action, as for the working M/S switches: no overlaid sibling and
 # no nested Button that could consume the touch or fire the action twice.
 actions=[action('Toggle Switch'),dict(action('Toggle Switch'),onAction='Enter Pressed')]
 k=local(f'pad_touch{i}',states,actions)
 c=placed(k,f'step_press{i}',x,y,w,h);parts.append(c)

# TRACKS previews use small static tiles, never short filmstrips.
for state in range(9):
 # Miniature PATTERN tiles: preserve all nine existing state values and geometry.
 # Playback outlines the tile without hiding its note/custom colour.
 outside=state==8
 active=not outside and bool(state&1)
 custom=not outside and bool(state&4)
 head=not outside and bool(state&2)
 bg='#1c2025' if outside else '#432449' if custom else '#352329' if active else C['panel']
 edge='#292e34' if outside else '#88518e' if custom else '#a9434c' if active else '#485057'
 im,dr=image(12,22)
 dr.rectangle((1,3,10,18),fill=bg,outline=edge)
 if head:dr.rectangle((0,2,11,19),outline=C['text'])
 save(f'tiny_state{state}.png',im)
track_pages=[]
for start in [0,8]:
 im,dr=image(1280,628);text(dr,(24,16),f'TRACKS / {start+1:02}–{start+8:02}',28)
 for title,x,y in [('MODE',880,86),('SHIFT / STEPS',880,260),('EVERY / CYCLES',1070,260),('CYCLE',880,340),('SHIFT',1070,340)]:text(dr,(x,y),title,19,C['muted'])
 fn=f'tracks_{start}.png';save(fn,im);tracks=[art(fn,0,0,1280,628)]
 for row in range(8):
  i=start+row;y=88+row*58;tracks += [button(f'edit_line{i}',f'A{i+1:02}',20,y,70,42),readout(f'name{i}',104,y,125,42,22)]
  for j in range(32):
   for state in range(9):
    c=art(f'tiny_state{state}.png',240+j*15,y+10,12,22);c['bounds']['additionalInvalidatingHandles']=[gate(f'trackcell{i}_{j}',state,9)];tracks.append(c)
  tracks += toggle(f'l{i}_mute','M',735,y,48,42)+toggle(f'l{i}_solo','S',793,y,48,42)
 tracks += [readout('line_scope',880,40,370,36,22),field('play_mode',880,116,360,48),*toggle('auto_rotate','AUTO ROTATE',880,190,360,46),field('auto_shift',880,292,168,48),field('auto_every',1070,292,170,48),readout('phase_cycle',880,362,168,38,23),readout('phase_offset',1070,362,170,38,23),button('reset_phase','RESET PHASE',880,430,360,48)]
 track_pages.append(tracks)
# SETUP: mode/profile dialogs are explicit, no native popup guesses.
im,dr=image(1280,628);text(dr,(20,4),'TARGET TYPE',18,C['muted']);text(dr,(510,4),'PROFILE / BANK',18,C['muted']);text(dr,(1070,4),'CHANNEL',18,C['muted']);text(dr,(20,130),'LINE',18,C['muted']);text(dr,(105,130),'MODE',18,C['muted']);text(dr,(230,130),'SOUND / PAD',18,C['muted']);text(dr,(820,130),'MIDI NOTE',18,C['muted']);save('setup.png',im)
setup_pages=[]
for start in [0,8]:
 setup=[art('setup.png',0,0,1280,628)]
 setup += [button('open_target','',20,38,450,48),placed(local('mode_text',[label(12,0,420,48,24)],None),'target_mode',20,38,450,48),button('open_mapping','INCIPIENCE / REVIEW',510,38,510,48,extra=[gate('target_mode',0,2)]),button('open_bank','',510,38,510,48,extra=[gate('target_mode',1,2)]),placed(local('bank_text',[label(12,0,470,48,26)]),'bank',510,38,510,48,[gate('target_mode',1,2)]),field('channel',1070,38,170,48),readout('port_label',20,92,1000,32,22)]
 for row in range(8):
  i=start+row;
  y=174+row*49;im,d=image(60,42);text(d,(4,18),f'{i+1:02}',23,anchor='lm');fn=f'line_{i}.png';save(fn,im);setup.append(art(fn,20,y,60,42))
  # A button owns clicks; its label is non-focusable and ignores presses.
  setup += toggle(f'l{i}_hold','',105,y,110,42)
  setup += [button(f'open_sound{i}','',230,y,525,42,extra=[gate('target_mode',0,2)]),readout(f'name{i}',245,y,475,42,25),field(f'l{i}_pad',230,y,525,42,25)]
  setup[-1]['bounds']['additionalInvalidatingHandles']=[gate('target_mode',1,2)]
  for k,mode in [('inote',0),('dnote',1)]:
   c=field(f'l{i}_{k}',820,y,420,42,26);c['bounds']['additionalInvalidatingHandles']=[gate('target_mode',mode,2)];setup.append(c)
 setup_pages.append(setup)
# Full-page overlays; no underlying controls show through.
overlays=[]
def overlay(dialog,title):
 im,d=image(1280,628);text(d,(40,25),title,32);filename=f'dialog{dialog}.png';save(filename,im);return [art(filename,0,0,1280,628)]
cs=overlay(2,'INCIPIENCE / DEFAULT NOTE MAP')
for i,name in enumerate(['KICK','MBRANE','CL HAT','OP HAT','CLAP','RIM','CRASH','RIDE','X1','X2','FM','CUSTOM','CUSTOM','CUSTOM','CUSTOM','CUSTOM']):
 im,d=image(570,38);text(d,(6,2),f'{i+1:02} - {name}',23);text(d,(430,2),str(36+i),23);fn=f'mapnotice{i}.png';save(fn,im);cs.append(art(fn,40+(i//8)*620,76+(i%8)*40,570,38))
im,d=image(1200,70);text(d,(10,10),'Replaces sixteen note assignments. Rhythms are preserved.',26);text(d,(10,42),'Check the current NOTE settings in your Incipience instance.',22,C['muted']);save('mapping_notice.png',im);cs.append(art('mapping_notice.png',40,420,1200,70));cs += [button('close','CANCEL',340,530,260,54),button('apply_mapping','APPLY MAPPING',650,530,300,54)];overlays.append((2,cs))
cs=overlay(3,'TARGET TYPE')
for i,title in enumerate(['DRUM INSTRUMENT','DRUM TRACK']):cs.append(button('choose_target',title,250,140+i*110,780,78,False,i,2,tag=f'mode_{i}'))
cs.append(button('close','CLOSE',510,530,260,54));overlays.append((3,cs))
cs=overlay(4,'CHOOSE INCIPIENCE SOUND')
for i,title in enumerate(P[I['map_sound']]['options']):cs.append(button('choose_sound',title,40+(i%3)*405,100+(i//3)*92,380,68,False,i,12,tag=f'sound_{i}'))
cs.append(button('close','CLOSE',510,530,260,54));overlays.append((4,cs))
cs=overlay(5,'DRUM TRACK BANK / LOCAL REFERENCE MAPPING')
for i,title in enumerate('ABCDEFGH'):cs.append(button('choose_bank',title,70+(i%4)*300,130+(i//4)*130,260,80,False,i,8,tag=f'bank_{i}'))
cs.append(button('close','CLOSE',510,530,260,54));overlays.append((5,cs))
# Native pages own their own complete setup overlays.
for component in parts:component['bounds']['additionalInvalidatingHandles'].append(gate('pattern_base',1,2))
for setup in setup_pages:
 for component in setup:component['bounds']['additionalInvalidatingHandles'].append(gate('setup_base',1,2))
 for dialog,cs in overlays:
  for original in cs:
   component=copy.deepcopy(original);component['bounds']['additionalInvalidatingHandles'].append(gate('dialog',dialog,6));setup.append(component)
pages=[('PATTERN',parts),('TR 01-08',track_pages[0]),('TR 09-16',track_pages[1]),('SET 01-08',setup_pages[0]),('SET 09-16',setup_pages[1])]
for name,children in pages:
 for control in children:
  x,y,w,h=map(int,control['bounds']['bounds'].split())
  if x<0 or y<0 or w<=0 or h<=0 or x+w>1280 or y+h>628:raise ValueError('Control outside native content: '+control['componentData']['name'])
 local(name,children)
D['tabs']=[dict(version=3,tabName=name,fnKeyIndex=i,fnKeySubIndex=0,qlinkBoundsData=['0 0 0 0'],componentName=name,initialSize='0 0 1280 628',scale=1.) for i,(name,_) in enumerate(pages)]
(A/'TUI.json').write_text(json.dumps(J,indent=2)+'\n')
for filename in ['Q-Links.json','Q-Links - 8by1.json']:
 q=json.loads(z.read('Plugin Skins/'+filename));template=q['Screen Mode Q-Links']['map'][0];rows=[]
 for tab in range(1,6):
  row=copy.deepcopy(template);row['Tab']=tab;row['SubTab']=1;row['Q-Links']={f'Q-Link {i}':-1 for i in range(1,17)}
  keys=[f'q{i}' for i in range(8)] if tab==1 else ['line_select16','play_mode','auto_rotate','auto_shift','auto_every'] if tab in (2,3) else ['line_select16','target_mode','channel','bank']
  for hw,k in zip([13,9,5,1,14,10,6,2],keys):row['Q-Links'][f'Q-Link {hw}']=I[k]
  rows.append(row)
 q['Screen Mode Q-Links']['map']=rows;(A/filename).write_text(json.dumps(q,indent=2)+'\n')
(OUT/'version.xml').write_text(f'<?xml version="1.0"?>\n<plugincontent version="1.0"><identifier>{SKIN_IDENTIFIER}</identifier><version>{VERSION.split("-",1)[0]}.0</version></plugincontent>\n',encoding='utf-8')
print('Native skin:',len(defs),'definitions;',len(list(A.glob('*.png'))),'PNG assets; five MPC pages')

receipt={"version":VERSION,"inputs":inputs(),"outputs":tree(OUT),"timestamp_utc":timestamp()}
(B/"build/skin-receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")

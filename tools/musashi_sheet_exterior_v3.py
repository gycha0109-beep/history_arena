"""Musashi sheet V1: original silhouette/material first. Blender 5.2.3.
Reference: user-approved 2026-11-14 4-view concept sheet.
No animation retargeting / no placeholder claims.
"""
from pathlib import Path
from mathutils import Vector
import bpy, math, random, json
R=random.Random(141126)
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'captures/qa/musashi_anatomy_reference_v2/musashi_anatomy_work.blend'
OUT=ROOT/'captures/qa/musashi_character_sheet_v3'
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SRC))
scene=bpy.context.scene
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
body=bpy.data.objects['SuperHero_Male']
scene.frame_set(1)
for o in [rig,body]: o.hide_render=False
def material(name,color,rough=.85,metal=0,noise_scale=140,variation=.18,bump=.06):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1)
 m.use_nodes=True
 nt=m.node_tree;n=nt.nodes;links=nt.links
 bsdf=n.get('Principled BSDF')
 bsdf.inputs['Base Color'].default_value=(*color,1)
 bsdf.inputs['Roughness'].default_value=rough
 bsdf.inputs['Metallic'].default_value=metal
 if variation:
  tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=noise_scale
  tex.inputs['Detail'].default_value=3.8;tex.inputs['Roughness'].default_value=.7
  ramp=n.new('ShaderNodeValToRGB')
  ramp.color_ramp.elements[0].position=.2
  ramp.color_ramp.elements[0].color=(*[max(0,c*(1-variation)) for c in color],1)
  ramp.color_ramp.elements[1].position=.8
  ramp.color_ramp.elements[1].color=(*[min(1,c*(1+variation)) for c in color],1)
  links.new(tex.outputs['Fac'],ramp.inputs['Fac'])
  links.new(ramp.outputs['Color'],bsdf.inputs['Base Color'])
  if bump:
   bm=n.new('ShaderNodeBump');bm.inputs['Strength'].default_value=bump
   bm.inputs['Distance'].default_value=.003
   links.new(tex.outputs['Fac'],bm.inputs['Height'])
   links.new(bm.outputs['Normal'],bsdf.inputs['Normal'])
 return m
MAT={
 'skin':material('Musashi warm sun-weathered skin',(.43,.255,.188),.73,variation=.10,noise_scale=95,bump=.03),
 'robe':material('Tattered deep charcoal indigo hemp',(.055,.052,.055),.98,variation=.34,noise_scale=250,bump=.20),
 'robe2':material('Layered faded charcoal',(.077,.071,.074),.97,variation=.27,noise_scale=210,bump=.16),
 'shadow':material('Under kimono black linen',(.036,.033,.039),.96,variation=.20,noise_scale=160,bump=.13),
 'stitch':material('Worn stitching ash grey',(.20,.177,.164),.95,variation=.15,noise_scale=250,bump=.03),
 'red':material('Weathered crimson cloth sash',(.27,.045,.05),.98,variation=.37,noise_scale=220,bump=.15),
 'red2':material('Deep burgundy faded silk sash',(.165,.030,.038),.98,variation=.28,noise_scale=180,bump=.09),
 'hair':material('Untamed dark brown-black hair',(.012,.010,.010),.92,variation=.42,noise_scale=180,bump=.04),
 'hair2':material('Hair highlights brown umber',(.029,.020,.016),.90,variation=.30,noise_scale=180,bump=.02),
 'wrap':material('Dark leather wrist and shin wraps',(.065,.052,.048),.88,variation=.30,noise_scale=250,bump=.11),
 'sole':material('Worn straw sandal sole',(.22,.16,.10),.96,variation=.35,noise_scale=180,bump=.17),
 'straw':material('Straw sandal rope',(.34,.22,.115),.98,variation=.25,noise_scale=250,bump=.18),
}
body.data.materials.clear();body.data.materials.append(MAT['skin'])
for name in ('Eyes','Eyebrows'):
 if name in bpy.data.objects:
  ob=bpy.data.objects[name]
  if name=='Eyebrows':ob.data.materials.clear();ob.data.materials.append(MAT['hair'])
  else: ob.data.materials.clear();ob.data.materials.append(material('Amber brown irises',(.12,.064,.038),.26,variation=.12,noise_scale=105,bump=0))
def mesh(name,v,f,mat,wfn=None,thick=0):
 me=bpy.data.meshes.new(name);me.from_pydata(v,[],f);me.update()
 ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob)
 if isinstance(mat,list):
  for m in mat:me.materials.append(m)
 else: me.materials.append(MAT.get(mat,mat) if isinstance(mat,str) else mat)
 for po in me.polygons:po.use_smooth=True
 if wfn:
  groups={}
  for i,pt in enumerate(v):
   for b,w in wfn(Vector(pt)).items():
    if w>.0001:
     if b not in groups:groups[b]=ob.vertex_groups.new(name=b)
     groups[b].add([i],float(w),'REPLACE')
  mod=ob.modifiers.new('Preserved human armature','ARMATURE');mod.object=rig;mod.use_deform_preserve_volume=True
 if thick:
  sol=ob.modifiers.new('Fabric thickness','SOLIDIFY');sol.thickness=thick;sol.offset=-.25
 return ob
def fixed(b):return lambda p:{b:1.}
def torso(p):
 t=max(0,min(1,(p.z-1.05)/.38))
 return {'spine_01':1-t,'spine_03':t}
def legs(side):
 def calc(p):
  t=max(0,min(1,(p.z-.36)/.36))
  return {'thigh_'+side:t,'calf_'+side:1-t}
 return calc
def ring_mesh(name,rings,mat,weight,segments=48,thick=.004,angle_start=0,angle_end=math.tau):
 v=[];f=[]
 for j,(z,rx,ry,cx,cy,phase) in enumerate(rings):
  for i in range(segments+1):
   a=angle_start+(angle_end-angle_start)*i/segments
   folds=1+.025*math.sin(7*a+phase)+.011*math.sin(13*a+2*phase)
   v.append((cx+rx*math.sin(a)*folds,cy+ry*math.cos(a)*folds,z+.003*math.sin(9*a+phase)))
 for j in range(len(rings)-1):
  for i in range(segments):
   aa=j*(segments+1)+i;bb=(j+1)*(segments+1)+i
   f.append((aa,aa+1,bb+1,bb))
 return mesh(name,v,f,mat,weight,thick)
# High-waist inner robe, dark crossed opening, not nude exposed body.
ring_mesh('01 upper black under-robe',[
 (1.05,.210,.153,0,.008,0),(1.23,.221,.162,0,.010,.1),
 (1.37,.278,.201,0,.012,.4),(1.54,.288,.181,0,.017,.3)],
 'shadow',torso,60,.002)
# Open-front kimono layered with narrow V-neck, interrupted at the chest.
outer=[]
for j in range(30):
 t=j/29;z=1.04+t*.495
 outer.append((z,.222+.064*t+.010*math.sin(t*math.pi),.185+.014*t,0,.012,.7))
ring_mesh('02 kimono outer open front',outer,'robe',torso,65,.008,
          math.pi+.31,3*math.pi-.31)
# Worn kimono collar strips, cut into diagonal strips on the upper chest.
def ribbon(name,points,width,mat,bone,thick=.006):
 vs=[];fs=[]
 for idx,p in enumerate(points):
  a=Vector(points[max(0,idx-1)]);b=Vector(points[min(len(points)-1,idx+1)])
  along=(b-a).normalized();N=along.cross(Vector((0,1,0))).normalized()
  if N.length<.01:N=Vector((1,0,0))
  v=Vector(p);w=width*(.92+.08*math.sin(idx*1.5))
  vs.extend([v-N*w/2,v+N*w/2])
 for i in range(len(points)-1):fs.append((2*i,2*i+1,2*i+3,2*i+2))
 return mesh(name,vs,fs,mat,bone,thick)
for side in (-1,1):
 p=[]
 for i in range(14):
  t=i/13
  x=side*(.153*(1-t)+.017*t)
  z=1.53-.34*t
  y=-.196 + .013*t
  p.append((x,y,z))
 ribbon('03 asymmetric kimono lapel '+str(side),p,.034,'robe2',torso,.005)
# Front body panels define crossed kimono silhouette, not bare-shoulder dress.
for ss in (-1,1):
 vertices=[];faces=[];NN=21;MM=31
 for j in range(MM):
  t=j/(MM-1)
  z=1.526-t*.44
  inner=.105*(1-t)+.010*t
  outer=.306*(1-t)+.22*t
  for i in range(NN+1):
   u=i/NN
   x=ss*(inner+(outer-inner)*u)
   y=-.195+.040*u+.016*t+.007*math.sin(u*math.pi)
   vertices.append((x,y,z))
 for j in range(MM-1):
  for i in range(NN):
   k=j*(NN+1)+i;faces.append((k,k+1,k+NN+2,k+NN+1))
 mesh('03a sculpted crossed chest body panel '+str(ss),vertices,faces,
      'robe2' if ss>0 else 'robe',torso,.005)
# Wide flared but intentionally asymmetric torn panels, knee length.
for k in range(11):
 n=11;first=k*math.tau/n-.065;last=(k+1)*math.tau/n+.07
 N=24;L=26;verts=[];faces=[]
 zbase=.605+R.uniform(-.085,.11)
 for j in range(L):
  t=j/(L-1)
  for i in range(N+1):
   a=first+(last-first)*i/N
   rz=zbase+.07*math.sin(k*.8+a*2)
   hem_tear=(R.uniform(-.027,.027) if j==L-1 else 0)
   z=1.045+t*(rz-1.045)+hem_tear
   # More volume behind; skirt opens from waist, layered folds catch light.
   radius=.210+(.095+.023*math.cos(k))*t
   spread=1+.06*math.sin(a*11+k)+.027*math.sin(a*22+2*k)
   x=math.sin(a)*radius*spread
   y=.008+math.cos(a)*radius*.82*spread
   if k%3==0: y+=.012*t
   verts.append((x,y,z))
 for j in range(L-1):
  for i in range(N):
   a=j*(N+1)+i;b=a+(N+1)
   faces.append((a,a+1,b+1,b))
 mesh('04 ragged overlapping kimono panel %02d'%k,verts,faces,
      'robe' if k%4 else 'robe2',fixed('pelvis'),.006)
# Pants with thick gathering over knees, separate leg surfaces.
for side,s in [('l',1),('r',-1)]:
 ring=[]
 for i in range(47):
  t=i/46;z=.945-.63*t
  rx=.123 + .042*math.sin(math.pi*t) - .033*t
  ry=.111 + .027*math.sin(math.pi*t) - .020*t
  phase=.9 if s==1 else 1.9
  x=s*(.114+.007*math.sin(t*math.pi))
  ring.append((z,rx,ry,x,.052,phase+t*5))
 ring_mesh('05 gathered hakama trousers '+side,ring,'shadow',legs(side),48,.004)
# Short shredded sleeves cover biceps but forearms still visibly wrapped.
for side,s in [('l',1),('r',-1)]:
 v=[];f=[];NS=32;NL=16
 for j in range(NL):
  t=j/(NL-1)
  x=s*(.214+.295*t)
  rad=.104+.007*math.sin(t*math.pi)-.009*t
  for i in range(NS+1):
   a=math.tau*i/NS
   ragged=(.009*math.sin(i*3.37+(.7 if s>0 else 1.3)) if j==NL-1 else 0)
   v.append((x+s*ragged,.060+rad*.79*math.cos(a),
             1.456+rad*math.sin(a)*(1+.07*math.sin(a*9+2*t))))
 for j in range(NL-1):
  for i in range(NS):
   a=j*(NS+1)+i;b=a+NS+1;f.append((a,a+1,b+1,b))
 mesh('06 loose torn sleeve '+side,v,f,'robe',fixed('upperarm_'+side),.006)
# Flat woven fabric wrapped around the forearms; no metal-like coils.
def fabric_helix(name,coords_fn,width,mat,bone,stops=190):
 vs=[];fs=[]
 for j in range(stops):
  t=j/(stops-1)
  pa,pb=coords_fn(t,width)
  vs.extend([pa,pb])
 for j in range(stops-1):
  k=2*j;fs.append((k,k+1,k+3,k+2))
 return mesh(name,vs,fs,mat,fixed(bone),.0015)
for side,s in [('l',1),('r',-1)]:
 def f(t,w):
  x=s*(.53+.18*t)
  a=math.tau*(3.3*t+.08)
  rr=.064+.003*(1-t)
  return ((x-w/2,.061+rr*math.cos(a),1.456+rr*math.sin(a)),
          (x+w/2,.061+rr*math.cos(a),1.456+rr*math.sin(a)))
 fabric_helix('07 aged linen forearm bandage '+side,f,.049,'wrap','lowerarm_'+side)
# Wide continuous dark red obi tied at the waist rather than stacked cords.
sashrings=[]
for j in range(24):
 t=j/23
 z=1.01+.121*t
 sashrings.append((z,.234+.005*math.sin(t*math.pi),.188+.005*math.cos(t*math.pi),
                  0,.010,t*3))
ring_mesh('08 single aged-crimson fabric obi',sashrings,'red',fixed('pelvis'),64,.005)
# Sash knot at belly (front y negative) and unequal fabric streamers.
def ellipsoid(name,center,scale,mat,bone,segments=20,rings=12):
 v=[];f=[]
 for j in range(rings+1):
  ph=math.pi*j/rings
  for i in range(segments+1):
   a=math.tau*i/segments
   v.append((center[0]+scale[0]*math.sin(ph)*math.cos(a),
             center[1]+scale[1]*math.sin(ph)*math.sin(a),
             center[2]+scale[2]*math.cos(ph)))
 for j in range(rings):
  for i in range(segments):
   a=j*(segments+1)+i;b=a+segments+1
   f.append((a,b,a+1) if j==rings-1 else (a,b,b+1,a+1))
 return mesh(name,v,f,mat,fixed(bone))
ellipsoid('09 tightly bound red knot',(.025,-.204,1.065),(.034,.013,.025),'red2','pelvis')
for idx in range(3):
 v=[];f=[];W=9;L=40
 x0=-.010+idx*.030
 bottom=[.60,.71,.67][idx]
 for j in range(L):
  t=j/(L-1)
  for i in range(W+1):
   u=(i/W-.5)
   w=(.045-.007*t)
   x=x0+w*u+.038*math.sin(t*math.pi*1.15+idx*.3)*t
   y=-.208-.009*math.sin(t*5+idx*.5)+.013*t
   z=1.043+(bottom-1.043)*t
   if j==L-1:z+=R.uniform(-.025,.022)
   v.append((x,y,z))
 for j in range(L-1):
  for i in range(W):
   a=j*(W+1)+i;b=a+W+1;f.append((a,a+1,b+1,b))
 mesh('10 hanging scarlet sash fringe %d'%idx,v,f,'red' if idx%2 else 'red2',fixed('pelvis'),.003)
# Flat shin bindings and wooden-straw waraji sandals.
for side,sn in [('l',1),('r',-1)]:
 def f(t,w):
  z=.425-.325*t
  a=math.tau*(4.4*t+.09)
  rr=.084+.015*(1-t)
  return ((sn*.114+rr*math.cos(a),.074+rr*.83*math.sin(a),z-w/2),
          (sn*.114+rr*math.cos(a),.074+rr*.83*math.sin(a),z+w/2))
 fabric_helix('11 bound calf fabric '+side,f,.060,'wrap','calf_'+side)
 ellipsoid('12 thin woven sandal footbed '+side,(sn*.114,-.049,.021),
           (.080,.15,.012),'sole','foot_'+side)
 for kk,z in enumerate((.061,.072)):
  pts=[]
  for j in range(25):
   t=j/24
   x=sn*.114+(t-.5)*.12
   yy=[-.09,-.014][kk]+.02*math.sin(math.pi*t)
   zz=z+.016*math.sin(math.pi*t)
   pts.append((x,yy,zz))
  ribbon('13 waraji strap '+side+str(kk),pts,.013,'wrap',fixed('foot_'+side),.001)
# Tied black hair as head-bound actual 3D mesh curves.
def hair_lock(name,path,radius,mat='hair',bone='Head'):
 points=[Vector(a) for a in path];verts=[];faces=[];seg=7
 for i,p in enumerate(points):
  tan=(points[min(len(points)-1,i+1)]-points[max(0,i-1)]).normalized()
  side=tan.cross(Vector((0,0,1))).normalized()
  if side.length<.001:side=Vector((1,0,0))
  up=tan.cross(side).normalized()
  r=radius*(1-i/max(1,len(points)-1))**.65+.0005
  for j in range(seg):
   a=math.tau*j/seg
   verts.append(tuple(p+r*(math.cos(a)*side+math.sin(a)*up)))
 for i in range(len(points)-1):
  for j in range(seg):
   a=i*seg+j;b=i*seg+(j+1)%seg
   faces.append((a,b,b+seg,a+seg))
 mesh(name,verts,faces,mat,fixed(bone))
def interp(p0,p1,p2,p3,n=11):
 a,b,c,d=[Vector(p) for p in (p0,p1,p2,p3)]
 return [tuple((1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d) for t in (i/(n-1) for i in range(n))]
# Hair cap follows scalp; root center forehead around -Y.
# Crown shell clipped away from the face, leaving forehead and ears exposed.
verts=[];faces=[];NW=48;NH=25
for j in range(NH+1):
 ph=.001+(math.pi-.002)*j/NH
 for i in range(NW+1):
  a=math.tau*i/NW
  x=.113*math.sin(ph)*math.cos(a)
  y=.028+.101*math.sin(ph)*math.sin(a)
  z=1.759+.105*math.cos(ph)
  verts.append((x,y,z))
for j in range(NH):
 for i in range(NW):
  k=j*(NW+1)+i;u=(verts[k],verts[k+1],verts[k+NW+1],verts[k+NW+2])
  if sum(1 for q in u if q[1] < -.047 and q[2]<1.79)>0:continue
  if sum(1 for q in u if q[2]<1.673)>0:continue
  faces.append((k,k+1,k+NW+2,k+NW+1))
mesh('14 clipped swept-hair cap',verts,faces,'hair',fixed('Head'),.002)
# Back-swept hair pulled into a topknot plus flyaway fringe.
for i in range(90):
 a=R.uniform(0,math.tau)
 phi=R.uniform(.1,1.32)
 x=.113*math.sin(phi)*math.cos(a)
 y=.010+.098*math.sin(phi)*math.sin(a)
 z=1.75+.106*math.cos(phi)
 q=(x,y,z)
 middle=(x*.85,y+.015,z+.036+R.uniform(.0,.035))
 end=(R.uniform(-.05,.05),.126+R.uniform(-.019,.023),1.88+R.uniform(-.018,.035))
 path=interp(q,middle,(end[0],end[1]-.015,end[2]-.02),end,12)
 hair_lock('15 swept hair strand %03d'%i,path,R.uniform(.002,.005),
           'hair2' if i%13==0 else 'hair')
# Hair knot and tuft are deliberately irregular, not a round smooth ball.
ellipsoid('16 raised bound topknot',(.003,.126,1.884),(.050,.051,.040),'hair','Head',26,14)
for i in range(22):
 x=R.uniform(-.055,.055);yb=R.uniform(.09,.16)
 end=(x+R.uniform(-.13,.13),yb+R.uniform(-.14,.15),1.89+R.uniform(-.03,.055))
 hair_lock('17 loose topknot spikes %02d'%i,interp((x,yb,1.89),
    (x+.02,yb+.015,1.98),(end[0],end[1],end[2]+.038),end,10),
    R.uniform(.0015,.004),'hair' if i%4 else 'hair2')
# Deliberately uneven hair hanging across brow and at temples.
for i in range(20):
 side=R.choice((-1,1))
 sx=R.uniform(.018,.113)*side
 p0=(sx,-.083,1.811+R.uniform(-.025,.03))
 p1=(sx*.96,-.12,1.77)
 p2=(sx*R.uniform(.6,1.4),-.137,1.69+R.uniform(-.025,.025))
 p3=(sx*R.uniform(.7,1.5),-.123,1.708+R.uniform(-.035,.040))
 hair_lock('18 loose fringe %02d'%i,interp(p0,p1,p2,p3,12),
           R.uniform(.002,.005),'hair' if i%10 else 'hair2')
for i in range(44):
 side=R.choice((-1,1));x0=side*R.uniform(.055,.115)
 p0=(x0,.080,1.78);p3=(x0+side*R.uniform(.0,.10),.14+R.uniform(-.05,.09),
                          1.63+R.uniform(-.06,.09))
 hair_lock('19 nape strand %02d'%i,interp(p0,(x0,.12,1.72),
        (p3[0],p3[1]+.05,1.60),p3,12),R.uniform(.002,.005))
# Scar/facial hair: minimal to preserve existing facial sculpture.

# Eye-level cheek scar: muted, not cartoonishly bright.
scar=material('Healed light facial scar',(.35,.21,.19),.85,variation=.09,noise_scale=70,bump=0)
ribbon('21 narrow diagonal cheek scar',[(.076,-.111,1.665),(.071,-.119,1.65),(.064,-.123,1.636)],
       .0025,scar,fixed('Head'),.0002)
# Materials / lighting / stage
stage=bpy.data.objects.get('QA stage')
if stage:
 stage.data.materials.clear()
 stage.data.materials.append(material('Neutral graphite photo floor',(.045,.045,.052),.9,variation=.09,noise_scale=3,bump=.01))
for l in [o for o in bpy.data.objects if o.type=='LIGHT']:
 l.data.energy*=.7
# Supplemental warm hair rim and broad warm key (without blowing skin whites).
def area(name,loc,power,size,color):
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=color
 obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj)
 obj.location=loc;obj.rotation_euler=(Vector((0,0,1.2))-obj.location).to_track_quat('-Z','Y').to_euler()
area('Musashi photographic soft key',(2.9,-3.0,3.3),180,3.4,(1,.83,.72))
area('Musashi cool contour',(-2.8,1.7,2.4),180,2.1,(.58,.68,1))
scene.world.color=(.07,.07,.08)
scene.render.engine='BLENDER_EEVEE'
scene.render.image_settings.file_format='PNG'
scene.render.resolution_x=800
scene.render.resolution_y=1150
scene.render.resolution_percentage=100
scene.render.film_transparent=False
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=-1.35
scene.camera.data.type='ORTHO'
cam=scene.camera
def setcam(position,target=(0,0,1.05)):
 cam.location=position
 cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
 cam.data.ortho_scale=2.55
bpy.context.view_layer.update()
for view,loc in [('front',(0,-4.8,1.4)),('left_side',(4.8,-.01,1.42)),
                 ('three_quarter',(3.3,-3.4,1.42)),('back',(0,4.8,1.4))]:
 setcam(loc)
 scene.render.filepath=str(OUT/(view+'.png'))
 bpy.ops.render.render(write_still=True)
 print('MUSASHI_RENDERED',view)
setcam((3.3,-3.4,1.42))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'musashi_sheet_exterior_v3.blend'))
from collections import Counter
c=Counter(o.name.split(' ')[1] if len(o.name.split(' '))>1 else 'misc' for o in bpy.data.objects)
(OUT/'model_status.json').write_text(json.dumps({
 'source':'2026-11-14 approved 4-view Musashi character sheet',
 'status':'first-pass 3D outfit and hair BLOCKOUT, not final production character',
 'preserved_skeleton':rig.name,'total_objects':len(bpy.data.objects),
 'outputs':['front.png','left_side.png','three_quarter.png','back.png',
   'musashi_sheet_exterior_v3.blend'],
 'unresolved':['face likeness','handcrafted garments','hair grooming','realistic textile detail',
 'clothing topology and deformation QA','rigged combat animations'],
 'object_groups':dict(c)},ensure_ascii=False,indent=2),encoding='utf-8')
print('MUSASHI_SHEET_V3_COMPLETE')

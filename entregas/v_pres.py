import sys; sys.path.insert(0,'/home/claude/re')
import engine
from engine import *
engine.BT = 0.6
# ---------- trilha de jornal sintetizada (100 bpm) ----------
BT = 0.6; L = 56; N = int(L*SR); mus = np.zeros((N,2), np.float32); rng = np.random.default_rng(3)
def put(x, at, g=1.0, pan=0.0):
    i=int(at*SR); n=min(len(x),N-i)
    if n>0: mus[i:i+n,0]+=x[:n]*g*(1-pan); mus[i:i+n,1]+=x[:n]*g*(1+pan)
prog=[(50,53,57),(46,50,53),(53,57,60),(48,52,55)]  # Dm Bb F C
for bar in range(int(L/(4*BT))+1):
    ch=prog[bar%4]; t0=bar*4*BT
    for k in range(8):
        put(note(mfreq(ch[0]-12),0.28,0.5,9,0.6),t0+k*BT/2,0.55)
    for k in range(4):
        tt=t0+k*BT; n=int(0.25*SR); tk=np.arange(n)/SR
        if k in (0,2): put((np.sin(2*np.pi*np.cumsum(50+80*np.exp(-tk*30))/SR)*np.exp(-tk*12)).astype(np.float32),tt,0.7)
        for h in (0,0.5):
            hn=int(0.05*SR); hx=sosfilt(butter(2,7000,'high',fs=SR,output='sos'),rng.standard_normal(hn))*np.exp(-np.arange(hn)/SR*90)
            put(hx.astype(np.float32),tt+h*BT,0.12 if h else 0.18,0.3)
    arp=[ch[0]+12,ch[1]+12,ch[2]+12,ch[1]+12]
    for k,m in enumerate(arp): put(note(mfreq(m),1.2,0.22,3.5,1.2),t0+k*BT+ (0.3 if k%2 else 0),0.8,-0.3)
    pad=sum(note(mfreq(m),4*BT,0.1,0.3,0.4) for m in ch); put(pad,t0,0.5)
0 or sf.write('/home/claude/music/news.wav', (mus/np.abs(mus).max()*0.9).astype(np.float32), SR)
# ---------- cortes ----------
C='pres'
SG=[(10.95,15.72,None),(30.96,35.12,'punch'),(35.55,46.74,'punch'),(46.86,50.10,'punch'),(57.88,63.86,'punch'),
    (87.30,89.97,'punch'),(92.24,95.42,'punch'),(154.90,158.36,'punch'),(158.36,162.78,None)]
segs=[dict(clip=C,a=a,b=b,tr=tr) for a,b,tr in SG]
P,TVp=plan(segs)
def src2out(s):
    for g in P:
        if g['a']-0.02<=s<g['b']: return g['t0']+(s-g['a'])
    return None
WS=[]
for g in P:
    for s,e,w in words(C,g['a'],g['b']):
        w=w.replace('Vajota','Varjota').strip(' ,.?').upper()
        if not w: continue
        WS.append((g['t0']+s-g['a'], g['t0']+min(e,g['b'])-g['a'], w, P.index(g)))
# agrupa em linhas (uma linha, máx ~940px)
SUBF=font('Inter-900',62)
def wpx(s): return SUBF.getbbox(s)[2]
LINES=[]; cur=[]
for w in WS:
    if cur and (wpx(' '.join(x[2] for x in cur+[w]))>900 or len(cur)>=4 or w[3]!=cur[-1][3] or w[0]-cur[-1][1]>0.5):
        LINES.append(cur); cur=[]
    cur.append(w)
if cur: LINES.append(cur)
# ---------- elementos ----------
NAVY=(10,16,34); RED=(222,32,44); YEL=(255,206,0)
def tseg(i): return P[i]['t0'], P[i]['t1']
def rr_mask(w,h,r):
    m=Image.new('L',(w,h),0); ImageDraw.Draw(m).rounded_rectangle([0,0,w-1,h-1],r,fill=255); return m
WX,WY,WW=40,330,1000; WH=1040; MASK=rr_mask(WW,WH,34)
def box(text,f,fg,bg,padx=26,pady=14,r=10):
    t=text_img(text,f,fg,pad=0); im=Image.new('RGBA',(t.width+2*padx,t.height+2*pady),(0,0,0,0))
    ImageDraw.Draw(im).rounded_rectangle([0,0,im.width-1,im.height-1],r,fill=bg); im.alpha_composite(t,(padx,pady)); return im
KICK=box('BASTIDORES DA CÂMARA',font('Inter-900',34),(255,255,255),RED,20,10,6)
HEAD1=text_img('PRESIDENTE DA CÂMARA FALA',font('Anton',76),(255,255,255),pad=4)
HEAD2=text_img('DO CONCURSO PÚBLICO',font('Anton',76),YEL,pad=4)
HANDLE=text_img('@falathiagoo',font('Inter-800',30),(255,255,255),pad=2)
CRED=text_img('Imagens: @roberto_lira_noticia',font('Inter-600',26),(200,206,220),pad=2)
_lt=text_img('VARJOTA-CE',font('Inter-900',28),(255,255,255),pad=2); LIVE=Image.new('RGBA',(_lt.width+34,_lt.height),(0,0,0,0)); ImageDraw.Draw(LIVE).ellipse([2,_lt.height//2-9,20,_lt.height//2+9],fill=RED); LIVE.alpha_composite(_lt,(34,0))
def lower(name,role):
    a=text_img(name,font('Inter-900',40),NAVY,pad=0); b=text_img(role,font('Inter-800',28),(255,255,255),pad=0)
    w=max(a.width,b.width)+60; im=Image.new('RGBA',(w,a.height+b.height+60),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.rectangle([0,0,w,a.height+28],fill=(255,255,255)); d.rectangle([0,a.height+28,w,im.height],fill=RED); d.rectangle([0,0,10,im.height],fill=YEL)
    im.alpha_composite(a,(30,14)); im.alpha_composite(b,(30,a.height+40)); return im
LT0=lower('PERGUNTA: ROBERTO LIRA','JORNALISTA'); LT1=lower('ROBERTO DO GARRONE','PRESIDENTE DA CÂMARA DE VARJOTA')
def card(lab,val):
    a=text_img(lab,font('Inter-900',30),(255,255,255),pad=0); b=text_img(val,font('Anton',62),NAVY,pad=0)
    w=max(a.width+40,b.width+60); im=Image.new('RGBA',(w,a.height+b.height+56),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.rectangle([0,0,a.width+40,a.height+18],fill=RED); d.rectangle([0,a.height+18,w,im.height],fill=(255,255,255))
    im.alpha_composite(a,(20,9)); im.alpha_composite(b,(30,a.height+30)); return im
CARDS=[(1,'PROJETO DE LEI','PROTOCOLADO NA CÂMARA'),(3,'NAS PALAVRAS DELE','“O PRIMEIRO DO MUNICÍPIO”'),
       (5,'EDITAL','“NOS PRÓXIMOS MESES”'),(7,'VAGAS','5 CARGOS EFETIVOS')]
CARDS=[(tseg(i)[0]+0.3,(tseg(i+1)[1] if i in (1,5,7) else tseg(i)[1])-0.2,card(l,v)) for i,l,v in CARDS]
RES=box('+ CADASTRO DE RESERVA',font('Inter-900',34),NAVY,YEL,18,10,6)
BGDARK=Image.new('RGBA',(W,H),NAVY+(150,))
def slide_in(c,im,t,t0,t1,x,y):
    if not t0<=t<t1: return
    p=e_back(clamp((t-t0)/0.45),1.3); q=clamp((t1-t)/0.3)
    xx=x-(1-p)*700+ (1-q)*80
    if p<0.9:  # rastro
        for k in (3,2,1): paste(c,im,xx-k*40*(1-p)+im.width/2,y+im.height/2,alpha=0.18*k*(1-p))
    paste(c,im,xx+im.width/2,y+im.height/2,alpha=q)
def odo(c,t,t0,x,y,target,col,size=330):
    # odômetro rolando até o alvo
    p=e_out(clamp((t-t0)/1.1)); v=p*target; f=font('Anton',size)
    s=f'{int(v)%100:02d}'; frac=v-int(v)
    for k,dig in enumerate(s):
        a=text_img(dig,f,col,pad=0); nxt=text_img(str((int(dig)+1)%10) if k==1 else dig,f,col,pad=0)
        hh=a.height+20; cx=x+(k-0.5)*a.width*1.05
        if k==1 and frac>0.01 and p<1:
            paste(c,a,cx,y-frac*hh*0.9,alpha=1-frac); paste(c,nxt,cx,y+(1-frac)*hh*0.9,alpha=frac)
        else: paste(c,a,cx,y)
TAIL=4.6
def overlay(c,t,n,SEGS,TV):
    fr=c.convert('RGB')
    win=fr.crop((0,45,1080,45+int(1080*WH/WW))).resize((WW,WH),Image.LANCZOS)
    bg=fr.resize((W//10,H//10),Image.BILINEAR).filter(ImageFilter.GaussianBlur(4)).resize((W,H),Image.BILINEAR).convert('RGBA')
    bg.alpha_composite(BGDARK); out=bg
    if t>=TV:  # fecho: janela encolhe e escurece
        q=e_io(clamp((t-TV)/0.6)); win=Image.blend(win,Image.new('RGB',win.size,NAVY),0.55*q)
        if q>0: win=win.filter(ImageFilter.GaussianBlur(8*q))
    wa=win.convert('RGBA'); wa.putalpha(MASK)
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); m=Image.new('L',(W,H),0); m.paste(MASK,(WX,WY)); sh.putalpha(m.filter(ImageFilter.GaussianBlur(24)).point(lambda v:int(v*0.6)))
    out.alpha_composite(sh,(0,14)); out.alpha_composite(wa,(WX,WY))
    d=ImageDraw.Draw(out); d.rounded_rectangle([WX,WY,WX+WW-1,WY+WH-1],34,outline=(255,255,255,70),width=3)
    # topo
    hp=e_out(clamp((t-2.4)/0.5)) if t<3.5 else 1
    paste(out,KICK,40+KICK.width/2,70,alpha=hp); paste(out,HANDLE,1040-HANDLE.width/2,70,alpha=hp)
    paste(out,HEAD1,540,165-40*(1-hp),alpha=hp); paste(out,HEAD2,540,255-40*(1-hp),alpha=clamp((t-2.6)/0.4) if t<3.5 else 1)
    lv=0.55+0.45*(math.sin(t*5)>0); paste(out,LIVE,WX+30+LIVE.width/2,WY+40,alpha=lv*(t<TV))
    paste(out,CRED,540,1880)
    if t<TV:
        slide_in(out,LT0,t,0.5,tseg(0)[1]-0.2,WX,WY+WH-LT0.height-40)
        slide_in(out,LT1,t,tseg(1)[0]+0.2,tseg(1)[0]+4.8,WX,WY+WH-LT1.height-40)
        for a,b,im in CARDS: slide_in(out,im,t,a,b,WX,1560)
        if tseg(8)[0]+0.2<=t<tseg(8)[1]-0.2: slide_in(out,RES,t,tseg(8)[0]+0.2,tseg(8)[1]-0.2,WX,1700)
        # legenda: uma linha, palavra ativa amarela
        for L in LINES:
            if L[0][0]-0.05<=t<L[-1][1]+0.25 and all(not (L2[0][0]-0.05<=t) or L2 is L or L2[0][0]<L[0][0] for L2 in LINES):
                pass
        act=[L for L in LINES if L[0][0]-0.05<=t]
        if act:
            L=act[-1]
            if t<L[-1][1]+0.35:
                ims=[text_img(w[2],SUBF,(YEL if w[0]<=t<w[1]+0.05 else (255,255,255)) if w[0]<=t else (255,255,255,110),stroke=6,sfill=(0,0,0),pad=4) for w in L]
                tw=sum(i.width for i in ims)+14*(len(ims)-1); x=540-tw/2; pin=clamp((t-L[0][0]+0.05)/0.15)
                for i in ims: paste(out,i,x+i.width/2,1450+12*(1-pin),alpha=pin); x+=i.width+14
    # abertura: gancho
    if t<2.6:
        a=clamp((2.6-t)/0.35); dk=Image.new('RGBA',(W,H),(0,0,0,int(150*a))); out.alpha_composite(dk)
        slam(out,big('ELEIÇÃO',200,(255,255,255)),t-0.05,2.5,y=720)
        slam(out,big('NA CÂMARA',170,YEL),t-0.45,2.1,y=900)
        if t>0.9:
            q=clamp((t-0.9)/0.25)*a; paste(out,box('QUINTA, 19 DE NOVEMBRO',font('Inter-900',46),(255,255,255),RED,24,14,8),540,1080,alpha=q,scale=0.9+0.1*q)
        if t>1.3: paste(out,text_img('E o atual presidente fala...',font('Serif-It',58),(255,255,255),pad=4),540,1200,alpha=clamp((t-1.3)/0.3)*a)
    # fecho
    if t>=TV:
        lt=t-TV; dk=Image.new('RGBA',(W,H),(0,0,0,int(110*e_io(clamp(lt/0.5))))); out.alpha_composite(dk)
        slam(out,big('PRESIDÊNCIA',150),lt-0.3,TAIL,y=640)
        slam(out,big('DA CÂMARA',150,YEL),lt-0.6,TAIL,y=800)
        if lt>0.9:
            q=clamp((lt-0.9)/0.3); paste(out,box('ELEIÇÃO NA QUINTA',font('Inter-900',52),(255,255,255),RED,26,14,8),540,960,alpha=q)
            odo(out,t,TV+1.0,540,1180,19,(255,255,255)); paste(out,text_img('/ 11',font('Anton',130),YEL,pad=4),540+250,1215,alpha=clamp((lt-1.9)/0.3))
        if lt>2.4: paste(out,text_img('Quem leva? Comenta aqui.',font('Inter-900',54),(255,255,255),stroke=4,sfill=(0,0,0),pad=4),540,1440,alpha=clamp((lt-2.4)/0.3),scale=0.94+0.06*clamp((lt-2.4)/0.3))
    return out
def extra(sfx):
    sfx(riser(1.0),-0.6,0.0); sfx(impact(1.0),0.05,0.35); sfx(impact(0.8),0.45,0.25); sfx(pop(),0.9,0.4)
    for a,b,im in CARDS: sfx(whoosh(0.35),a-0.1,0.18); sfx(pop(),a+0.25,0.25)
    sfx(whoosh(0.5),TVp-0.2,0.22); sfx(impact(1.0),TVp+0.3,0.4); sfx(impact(0.9),TVp+0.6,0.3)
    for k in range(10): sfx(tick(),TVp+1.0+k*0.1,0.3)
    sfx(impact(0.8),TVp+2.1,0.3)
GR='eq=contrast=1.06:saturation=1.08:gamma=0.98,colorbalance=rs=0.02:bs=-0.02,unsharp=5:5:0.8'
run('falathiagoo_presidencia_camara_v1',GR,segs,dict(file='/home/claude/music/news.wav',offset=0,vol=(0.5,0.12),dips=[]),overlay,
    speech_idx=tuple(range(len(segs))),voice_level=0.1,tail=TAIL,sfx_extra=extra,grain_amt=0.06,bloom_on=False)

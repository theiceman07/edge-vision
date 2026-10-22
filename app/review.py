"""Fast label review: python review.py  ->  http://localhost:5001
Click a box to toggle it off/on. Drag on empty space to add a box. Enter = save & next, Backspace = back.
Reviewed labels are written to review/<image>.txt (class from the photo's folder)."""
import glob, json, os
from pathlib import Path
import cv2
from flask import Flask, jsonify, request, send_file
from autolabel import refine, CLASSES

app = Flask(__name__)
RAW = json.load(open("ds_my/raw.json"))
ITEMS = sorted(p for p in RAW if "/nut/" in p or "/bolt/" in p)
os.makedirs("review", exist_ok=True)


def cls_of(p):
    return 1 if "/nut/" in p else 0


def lab(p):
    return Path("review") / (Path(p).stem + ".json")


@app.route("/api/n")
def n():
    done = sum(lab(p).exists() for p in ITEMS)
    first = next((i for i, p in enumerate(ITEMS) if not lab(p).exists()), 0)
    return jsonify(n=len(ITEMS), done=done, first=first)


@app.route("/api/item/<int:i>")
def item(i):
    p = ITEMS[i]
    h, w = cv2.imread(p).shape[:2]
    if lab(p).exists():
        boxes = json.load(open(lab(p)))
    else:                                           # loose proposals; you delete the wrong ones
        boxes = [[b[0], b[1], b[2], b[3], 1] for b in refine(RAW[p], cls_of(p), w, h, 0.004)]
    return jsonify(w=w, h=h, boxes=boxes, cls=CLASSES[cls_of(p)], reviewed=lab(p).exists(), name=Path(p).name)


@app.route("/img/<int:i>")
def img(i):
    return send_file(ITEMS[i])


@app.route("/api/save/<int:i>", methods=["POST"])
def save(i):
    p = ITEMS[i]
    boxes = request.get_json()
    json.dump(boxes, open(lab(p), "w"))
    h, w = cv2.imread(p).shape[:2]
    with open(Path("review") / (Path(p).stem + ".txt"), "w") as f:
        for x, y, bw, bh, on in boxes:
            if on:
                f.write(f"{cls_of(p)} {(x+bw/2)/w:.6f} {(y+bh/2)/h:.6f} {bw/w:.6f} {bh/h:.6f}\n")
    return jsonify(ok=True)


@app.route("/")
def index():
    return PAGE


PAGE = """<!doctype html><meta charset=utf-8><title>Label review</title>
<style>body{margin:0;background:#111;color:#eee;font:15px system-ui}#top{padding:8px 14px;display:flex;gap:16px;align-items:center}
canvas{display:block;margin:0 auto;cursor:crosshair}b{color:#7cf}kbd{background:#333;padding:1px 6px;border-radius:4px}</style>
<div id=top><span id=info></span><span>click box = toggle &nbsp; drag = add &nbsp; <kbd>Enter</kbd> save+next &nbsp; <kbd>Backspace</kbd> back</span></div>
<canvas id=c></canvas>
<script>
let i=0,N=0,D=null,sc=1,drag=null;const c=document.getElementById('c'),g=c.getContext('2d'),img=new Image();
async function init(){const r=await (await fetch('/api/n')).json();N=r.n;i=r.first;load()}
async function load(){D=await (await fetch('/api/item/'+i)).json();img.onload=draw;img.src='/img/'+i;
 document.getElementById('info').innerHTML=`<b>${i+1}/${N}</b> &nbsp; class: <b>${D.cls}</b> &nbsp; ${D.reviewed?'(reviewed)':''} &nbsp; boxes on: ${D.boxes.filter(b=>b[4]).length}`}
function draw(){sc=Math.min(1.5,(innerWidth-20)/D.w,(innerHeight-60)/D.h);c.width=D.w*sc;c.height=D.h*sc;g.drawImage(img,0,0,c.width,c.height);
 D.boxes.forEach(b=>{g.lineWidth=2;g.strokeStyle=b[4]?(D.cls=='nut'?'#3f3':'#4af'):'rgba(255,60,60,.7)';g.setLineDash(b[4]?[]:[5,4]);g.strokeRect(b[0]*sc,b[1]*sc,b[2]*sc,b[3]*sc)});
 if(drag){g.setLineDash([]);g.strokeStyle='#ff0';g.strokeRect(drag.x0,drag.y0,drag.x1-drag.x0,drag.y1-drag.y0)}
 document.getElementById('info').innerHTML=document.getElementById('info').innerHTML.replace(/boxes on: \\d+/,'boxes on: '+D.boxes.filter(b=>b[4]).length)}
const pos=e=>{const r=c.getBoundingClientRect();return[e.clientX-r.left,e.clientY-r.top]};
c.onmousedown=e=>{const[x,y]=pos(e);drag={x0:x,y0:y,x1:x,y1:y}};
c.onmousemove=e=>{if(drag){[drag.x1,drag.y1]=pos(e);draw()}};
c.onmouseup=e=>{const d=drag;drag=null;if(Math.abs(d.x1-d.x0)<6&&Math.abs(d.y1-d.y0)<6){const x=d.x0/sc,y=d.y0/sc;
  let best=-1,ba=1e18;D.boxes.forEach((b,k)=>{if(x>=b[0]&&x<=b[0]+b[2]&&y>=b[1]&&y<=b[1]+b[3]&&b[2]*b[3]<ba){ba=b[2]*b[3];best=k}});
  if(best>=0)D.boxes[best][4]^=1}else{const x0=Math.min(d.x0,d.x1)/sc,y0=Math.min(d.y0,d.y1)/sc;D.boxes.push([Math.round(x0),Math.round(y0),Math.round(Math.abs(d.x1-d.x0)/sc),Math.round(Math.abs(d.y1-d.y0)/sc),1])}draw()};
async function save(){await fetch('/api/save/'+i,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(D.boxes)})}
onkeydown=async e=>{if(e.key=='Enter'){await save();if(i<N-1){i++;load()}else document.getElementById('info').textContent='ALL DONE - tell Claude'}
 if(e.key=='Backspace'&&i>0){e.preventDefault();i--;load()}};
init()
</script>"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)

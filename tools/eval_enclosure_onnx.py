# Edit the model path (app/enclosure.onnx or app/enclosure_int8.onnx) at the InferenceSession line. Own evaluation: conf 0.25, IoU 0.5, letterbox 480, NMS 0.7, AP50 all-point at conf 0.001.
import cv2, numpy as np, onnxruntime as ort, glob, os, sys, json
R="/home/juice/edge computing/edge-vision"
ds=R+"/training/enclosure_ds/test"
names=["enclosure_good","enclosure_defective"]
s=ort.InferenceSession(R+"/app/enclosure.onnx",providers=["CPUExecutionProvider"])
inp=s.get_inputs()[0].name; S_=480
def iou(a,b):
    x1=max(a[0],b[0]);y1=max(a[1],b[1]);x2=min(a[2],b[2]);y2=min(a[3],b[3])
    i=max(0,x2-x1)*max(0,y2-y1); u=(a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-i
    return i/u if u>0 else 0
def pred(img,conf):
    h,w=img.shape[:2]; r=min(S_/h,S_/w); nh,nw=round(h*r),round(w*r)
    im=cv2.resize(img,(nw,nh)); can=np.full((S_,S_,3),114,np.uint8)
    dy,dx=(S_-nh)//2,(S_-nw)//2; can[dy:dy+nh,dx:dx+nw]=im
    x=can[:,:,::-1].transpose(2,0,1)[None].astype(np.float32)/255
    o=s.run(None,{inp:x})[0][0].T
    sc=o[:,4:]; c=sc.argmax(1); p=sc.max(1); m=p>=conf; o,c,p=o[m],c[m],p[m]
    b=np.stack([o[:,0]-o[:,2]/2,o[:,1]-o[:,3]/2,o[:,0]+o[:,2]/2,o[:,1]+o[:,3]/2],1)
    b=(b-[dx,dy,dx,dy])/r
    k=cv2.dnn.NMSBoxes([[x1,y1,x2-x1,y2-y1] for x1,y1,x2,y2 in b.tolist()],p.tolist(),conf,0.7)
    k=np.array(k).flatten().astype(int)
    return [(b[i].tolist(),int(c[i]),float(p[i])) for i in k]
def gt(f,h,w):
    out=[]
    if os.path.exists(f):
        for l in open(f):
            q=l.split()
            if len(q)>=5:
                c,x,y,bw,bh=int(q[0]),*map(float,q[1:5])
                out.append(([(x-bw/2)*w,(y-bh/2)*h,(x+bw/2)*w,(y+bh/2)*h],c))
    return out
imgs=sorted(glob.glob(ds+"/images/*.jpg"))
def run(conf):
    tp=[[] for _ in names]; ngt=[0,0]; errs=[]; P={}
    for f in imgs:
        img=cv2.imread(f); h,w=img.shape[:2]
        g=gt(ds+"/labels/"+os.path.basename(f)[:-4]+".txt",h,w); pr=pred(img,conf); P[f]=pr
        for _,c in g: ngt[c]+=1
        used=set()
        for b,c,p in sorted(pr,key=lambda t:-t[2]):
            best,bj=0,-1
            for j,(gb,gc) in enumerate(g):
                if gc==c and j not in used:
                    v=iou(b,gb)
                    if v>best: best,bj=v,j
            if best>=0.5: used.add(bj); tp[c].append((p,1))
            else:
                tp[c].append((p,0))
                cl=[gc for gb,gc in g if gc!=c and iou(b,gb)>=0.5]
                errs.append((os.path.basename(f),"class confusion (pred %s, gt %s)"%(names[c],names[cl[0]]) if cl else "false positive %s"%names[c],round(p,2)))
        for j,(gb,gc) in enumerate(g):
            if j not in used: errs.append((os.path.basename(f),"missed %s"%names[gc],None))
    return tp,ngt,errs
tp,ngt,errs=run(0.001)
ap=[]
for c in range(2):
    t=sorted(tp[c],key=lambda x:-x[0]); tpc=np.cumsum([x[1] for x in t]); fpc=np.cumsum([1-x[1] for x in t])
    rec=tpc/max(ngt[c],1); prec=tpc/np.maximum(tpc+fpc,1e-9)
    mrec=np.concatenate([[0],rec,[1]]); mpre=np.concatenate([[1],prec,[0]])
    mpre=np.flip(np.maximum.accumulate(np.flip(mpre))); i=np.where(mrec[1:]!=mrec[:-1])[0]
    ap.append(float(((mrec[i+1]-mrec[i])*mpre[i+1]).sum()))
tp,ngt2,errs=run(0.25)
print("test images",len(imgs),"gt per class",dict(zip(names,ngt)))
for c in range(2):
    n=sum(x[1] for x in tp[c]); d=len(tp[c])
    print(names[c],"TP",n,"pred",d,"gt",ngt[c],"P %.3f R %.3f AP50 %.3f"%(n/max(d,1),n/max(ngt[c],1),ap[c]))
T=sum(x[1] for c in range(2) for x in tp[c]); D=sum(len(tp[c]) for c in range(2))
print("ALL P %.3f R %.3f mAP50 %.3f"%(T/max(D,1),T/sum(ngt),np.mean(ap)))
for e in errs: print(e)

"""Run results/weights/best.onnx on ds3/test (320 px letterless resize), list wrong detections (conf>=0.25, IoU>=0.5)."""
import glob, json, os, sys
import cv2, numpy as np, onnxruntime as ort

NAMES = ["bolt", "nut"]; CONF, IOU_T, NMS_T = 0.25, 0.5, 0.7
sess = ort.InferenceSession("results/weights/best.onnx", providers=["CPUExecutionProvider"])
inp = sess.get_inputs()[0].name

def iou(a, b):
    x1, y1, x2, y2 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    i = max(0, x2 - x1) * max(0, y2 - y1)
    return i / ((a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - i + 1e-9)

def predict(img):
    x = cv2.resize(img, (320, 320))[:, :, ::-1].transpose(2, 0, 1)[None].astype(np.float32) / 255
    out = sess.run(None, {inp: np.ascontiguousarray(x)})[0][0]      # (6, N)
    out = out.T; sc = out[:, 4:].max(1); cl = out[:, 4:].argmax(1); k = sc >= CONF
    out, sc, cl = out[k], sc[k], cl[k]
    boxes = np.stack([out[:,0]-out[:,2]/2, out[:,1]-out[:,3]/2, out[:,0]+out[:,2]/2, out[:,1]+out[:,3]/2], 1) / 320
    order = np.argsort(-sc); keep = []
    for i in order:
        if all(iou(boxes[i], boxes[j]) < NMS_T for j in keep): keep.append(i)
    return [(boxes[i], int(cl[i]), float(sc[i])) for i in keep]

def labels(path):
    res = []
    for l in open(path):
        p = l.split()
        if not p: continue
        c = int(p[0]); v = list(map(float, p[1:]))
        if len(v) == 4:
            x, y, w, h = v; res.append(((x-w/2, y-h/2, x+w/2, y+h/2), c))
        else:
            xs, ys = v[0::2], v[1::2]; res.append(((min(xs), min(ys), max(xs), max(ys)), c))
    return res

errs = []; tp = 0
for f in sorted(glob.glob("ds3/test/images/*.jpg")):
    img = cv2.imread(f); gt = labels(f.replace("images", "labels").rsplit(".", 1)[0] + ".txt")
    pr = predict(img); used = set()
    for b, c, s in pr:
        best, bj = 0, -1
        for j, (g, gc) in enumerate(gt):
            v = iou(b, g)
            if v > best and j not in used: best, bj = v, j
        if best >= IOU_T:
            used.add(bj)
            if gt[bj][1] == c: tp += 1
            else: errs.append(dict(img=f, kind="class confusion", pred=NAMES[c], true=NAMES[gt[bj][1]], conf=round(s,2), box=b.tolist()))
        else:
            errs.append(dict(img=f, kind="false positive", pred=NAMES[c], true="-", conf=round(s,2), box=b.tolist()))
    for j, (g, gc) in enumerate(gt):
        if j not in used: errs.append(dict(img=f, kind="missed", pred="-", true=NAMES[gc], conf=0, box=list(g)))
print("correct detections:", tp, "errors:", len(errs))
from collections import Counter; print(Counter(e["kind"] for e in errs))
json.dump(errs, open("errors/errors.json", "w"), indent=1)

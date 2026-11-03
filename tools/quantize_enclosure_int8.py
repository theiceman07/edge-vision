# Usage: python quantize_enclosure_int8.py <scratch_dir>  (needs onnx, onnxruntime, opencv). Opset 12 -> 13 conversion (enc_pre13.onnx) was done by hand with onnx.version_converter before this step; detect head (/model.23) kept FP32 because quantising it gave 0 detections.
import cv2,glob,numpy as np,sys
from onnxruntime.quantization import quantize_static,CalibrationDataReader,QuantFormat,QuantType
from onnxruntime.quantization.shape_inference import quant_pre_process
R="/home/juice/edge computing/edge-vision"; S=sys.argv[1]
quant_pre_process(R+"/app/enclosure.onnx",S+"/enc_pre.onnx",skip_symbolic_shape=True)
imgs=sorted(glob.glob(R+"/training/enclosure_ds/train/images/*.jpg"))[::max(1,len(glob.glob(R+"/training/enclosure_ds/train/images/*.jpg"))//100)][:100]
def prep(f):
    img=cv2.imread(f);h,w=img.shape[:2];r=min(480/h,480/w);nh,nw=round(h*r),round(w*r)
    c=np.full((480,480,3),114,np.uint8);dy,dx=(480-nh)//2,(480-nw)//2;c[dy:dy+nh,dx:dx+nw]=cv2.resize(img,(nw,nh))
    return np.ascontiguousarray(c[:,:,::-1].transpose(2,0,1)[None].astype(np.float32)/255)
class D(CalibrationDataReader):
    def __init__(s): s.it=iter(imgs)
    def get_next(s):
        f=next(s.it,None); return None if f is None else {"images":prep(f)}
print(len(imgs),"calib images")
quantize_static(S+"/enc_pre13.onnx",S+"/enclosure_int8.onnx",D(),quant_format=QuantFormat.QDQ,activation_type=QuantType.QUInt8,weight_type=QuantType.QInt8,per_channel=True,nodes_to_exclude=[n.name for n in __import__('onnx').load(S+'/enc_pre13.onnx').graph.node if n.name.startswith('/model.23')])

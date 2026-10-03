import cv2
import numpy as np
import nncase
from pathlib import Path

def letterbox(image, size, color=114):
    h,w=image.shape[:2]
    s=min(size/w,size/h)
    nw,nh=max(1,int(round(w*s))),max(1,int(round(h*s)))
    r=cv2.resize(image,(nw,nh),interpolation=cv2.INTER_LINEAR)
    c=np.full((size,size,3),color,dtype=np.uint8)
    l=(size-nw)//2; t=(size-nh)//2
    c[t:t+nh,l:l+nw]=r
    return c

for size,name in [(320,'best_320.kmodel'),(640,'best_640.kmodel')]:
    img=cv2.imread(r'C:\k230_deploy\dataset\valid\images\bd_mp4-103_jpg.rf.1072721ea3b870f390df053933e8f0e2.jpg')
    img=letterbox(img,size)
    inp=img.transpose(2,0,1)[None,...].astype(np.uint8)
    sim=nncase.Simulator()
    sim.load_model(Path(r'C:\k230_deploy\kmodel',name).read_bytes())
    print(name, 'inputs',sim.inputs_size,'outputs',sim.outputs_size)
    for i in range(sim.inputs_size):
        desc=sim.get_input_desc(i)
        print(' input',i,'shape',sim.get_input_shape(i),'dtype',desc.dtype,'size',desc.size)
    for i in range(sim.outputs_size):
        desc=sim.get_output_desc(i)
        print(' output',i,'shape',sim.get_output_shape(i),'dtype',desc.dtype,'size',desc.size)
    sim.set_input_tensor(0,nncase.RuntimeTensor.from_numpy(inp))
    sim.run()
    out=sim.get_output_tensor(0).to_numpy()
    print(' result',out.shape,out.dtype,float(out.min()),float(out.max()))

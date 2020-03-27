from __future__ import print_function

import os,sys,argparse

import caffe
import flask
import io
import json
import numpy as np

app = flask.Flask(__name__)
 
def LoadImage(prototxt,caffemodel,labels):
  import numpy as np
  import xdnn_io
  global net
  net = caffe.Net(prototxt,caffemodel,caffe.TEST)
  print (net.blobs['data'].data.shape)
  return net  

def InferImage(net,image,labels):
  import numpy as np
  import xdnn_io
  transformer = caffe.io.Transformer({'data': net.blobs['data'].data.shape})
  transformer.set_transpose('data', (2,0,1))
  # transformer.set_mean('data', np.array([104,117,123]))
  # transformer.set_raw_scale('data', 255)
  transformer.set_channel_swap('data', (2,1,0)) # if using RGB instead if BGR
  net.blobs['data'].data[...] = transformer.preprocess('data', image)
  ptxtShape = net.blobs["data"].data.shape
  print ("Running with shape of: ",ptxtShape)
  out = net.forward()
  for key in out:
    try:
      if out[key].shape[1] == 1000:
        softmax = out[key]
    except:
      pass
  Labels = xdnn_io.get_labels(labels)
  xdnn_io.printClassification(softmax,[image],Labels)
  return xdnn_io.getClassification(softmax,[image],Labels) 

@app.route("/predict", methods=["POST"])
def predict():
  data = {"success": False}

  global prototxt
  global model
  global synset_words

  if flask.request.method == "POST":
    # Get image
    images = flask.request.form["image"]

    # Decode array
    images = json.loads(images)

    # Inference
    images = np.array(images, dtype=np.float32)
    images = images.reshape((-1, 224, 224, 3))

    responses = []

    for i in range(images.shape[0]):
      image = images[i]
      responses.append(InferImage(net, image, synset_words))

    # Write response
    data["success"] = True
    data["response"] = responses

  return flask.jsonify(data)

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='pyXFDNN')
  parser.add_argument('--caffemodel', default="/opt/models/caffe/bvlc_googlenet/bvlc_googlenet.caffemodel", help='path to caffemodel file eg: /opt/models/caffe/bvlc_googlenet/bvlc_googlenet.caffemodel')
  parser.add_argument('--prototxt', default="xfdnn_auto_cut_deploy.prototxt", help='path to  prototxt file eg: xfdnn_auto_cut_deploy.prototxt')
  parser.add_argument('--synset_words', default="$HOME/CK-TOOLS/dataset-imagenet-ilsvrc2012-aux/synset_words.txt", help='path to synset_words eg: $HOME/CK-TOOLS/dataset-imagenet-ilsvrc2012-aux/synset_words.txt')
  parser.add_argument('--port', default=5000)
  
  args = vars(parser.parse_args())

  if args["caffemodel"]:
    model=args["caffemodel"]
  
  if args["prototxt"]:
    prototxt=args["prototxt"]

  if args["synset_words"]:
    synset_words=args["synset_words"]
  
  if args["port"]:
    port=args["port"]
  else:
    port=9000 

  print("Loading FPGA with image...")
  net = LoadImage(prototxt, model, synset_words)
  
  print("Starting Flask Server...")
  app.run('0.0.0.0', port=port)


import cv2
import numpy as np
import vart
import xir
import argparse
import os
import time

# ---------------------- CARICA CLASSI DA FILE ---------------------- #
def load_classes(class_file_path):
    with open(class_file_path, 'r') as f:
        return [line.strip() for line in f.readlines() if line.strip()]

# ---------------------- PREPROCESS YOLO ---------------------- #
def preprocess_fn(frame, input_shape):
    image = cv2.resize(frame, (input_shape[2], input_shape[1]))
    image = image / 255.0
    image = image.astype(np.float32)
    image = np.expand_dims(image, axis=0)
    return image

# ---------------------- SIGMOID FUNCTION ---------------------- #
def sigmoid(x):
    return 1 / (1 + np.exp(-x))

# ---------------------- TROVA IL SUBGRAPH DEL DPU ---------------------- #
def get_child_subgraph_dpu(graph: "Graph"):
    root_subgraph = graph.get_root_subgraph()
    child_subgraphs = root_subgraph.toposort_child_subgraph()
    return [cs for cs in child_subgraphs if cs.has_attr("device") and cs.get_attr("device").upper() == "DPU"]

# ---------------------- INFERENZA DPU ---------------------- #
def runDPU(dpu, frame, results):
    inputTensors = dpu.get_input_tensors()
    outputTensors = dpu.get_output_tensors()
    input_shape = tuple(inputTensors[0].dims)

    input_data = preprocess_fn(frame, input_shape)
    output_data = np.empty(outputTensors[0].dims, dtype=np.float32)

    job_id = dpu.execute_async([input_data], [output_data])
    dpu.wait(job_id)

    results.append(output_data)

# ---------------------- (OPZIONALE) POSTPROCESS YOLO ---------------------- #
def postprocess(output_data, frame, class_names, threshold=0.05):
    # Questa funzione è lasciata intatta ma disabilitata nello script principale.
    # Può essere riattivata per visualizzare le predizioni.
    return frame

# ---------------------- PROCESSA IMMAGINI DA DATASET ---------------------- #
def process_dataset(model, dataset_path, output_path, class_file):
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    class_names = load_classes(class_file)
    g = xir.Graph.deserialize(model)
    subgraphs = get_child_subgraph_dpu(g)
    dpu_runner = vart.Runner.create_runner(subgraphs[0], "run")

    image_names = sorted(os.listdir(dataset_path))  # <-- PUNTO 2: ordinato

    total_time = 0
    count = 0

    for img_name in image_names:
        img_path = os.path.join(dataset_path, img_name)
        frame = cv2.imread(img_path)
        if frame is None:
            continue

        results = []
        t0 = time.time()
        runDPU(dpu_runner, frame, results)
        total_time += time.time() - t0
        count += 1

        if results:
            # PUNTO 3: DISABILITA POSTPROCESS per benchmark puro
            # frame = postprocess(results[0], frame, class_names)
            pass

            # SALVATAGGIO IMMAGINI OPZIONALE — disattiva per puro benchmarking
            # output_img_path = os.path.join(output_path, img_name)
            # cv2.imwrite(output_img_path, frame)

        if count % 100 == 0:
            print(f"Elaborate {count} immagini...")

    print(f"\nTotale immagini: {count}")
    print(f"Tempo totale: {total_time:.2f} sec")
    print(f"Tempo medio per immagine: {total_time / count:.4f} sec")

# ---------------------- ENTRY POINT ---------------------- #
if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('-m', '--model', type=str, default='model_dir/pynqdpu.tf_yolov3_voc.DPUCZDX8G_ISA1_B4096.2.5.0.xmodel', help='Path del modello .xmodel')
    ap.add_argument('-i', '--input', type=str, default='/input_images/img', help='Cartella con le immagini di input')
    ap.add_argument('-o', '--output', type=str, default='output_images', help='Cartella di output per le immagini elaborate')
    ap.add_argument('-c', '--classes', type=str, default='/input_images/classes.txt', help='File con le classi (una per riga)')
    args = ap.parse_args()

    process_dataset(args.model, args.input, args.output, args.classes)


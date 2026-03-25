import cv2
import numpy as np
import vart
import xir
import argparse
import os

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

# ---------------------- POSTPROCESS YOLO ---------------------- #
def postprocess(output_data, frame, class_names, threshold=0.05):
    HEIGHT, WIDTH = frame.shape[:2]
    results = []
    scale_factor = 2.5

    num_cells = output_data.shape[1]
    num_classes = output_data.shape[-1] - 5
    output_data = output_data.reshape(num_cells, num_cells, 3, -1)

    for row in range(num_cells):
        for col in range(num_cells):
            for anchor in range(3):
                detection = output_data[row, col, anchor]
                x, y, w, h, obj_confidence = detection[:5]
                class_scores = detection[5:]

                if obj_confidence < threshold:
                    continue

                class_id = np.argmax(class_scores)
                confidence = class_scores[class_id]

                if confidence > threshold:
                    w = (np.exp(w) * WIDTH) / num_cells * scale_factor
                    h = (np.exp(h) * HEIGHT) / num_cells * scale_factor
                    x = ((col + sigmoid(x)) / num_cells) * WIDTH - (w / 2)
                    y = ((row + sigmoid(y)) / num_cells) * HEIGHT - (h / 2)

                    x = max(0, min(x, WIDTH - 1))
                    y = max(0, min(y, HEIGHT - 1))
                    w = max(10, min(w, WIDTH - x))
                    h = max(10, min(h, HEIGHT - y))

                    results.append((int(x), int(y), int(w), int(h), class_id, confidence))

    if results:
        boxes = np.array([r[:4] for r in results])
        scores = np.array([r[5] for r in results])
        indices = cv2.dnn.NMSBoxes(boxes.tolist(), scores.tolist(), threshold, 0.5)

        for i in indices.flatten():
            x, y, w, h, class_id, confidence = results[i]
            label = class_names[class_id] if class_id < len(class_names) else f"Unknown {class_id}"
            color = (0, 255, 0)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 3)
            label_text = f"{label}: {confidence:.2f}"
            cv2.putText(frame, label_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    return frame

# ---------------------- PROCESSA IMMAGINI DA DATASET ---------------------- #
def process_dataset(model, dataset_path, output_path, class_file):
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    class_names = load_classes(class_file)
    g = xir.Graph.deserialize(model)
    subgraphs = get_child_subgraph_dpu(g)
    dpu_runner = vart.Runner.create_runner(subgraphs[0], "run")

    for img_name in os.listdir(dataset_path):
        img_path = os.path.join(dataset_path, img_name)
        frame = cv2.imread(img_path)
        if frame is None:
            continue

        results = []
        runDPU(dpu_runner, frame, results)

        if results:
            frame = postprocess(results[0], frame, class_names)

            output_img_path = os.path.join(output_path, img_name)
            cv2.imwrite(output_img_path, frame)
            print(f"Saved: {output_img_path}")
        else:
            print(f"No results for: {img_name}")

# ---------------------- ENTRY POINT ---------------------- #
if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('-m', '--model', type=str, default='model_dir/pynqdpu.tf_yolov3_voc.DPUCZDX8G_ISA1_B4096.2.5.0.xmodel', help='Path del modello .xmodel')
    ap.add_argument('-i', '--input', type=str, default='/input_images/img', help='Cartella con le immagini di input')
    ap.add_argument('-o', '--output', type=str, default='output_images', help='Cartella di output per le immagini elaborate')
    ap.add_argument('-c', '--classes', type=str, default='/input_images/classes.txt', help='File con le classi (una per riga)')
    args = ap.parse_args()

    process_dataset(args.model, args.input, args.output, args.classes)


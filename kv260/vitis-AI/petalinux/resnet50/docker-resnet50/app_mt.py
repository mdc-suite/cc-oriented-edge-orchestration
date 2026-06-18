import os
import cv2
import numpy as np
import vart
import xir
import argparse

# ------------------- CARICA CLASSI IMAGENET ------------------- #
def load_imagenet_classes(filepath):
    with open(filepath, 'r') as f:
        return [line.strip() for line in f.readlines()]

# ------------------- PREPROCESS RESNET50 ------------------- #
def preprocess_fn(image, input_shape, fix_scale=1.0, fix_mean=0.0):
    image = cv2.resize(image, (input_shape[2], input_shape[1]))
    image = image.astype(np.float32)
    image = image - fix_mean
    image = image * fix_scale
    image = image.astype(np.int8)
    image = np.expand_dims(image, axis=0)
    return image


# ------------------- TROVA SUBGRAPH DPU ------------------- #
def get_child_subgraph_dpu(graph: "Graph"):
    root_subgraph = graph.get_root_subgraph()
    return [s for s in root_subgraph.toposort_child_subgraph() if s.has_attr("device") and s.get_attr("device").upper() == "DPU"]

# ------------------- INFERENZA RESNET ------------------- #
def run_resnet(model_path, input_dir, output_dir, class_file):
    classes = load_imagenet_classes(class_file)

    g = xir.Graph.deserialize(model_path)
    subgraphs = get_child_subgraph_dpu(g)
    runner = vart.Runner.create_runner(subgraphs[0], "run")

    input_tensor = runner.get_input_tensors()[0]
    output_tensor = runner.get_output_tensors()[0]
    input_shape = tuple(input_tensor.dims)
    output_shape = tuple(output_tensor.dims)

    # Scaling/offset (assunti comuni per ResNet50 quantizzato, verificabili da quantizer.json)
    fix_scale = 1.0  # o es. 1/128
    fix_mean = 0.0   # o es. 128.0
    # Puoi usare valori corretti da quantizer.json se lo hai

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in os.listdir(input_dir):
        path = os.path.join(input_dir, filename)
        image = cv2.imread(path)
        if image is None:
            continue

        input_data = preprocess_fn(image, input_shape, fix_scale, fix_mean)
        output_data = np.empty(output_shape, dtype=np.int8)

        job_id = runner.execute_async([input_data], [output_data])
        runner.wait(job_id)

        # Softmax + classifica
        logits = output_data.flatten().astype(np.float32)
        probs = np.exp(logits - np.max(logits))
        probs /= np.sum(probs)
        top_class = np.argmax(probs)

        label = classes[top_class] if top_class < len(classes) else f"Class {top_class}"
        print(f"{filename}: {label} ({probs[top_class]*100:.2f}%)")

        # Scrive il nome sulla foto
        out_img = image.copy()
        cv2.putText(out_img, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.imwrite(os.path.join(output_dir, filename), out_img)

# ------------------- MAIN ------------------- #
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--model', default='model_dir/pynqdpu.tf2_resnet50.DPUCZDX8G_ISA1_B4096.2.5.0.xmodel')
    parser.add_argument('-i', '--input', default='/input_images/img')
    parser.add_argument('-o', '--output', default='output_images')
    parser.add_argument('-c', '--classes', default='/input_images/classes.txt')
    args = parser.parse_args()

    run_resnet(args.model, args.input, args.output, args.classes)


from sklearn.metrics.pairwise import cosine_similarity
import numpy as np 
import pandas as pd 
import json 
import argparse
import os 
import shutil
from pathlib import Path

def return_k_closest(index, data, k, metric="cosine"):
    '''
    data: (2d array, represents list of feature vectors)
    Return k closest indices to a given index, where first element is closest (the given index itself)
    '''
    if metric=="cosine":
        similarity_matrix = cosine_similarity(data)
    else:
        raise Exception("Only handles cosine metric for now.")
    print(f"Median cosine similarity: {np.median(similarity_matrix)}")
    print(f"Top 10% cosine similarity: {np.percentile(similarity_matrix, 90)}")
    
    similarity_vector = similarity_matrix[index]
    top_k_indices = list(np.argsort(similarity_vector)[-k:])
    top_k_indices.reverse()
    return np.array(top_k_indices)

SAVE_FOLDER = "../output"
DATA_PATH = "../data/cfd"
def generate_k_closest(index, embeddings_file_path, k, metric="cosine"):
    '''
    index: (int) represents the index of the desired point of ref in the data array
    Save the k closest images to a reference image in a folder
    '''
    embedding_data = pd.read_csv(embeddings_file_path)
    embeddings = embedding_data['imageEmbedding'].values
    image_names = embedding_data['imageName'].values 
    embeddings = np.array([json.loads(embedding) for embedding in embeddings])  
    top_k_indices = return_k_closest(index, embeddings, k, metric)
    new_folder = os.path.join(SAVE_FOLDER, "nearest_images")
    if os.path.exists(new_folder): 
        shutil.rmtree(new_folder)    
    os.mkdir(new_folder)

    #save the k closest in the folder in decreasing similarity order
    for i in range(0, len(top_k_indices)):
        image_folder = image_names[top_k_indices[i]]
        image_path = None
        image_files = os.listdir(os.path.join(DATA_PATH, image_folder)) 
        if len(image_files) > 1:
            for image_file in image_files:
                if Path(image_file).stem[-1] == "N":
                    image_path = os.path.join(DATA_PATH, image_folder, image_file) 
            if image_path is None:
                print(f"Folder {image_folder} contains no neutral image")
        elif len(image_files) == 0:
            print(f"Folder {image_folder} contains no images")
        else:
            image_path = os.path.join(DATA_PATH, image_folder, image_files[0])
        
        if i == 0:
            new_path = os.path.join(new_folder, f"1original_refIndex_{index}.png")
        else:
            new_path = os.path.join(new_folder, f"{i+1}_closest_refIndex_{index}.png")
        shutil.copy(image_path, new_path)
    return 





if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--k",type=int, required=True, help="number of closest indices")
    parser.add_argument("--index", type=int, required=True, help="index to find the closest around")

    args = parser.parse_args()
    generate_k_closest(args.index,"../embeddings/facenet512_CFD_embeddings.csv",args.k)
    print("Finished saving k closest")
    

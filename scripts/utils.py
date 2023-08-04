import numpy as np 
from datasets import load_dataset 
import os 
import shutil
from pathlib import Path
import pandas as pd 
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances
from online import ImageGraph
DATA_PATH = "../data/cfd"
FOLDER_SAVE_PATH = "../clusters"

def generate_cluster_folders(df, cluster_folder_path, data="hugging"):
    '''
    Given pandas dataframe containing cluster label and filename, create subfolders that contain all corresponding images
    '''
    cluster_labels = df.iloc[:, 1].values
    image_names = df.iloc[:,2].values 
    cluster_indices = {}
    for i in range(0, len(cluster_labels)):
        if cluster_labels[i] in cluster_indices:
            cluster_indices[cluster_labels[i]].append(i)
        else:
            cluster_indices[cluster_labels[i]] = [i]
    for k,v in cluster_indices.items():
        new_cluster_path = os.path.join(cluster_folder_path, f"cluster_{k}")
        print("new path", new_cluster_path)
        if not os.path.exists(new_cluster_path): os.mkdir(new_cluster_path)
        
        if data=="hugging":
            celeb_faces = load_dataset("ashraq/tmdb-people-image", split='train')
            for idx in v:
                hugging_idx = int(image_names[idx].split("_")[-1])
                profile = celeb_faces[hugging_idx]
                face = profile['image']
                new_path = os.path.join(new_cluster_path, f'{image_names[idx]}.png')
                face.save(new_path)
        else:
            #add all images in the cluster to the cluster folder
            for image_folder_index in v:
                image_folder = image_names[image_folder_index]
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
                new_path = os.path.join(cluster_folder_path, f"cluster_{k}", f'{Path(image_path).stem}.png')
                shutil.copy(image_path, new_path)
    return 

def driver_generate_cluster_folders(cluster_csv_path):
    df = pd.read_csv(cluster_csv_path)
    #create a folder to save the cluster subfolders
    new_folder_path = os.path.join(FOLDER_SAVE_PATH, f"{Path(cluster_csv_path).stem}")
    if not os.path.exists(new_folder_path): os.mkdir(new_folder_path)
    generate_cluster_folders(df, new_folder_path)


def make_cfd_no_folders():
    '''
    Create one folder that contains all images with no subfolders
    '''
    new_folder_path = "../data/cfd_images"
    if os.path.exists(new_folder_path): 
        shutil.rmtree(new_folder_path)    
    os.mkdir(new_folder_path)

    i = 0
    for folder in os.listdir(DATA_PATH):
        images = os.listdir(os.path.join(DATA_PATH, folder))
        image_path = None   
        if len(images) > 1:
            for image_file in images:
                if Path(image_file).stem[-1] == "N":
                    image_path = os.path.join(DATA_PATH, folder, image_file) 
            if image_path is None:
                print(f"Folder {folder} contains no neutral image")
        elif len(images) == 0:
            print(f"Folder {folder} contains no images")
        else:
            image_path = os.path.join(DATA_PATH, folder, images[0])
        
        if image_path is not None:
            new_path = os.path.join(new_folder_path, f'{i}_{Path(image_path).stem}.png')
            shutil.copy(image_path, new_path)
        i += 1
    return 

def remove_nan(file_path):
    if Path(file_path).suffix == ".csv": 
        df = pd.read_csv(file_path)
    elif Path(file_path).suffix == ".pkl":
        df = pd.read_pickle(file_path)
    else:
        print(f'{file_path} is not type pickle or csv')
        return 
    
    def filter_fn(row):
        return np.all(row['embeddings'] != None) 
    mask = df.apply(filter_fn, axis=1)
    no_nans = df[mask]
    new_path = f'../embeddings/{Path(file_path).stem}_nonan.pkl'
    no_nans.to_pickle(new_path)
    return 

def save_hf_disk():
    celeb_faces = load_dataset("ashraq/tmdb-people-image", split='train')
    celeb_faces.save_to_disk("../data/tmdb-people-image")

def save_sim_matrix(embeddings_file):
    df = pd.read_pickle(embeddings_file)
    embeddings = df['embeddings'].to_numpy()
    embedding_matrix = np.stack(embeddings)
    similarity_matrix = cosine_similarity(embedding_matrix)
    print(similarity_matrix)
    save_path = f"../files/simMatrix_{Path(embeddings_file).stem}.npy"
    np.save(save_path, similarity_matrix)
    return 

def save_hf_dataset_idxs(embeddings_file):
    df = pd.read_pickle(embeddings_file)
    image_names = df['image_names'].to_numpy()
    hf_dataset_idxs = np.array([int(name.split("_")[-1]) for name in image_names])
    print(hf_dataset_idxs[:5])
    save_path = f"../files/hf_dataset_idxs_{Path(embeddings_file).stem}.npy"
    np.save(save_path, hf_dataset_idxs)



def test_get_clusters():

    def _get_top_rated_cluster(cluster_size, sim_threshold, generateValues, sim_matrix):
        lst_subset_vals = [] #contains tuples of (cluster_sum_val, cluster_indices)
        #find the max value subset of size cluster_size where each pairwise sim is larger than sim_threshold
        def backtrack(cur_lst, search_from_idx, num_items):
            #enumerate our imageValues tuples from [0, N), cur_lst contains the indices corresponding to the tuples
            if num_items == cluster_size:
                sum_val = 0
                for idx in cur_lst:
                    img_index, img_val = generateValues[idx]
                    sum_val += img_val 
                lst_subset_vals.append((sum_val, cur_lst))
                return 
            for i in range(search_from_idx, len(generateValues)):
                new_lst = cur_lst.copy()
                new_lst.append(i)
                if num_items > 0:
                    #check if new item has pairwise similarity larger than threshold for all in cur_lst
                    is_sim_enough = True 
                    for cur_elm_idx in cur_lst:
                        pairwise_sim_val = sim_matrix[i][cur_elm_idx]
                        if pairwise_sim_val < sim_threshold:
                            is_sim_enough = False 
                            break 
                    if not is_sim_enough: continue 
                backtrack(new_lst, i+1, num_items + 1)
            return
        backtrack([], 0, 0)
        max_cluster_obj = max(lst_subset_vals, key=lambda x: x[0])
        return max_cluster_obj[1]


    def get_top_rated_cluster(cluster_size, sim_threshold, imageValues, sim_matrix):
        '''
        Finds the maximal value point and greedily generates a cluster of points closest to it
        If it is not possible to generate a cluster around the maximal point such that the sim is larger than threshold, 
        it uses the second largest value point and so on  
        '''
        sorted_image_vals = sorted(imageValues, key=lambda x: x[1], reverse=True)
        print(sorted_image_vals)
        #try to build cluster around highest point and find next best if not 
        for i in range(0, len(sorted_image_vals)):
            center_point = sorted_image_vals[i]
            center_emb_index = center_point[0]
            print(f"center embed index {center_emb_index}")
            cluster_embedding_indices = []
            #get most sim indices in descending order
            sorted_sim_point_indices = np.argsort(-1*sim_matrix[center_emb_index])
            assert sorted_sim_point_indices[0] == center_emb_index
            for j in range(0, cluster_size):
                other_idx = sorted_sim_point_indices[j]
                if sim_matrix[center_emb_index][other_idx] > sim_threshold:
                    cluster_embedding_indices.append(other_idx)
                else:
                    break 
            if len(cluster_embedding_indices) == cluster_size:
                return cluster_embedding_indices
        return 
    '''
    1  0.5   0.9
    0.5  1  0.7  
    0.9  0.7  1 
    '''

    test_sim_matrix = np.array([[1,0.5,0.9], [0.5,1,0.7], [0.9, 0.7, 1]])
    generateValues = [(0, 7), (1, 8), (2, 2)]
    cluster_size = 2
    sim_threshold = 0.5
    print(f'Answer should be [(, [0,2])] {get_top_rated_cluster(cluster_size, 0.71, generateValues, test_sim_matrix)}')


if __name__ == "__main__":
    #make_cfd_no_folders()
    #driver_generate_cluster_folders("../files/KMEANS_k=100_female_5000_5-5_nonan.csv")
    #remove_nan('../embeddings/female_5000_5-5.pkl')
    #df = pd.read_csv("../files/KMEANS_k=10_female_5000_5-5_nonan.csv", index_col=0)
    #print(df.head())
    #print(df.iloc[:,1].values)
    #save_hf_disk()


    #save_sim_matrix("../embeddings/female_5000_5-5_nonan.pkl")
    save_hf_dataset_idxs("../embeddings/female_5000_5-5_nonan.pkl")
    #test_get_clusters()
    #df = pd.read_pickle('../embeddings/female_5000_5-5_nonan.pkl')
    #print(df.head())

     
     
        
            




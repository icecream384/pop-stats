"""
Split large city JSON files (>1MB) into 1MB chunks for parallel CDN loading.
Each chunk is a standalone JSON that can be loaded independently.
The merged result is identical to the original grids array.

Output: data/成都.json -> data/chengdu/chunk_0.json, data/chengdu/chunk_1.json, ...
        + data/chengdu/meta.json (contains name, bbox, gridsize, chunk count)

Small files (<1MB) stay as-is.
"""
import json
import os
import math

BASE_DIR = r"D:\AAA\AI\claude\人口统计"
DATA_DIR = os.path.join(BASE_DIR, "data")
CHUNK_SIZE = 800 * 1024  # 800KB target per chunk

def split_file(filename):
    filepath = os.path.join(DATA_DIR, filename)
    size = os.path.getsize(filepath)

    if size < CHUNK_SIZE:
        print(f"  SKIP {filename}: {size/1024:.0f}KB (small enough)")
        return

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    name = data['n']
    bbox = data['b']
    gridsize = data['s']
    scale = data['m']
    grids = data['g']

    total_grids = len(grids)
    # Estimate: one grid = ~18 chars JSON = ~18 bytes
    bytes_per_grid = size / total_grids
    grids_per_chunk = max(1, int(CHUNK_SIZE / bytes_per_grid))
    num_chunks = math.ceil(total_grids / grids_per_chunk)

    # Create city subdirectory
    city_dir = os.path.join(DATA_DIR, filename.replace('.json', ''))
    os.makedirs(city_dir, exist_ok=True)

    # Write meta
    meta = {
        "n": name,
        "b": bbox,
        "s": gridsize,
        "m": scale,
        "c": num_chunks,
        "t": total_grids
    }
    with open(os.path.join(city_dir, 'meta.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False)

    # Write chunks
    for ci in range(num_chunks):
        start = ci * grids_per_chunk
        end = min(start + grids_per_chunk, total_grids)
        chunk_grids = grids[start:end]
        chunk_data = {
            "i": ci,
            "g": chunk_grids
        }
        chunk_path = os.path.join(city_dir, f'{ci}.json')
        with open(chunk_path, 'w', encoding='utf-8') as f:
            json.dump(chunk_data, f, ensure_ascii=False, separators=(',', ':'))
        chunk_size = os.path.getsize(chunk_path)
        print(f"  Chunk {ci}: grids {start}-{end-1} ({len(chunk_grids)}), {chunk_size/1024:.0f}KB")

    print(f"  {filename}: {size/1024:.0f}KB -> {num_chunks} chunks")


def main():
    files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith('.json')])
    for filename in files:
        split_file(filename)
    print("\nDone!")


if __name__ == '__main__':
    main()

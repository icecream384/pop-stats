"""
Tile preprocessing: split city grids into 0.05°×0.05° spatial tiles.
Reads both single-file and chunked city data, outputs:
  data/城市/index.json  — tile index with bbox+count for each tile
  data/城市/t_<row>_<col>.json — grids in that tile
  data/城市/meta.json   — basic city metadata
"""
import json
import os
import math
import shutil

BASE_DIR = r"D:\AAA\AI\claude\人口统计"
DATA_DIR = os.path.join(BASE_DIR, "data")
OUT_DIR = os.path.join(BASE_DIR, "data_tiled")
TILE_DEG = 0.05  # ~5.5km at equator, ~5km in mid-latitudes

os.makedirs(OUT_DIR, exist_ok=True)


def load_city_data(name):
    """Load all grids for a city, supporting both single-file and chunked formats."""
    single_file = os.path.join(DATA_DIR, f"{name}.json")
    chunk_dir = os.path.join(DATA_DIR, name)
    meta_file = os.path.join(chunk_dir, "meta.json")

    if os.path.isdir(chunk_dir) and os.path.exists(meta_file):
        # Chunked format
        with open(meta_file, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        all_grids = []
        for i in range(meta['c']):
            chunk_file = os.path.join(chunk_dir, f"{i}.json")
            with open(chunk_file, 'r', encoding='utf-8') as f:
                chunk = json.load(f)
            all_grids.extend(chunk['g'])
        return meta['n'], meta['b'], meta['s'], meta.get('m', 100000), all_grids

    elif os.path.exists(single_file):
        # Single-file format
        with open(single_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['n'], data['b'], data['s'], data.get('m', 100000), data['g']

    else:
        print(f"  WARN: {name} not found (tried {single_file} and {chunk_dir})")
        return None


def tile_city(name):
    """Split a city into spatial tiles."""
    result = load_city_data(name)
    if result is None:
        return

    city_name, bbox, grid_size, scale, grids = result
    min_lng, min_lat, max_lng, max_lat = bbox

    # Create output directory for this city
    city_dir = os.path.join(OUT_DIR, city_name)
    os.makedirs(city_dir, exist_ok=True)

    # Round bbox to tile boundaries
    tile_min_lat = math.floor(min_lat / TILE_DEG) * TILE_DEG
    tile_max_lat = math.ceil(max_lat / TILE_DEG) * TILE_DEG
    tile_min_lng = math.floor(min_lng / TILE_DEG) * TILE_DEG
    tile_max_lng = math.ceil(max_lng / TILE_DEG) * TILE_DEG
    n_rows = int(round((tile_max_lat - tile_min_lat) / TILE_DEG))
    n_cols = int(round((tile_max_lng - tile_min_lng) / TILE_DEG))

    # Bucket grids into tiles
    tile_map = {}  # (row, col) -> [grids]
    for g in grids:
        lng = g[0] / scale
        lat = g[1] / scale
        # Use tile grid full extent (ceil/floor to TILE_DEG) rather than bbox
        if lng < tile_min_lng or lng > tile_max_lng or lat < tile_min_lat or lat > tile_max_lat:
            continue  # skip truly out-of-bounds
        row = int((lat - tile_min_lat) / TILE_DEG)
        col = int((lng - tile_min_lng) / TILE_DEG)
        row = max(0, min(n_rows - 1, row))
        col = max(0, min(n_cols - 1, col))
        key = (row, col)
        if key not in tile_map:
            tile_map[key] = []
        tile_map[key].append(g)

    # Build tile index
    tile_index = {}
    for (row, col), tile_grids in sorted(tile_map.items()):
        t_min_lat = tile_min_lat + row * TILE_DEG
        t_max_lat = t_min_lat + TILE_DEG
        t_min_lng = tile_min_lng + col * TILE_DEG
        t_max_lng = t_min_lng + TILE_DEG
        fname = f"t_{row}_{col}"
        key_str = f"{row}_{col}"
        tile_index[key_str] = {
            "b": [round(t_min_lng, 6), round(t_min_lat, 6), round(t_max_lng, 6), round(t_max_lat, 6)],
            "c": len(tile_grids)
        }

        # Write tile file
        tile_path = os.path.join(city_dir, fname + '.json')
        with open(tile_path, 'w', encoding='utf-8') as f:
            json.dump({"g": tile_grids}, f, ensure_ascii=False, separators=(',', ':'))

    # Write index
    index = {
        "n": city_name,
        "b": bbox,
        "s": grid_size,
        "m": scale,
        "td": TILE_DEG,
        "to": [tile_min_lat, tile_min_lng],  # tile grid origin
        "nr": n_rows,
        "nc": n_cols,
        "tiles": tile_index  # key: "row_col" -> {b, c}
    }
    with open(os.path.join(city_dir, 'index.json'), 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, separators=(',', ':'))

    # Stats
    tile_sizes = [len(v) for v in tile_map.values()]
    total_tiles = len(tile_map)
    single_file_size = sum(os.path.getsize(os.path.join(city_dir, f"t_{k[0]}_{k[1]}.json")) for k in tile_map)
    total_json_size = single_file_size + os.path.getsize(os.path.join(city_dir, 'index.json'))
    original_size = sum(os.path.getsize(f) for f in (
        [os.path.join(DATA_DIR, f"{name}.json")]
        if os.path.exists(os.path.join(DATA_DIR, f"{name}.json"))
        else [os.path.join(DATA_DIR, name, f"{i}.json") for i in range(
            json.load(open(os.path.join(DATA_DIR, name, 'meta.json'), 'r', encoding='utf-8'))['c']
        )]
    ))

    print(f"  {city_name}: {len(grids)} grids → {total_tiles} tiles "
          f"(avg {sum(tile_sizes)//max(1,total_tiles)} grids/tile), "
          f"{original_size/1024:.0f}KB → {total_json_size/1024:.0f}KB")


def main():
    # Collect all city names
    cities = set()
    for f in os.listdir(DATA_DIR):
        if f.endswith('.json'):
            with open(os.path.join(DATA_DIR, f), 'r', encoding='utf-8') as jf:
                data = json.load(jf)
            cities.add(data['n'])
        elif os.path.isdir(os.path.join(DATA_DIR, f)):
            meta_path = os.path.join(DATA_DIR, f, 'meta.json')
            if os.path.exists(meta_path):
                with open(meta_path, 'r', encoding='utf-8') as jf:
                    meta = json.load(jf)
                cities.add(meta['n'])

    print(f"Processing {len(cities)} cities...\n")
    for city in sorted(cities):
        tile_city(city)

    print(f"\nDone! Output in: {OUT_DIR}")


if __name__ == '__main__':
    main()

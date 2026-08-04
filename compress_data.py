"""
Re-encode all 52 city JSON files to integer format for smaller size.
Format: [[lng×100000, lat×100000, rp, rd, wp, wd, mp, md, op, od], ...]
All population/density values rounded to integers.
"""
import json
import os

BASE_DIR = r"D:\AAA\AI\claude\人口统计"
DATA_DIR = os.path.join(BASE_DIR, "data")

def reencode_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    name = data['name']
    bbox = [round(v, 6) for v in data['bbox']]
    grid_size = data['gridSize']
    grids = data['grids']

    new_grids = []
    for g in grids:
        lng, lat, rp, rd, wp, wd, mp, md, op, od = g
        new_grids.append([
            int(round(lng * 100000)),  # lng: 104.06580 -> 10406580
            int(round(lat * 100000)),  # lat: 30.65750 -> 3065750
            int(round(rp)),            # 居住人口 (whole integer)
            int(round(rd)),            # 居住密度
            int(round(wp)),            # 工作人口
            int(round(wd)),            # 工作密度
            int(round(mp)),            # 职住净人口
            int(round(md)),            # 职住净密度
            int(round(op)),            # 加班人口
            int(round(od)),            # 加班密度
        ])

    # Precision metadata
    output = {
        "n": name,
        "b": bbox,
        "s": grid_size,
        "m": 100000,  # multiplier for lng/lat
        "g": new_grids,
    }

    return output


def main():
    files = [f for f in os.listdir(DATA_DIR) if f.endswith('.json')]
    total_old = 0
    total_new = 0

    for filename in sorted(files):
        filepath = os.path.join(DATA_DIR, filename)
        old_size = os.path.getsize(filepath)
        total_old += old_size

        output = reencode_file(filepath)

        json_str = json.dumps(output, ensure_ascii=False, separators=(',', ':'))
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(json_str)

        new_size = os.path.getsize(filepath)
        total_new += new_size
        ratio = old_size / new_size if new_size > 0 else 0
        print(f"{output['n']}: {old_size/1024:.0f}KB -> {new_size/1024:.0f}KB ({ratio:.1f}x smaller)")

    print(f"\nTotal: {total_old/1024/1024:.1f}MB -> {total_new/1024/1024:.1f}MB ({total_old/total_new:.1f}x)")


if __name__ == '__main__':
    main()

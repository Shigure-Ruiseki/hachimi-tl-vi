import json
import os
import shutil

def merge_json(old_data, new_data):
    if isinstance(old_data, dict) and isinstance(new_data, dict):
        result = dict(new_data)
        for key, value in old_data.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_json(value, result[key])
            else:
                result[key] = value
        return result
    return old_data if old_data is not None else new_data

vn_dir = "vn_repo/localized_data"
target_dir = "localized_data"

vi_exclusive_files = set()

for root, _, files in os.walk(vn_dir):
    for file in files:
        vn_file_path = os.path.join(root, file)
        rel_path = os.path.relpath(vn_file_path, vn_dir)
        target_file_path = os.path.join(target_dir, rel_path)

        if not os.path.exists(target_file_path):
            os.makedirs(os.path.dirname(target_file_path), exist_ok=True)
            shutil.copy2(vn_file_path, target_file_path)
            vi_exclusive_files.add(target_file_path)
        elif "includes_win" in file:
            shutil.copy2(vn_file_path, target_file_path)

for root, _, files in os.walk(target_dir):
    for file in files:
        if file.endswith(".json"):
            file_path = os.path.join(root, file)
            
            if file_path in vi_exclusive_files:
                continue

            vn_equivalent = os.path.join(vn_dir, os.path.relpath(file_path, target_dir))
            
            if os.path.exists(vn_equivalent):
                with open(vn_equivalent, "r", encoding="utf-8") as f:
                    vi_json = json.load(f)
                with open(file_path, "r", encoding="utf-8") as f:
                    en_json = json.load(f)

                merged = merge_json(vi_json, en_json)

                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(merged, f, ensure_ascii=False)
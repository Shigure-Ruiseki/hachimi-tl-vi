import json
import os
import shutil
import sys
import datetime

def sort_dict_by_key(d):
    if not isinstance(d, dict):
        return d
    
    def get_sort_key(item):
        key = item[0]
        if key.isdigit():
            return (0, int(key)) 
        else:
            return (1, key.lower()) 
            
    return {k: sort_dict_by_key(v) for k, v in sorted(d.items(), key=get_sort_key)}

def merge_json(old_data, new_data, path, log_file):
    if isinstance(old_data, dict) and isinstance(new_data, dict):
        result = dict(old_data)
        for key, value in new_data.items():
            if key in result:
                if isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_json(result[key], value, f"{path}.{key}", log_file)
            else:
                log_file.write(f"[NEW KEY] {path}.{key}\n")
                result[key] = value
        return result
    
    return old_data if old_data is not None else new_data

def merge_folders(old_dir, new_dir):
    if not os.path.exists(old_dir):
        return

    with open("merge_log.txt", "w", encoding="utf-8") as log_file:
        log_file.write(f"Log merge: {new_dir} -> {old_dir}\n")
        log_file.write(f"Thời gian: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write("-" * 50 + "\n")

        for root, _, files in os.walk(old_dir):
            for file in files:
                old_path = os.path.join(root, file)
                rel_path = os.path.relpath(old_path, old_dir)
                new_path = os.path.join(new_dir, rel_path) if os.path.exists(new_dir) else ""

                if file.endswith(".json"):
                    try:
                        with open(old_path, "r", encoding="utf-8") as f:
                            old_json = json.load(f)
                        
                        new_json = {}
                        if new_path and os.path.exists(new_path):
                            with open(new_path, "r", encoding="utf-8") as f:
                                new_json = json.load(f)

                        merged = merge_json(old_json, new_json, rel_path, log_file)

                        sorted_merged = sort_dict_by_key(merged)
                        
                        with open(old_path, "w", encoding="utf-8") as f:
                            json.dump(sorted_merged, f, ensure_ascii=False, indent=2, sort_keys=False)
                        
                        log_file.write(f"[PASSED/MERGED JSON] {rel_path}\n")
                    except Exception as e:
                        log_file.write(f"[ERROR JSON] {rel_path}: {e}\n")

        if os.path.exists(new_dir):
            for root, _, files in os.walk(new_dir):
                for file in files:
                    new_path = os.path.join(root, file)
                    rel_path = os.path.relpath(new_path, new_dir)
                    old_path = os.path.join(old_dir, rel_path)

                    if not os.path.exists(old_path):
                        os.makedirs(os.path.dirname(old_path), exist_ok=True)
                        if file.endswith(".json"):
                            try:
                                with open(new_path, "r", encoding="utf-8") as f:
                                    new_json = json.load(f)
                                sorted_new = sort_dict_by_key(new_json)
                                with open(old_path, "w", encoding="utf-8") as f:
                                    json.dump(sorted_new, f, ensure_ascii=False, indent=2, sort_keys=False)
                                log_file.write(f"[NEW JSON FROM EN] {rel_path}\n")
                            except Exception as e:
                                log_file.write(f"[ERROR NEW JSON] {rel_path}: {e}\n")
                        else:
                            shutil.copy2(new_path, old_path)
                            log_file.write(f"[NEW FILE FROM EN] {rel_path}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    
    target_dir = sys.argv[1]
    source_dir = sys.argv[2] if len(sys.argv) > 2 else ""
    merge_folders(target_dir, source_dir)
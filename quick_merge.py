import json
import os
import shutil
import sys
import datetime

def sort_dict_by_natural_key(d):
    """
    Sắp xếp dictionary theo thứ tự tự nhiên (Natural Sort) A-Z và tăng dần số.
    """
    if not isinstance(d, dict):
        return d
        
    def get_sort_key(item):
        key = item[0]
        # Nếu key hoàn toàn là số, chuyển về kiểu int để so sánh số lớn bé
        if key.isdigit():
            return (0, int(key))
        # Nếu key chứa ký tự chữ, so sánh theo string viết thường
        return (1, key.lower())

    # Đệ quy để sắp xếp toàn bộ các tầng object con bên trong
    return {k: sort_dict_by_natural_key(v) for k, v in sorted(d.items(), key=get_sort_key)}

def merge_json(old_data, new_data, path, log_file):
    if isinstance(old_data, dict) and isinstance(new_data, dict):
        result = dict(old_data)
        
        for key, value in new_data.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_json(result[key], value, f"{path}.{key}", log_file)
            
            elif key not in result:
                log_file.write(f"[NEW KEY] {path}.{key}\n")
                result[key] = value
            
            else:
                pass
                
        return dict(sorted(result.items()))
    
    return old_data if old_data is not None else new_data

def merge_folders(old_dir, new_dir):
    if not os.path.exists(old_dir) or not os.path.exists(new_dir):
        return

    with open("merge_log.txt", "w", encoding="utf-8") as log_file:
        log_file.write(f"Log merge: {new_dir} -> {old_dir}\n")
        log_file.write(f"Thời gian: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write("-" * 50 + "\n")

        for root, _, files in os.walk(new_dir):
            for file in files:
                new_path = os.path.join(root, file)
                rel_path = os.path.relpath(new_path, new_dir)
                old_path = os.path.join(old_dir, rel_path)

                os.makedirs(os.path.dirname(old_path), exist_ok=True)

                if file.endswith(".json"):
                    try:
                        with open(new_path, "r", encoding="utf-8") as f:
                            new_json = json.load(f)
                        
                        old_json = {}
                        if os.path.exists(old_path):
                            with open(old_path, "r", encoding="utf-8") as f:
                                old_json = json.load(f)

                        merged = merge_json(old_json, new_json, rel_path, log_file)

                        final_sorted_json = sort_dict_by_natural_key(merged)

                        with open(old_path, "w", encoding="utf-8") as f:
                            json.dump(final_sorted_json, f, ensure_ascii=False, indent=2, sort_keys=True)
                        
                        log_file.write(f"[MERGED JSON] {rel_path}\n")
                    except Exception as e:
                        log_file.write(f"[ERROR JSON] {rel_path}: {e}\n")
                else:
                    if not os.path.exists(old_path):
                        shutil.copy2(new_path, old_path)
                        log_file.write(f"[NEW FILE] {rel_path}\n")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(1)

    merge_folders(sys.argv[1], sys.argv[2])
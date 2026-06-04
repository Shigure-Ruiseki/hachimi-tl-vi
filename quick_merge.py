import json
import os
import shutil
import sys
import datetime
import copy

def sort_dict_by_natural_key(d):
    if not isinstance(d, dict):
        return d
    def get_sort_key(item):
        key = item[0]
        if key.isdigit():
            return (0, int(key))
        else:
            return (1, key.lower())
    return {k: sort_dict_by_natural_key(v) for k, v in sorted(d.items(), key=get_sort_key)}

def merge_json(old_data, new_data, path, log_file):
    if old_data is not None and isinstance(old_data, dict):
        result = copy.deepcopy(old_data)
    else:
        result = {}

    if isinstance(new_data, dict):
        for key, value in new_data.items():
            current_path = f"{path}->{key}" if path else key
            
            # TRƯỜNG HỢP ĐẶC BIỆT: Lệch tầng cấu trúc (VN bọc trong ID nhóm như "92", còn EN là key trần)
            # Nếu key của EN trùng với key nằm BÊN TRONG một nhóm của VN
            target_group = None
            if key not in result:
                for g_key, g_val in result.items():
                    if isinstance(g_val, dict) and key in g_val:
                        target_group = g_key
                        break
            
            # Nếu tìm thấy nhóm bọc tương ứng trong VN, tiến hành merge trực tiếp vào nhóm đó
            if target_group is not None:
                if not isinstance(value, dict):
                    # Nếu key đã có sẵn trong nhóm của VN dưới dạng text -> Giữ nguyên bản dịch VN
                    log_file.write(f"[KEEP OLD IN GROUP] {target_group}->{key}: Giữ bản dịch VN -> '{result[target_group][key]}' (Bỏ qua EN)\n")
                else:
                    result[target_group][key] = merge_json(result[target_group][key], value, f"{target_group}->{key}", log_file)
                continue

            # --- LOGIC MERGE TIÊU CHUẨN ---
            # 1. Cả hai bên trùng cấu trúc Dict -> Đệ quy sâu
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_json(result[key], value, current_path, log_file)
            
            # 2. EN là Dict nhưng VN chưa có hoặc lệch kiểu
            elif isinstance(value, dict):
                log_file.write(f"[NEW BLOCK]  {current_path}: (Tạo cấu trúc Dict mới từ EN)\n")
                old_sub = result[key] if (key in result and isinstance(result[key], dict)) else {}
                result[key] = merge_json(old_sub, value, current_path, log_file)
                
            # 3. Key mới hoàn toàn từ EN -> Thêm vào VN
            elif key not in result:
                log_file.write(f"[NEW KEY]    {current_path}: Lấy từ EN -> '{value.strip()}'\n")
                result[key] = copy.deepcopy(value)
                
            # 4. Trùng key dạng phẳng và VN đã có text -> Giữ nguyên bản dịch VN
            else:
                log_file.write(f"[KEEP OLD]   {current_path}: Giữ bản dịch VN -> '{result[key]}' (Bỏ qua EN)\n")
                pass
                
        return result
    
    return old_data if old_data is not None else copy.deepcopy(new_data)

def merge_folders(old_dir, new_dir):
    if not os.path.exists(old_dir) or not os.path.exists(new_dir):
        return

    with open("merge_log.txt", "w", encoding="utf-8") as log_file:
        log_file.write(f"Log merge hoàn chỉnh (Fix lệch tầng cấu trúc): {new_dir} -> {old_dir}\n")
        log_file.write(f"Thời gian chạy: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write("-" * 80 + "\n")

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
                        if os.path.exists(old_path) and os.path.getsize(old_path) > 0:
                            with open(old_path, "r", encoding="utf-8") as f:
                                try:
                                    old_json = json.load(f)
                                except json.JSONDecodeError:
                                    old_json = {}

                        log_file.write(f"\n[PROCESSING FILE] {rel_path}\n")
                        merged = merge_json(old_json, new_json, "", log_file)
                        
                        # Sắp xếp lại tự nhiên A-Z & Số
                        sorted_merged = sort_dict_by_natural_key(merged)
                        
                        with open(old_path, "w", encoding="utf-8") as f:
                            json.dump(sorted_merged, f, ensure_ascii=False, indent=2, sort_keys=False)
                        
                        log_file.write(f"[SUCCESS] Đã merge thành công file: {rel_path}\n")
                    except Exception as e:
                        log_file.write(f"[ERROR JSON] {rel_path}: {e}\n")
                else:
                    if not os.path.exists(old_path):
                        shutil.copy2(new_path, old_path)
                        log_file.write(f"[NEW FILE NON-JSON] {rel_path}\n")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(1)

    merge_folders(sys.argv[1], sys.argv[2])
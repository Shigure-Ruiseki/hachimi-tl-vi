import json
import os
import shutil
import sys
import datetime

def sort_dict_by_natural_key(d):
    """
    Sắp xếp các key trong dictionary theo thứ tự tự nhiên:
    - Nếu key là số (isdigit): Ép kiểu về int để sắp xếp đúng (ví dụ: 2 nhỏ hơn 10).
    - Nếu key là chữ: Sắp xếp theo bảng chữ cái A-Z (không phân biệt hoa thường).
    """
    if not isinstance(d, dict):
        return d
    
    def get_sort_key(item):
        key = item[0]
        if key.isdigit():
            return (0, int(key))  # Ưu tiên số lên trước, xếp theo giá trị số thực tế
        else:
            return (1, key.lower())  # Chữ nằm sau, xếp theo bảng chữ cái
            
    return {k: sort_dict_by_natural_key(v) for k, v in sorted(d.items(), key=get_sort_key)}

def merge_json(old_data, new_data, path, log_file):
    if isinstance(old_data, dict) and isinstance(new_data, dict):
        result = dict(old_data)
        
        for key, value in new_data.items():
            current_path = f"{path}->{key}" if path else key
            
            # Trường hợp 1: Cả 2 đều là dict -> Tiếp tục đệ quy sâu hơn
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_json(result[key], value, current_path, log_file)
            
            # Trường hợp 2: Key mới tinh xuất hiện từ file EN -> Thêm vào file VN
            elif key not in result:
                if isinstance(value, dict):
                    log_file.write(f"[NEW BLOCK]  {current_path}: (Cấu trúc Dict mới từ EN)\n")
                else:
                    log_file.write(f"[NEW KEY]    {current_path}: Lấy từ EN -> '{value}'\n")
                result[key] = value
            
            # Trường hợp 3: Key đã có sẵn ở file VN -> Giữ nguyên để bảo toàn bản dịch
            else:
                if not isinstance(result[key], dict):
                    log_file.write(f"[KEEP OLD]   {current_path}: Giữ bản dịch VN -> '{result[key]}' (Bỏ qua EN: '{value}')\n")
                pass
                
        return result
    
    return old_data if old_data is not None else new_data

def merge_folders(old_dir, new_dir):
    if not os.path.exists(old_dir) or not os.path.exists(new_dir):
        return

    with open("merge_log.txt", "w", encoding="utf-8") as log_file:
        log_file.write(f"Log merge chi tiết: {new_dir} -> {old_dir}\n")
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
                        if os.path.exists(old_path):
                            with open(old_path, "r", encoding="utf-8") as f:
                                old_json = json.load(f)

                        log_file.write(f"\n[PROCESSING FILE] {rel_path}\n")
                        merged = merge_json(old_json, new_json, "", log_file)
                        
                        # Thực hiện sắp xếp tự nhiên A-Z & Số trước khi ghi file
                        sorted_merged = sort_dict_by_natural_key(merged)
                        
                        with open(old_path, "w", encoding="utf-8") as f:
                            # Đặt sort_keys=False để áp dụng chính xác thứ tự từ hàm sort_dict_by_natural_key
                            json.dump(sorted_merged, f, ensure_ascii=False, indent=2, sort_keys=False)
                        
                        log_file.write(f"[SUCCESS] Đã ghi đè thành công file: {rel_path}\n")
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
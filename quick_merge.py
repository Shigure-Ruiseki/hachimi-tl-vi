import json
import os
import shutil
import sys
import datetime

def sort_dict_by_key(d):
    """Sắp xếp dictionary theo số thực tế và chữ cái A-Z"""
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
    """
    Gộp file thông minh: 
    - Giữ lại các bản dịch Tiếng Việt đang có ở old_data.
    - Điền bổ sung toàn bộ key thiếu từ new_data (Tiếng Anh).
    """
    # Nếu dữ liệu cũ không tồn tại hoặc không phải là dict, lấy toàn bộ dữ liệu mới làm khung
    if not isinstance(old_data, dict):
        return new_data if isinstance(new_data, dict) else old_data

    if isinstance(old_data, dict) and isinstance(new_data, dict):
        result = dict(old_data)
        for key, value in new_data.items():
            if key in result:
                # Nếu cả 2 bên đều là dict con, tiến hành đệ quy sâu hơn
                if isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_json(result[key], value, f"{path}.{key}", log_file)
            else:
                # Key có ở file EN nhưng chưa có ở file VN -> Bổ sung vào
                log_file.write(f"[NEW KEY FROM EN] {path}.{key}\n")
                result[key] = value
        return result
    
    return old_data

def merge_folders(old_dir, new_dir):
    # Trường hợp chạy Force Sort cuối (chỉ truyền 1 tham số target_dir)
    if not new_dir or new_dir == "":
        if not os.path.exists(old_dir):
            return
        for root, _, files in os.walk(old_dir):
            for file in files:
                if file.endswith(".json"):
                    old_path = os.path.join(root, file)
                    try:
                        with open(old_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        sorted_data = sort_dict_by_key(data)
                        with open(old_path, "w", encoding="utf-8") as f:
                            json.dump(sorted_data, f, ensure_ascii=False, indent=2, sort_keys=False)
                    except Exception:
                        pass
        return

    # Trường hợp gộp thư mục đầy đủ
    if not os.path.exists(new_dir):
        print(f"Thư mục nguồn không tồn tại: {new_dir}")
        return
    os.makedirs(old_dir, exist_ok=True)

    with open("merge_log.txt", "w", encoding="utf-8") as log_file:
        log_file.write(f"Log merge: {new_dir} -> {old_dir}\n")
        log_file.write(f"Thời gian: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write("-" * 50 + "\n")

        # Quét THƯ MỤC GỐC EN (new_dir) để bảo đảm lấy đủ mọi file json hiện có
        for root, _, files in os.walk(new_dir):
            for file in files:
                new_path = os.path.join(root, file)
                rel_path = os.path.relpath(new_path, new_dir)
                old_path = os.path.join(old_dir, rel_path)

                os.makedirs(os.path.dirname(old_path), exist_ok=True)

                if file.endswith(".json"):
                    try:
                        # Đọc file Tiếng Anh chuẩn
                        with open(new_path, "r", encoding="utf-8") as f:
                            new_json = json.load(f)
                        
                        # Đọc file Tiếng Việt nếu đã tồn tại
                        old_json = {}
                        if os.path.exists(old_path) and os.path.getsize(old_path) > 0:
                            with open(old_path, "r", encoding="utf-8") as f:
                                try:
                                    old_json = json.load(f)
                                except json.JSONDecodeError:
                                    old_json = {}

                        # Thực hiện gộp dữ liệu (Giữ dịch VN, lấy thêm key EN thiếu)
                        merged = merge_json(old_json, new_json, rel_path, log_file)
                        
                        # Sắp xếp lại dải số (ví dụ: 41131001) tăng dần từ bé đến lớn
                        sorted_merged = sort_dict_by_key(merged)
                        
                        with open(old_path, "w", encoding="utf-8") as f:
                            json.dump(sorted_merged, f, ensure_ascii=False, indent=2, sort_keys=False)
                        
                        log_file.write(f"[MERGED & SORTED] {rel_path}\n")
                    except Exception as e:
                        log_file.write(f"[ERROR JSON] {rel_path}: {e}\n")
                else:
                    # File cấu hình khác nếu VN chưa có thì copy nguyên bản từ EN sang
                    if not os.path.exists(old_path):
                        shutil.copy2(new_path, old_path)
                        log_file.write(f"[NEW NON-JSON] {rel_path}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    
    target_dir = sys.argv[1]
    source_dir = sys.argv[2] if len(sys.argv) > 2 else ""
    merge_folders(target_dir, source_dir)
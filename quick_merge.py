import json
import os
import shutil
import sys


def merge_json(old_data, new_data):
    """
    Hòa trộn dữ liệu JSON: Nếu trùng key, ưu tiên giữ nguyên giá trị cũ (old_data).
    Chỉ thêm vào những key mới xuất hiện từ bản update (new_data).
    """
    if isinstance(old_data, dict) and isinstance(new_data, dict):
        # Khởi tạo kết quả bằng bản dịch cũ của local
        result = dict(old_data)

        for key, value in new_data.items():
            # CHÌA KHÓA: Chỉ thêm key mới nếu nó CHƯA TỒN TẠI trong bản cũ của local
            if key not in result:
                result[key] = value

        return dict(sorted(result.items()))

    # Nếu không phải dict, ưu tiên giữ lại dữ liệu cũ của local
    return old_data if old_data else new_data


def merge_folders(old_dir, new_dir):
    """
    Duyệt thư mục update trên máy (new_dir) để bổ sung vào thư mục local (old_dir).
    """
    # Kiểm tra xem các thư mục nhập vào có tồn tại không
    if not os.path.exists(old_dir):
        print(f"[-] Thư mục Local không tồn tại: {old_dir}")
        return
    if not os.path.exists(new_dir):
        print(f"[-] Thư mục Update không tồn tại: {new_dir}")
        return

    print(f"[+] Đang tiến hành quét và gộp từ '{new_dir}' vào '{old_dir}'...")

    for root, _, files in os.walk(new_dir):
        for file in files:
            new_path = os.path.join(root, file)

            # Tính toán đường dẫn tương đối để đối chiếu sang thư mục local
            rel_path = os.path.relpath(new_path, new_dir)
            old_path = os.path.join(old_dir, rel_path)

            # Tự động tạo thư mục con ở local nếu bên update có thư mục mới
            os.makedirs(os.path.dirname(old_path), exist_ok=True)

            if file.endswith(".json"):
                try:
                    # Đọc file update mới trên máy
                    with open(new_path, "r", encoding="utf-8") as f:
                        new_json = json.load(f)

                    # Đọc file local cũ nếu đã có sẵn
                    if os.path.exists(old_path):
                        with open(old_path, "r", encoding="utf-8") as f:
                            old_json = json.load(f)
                    else:
                        old_json = {}

                    # Thực hiện merge bảo vệ bản dịch tiếng Việt
                    merged = merge_json(old_json, new_json)

                    with open(old_path, "w", encoding="utf-8") as f:
                        json.dump(
                            merged,
                            f,
                            ensure_ascii=False,
                            indent=2,
                            sort_keys=True
                        )

                    print(f"[MERGE JSON - TRÙNG KEY GIỮ VI] {rel_path}")

                except Exception as e:
                    print(f"[ERROR JSON] {rel_path}: {e}")

            else:
                # Đối với file asset, font... CHỈ copy nếu local CHƯA CÓ
                if not os.path.exists(old_path):
                    shutil.copy2(new_path, old_path)
                    print(f"[ADD NEW FILE] {rel_path}")
                else:
                    print(f"[SKIP] {rel_path} (File đã có ở local, không ghi đè)")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Cách dùng: python quick_merge.py <thư_mục_local_vi> <thư_mục_update_en_trên_máy>")
        print("Ví dụ:    python quick_merge.py C:\\Project\\main-vi  C:\\Project\\main-en")
        sys.exit(1)

    old_dir = sys.argv[1]
    new_dir = sys.argv[2]

    merge_folders(old_dir, new_dir)
    print("\n[+] XỬ LÝ HOÀN THÀNH!")
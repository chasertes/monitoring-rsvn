import concurrent.futures
import json
import os
import subprocess
import openpyxl

# --- НАСТРОЙКИ ---
EXCEL_FILE = "cameras.xlsx"
OUTPUT_DIR = "metrics_json"
MAX_WORKERS = 4         # Ограничение под 100 Мбит/с канал
MEASURE_DURATION = "180s" # Время замера для камерn


def check_camera(task):
    camera_id, order_no, password, rtsp_url, operator = task
    
    if not rtsp_url or not str(rtsp_url).startswith("rtsp://"):
        return

    output_file = os.path.join(OUTPUT_DIR, f"{camera_id}.json")

    command = [
        "wink-rtsp-stats.exe",
        "monitor",
        str(rtsp_url).strip(),
        "--duration", MEASURE_DURATION,
        "--output", "json"
    ]

    meta_info = {
        "camera_id": str(camera_id),
        "order_no": str(order_no) if order_no else "-",
        "password": str(password) if password else "-",
        "operator": str(operator) if operator else "-",
        "target": str(rtsp_url).strip()
    }

    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.stdout.strip():
            try:
                metrics_data = json.loads(result.stdout)
                metrics_data.update(meta_info)
            except json.JSONDecodeError:
                metrics_data = {**meta_info, "status": "bad_json", "raw_output": result.stdout.strip()}
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(metrics_data, f, indent=4, ensure_ascii=False)
            print(f"[OK] Камера №{camera_id} ({operator}) — метрики записаны.")

        else:
            meta_info.update({
                "status": "failed",
                "exit_code": result.returncode,
                "error": result.stderr.strip()
            })
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(meta_info, f, indent=4, ensure_ascii=False)
            print(f"[ERROR] Камера №{camera_id} — Ошибка опроса: {result.stderr.strip()}")

    except Exception as e:
        print(f"[CRITICAL] Системная ошибка на камере №{camera_id}: {e}")


def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    if not os.path.exists(EXCEL_FILE):
        print(f"Ошибка: Файл {EXCEL_FILE} не найден!")
        return

    print(f"Читаем данные из {EXCEL_FILE}...")
    wb = openpyxl.load_workbook(EXCEL_FILE, data_only=True)
    sheet = wb.active

    tasks = []
    # Читаем данные со 2-й строки, захватывая максимум 5 колонок (по столбец E включительно)
    for row in sheet.iter_rows(min_row=2, max_col=5, values_only=True):
        if len(row) < 5:
            # На случай, если в строке физически меньше 5 заполненных ячеек
            row = list(row) + ["-"] * (5 - len(row))
            
        camera_id, order_no, password, rtsp_url, operator = row
        if camera_id and rtsp_url:
            tasks.append((camera_id, order_no, password, rtsp_url, operator))

    print(f"Запуск сбора для {len(tasks)} камер. Одновременно воркеров: {MAX_WORKERS}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        executor.map(check_camera, tasks)

    print("Сбор метрик из Excel завершен.")


if __name__ == "__main__":
    main()

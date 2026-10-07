import glob
import json
import os
import re

INPUT_DIR = "metrics_json"
OUTPUT_HTML = "report-wink.html"


def extract_ip(url):
    match = re.search(r"rtsp://(?:[^@]+@)?([^:/?]+)", url)
    return match.group(1) if match else "unknown"


def get_camera_number(file_path):
    filename = os.path.basename(file_path)
    name_without_ext, _ = os.path.splitext(filename)
    try:
        return int(name_without_ext)
    except ValueError:
        return float("inf")


def parse_json_files():
    rows_html = ""
    json_files = glob.glob(os.path.join(INPUT_DIR, "*.json"))

    total_cams = 0
    ok_count = 0
    warn_count = 0
    crit_count = 0

    if not json_files:
        return (
            "<tr><td colspan='10' style='text-align:center;'>Нет файлов JSON в папке metrics_json/</td></tr>",
            0,
            0,
            0,
            0,
        )

    json_files.sort(key=get_camera_number)

    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            camera_id = data.get("camera_id", "-")
            order_no = data.get("order_no", "-")
            password = data.get("password", "-")
            operator = data.get("operator", "-")
            url = data.get("target", "-")
            ip_address = extract_ip(url)

            status = "Unknown"
            bitrate_mbps = 0.0
            loss_pct = 0.0
            jitter_val = 0.0
            jitter_str = "-"
            row_class = ""
            total_cams += 1

            if data.get("status") in ["failed", "bad_json"]:
                status = (
                    "CRITICAL (No Conn)"
                    if data.get("status") == "failed"
                    else "ERROR (Bad JSON)"
                )
                row_class = "error"
                crit_count += 1
            elif "summary" in data:
                summary = data["summary"]
                total_bitrate_kbps = summary.get("total_bitrate_kbps_avg", 0.0)
                bitrate_mbps = round(total_bitrate_kbps / 1000, 2)

                packets_received = summary.get("total_packets", 0)
                packets_lost = summary.get("total_packets_lost_estimated", 0)
                total_expected = packets_received + packets_lost

                if total_expected > 0:
                    loss_pct = round((packets_lost / total_expected) * 100, 2)

                for stream in data.get("streams", []):
                    if stream.get("media_type") == "video":
                        jitter_val = round(stream.get("jitter_ms_avg", 0.0), 1)
                        jitter_str = f"{jitter_val}"
                        break

                if loss_pct > 10.0:
                    status = f"BAD ({loss_pct}% Loss)"
                    row_class = "error"
                    crit_count += 1
                elif total_bitrate_kbps < 50:
                    status = "STALLED (No Stream)"
                    row_class = "error"
                    crit_count += 1
                elif bitrate_mbps < 5.0:
                    status = "LOW BITRATE"
                    row_class = "warning"
                    warn_count += 1
                elif loss_pct > 2.0:
                    status = f"WARNING ({loss_pct}% Loss)"
                    row_class = "warning"
                    warn_count += 1
                else:
                    status = "GOOD"
                    row_class = "good"
                    ok_count += 1

            ip_link = (
                f'<a class="cam-link" href="http://{ip_address}" target="_blank">{ip_address}</a>'
                if ip_address != "unknown"
                else "-"
            )

            rows_html += f"""
            <tr class="{row_class}">
                <td data-val="{camera_id}"><strong>{camera_id}</strong></td>
                <td>{order_no}</td>
                <td>{operator}</td>
                <td class="pass-cell copy-click" onclick="copyText(this)">{password}</td>
                <td>{ip_link}</td>
                <td class="url-cell copy-click" title="Кликните для копирования" onclick="copyText(this)">{url}</td>
                <td class="status-cell"><strong>{status}</strong></td>
                <td data-val="{bitrate_mbps}">{bitrate_mbps}</td>
                <td data-val="{loss_pct}">{loss_pct}%</td>
                <td data-val="{jitter_val}">{jitter_str}</td>
            </tr>
            """
        except Exception:
            continue

    return rows_html, total_cams, ok_count, warn_count, crit_count
def main():
    table_rows, total, ok, warn, crit = parse_json_files()

    html_template = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Мониторинг видеопотоков</title>
    <script src="xlsx.full.min.js"></script>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; background-color: #f4f6f9; margin: 0; padding: 0; color: #333; }}
        .container {{ max-width: 1650px; margin: 0 auto; background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .top-sticky-panel {{ position: sticky; top: 0; background: #f4f6f9; padding: 20px 20px 0 20px; z-index: 100; }}
        .panel-card {{ background: white; padding: 15px 20px; border-radius: 8px 8px 0 0; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        h1 {{ text-align: center; color: #2c3e50; margin: 0 0 15px 0; font-size: 24px; }}
        
        .search-container {{ display: flex; gap: 15px; margin-top: 5px; }}
        input[type="text"] {{ flex: 1; padding: 12px; margin: 0; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; font-size: 16px; }}
        
        .export-btn {{ background-color: #1f7a42; color: white; border: none; padding: 0 20px; border-radius: 4px; font-size: 15px; font-weight: 600; cursor: pointer; display: flex; align-items: center; transition: background 0.2s; }}
        .export-btn:hover {{ background-color: #16562f; }}
        
        .cb-btn {{ background-color: #0288d1; color: white; border: none; padding: 0 20px; border-radius: 4px; font-size: 15px; font-weight: 600; cursor: pointer; display: flex; align-items: center; transition: background 0.2s; }}
        .cb-btn:hover {{ background-color: #01579b; }}

        .stats-bar {{ display: flex; justify-content: space-between; margin-bottom: 15px; gap: 15px; }}
        .stat-card {{ flex: 1; padding: 10px 15px; border-radius: 6px; text-align: center; font-size: 14px; font-weight: 600; box-shadow: inset 0 0 0 1px rgba(0,0,0,0.05); }}
        .stat-total {{ background-color: #e3f2fd; color: #0d47a1; }}
        .stat-ok {{ background-color: #e8f5e9; color: #1b5e20; }}
        .stat-warn {{ background-color: #fff3e0; color: #e65100; }}
        .stat-crit {{ background-color: #ffebee; color: #b71c1c; }}
        .stat-num {{ font-size: 20px; line-height: 24px; font-weight: bold; margin-top: 2px; }}
        
        .table-wrapper {{ padding: 0 20px 20px 20px; background: white; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
        th, td {{ padding: 12px 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #34495e; color: white; cursor: pointer; user-select: none; position: sticky; top: 225px; z-index: 90; box-shadow: 0 2px 2px rgba(0,0,0,0.1); }}
        th:hover {{ background-color: #2c3e50; }}
        th.sort-asc::after {{ content: " ▲"; font-size: 10px; }}
        th.sort-desc::after {{ content: " ▼"; font-size: 10px; }}
        tr:hover {{ background-color: #f1f1f1 !important; }}
        .url-cell {{ max-width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #777; font-size: 11px; }}
        .pass-cell {{ font-family: monospace; color: #444; }}
        .cam-link {{ color: #0288d1; text-decoration: none; font-weight: 600; }}
        .cam-link:hover {{ text-decoration: underline; color: #01579b; }}
        
        .copy-click {{ cursor: pointer; position: relative; }}
        .copy-click:hover {{ background-color: #e0f2f1 !important; text-decoration: underline; }}
        
        .toast-tip {{ position: absolute; background: #333; color: #fff; padding: 4px 8px; font-size: 11px; border-radius: 4px; pointer-events: none; z-index: 200; white-space: nowrap; box-shadow: 0 2px 5px rgba(0,0,0,0.2); animation: fadeInOut 0.6s ease-in-out; }}
        @keyframes fadeInOut {{ 0% {{ opacity: 0; transform: translateY(0); }} 20% {{ opacity: 1; transform: translateY(-8px); }} 80% {{ opacity: 1; transform: translateY(-8px); }} 100% {{ opacity: 0; transform: translateY(-15px); }} }}



        /* --- СТАНДАРТНЫЕ ЦВЕТА СТАТУСОВ --- */
        .good, .stat-ok {{ background-color: #e8f5e9; color: #2e7d32; }}
        .warning, .stat-warn {{ background-color: #fff3e0; color: #ef6c00; }}
        .error, .stat-crit {{ background-color: #ffebee; color: #c62828; }}

        /* --- МЯГКИЙ И ГАРМОНИЧНЫЙ РЕЖИМ ДЛЯ ДАЛЬТОНИКОВ --- */
        /* Принудительно меняем палитру и в таблице, и в верхних виджетах статистики */
        body.color-blind-mode .good, 
        body.color-blind-mode .stat-ok {{ 
            background-color: #e3f2fd !important; 
            color: #0d47a1 !important; 
        }} /* Мягкий синий */

        body.color-blind-mode .warning, 
        body.color-blind-mode .stat-warn {{ 
            background-color: #ffe0b2 !important; 
            color: #e65100 !important; 
        }} /* Четкий оранжевый */

        body.color-blind-mode .error, 
        body.color-blind-mode .stat-crit {{ 
            background-color: #f8bbd0 !important; 
            color: #880e4f !important; 
        }} /* Комфортный бордово-розовый (вместо агрессивного черного/красного) */

        /* Корректируем цвет линка в режиме дальтоника для лучшей читаемости */
        body.color-blind-mode .cam-link {{ 
            color: #0d47a1 !important; 
        }}
        body.color-blind-mode .error .cam-link {{ 
            color: #880e4f !important; 
        }}
    </style>

</head>
<body>
<div class="container">
    <div class="top-sticky-panel">
        <div class="panel-card">
            <h1>📊 Сводный отчет мониторинга видеопотоков</h1>
            <div class="stats-bar">
                <div class="stat-card stat-total">Всего камер<div class="stat-num">{total}</div></div>
                <div class="stat-card stat-ok">Статус GOOD<div class="stat-num">{ok}</div></div>
                <div class="stat-card stat-warn">Низкий битрейт / Потери<div class="stat-num">{warn}</div></div>
                <div class="stat-card stat-crit">Критические ошибки<div class="stat-num">{crit}</div></div>
            </div>
            <div class="search-container">
                <input type="text" id="searchInput" onkeyup="filterTable()" placeholder="Глобальный поиск по ID, заказу, оператору, IP или точному статусу (GOOD, LOW BITRATE, WARNING)...">
                <button class="cb-btn" onclick="toggleColorBlind()">👁️</button>
                <button class="export-btn" onclick="exportToExcel()">🟢 Выгрузить в Excel</button>
            </div>
        </div>
    </div>
    <div class="table-wrapper">
        <table id="streamsTable">
            <thead>
                <tr>
                    <th onclick="sortTable(0)">№ по ТЗ</th>
                    <th onclick="sortTable(1)">№ CMS-Заказа</th>
                    <th onclick="sortTable(2)">Оператор</th>
                    <th onclick="sortTable(3)">Админ. пароль</th>
                    <th onclick="sortTable(4)">IP Камеры</th>
                    <th onclick="sortTable(5)">Полный RTSP URL</th>
                    <th onclick="sortTable(6)">Статус</th>
                    <th onclick="sortTable(7)">Битрейт (mbps)</th>
                    <th onclick="sortTable(8)">Потери (%)</th>
                    <th onclick="sortTable(9)">Джиттер (ms)</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
    </div>
</div>
"""
    html_template += """
<script>
    // Проверка и применение режима дальтоника при загрузке страницы
    if (localStorage.getItem("colorBlindMode") === "true") {
        document.body.classList.add("color-blind-mode");
    }

    // Функция переключения режима дальтоника
    function toggleColorBlind() {
        var isBlind = document.body.classList.toggle("color-blind-mode");
        localStorage.setItem("colorBlindMode", isBlind);
    }

    // Быстрое копирование текста в буфер обмена по клику
    function copyText(cell) {
        var textToCopy = cell.textContent || cell.innerText;
        if (!textToCopy || textToCopy === "-") return;

        navigator.clipboard.writeText(textToCopy).then(function() {
            var oldTips = document.querySelectorAll(".toast-tip");
            oldTips.forEach(t => t.remove());

            var tip = document.createElement("div");
            tip.className = "toast-tip";
            tip.innerText = "Скопировано!";
            document.body.appendChild(tip);

            var rect = cell.getBoundingClientRect();
            tip.style.left = (rect.left + window.scrollX + (rect.width / 2) - 40) + "px";
            tip.style.top = (rect.top + window.scrollY - 25) + "px";

            setTimeout(function() { tip.remove(); }, 600);
        }).catch(function(err) {
            console.error("Не удалось скопировать текст: ", err);
        });
    }

    // Фильтрация таблицы с исключением паролей (индекс 3)
    function filterTable() {
        var input = document.getElementById("searchInput").value.toUpperCase();
        var table = document.getElementById("streamsTable");
        var rows = table.getElementsByTagName("tr");

        for (var i = 1; i < rows.length; i++) {
            var row = rows[i];
            var cells = row.getElementsByTagName("td");
            var matchFound = false;

            for (var j = 0; j < cells.length; j++) {
                if (j === 3) continue; 

                if (cells[j]) {
                    var cellText = cells[j].textContent || cells[j].innerText;
                    if (cellText.toUpperCase().indexOf(input) > -1) {
                        matchFound = true;
                        break;
                    }
                }
            }
            row.style.display = matchFound ? "" : "none";
        }
    }

    // Интерактивная сортировка по клику на заголовки
    function sortTable(colIndex) {
        var table = document.getElementById("streamsTable");
        var tbody = table.tBodies[0];
        var rows = Array.from(tbody.rows);
        var th = table.querySelectorAll("th")[colIndex];
        var isAsc = th.classList.contains("sort-asc");
        
        table.querySelectorAll("th").forEach(el => el.classList.remove("sort-asc", "sort-desc"));
        
        var direction = isAsc ? -1 : 1;
        th.classList.add(isAsc ? "sort-desc" : "sort-asc");

        rows.sort(function(rowA, rowB) {
            var cellA = rowA.cells[colIndex];
            var cellB = rowB.cells[colIndex];
            
            var valA = cellA.hasAttribute("data-val") ? parseFloat(cellA.getAttribute("data-val")) : cellA.textContent.trim().toUpperCase();
            var valB = cellB.hasAttribute("data-val") ? parseFloat(cellB.getAttribute("data-val")) : cellB.textContent.trim().toUpperCase();
            
            if (!isNaN(valA) && !isNaN(valB)) { return (valA - valB) * direction; }
            if (valA < valB) return -1 * direction;
            if (valA > valB) return 1 * direction;
            return 0;
        });

        rows.forEach(row => tbody.appendChild(row));
    }

    // Экспорт текущего состояния таблицы в Excel
    function exportToExcel() {
        var table = document.getElementById("streamsTable");
        var rows = table.getElementsByTagName("tr");
        var exportData = [];

        var headers = [];
        var ths = table.getElementsByTagName("th");
        for (var i = 0; i < ths.length; i++) {
            headers.push(ths[i].textContent.trim());
        }
        exportData.push(headers);

        for (var i = 1; i < rows.length; i++) {
            if (rows[i].style.display !== "none") {
                var rowData = [];
                var tds = rows[i].getElementsByTagName("td");
                for (var j = 0; j < tds.length; j++) {
                    rowData.push(tds[j].textContent.trim());
                }
                exportData.push(rowData);
            }
        }

        var wb = XLSX.utils.book_new();
        var ws = XLSX.utils.aoa_to_sheet(exportData);
        XLSX.utils.book_append_sheet(wb, ws, "Мониторинг");
        
        XLSX.writeFile(wb, "Report_Cams_" + new Date().toLocaleDateString() + ".xlsx");
    }
</script>
</body>
</html>
"""

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"[УСПЕХ] Автономный отчет полностью сгенерирован: {OUTPUT_HTML}")


if __name__ == "__main__":
    main()

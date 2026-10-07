import os
import json
import glob
import re
from datetime import datetime

METRICS_DIR = "scanned_metrics"
REPORT_FILE = "report-snmp.html"

def load_metrics():
    cameras = []
    json_files = glob.glob(os.path.join(METRICS_DIR, "*.json"))
    
    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # ДОБАВИТЬ ЭТУ СТРОКУ:
                data["file_source"] = os.path.basename(file_path)
                cameras.append(data)
        except Exception as e:
            print(f"Ошибка чтения файла {file_path}: {e}")
            
    try:
        cameras.sort(key=lambda x: int(''.join(filter(str.isdigit, str(x.get("tz_number", "99999")))) or 99999))
    except:
        cameras.sort(key=lambda x: str(x.get("tz_number", "")))
    return cameras

def parse_uptime(timeticks_str):
    if not timeticks_str: return "Н/Д"
    timeticks_str = str(timeticks_str).strip()
    
    if ":" in timeticks_str:
        days = 0
        days_match = re.search(r'(\d+)\s+day', timeticks_str)
        if days_match: days = int(days_match.group(1))
        time_part = timeticks_str.split(",")[-1].strip()
        time_split = time_part.split(":")
        if len(time_split) >= 2:
            hours = int(time_split[0])
            minutes = int(time_split[1])
            result = []
            if days > 0: result.append(f"{days} дн.")
            if hours > 0 or days > 0: result.append(f"{hours} ч.")
            result.append(f"{minutes} мин.")
            return " ".join(result)
            
    try:
        clean_ticks = int(''.join(filter(str.isdigit, timeticks_str)))
        total_seconds = clean_ticks // 100
        days = total_seconds // 86400
        rem_seconds = total_seconds % 86400
        hours = rem_seconds // 3600
        minutes = (rem_seconds % 3600) // 60
        result = []
        if days > 0: result.append(f"{days} дн.")
        if hours > 0 or days > 0: result.append(f"{hours} ч.")
        result.append(f"{minutes} мин.")
        return " ".join(result) if result else "0 мин."
    except ValueError: pass
    
    if ")" in timeticks_str: return timeticks_str.split(")")[-1].strip()
    return timeticks_str

def get_uptime_days(timeticks_str):
    if not timeticks_str: return 0.0
    timeticks_str = str(timeticks_str).strip()
    if ":" in timeticks_str:
        days_match = re.search(r'(\d+)\s+day', timeticks_str)
        if days_match: return float(days_match.group(1))
    try:
        clean_ticks = int(''.join(filter(str.isdigit, timeticks_str)))
        return float(clean_ticks / 100 / 86400)
    except ValueError:
        return 0.0

def format_mac(mac_str):
    if not mac_str or mac_str == "Н/Д": return "Н/Д"
    clean = mac_str.replace("0x", "").replace(":", "").replace("-", "").strip()
    if len(clean) == 12:
        return ":".join(clean[i:i+2].upper() for i in range(0, 12, 2))
    return mac_str

def format_speed(speed_val):
    if not speed_val or speed_val == "Н/Д": return "Н/Д"
    try:
        bps = int(speed_val)
        if bps == 0: return "Ссылка отключена (Down)"
        mbps = bps / 1_000_000
        if mbps >= 1000: return f"{mbps / 1000:.0f} Гбит/с"
        return f"{mbps:.0f} Мбит/с"
    except ValueError: return speed_val
def generate_html(cameras):
    now_str = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    operators = sorted(list(set(str(cam.get('operator', 'Н/Д')) for cam in cameras)))
    op_options = "".join(f'<option value="{op}">{op}</option>' for op in operators)
    
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Отчет по SNMP мониторингу камер</title>
    <!-- ИСПРАВЛЕНО: Полная и корректная ссылка на библиотеку SheetJS для экспорта -->
    <script src="xlsx.full.min.js"></script>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; color: #333; margin: 0; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        header {{ background: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }}
        h1 {{ margin: 0; color: #1e293b; font-size: 24px; }}
        .timestamp {{ color: #64748b; font-size: 14px; }}
        .filter-panel {{ background: #ffffff; padding: 15px 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 20px; display: flex; flex-wrap: wrap; gap: 15px; align-items: flex-end; }}
        .filter-group {{ display: flex; flex-direction: column; gap: 5px; }}
        .filter-group label {{ font-size: 12px; font-weight: 600; color: #475569; }}
        .filter-group select, .filter-group input {{ padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 14px; background-color: #fff; min-width: 180px; outline: none; }}
        .filter-group select:focus, .filter-group input:focus {{ border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,0.2); }}
        .btn-excel {{ background-color: #16a34a; color: white; border: none; padding: 9px 16px; border-radius: 6px; font-size: 14px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 8px; transition: background 0.2s; margin-left: auto; height: 38px; }}
        .btn-excel:hover {{ background-color: #15803d; }}
        .card {{ background: #ffffff; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 25px; overflow: hidden; border-left: 5px solid #3b82f6; }}
        .card.non-compliant {{ border-left-color: #ef4444; background: #fff5f5; }}
        .card-header {{ background: #f8fafc; padding: 15px 20px; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; }}
        .card.non-compliant .card-header {{ background: #fee2e2; }}
        .camera-title {{ font-size: 16px; color: #0f172a; }}
        .camera-title b {{ font-size: 18px; color: #1e3a8a; }}
        .badge {{ padding: 5px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; }}
        .badge-success {{ background: #dcfce7; color: #15803d; }}
        .badge-warning {{ background: #fef9c3; color: #a16207; }}
        .badge-danger {{ background: #fee2e2; color: #b91c1c; }}
        .card-body {{ padding: 20px; display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        @media (max-width: 768px) {{ .card-body {{ grid-template-columns: 1fr; }} .filter-panel {{ flex-direction: column; align-items: stretch; }} .btn-excel {{ margin-left: 0; }} }}
        .info-block h3 {{ margin-top: 0; color: #475569; font-size: 15px; border-bottom: 2px solid #f1f5f9; padding-bottom: 5px; }}
        .info-grid {{ display: grid; grid-template-columns: auto 1fr; gap: 8px 15px; font-size: 14px; }}
        .info-label {{ color: #64748b; font-weight: 500; }}
        .info-value {{ color: #1e293b; word-break: break-all; }}
        .client-list {{ list-style: none; padding: 0; margin: 0; }}
        .client-item {{ background: #f8fafc; padding: 6px 12px; border-radius: 4px; margin-bottom: 5px; font-size: 13px; display: flex; justify-content: space-between; }}
    </style>
</head>
<body>
<div class="container">
    <header>
        <div>
            <h1>Панель аналитики IP-камер видеонаблюдения по SNMP</h1>
            <div class="timestamp">Обновлено: {now_str}</div>
        </div>
        <div>
            <span class="badge badge-success" id="total-badge">Всего устройств: {len(cameras)}</span>
        </div>
    </header>

    <div class="filter-panel">
        <div class="filter-group" style="flex-grow: 1; min-width: 250px;">
            <label for="filter-search">Поиск по ключевым словам (ТЗ, Заказ, IP, MAC):</label>
            <input type="text" id="filter-search" placeholder="Введите текст для поиска..." oninput="applyFilters()">
        </div>
        <div class="filter-group">
            <label for="filter-operator">Фильтр по оператору:</label>
            <select id="filter-operator" onchange="applyFilters()">
                <option value="all">Все операторы</option>
                {op_options}
            </select>
        </div>
        <div class="filter-group">
            <label for="filter-speed">Скорость линка:</label>
            <select id="filter-speed" onchange="applyFilters()">
                <option value="all">Любая скорость</option>
                <option value="10">10 Мбит/с</option>
                <option value="100">100 Мбит/с</option>
                <option value="1000">1 Гбит/с</option>
            </select>
        </div>
        <div class="filter-group">
            <label for="filter-clients">Активные клиенты:</label>
            <select id="filter-clients" onchange="applyFilters()">
                <option value="all">Все камеры</option>
                <option value="active">С активными зрителями (>0)</option>
                <option value="empty">Без зрителей (0)</option>
            </select>
        </div>
        <div class="filter-group">
            <label for="filter-compliance">Критерии соответствия:</label>
            <select id="filter-compliance" onchange="applyFilters()">
                <option value="all">Показать все камеры</option>
                <option value="violators">⚠️ Только нарушения (Uptime &lt; 1дн или Скорость &lt; 100M)</option>
            </select>
        </div>
        <button onclick="exportToExcel()" class="btn-excel">Выгрузить отфильтрованное 📊 в Excel (.xlsx)</button>
    </div>
    <main id="camera-list">
"""
    for cam in cameras:
        rtsp_count = cam.get("active_rtsp_sessions_count", 0)
        rtsp_badge_class = "badge-success" if rtsp_count > 0 else "badge-warning"
        rtsp_badge_text = f"Трансляция активна ({rtsp_count} устр.)" if rtsp_count > 0 else "Нет активных зрителей"
        
        uptime_raw = cam.get("sys_uptime", "0")
        uptime_cleaned = parse_uptime(uptime_raw)
        uptime_days = get_uptime_days(uptime_raw)
        
        raw_speed = cam.get('interface_speed', '0')
        speed_mbps = 0
        if raw_speed and raw_speed != "Н/Д":
            try: speed_mbps = int(raw_speed) // 1_000_000
            except: pass
            
        is_compliant_violation = (uptime_days < 1.0) or (speed_mbps < 100)
        card_class = "card non-compliant" if is_compliant_violation else "card"
        
        compliance_badge = ""
        if is_compliant_violation:
            reasons = []
            if uptime_days < 1.0: reasons.append("Uptime < 1 дн.")
            if speed_mbps < 100: reasons.append("Скорость < 100 Мбит/с")
            compliance_badge = f'<span class="badge badge-danger" style="margin-right: 10px;">⚠️ Нарушение: {", ".join(reasons)}</span>'
        # ДОБАВИТЬ ЭТОТ БЛОК ПЕРЕД ФОРМИРОВАНИЕМ СТРОКИ HTML:
        try:
            receives_val = f"{int(cam.get('ip_in_receives', 0) or 0):,}"
            requests_val = f"{int(cam.get('ip_out_requests', 0) or 0):,}"
            # Добавили проверку поля ошибок, на котором скрипт падает сейчас:
            errors_val = int(cam.get('ip_in_hdr_errors', 0) or 0)
        except ValueError as e:
            problem_file = cam.get("file_source", "Неизвестный файл")
            print(f"\n[ОШИБКА] Сбой в файле: {problem_file}")
            print(f"ip_in_receives: '{cam.get('ip_in_receives')}'")
            print(f"ip_out_requests: '{cam.get('ip_out_requests')}'")
            print(f"ip_in_hdr_errors: '{cam.get('ip_in_hdr_errors')}'")
            raise e

        # Исправлено: кавычки внутри стилей заменены на двойные, чтобы не конфликтовать с f-строкой
        html += f"""
        <div class="{card_class}" 
             data-operator="{cam.get('operator', 'Н/Д')}" 
             data-speed="{speed_mbps}" 
             data-clients="{rtsp_count}"
             data-compliance="{'fail' if is_compliant_violation else 'pass'}"
             data-tz="{cam.get('tz_number', 'Н/Д')}"
             data-order="{cam.get('order_number', 'Н/Д')}"
             data-ip="{cam.get('ip', 'Н/Д')}"
             data-mac="{format_mac(cam.get('mac_address_v6') or cam.get('mac_address_v4') or 'Н/Д')}"
             data-uptime="{uptime_cleaned}"
             data-speed-text="{format_speed(cam.get('interface_speed', 'Н/Д'))}"
             data-errors="{cam.get('ip_in_hdr_errors', 0)}">
            <div class="card-header">
                <span class="camera-title">
                    <b>Камера № {cam.get('tz_number', 'Н/Д')}</b> | Заказ № {cam.get('order_number', 'Н/Д')} | Опер: {cam.get('operator', 'Н/Д')}
                </span>
                <div>
                    {compliance_badge}
                    <span class="badge {rtsp_badge_class}">{rtsp_badge_text}</span>
                </div>
            </div>
            <div class="card-body">
                <div class="info-block">
                    <h3>Системные данные (SNMP)</h3>
                    <div class="info-grid">
                        <div class="info-label">IP-адрес:</div>
                        <div class="info-value"><b>{cam.get('ip')}</b></div>
                        
                        <div class="info-label">Uptime:</div>
                        <div class="info-value" style="{"color: #b91c1c; font-weight: bold;" if uptime_days < 1.0 else ""}">{uptime_cleaned}</div>
                        
                        <div class="info-label">MAC-адрес:</div>
                        <div class="info-value" style="font-family: monospace; font-weight: bold;">
                            {format_mac(cam.get('mac_address_v6') or cam.get('mac_address_v4') or 'Н/Д')}
                        </div>
                        
                        <div class="info-label">Скорость линка:</div>
                        <div class="info-value" style="font-weight: bold; color: {"#b91c1c" if speed_mbps < 100 else "#2563eb"};">
                            {format_speed(cam.get('interface_speed', 'Н/Д'))}
                        </div>
                        
                        <div class="info-label">Имя устройства:</div>
                        <div class="info-value">{cam.get('sys_name', 'Без имени')}</div>
                    </div>
                </div>
                <div class="info-block">
                    <h3>Сетевой трафик и подключения</h3>
                    <div class="info-grid" style="margin-bottom: 15px;">
                        <div class="info-label">Получено пакетов:</div>
                        <div class="info-value">{receives_val}</div>

                        <div class="info-label">Отправлено пакетов:</div>
                        <div class="info-value">{requests_val}</div>                        
                        <div class="info-label">Ошибки IP (Вход.):</div>
                        <div class="info-value" style="color: {"red" if errors_val > 0 else "inherit"}">
                        {errors_val}
                        </div>

                    </div>
                    <div style="font-size: 14px; font-weight: 500; color: #475569; margin-bottom: 5px;">
                        Адреса клиентов (RTSP поток):
                    </div>
        """
        clients = cam.get("connected_clients", [])
        if clients:
            html += '<ul class="client-list">'
            for client in clients:
                # ИСПРАВЛЕНО: убран некорректный символ из кода JS
                html += f"""
                <li class="client-item">
                    <span>🖥️ {client['client_ip']}</span>
                    <span style="color: #94a3b8;">порт: {client['client_port']}</span>
                </li>
                """
            html += '</ul>'
        else:
            html += '<div style="font-size: 13px; color: #94a3b8; font-style: italic;">Активные подключения отсутствуют</div>'
            
        html += """
                </div>
            </div>
        </div>
        """

    html += """</main></div>

<script>
function applyFilters() {
    const searchQuery = document.getElementById('filter-search').value.toLowerCase().trim();
    const opFilter = document.getElementById('filter-operator').value;
    const speedFilter = document.getElementById('filter-speed').value;
    const clientsFilter = document.getElementById('filter-clients').value;
    const complianceFilter = document.getElementById('filter-compliance').value;

    const cards = document.querySelectorAll('.card');
    let visibleCount = 0;

    cards.forEach(card => {
        const cardTz = card.getAttribute('data-tz').toLowerCase();
        const cardOrder = card.getAttribute('data-order').toLowerCase();
        const cardOp = card.getAttribute('data-operator');
        const cardIp = card.getAttribute('data-ip').toLowerCase();
        const cardMac = card.getAttribute('data-mac').toLowerCase();
        
        const cardSpeed = parseInt(card.getAttribute('data-speed') || '0');
        const cardClients = parseInt(card.getAttribute('data-clients') || '0');
        const cardCompliance = card.getAttribute('data-compliance');

        let show = true;

        if (searchQuery !== '') {
            const matchesSearch = cardTz.includes(searchQuery) || 
                                  cardOrder.includes(searchQuery) || 
                                  cardOp.toLowerCase().includes(searchQuery) || 
                                  cardIp.includes(searchQuery) || 
                                  cardMac.includes(searchQuery);
            if (!matchesSearch) show = false;
        }

        if (opFilter !== 'all' && cardOp !== opFilter) show = false;
        if (speedFilter !== 'all' && parseInt(speedFilter) !== cardSpeed) show = false;
        if (clientsFilter === 'active' && cardClients === 0) show = false;
        if (clientsFilter === 'empty' && cardClients > 0) show = false;
        if (complianceFilter === 'violators' && cardCompliance === 'pass') show = false;

        if (show) {
            card.style.display = 'block';
            visibleCount++;
        } else {
            card.style.display = 'none';
        }
    });

    document.getElementById('total-badge').innerText = 'Отфильтровано устройств: ' + visibleCount;
}

function exportToExcel() {
    const cards = document.querySelectorAll('.card');
    const exportData = [];
    
    const headers = [
        "№ ТЗ", "№ Заказа", "Оператор", "IP-адрес", "MAC-адрес", 
        "Uptime", "Скорость порта", "Активные сессии", "Ошибки IP (Вход.)", "Статус критериев"
    ];
    exportData.push(headers);
    
    cards.forEach(card => {
        if (card.style.display !== 'none') {
            const isFailed = card.getAttribute('data-compliance') === 'fail';
            exportData.push([
                card.getAttribute('data-tz'),
                card.getAttribute('data-order'),
                card.getAttribute('data-operator'),
                card.getAttribute('data-ip'),
                card.getAttribute('data-mac'),
                card.getAttribute('data-uptime'),
                card.getAttribute('data-speed-text'),
                parseInt(card.getAttribute('data-clients') || '0'),
                parseInt(card.getAttribute('data-errors') || '0'),
                isFailed ? "⚠️ НЕ СООТВЕТСТВУЕТ" : "✅ Норма"
            ]);
        }
    });
    
    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.aoa_to_sheet(exportData);
    
    ws['!cols'] = [];
    for (let i = 0; i < headers.length; i++) {
        let max_len = 0;
        exportData.forEach(row => {
            const val = row[i] ? row[i].toString() : '';
            if (val.length > max_len) max_len = val.length;
        });
        ws['!cols'].push({ wch: max_len + 3 });
    }
    
    XLSX.utils.book_append_sheet(wb, ws, "Отфильтрованные камеры");
    XLSX.writeFile(wb, "camera_filtered_report.xlsx");
}
</script>
</body>
</html>
"""
    return html

def main():
    cameras_data = load_metrics()
    if not cameras_data:
        print(f"Ошибка: Не найдено JSON файлов. Сначала запустите сканирование.")
        return
        
    html_content = generate_html(cameras_data)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[УСПЕХ] HTML Панель создана: {os.path.abspath(REPORT_FILE)}")

if __name__ == "__main__":
    main()

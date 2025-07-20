import os
import re
import json
from datetime import datetime

# Регулярное выражение для разбора строки лога
LOG_REGEX = r'^(\S+) - - $([^$]+)$ "(\w+) (\S+) HTTP/\d\.\d" (\d{3}) (\d+|-) "([^"]*)" "([^"]*)" (\d+)$'

# Поддерживаемые HTTP-методы
HTTP_METHODS = {"GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"}

def parse_log_line(line):
    match = re.match(LOG_REGEX, line)
    if not match:
        return None

    ip, timestamp, method, url, status, size, referer, user_agent, duration = match.groups()
    return {
        'ip': ip,
        'date': timestamp,
        'method': method,
        'url': url,
        'status': status,
        'size': size,
        'refer': referer,
        'user_agent': user_agent,
        'duration': int(duration)
    }

def analyze_log_file(file_path):
    stats = {
        'total_requests': 0,
        'top_ips': {},
        'top_longest': [],
        'total_stat': {m: 0 for m in HTTP_METHODS}
    }

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data = parse_log_line(line.strip())
            if not data:
                continue

            # Общее количество запросов
            stats['total_requests'] += 1

            # Подсчёт IP
            ip = data['ip']
            stats['top_ips'][ip] = stats['top_ips'].get(ip, 0) + 1

            # Подсчёт методов
            method = data['method']
            if method in HTTP_METHODS:
                stats['total_stat'][method] += 1

            # Топ самых долгих запросов
            stats['top_longest'].append({
                'ip': data['ip'],
                'date': '[' + data['date'] + ']',
                'method': data['method'],
                'url': data['url'],
                'duration': data['duration']
            })

    # Сортировка и выборка top 3
    stats['top_ips'] = dict(sorted(stats['top_ips'].items(), key=lambda x: -x[1])[:3])
    stats['top_longest'] = sorted(stats['top_longest'], key=lambda x: -x['duration'])[:3]

    return stats

def save_stats_to_json(stats, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)

def main(path):
    if os.path.isfile(path):
        files = [path]
    elif os.path.isdir(path):
        files = [os.path.join(path, f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    else:
        print(f"Ошибка: Путь '{path}' не существует.")
        return

    for file in files:
        print(f"\nАнализ файла: {file}")
        stats = analyze_log_file(file)
        output_file = f"{file}.json"
        save_stats_to_json(stats, output_file)
        print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Использование: python analyzer.py <путь_к_логам>")
    else:
        main(sys.argv[1])
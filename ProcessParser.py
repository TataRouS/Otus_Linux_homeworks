import subprocess
import re
from datetime import datetime

def get_ps_output():
    """Выполняет команду ps aux и возвращает её вывод"""
    result = subprocess.run(['ps', 'aux'], stdout=subprocess.PIPE, text=True)
    return result.stdout

def parse_ps_output(output):
    lines = output.strip().split('\n')
    headers = lines[0].split()
    data_lines = lines[1:]
    processes = []
    users = set()
    user_process_count = {}
    total_cpu = 0.0
    total_mem = 0.0
    max_mem = 0.0
    max_cpu = 0.0
    max_mem_proc = ""
    max_cpu_proc = ""

    for line in data_lines:
        parts = re.split(r'\s+', line, maxsplit=10)  # Безопасное разделение
        if len(parts) < 11:
            continue

        user = parts[0]
        cpu = float(parts[2])
        mem = float(parts[3])
        command = parts[10].strip()

        # Обрезаем имя процесса до 20 символов
        short_command = command[:20] if len(command) > 20 else command

        # Подсчёт
        users.add(user)
        user_process_count[user] = user_process_count.get(user, 0) + 1
        total_cpu += cpu
        total_mem += mem

        # Определяем лидера по памяти и CPU
        if mem > max_mem:
            max_mem = mem
            max_mem_proc = short_command
        if cpu > max_cpu:
            max_cpu = cpu
            max_cpu_proc = short_command

        processes.append({
            'user': user,
            'cpu': cpu,
            'mem': mem,
            'command': short_command
        })

    return {
        'users': sorted(users),
        'total_processes': len(processes),
        'user_process_count': user_process_count,
        'total_cpu': round(total_cpu, 1),
        'total_mem': round(total_mem, 1),
        'max_mem_proc': f"{max_mem_proc} ({max_mem})",
        'max_cpu_proc': f"{max_cpu_proc} ({max_cpu})"
    }


def generate_report(data, report=None):
    report = []
    report.append("Отчёт о состоянии системы:")
    report.append(f"Пользователи системы: {', '.join([f"'{u}'" for u in data['users']])}")
    report.append(f"Процессов запущено: {data['total_processes']}\n")
    report.append("Пользовательских процессов:")

    for user, count in data['user_process_count'].items():
        report.append(f"{user}: {count}")

    report.append("\nВсего памяти используется: {}%".format(data['total_mem']))
    report.append("Всего CPU используется: {}%".format(data['total_cpu']))
    report.append("Больше всего памяти использует: {}".format(data['max_mem_proc']))
    report.append("Больше всего CPU использует: {}".format(data['max_cpu_proc']))

    full_report = '\n'.join(report)
    print(full_report)

    return full_report


def save_report_to_file(report):
    now = datetime.now().strftime("%d-%m-%Y-%H:%M")
    filename = f"{now}-scan.txt"
    with open(filename, 'w') as f:
        f.write(report)
    print(f"\nОтчёт сохранён в файл: {filename}")


if __name__ == "__main__":
    ps_output = get_ps_output()
    parsed_data = parse_ps_output(ps_output)
    report = generate_report(parsed_data)
    save_report_to_file(report)
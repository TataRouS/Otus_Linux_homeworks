# echo_server.py
import socket
from http import HTTPStatus
from urllib.parse import parse_qs, urlparse


def parse_request(data):
    """Разбираем HTTP-запрос и возвращаем метод, путь, заголовки и тело."""
    lines = data.split(b'\r\n')
    if not lines or not lines[0]:
        return None, None, {}, b''

    # Первая строка: METHOD PATH VERSION
    request_line = lines[0].decode('utf-8')
    parts = request_line.split()
    if len(parts) < 2:
        return None, None, {}, b''

    method = parts[0]
    path = parts[1]

    # Парсим заголовки
    headers = {}
    i = 1
    while i < len(lines) and lines[i]:
        if b':' in lines[i]:
            key, value = lines[i].split(b':', 1)
            headers[key.decode('utf-8').strip()] = value.decode('utf-8').strip()
        i += 1

    # Тело (если есть)
    body_start = i + 1
    body = b'\r\n'.join(lines[body_start:])

    return method, path, headers, body


def get_status_from_query(query):
    """Извлекаем статус из параметра status, валидируем и возвращаем int."""
    try:
        params = parse_qs(query)
        status_list = params.get('status', [])
        if status_list:
            status = int(status_list[0])
            # Проверяем, существует ли такой статус в HTTPStatus
            if status in HTTPStatus._value2member_map_:
                return status
    except (ValueError, TypeError):
        pass
    return 200  # По умолчанию


def handle_client(client_socket, client_address):
    """Обработка одного клиента."""
    try:
        request_data = b''
        client_socket.settimeout(5.0)  # Защита от зависания

        while True:
            chunk = client_socket.recv(4096)
            request_data += chunk
            if len(chunk) < 4096:
                break

        if not request_data:
            return

        method, path, headers, body = parse_request(request_data)
        if not method:
            method = 'UNKNOWN'

        # Парсим URL, чтобы получить query-параметры
        parsed_url = urlparse(path)
        status_code = get_status_from_query(parsed_url.query)

        # Получаем текстовую фразу статуса
        try:
            status_phrase = HTTPStatus(status_code).phrase
        except ValueError:
            status_code = 200
            status_phrase = HTTPStatus.OK.phrase

        # Формируем тело ответа
        response_body_lines = [
            f"Request Method: {method}",
            f"Request Source: {client_address}",
            f"Response Status: {status_code} {status_phrase}",
        ]

        # Добавляем все заголовки
        for key, value in headers.items():
            response_body_lines.append(f"{key}: {value}")

        response_body = "\r\n".join(response_body_lines)
        response_body_bytes = response_body.encode('utf-8')

        # Формируем HTTP-ответ
        response = (
            f"HTTP/1.1 {status_code} {status_phrase}\r\n"
            f"Content-Type: text/plain; charset=utf-8\r\n"
            f"Content-Length: {len(response_body_bytes)}\r\n"
            f"Connection: close\r\n"
            f"\r\n"
        ).encode('utf-8') + response_body_bytes

        client_socket.sendall(response)

    except Exception as e:
        # На всякий случай, чтобы сервер не упал
        print(f"Ошибка при обработке клиента: {e}")
        try:
            # Отправляем 500 в случае ошибки
            error_body = "Internal Server Error"
            response = (
                "HTTP/1.1 500 Internal Server Error\r\n"
                "Content-Type: text/plain; charset=utf-8\r\n"
                f"Content-Length: {len(error_body)}\r\n"
                "Connection: close\r\n"
                "\r\n"
                f"{error_body}"
            )
            client_socket.sendall(response.encode('utf-8'))
        except:
            pass
    finally:
        client_socket.close()


def run_server(host='127.0.0.1', port=8080):
    #Запуск сервера
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Echo-сервер запущен на http://{host}:{port}")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            handle_client(client_socket, client_address)
    except KeyboardInterrupt:
        print("\nСервер остановлен.")
    finally:
        server_socket.close()


if __name__ == "__main__":
    run_server()
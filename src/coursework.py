import io
import json
import sys
from pathlib import PurePosixPath

import requests
from pydantic_settings import BaseSettings, SettingsConfigDict
from requests.exceptions import HTTPError, JSONDecodeError, RequestException


class Settings(BaseSettings):
    yandex_disk_token: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


class IpifyClient:
    BASE_URL = "https://api.ipify.org"

    def get_current_ip(self) -> str:
        params = {"format": "json"}
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            ip_address = data.get("ip")
            if not ip_address:
                raise ValueError(f"В ответе ipify нет поля IP. Получено: {data}")
            return ip_address
        except HTTPError as e:
            raise RuntimeError(f"API ipify вернул ошибку: {e}") from e
        except RequestException as e:
            raise ConnectionError("Не удалось подключиться к сервису ipify") from e
        except JSONDecodeError as e:
            raise ValueError("Некорректный формат ответа от API (ожидался JSON)") from e


class IpInfoClient:
    BASE_URL = "https://ipinfo.io"

    def get_geo_data(self, ip_address: str) -> dict:
        url = f"{self.BASE_URL}/{ip_address}/geo"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            if not data:
                raise ValueError("API ipinfo вернул пустой ответ")
            return data
        except HTTPError as e:
            raise RuntimeError(f"Ошибка API: {e.response.status_code} {e.response.reason}") from e
        except RequestException as e:
            raise ConnectionError("Ошибка сети при запросе к ipinfo.io") from e
        except JSONDecodeError as e:
            raise ValueError("Ответ от API не является корректным JSON") from e


class YandexDiskClient:
    # Исправлено: Базовый URL теперь ведет на корневой интерфейс диска,
    # что позволит гибко обращаться и к /resources, и к /resources/upload
    API_BASE_URL = "https://cloud-api.yandex.net/v1/disk"

    def __init__(self, ya_disk_token: str):
        self.ya_disk_token = ya_disk_token
        self.headers = {"Authorization": f"OAuth {self.ya_disk_token}"}

    def _build_url(self, endpoint: str) -> str:
        """Возвращает конечный URL для API Yandex Disk."""
        return f"{self.API_BASE_URL}/{endpoint.lstrip('/')}"

    def create_folder(self, disk_folder_path: str) -> None:
        url = self._build_url("resources")
        params = {"path": disk_folder_path}
        try:
            response = requests.put(url, headers=self.headers, params=params)
            response.raise_for_status()
            print(f"Папка '{disk_folder_path}' успешно создана на Яндекс Диске.")
        except HTTPError as e:
            if e.response.status_code == 409:
                print(f"Папка '{disk_folder_path}' уже существует.")
            else:
                raise RuntimeError(
                    f"Ошибка при создании папки: {e.response.status_code} {e.response.reason}"
                ) from e
        except RequestException as e:
            raise ConnectionError("Ошибка сети при запросе к Яндекс Диску") from e
        except JSONDecodeError as e:
            raise ValueError("Ответ от API Яндекс Диска не является корректным JSON") from e

    def upload_file_from_memory(self, folder_path: str, filename: str, data: dict) -> None:
        try:
            disk_file_path = str(PurePosixPath(folder_path) / filename)

            # Корректный эндпоинт для запроса ссылки загрузки: /v1/disk/resources/upload
            upload_endpoint_url = self._build_url("resources/upload")
            params = {"path": disk_file_path, "overwrite": "true"}

            response = requests.get(upload_endpoint_url, headers=self.headers, params=params)
            response.raise_for_status()

            href = response.json().get("href")
            if not href:
                raise ValueError("В ответе API отсутствует ссылка 'href' для загрузки.")

            json_string = json.dumps(data, ensure_ascii=False, indent=4)
            file_bytes = json_string.encode("utf-8")
            memory_file = io.BytesIO(file_bytes)

            files = {"file": (filename, memory_file, "application/json")}
            put_response = requests.put(href, files=files)
            put_response.raise_for_status()

            print(f"Файл '{filename}' успешно загружен в папку '{folder_path}' без сохранения на ПК.")

        except HTTPError as e:
            raise RuntimeError(
                f"Ошибка API при загрузке файла: {e.response.status_code} {e.response.reason}"
            ) from e
        except RequestException as e:
            raise ConnectionError("Ошибка сети при операции загрузки на Яндекс Диск") from e
        except JSONDecodeError as e:
            raise ValueError("Ответ от API Яндекс Диска не является корректным JSON") from e


def main():
    """Работа по разделу ООП.

    Лектор: Тимур Анвартдинов
    """
    try:
        # Читаем яндекс токен
        settings = Settings()

        ipify_client = IpifyClient()
        my_ip = ipify_client.get_current_ip()

        ipinfo_client = IpInfoClient()
        my_ip_info = ipinfo_client.get_geo_data(my_ip)

        yandex_client = YandexDiskClient(ya_disk_token=settings.yandex_disk_token)
        folder_name = "P160"
        file_name = "info_ip.json"

        yandex_client.create_folder(folder_name)
        yandex_client.upload_file_from_memory(
            folder_path=folder_name, filename=file_name, data=my_ip_info
        )
        print("Выполнение программы успешно завершено.")

    except ConnectionError as e:
        print(f"Ошибка сети: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Ошибка обработки данных: {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"Критическая ошибка API: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Непредвиденная системная ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
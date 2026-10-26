#import os
#from dotenv import load_dotenv
import requests
from pydantic_settings import BaseSettings, SettingsConfigDict
from requests.exceptions import HTTPError, JSONDecodeError, RequestException


class Settings(BaseSettings):
    yandex_disk_token: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"              # Игнорировать лишние переменные в .env, которых нет в классе
    )


class IpifyClient:
    #https://api.ipify.org/?format=json
    BASE_URL = "https://api.ipify.org"

    def get_current_ip(self) -> str:
        params = {"format": "json"}
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            ip_address = data.get("ip")
            if not ip_address:
                raise ValueError(f"В ответе ipifi нет поля IP. Получено: {data}")
            return ip_address
        except HTTPError as e:
            raise RuntimeError(f"API ipify вернул ошибку: {e}") from e
        except RequestException as e:
            raise ConnectionError("Не удалось подключиться к сервису ipify") from e
        except JSONDecodeError as e:
            raise ValueError("Некорректный формат ответа от API (ожидался JSON)") from e


class IpInfoClient:
    #https://ipinfo.io/188.242.138.63/geo
    BASE_URL = "https://ipinfo.io"
    def get_geo_data(self, ip_address: str) -> dict:
        url = f"{self.BASE_URL}/{ip_address}/geo"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            if not data:
                raise ValueError("API вернул пустой ответ")
            return data
        except HTTPError as e:
            raise RuntimeError(f"Ошибка API: {e.response.status_code} {e.response.reason}") from e
        except RequestException as e:
            raise ConnectionError("Ошибка сети при запросе к ipinfo.io") from e
        except JSONDecodeError as e:
            raise ValueError("Ответ от API не является корректным JSON") from e

class YandexDiskClient:
    API_BASE_URL = "https://cloud-api.yandex.net/v1/disk"

    def __init__(self, ya_disk_token: str):
        self.ya_disk_token = ya_disk_token
        self.headers = {"Authorization": f"OAuth {self.ya_disk_token}"}
    def get_resources(self, path):
        pass
    def _build_url(self, endpoint: str) -> str:
        """Возвращает конечный URL для API Yandex Disk."""
        return f"{self.API_BASE_URL}/{endpoint.lstrip('/')}"
    def create_folder(self, disk_folder_path: str):
        url = self._build_url("resources")
        params = {
            "path": disk_folder_path,
            "overwrite": "true",
            "fields": "name,created",
            }
        response = requests.put(url, headers=self.headers, params=params)
    def upload_file_from_memory(self, folder_path: str, filename: str, data: dict):
        pass

def main():
    """Работа по разделу ООП.
    Лектор: Тимур Анвартдинов"""

    # load_dotenv() # Загружаем переменные из .env
    # api_key = os.getenv("YANDEX_DISK_TOKEN")  # os.environ.get("YANDEX_DISK_TOKEN")
    # if not api_key:
    #     raise ValueError("Отсутствует токен для работы с Yandex Disk!")
    # print(api_key)

    # Читаем яндекс токен
    settings = Settings()
    #print(settings.yandex_disk_token)

    ipify_client = IpifyClient()
    my_ip = ipify_client.get_current_ip()
    print(f" Мой IP адрес: {my_ip}")

    ipinfo_client = IpInfoClient()
    my_city = ipinfo_client.get_geo_data(my_ip)
    print(my_city.get("city"))

    yandex_client = YandexDiskClient(ya_disk_token=settings.yandex_disk_token)

# Эта конструкция проверяет, как был запущен файл
if __name__ == "__main__":
    main()

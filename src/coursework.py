#import os
#from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    yandex_disk_token: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"              # Игнорировать лишние переменные в .env, которых нет в классе
    )

class YandexDiskClient:
    API_BASE_URL = "https://cloud-api.yandex.net/v1/disk"

    def __init__(self, ya_disk_token: str):
        self.ya_disk_token = ya_disk_token

    def get_resources(self, path):
        pass

def main():
    """Работа по курсу ООП"""

    # load_dotenv() # Загружаем переменные из .env
    # api_key = os.getenv("YANDEX_DISK_TOKEN")  # os.environ.get("YANDEX_DISK_TOKEN")
    # if not api_key:
    #     raise ValueError("Отсутствует токен для работы с Yandex Disk!")
    # print(api_key)

    settings = Settings()
    print(settings.yandex_disk_token)


# Эта конструкция проверяет, как был запущен файл
if __name__ == "__main__":
    main()

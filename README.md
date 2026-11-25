# Калькулятор страхования «Грузовичкоф Автофлот»

Сервис расчёта страховой премии и страховой суммы для грузоперевозок (`GruzovichkofAvtoflotMSP`), построенный на базе Flask и `innoseti-calc-api`.

## Поддерживаемые страховые компании

Расчёт выполняется для типа страхования `cargo` в валюте `RUB`. Выбор и доступность страховой компании зависят от даты расчёта (настраивается в `config.py`):

| Страховая компания | Дата начала действия |
| --- | --- |
| `RenaissanceMSP` | `2023-06-15` |
| `AlfastrahMSP` | `2023-09-01` |
| `SberbankInsMSP` | `2024-10-01` |
| `SogazMSP` | `2024-11-18` |

## Структура проекта

- `server_gruzovichkof_avtoflot.py` — основной модуль сервера: инициализация `ApiTemplate`, проверка входных полей (`check_fields`), расчёт (`calculator`) и эндпоинт конфигурации `/api/v1/calc_config`.
- `calculation.py` — функции расчёта страховой премии, страховой суммы и секции (включая отдельную логику для `SogazMSP`).
- `distribution.py` — определение страховой компании (`get_insurer_msp`) по дате запроса.
- `custom_tariff_loader.py` — загрузка тарифов (`CustomTariffLoader`).
- `config.py` — настройки сервера, перечень страховых компаний, даты их действия и поддерживаемые валюты.
- `wsgi.py` — точка входа WSGI-приложения.
- `gunicorn.conf.py` — конфигурация Gunicorn.
- `requirements.txt` — зависимости проекта.

## Эндпоинты API

- `/api/v1/calc_price_all` — одиночный расчёт страховой премии.
- `/api/v1/calc_price_bulk_all` — пакетный расчёт страховой премии.
- `/api/v1/calc_config` — получение конфигурации калькулятора (требует технической авторизации `@api.auth(tech=True)`).

## Переменные окружения

```dotenv
TOKEN=<dev/prod token>
TOKEN_TECH=<tech token> for the config endpoint
ENV=dev/prod

REDIS_HOST=<redis host>
REDIS_PORT=6379
REDIS_DB=0
USE_AUTH=0/1
WD=/path_to_calc/calc_module
DEBUG=0/1
USE_RELOADER=0
PROCESSES=10

CURRENCIES_SERVER_HOST=ip
CURRENCIES_SERVER_PORT=port
CURRENCIES_SERVER_LOGIN=pass
CURRENCIES_SERVER_PASSWORD=pass
CURRENCIES_SERVER_API_VERSION=v2
BROKER_TOKEN=Bearer token
```

## Установка и запуск

1. Установите зависимости:

```bash
pip install -r requirements.txt
```

2. Создайте файл `.env` и заполните необходимые переменные окружения.

3. Запустите сервер:

- напрямую через Python (передав порт первым аргументом):

```bash
python server_gruzovichkof_avtoflot.py 5000
```

- через Gunicorn:

```bash
gunicorn -c gunicorn.conf.py -b 0.0.0.0:5000 wsgi:app
```

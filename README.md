# Инструкция по локальной установке и запуску 

### 1. Установка зависимостей

Перед началом работы убедитесь, что у вас установлен Python 3.10+ и pipenv для управления зависимостями Python.

```bash
pip install pipenv
```

Установка зависимостей из файла requirements.txt:

```bash
pip install -r requrements.txt
```

### 2. Настройка базы данных
Сервис использует PostgreSQL. Создайте базу данных и настройте соединение в файле app/.env.

```
BASE=postgresql://username:password@localhost/database_name
```

### 3. Запуск
Определите функцию local_startup в файле main.py в блоке if __name__ == "__main__":<br>
и выполните файл main.py
```bash
python main.py
```


## Инструкция для запуска через docker

По умолчанию достаточно ввести команду находясь в директории с файлом docker-compose.yml:
```bash
docker-compose up -d
```


### 1. Настройка базы данных
Заполните поля в файле docker-compose.yml:
```
POSTGRES_USER: username
POSTGRES_DB: database_name
POSTGRES_PASSWORD: password
```
Настройте соединение в файле app/.env.
```
BASE=postgresql://username:password@localhost/database_name
```

### 2. Запуск
Определите функцию docker_startup() в файле main.py в блоке if __name__ == "__main__":<br>
и примените команду находясь в директории с файлом docker-compose.yml:
```bash
docker-compose up -d
```



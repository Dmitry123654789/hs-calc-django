## Задачи

### Функционал

* на portal-order и glukhar написать процент дилера
* excel, кп

### Стилистические изменения

* Поработать над стилем сайта

### Другое

* Проверить правильность всех расчетов

### Тестовы данные

* админ -> admin

пароль: 12345678

## Установка и запуск

### 1. Клонирование репозитория и переход в папку проекта

```bash
https://github.com/Dmitry123654789/hs-calc-django.git
cd hs-calc-django
```

### 2. Создание и активация виртуального окружения

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Установка зависимостей

**Для разработки (dev режим):**

```bash
pip install -r requirements/dev.txt
```

*Включает все зависимости для разработки, включая инструменты для тестирования, линтеры и отладку.*

**Для production (prod режим):**

```bash
pip install -r requirements/prod.txt
```

*Содержит только минимальный набор пакетов, необходимых для работы приложения.*

**Для запуска тестов (test режим):**

```bash
pip install -r requirements/test.txt
```

*Включает зависимости для тестирования и проверки качества кода.*

### 4. Настройка переменных окружения

Создайте файл `.env` необходимые переменные.
Пример заполнения можно увидеть в файле `template.env`

**Для копирования настроек из template.env в .env:**

**Windows:**

```bash
copy template.env .env
```

**Mac/Linux:**

```bash
cp template.env .env
```

**После создания файла `.env` обязательно отредактируйте его, заполнив реальные значения переменных вместо
placeholder'ов.**

### 5. Переход в корень проекта

```bash
cd hs_calc
```

### 6. Создание тестовых данных

```bash
python manage.py migrate
```

### 7. Загрузка необходимых данных для расчетов и admin пользователя

```bash
python manage.py loaddata mydata
```

### 8. Запуск сервера

```bash
python manage.py runserver
```

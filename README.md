# OOP_PythonTask_CRUD

## Как это кушатц

Создаем .venv:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
source .venv\Scripts\activate    # Windows
```

Ставим зависимости
```bash
pip install -r requirements.txt
```

Запускакм сервер
```bash
uvicorn main:app --reload
```
Если что-то идет не по плану, то в целом список зависимостей такой:
```bash
pip install fastapi uvicorn
```

---------------

Импортируйте `Collection.postman_collection.json` в postman для проверки
Либо используйте `localhost/docs` для досупа к сваггеру, там тоже можно пощупать апишку
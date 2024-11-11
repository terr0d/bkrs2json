# Конвертер DSL в JSON для словарей bkrs.info

## Описание

Простой скрипт, который обрабатывает файлы DSL, содержащие китайско-русские словарные статьи с портала bkrs.info, и преобразует их в структурированный JSON-формат. Извлекает китайские слова, их пиньинь и значения на русском, очищая их от лишних тегов и примеров.

## Использование

```cmd
python bkrs2json.py <input_directory> <output_file> [--alt-format]

# <input_directory> : Директория с .dsl файлами для обработки
# <output_file>     : Путь и имя файла для выходного JSON
# [--alt-format]    : Опциональный флаг для альтернативного формата вывода
```

### Стандартный формат вывода:

```json
[
    {
        "some word": ["pinyin of the word", ["meaning_1", "meaning_2"]]
    },
]
```
### Альтернативный формат вывода (с флагом --alt-format):
```json
[
    {
        "word": "some word",
        "pinyin": "pinyin of the word",
        "meanings": ["meaning_1", "meaning_2"]
    },
]
```

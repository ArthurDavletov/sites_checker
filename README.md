# [site_checker](https://github.com/ArthurDavletov/sites_checker)

Программа для тестирования http-сайтов (задание для стажировки Infotecs)

## Описание работы

Программа запускает указанное пользователем количество запросов на хост и измеряет время запросов.

Вывод осуществляется в консоли или файл в виде таблицы.

|   Host   | Success | Failed | Errors | Min | Max | Avg |
|:--------:|:-------:|:------:|:------:|:---:|:---:|:---:|
|  Хост    |    1    |   0    |   0    |  1  |  1  |  1  |
|  Хост_2  |    1    |   0    |   0    |  2  |  2  |  2  |
|  Хост_3  |    0    |   0    |   2    |     |     |     |

Все запросы осуществляются в асинхронном режиме с использованием aiohttp.

Также были написаны unittest для тестирования самой программы.

Документация функций и вывод ошибок в человекочитаемом виде на английском языке.

## Инструкция по запуску

### Установка необходимых компонентов

Для запуска необходима версия Python 3.10 и позже ([официальный сайт](https://www.python.org/downloads/))

### Виртуальное окружение

Рекомендуется использовать виртуальное окружение с установленной библиотекой aiohttp из requirements.txt.
Виртуальное окружение устанавливается единожды. При дальнейшем требуется лишь его активация

#### Установка на Windows

```console
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

#### Установка на Linux

```console
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### Активация на Windows

```console
.venv\Scripts\activate
```

#### Активация на Linux

```console
source .venv/bin/activate
```

### Запуск

Программу запускают в консоли.

```python ./bench.py [-h] [-C COUNT] (-H HOSTS | -F HOSTS) [-O OUTPUT]```

Она принимает **аргументы**:

* -H, --help. Выводит помощь.
* -C, --count. Количество запросов (по умолчанию 1)
* -H, --hosts. Список хостов, разделённых запятыми.
* -F, --file. Файл с сайтами, разбитыми на строки.
* -O, --output. Файл для вывода таблицы.
Если не указан, то вывод осуществляется в консоль

**Требования** к аргументам:

* Число запросов должно быть положительным числом.
* Хосты обязаны быть указаны.
**Либо** через файл, **либо** в строчке, разделёнными запятыми.
Если указать и файл (-F), и хосты (-H), произодёт ошибка.
* Сайты должны соотвествовать формату из [раздела 2.1 из RFC 1808](https://www.ietf.org/rfc/rfc1808.txt#:~:text=%3Cscheme%3E%3A//%3Cnet_loc%3E/%3Cpath%3E%3B%3Cparams%3E%3F%3Cquery%3E%23%3Cfragment%3E):
`http://yandex.ru/...`, `https://google.com/...` и т.д.



## Примеры работы

### Простой запуск

```console
python .\bench.py -H "https://yandex.ru,https://google.com" -C 2
```

```text
+----------------------+-----------+----------+----------+---------+---------+---------+
|         Host         |  Success  |  Failed  |  Errors  |   Min   |   Max   |   Avg   |
+----------------------+-----------+----------+----------+---------+---------+---------+
|  https://yandex.ru   |     2     |    0     |    0     |   1.83  |   1.91  |   1.87  |
+----------------------+-----------+----------+----------+---------+---------+---------+
|  https://google.com  |     2     |    0     |    0     |  2.235  |  2.242  |  2.239  |
+----------------------+-----------+----------+----------+---------+---------+---------+
```

### Запуск сайтов с "плохими" статус-кодами без указания количества запросов

```console
python .\bench.py -H "https://yandex.ru/404,https://google.com/404"
```

```text
+--------------------------+-----------+----------+----------+---------+---------+---------+
|           Host           |  Success  |  Failed  |  Errors  |   Min   |   Max   |   Avg   |
+--------------------------+-----------+----------+----------+---------+---------+---------+
|  https://yandex.ru/404   |     0     |    1     |    0     |  0.502  |  0.502  |  0.502  |
+--------------------------+-----------+----------+----------+---------+---------+---------+
|  https://google.com/404  |     0     |    1     |    0     |  1.026  |  1.026  |  1.026  |
+--------------------------+-----------+----------+----------+---------+---------+---------+
```

### Запуск несуществующих сайтов

```console
python .\bench.py -H "https://hello.world2005,http://anime.forever/" -C 1
```

```text
+---------------------------+-----------+----------+----------+-------+--------+-------+
|            Host           |  Success  |  Failed  |  Errors  |  Min  |  Max   |  Avg  |
+---------------------------+-----------+----------+----------+-------+--------+-------+
|  https://hello.world2005  |     0     |    0     |    1     |       |        |       |
+---------------------------+-----------+----------+----------+-------+--------+-------+
|   http://anime.forever/   |     0     |    0     |    1     |       |        |       |
+---------------------------+-----------+----------+----------+-------+--------+-------+
```

### Запуск с файла

```console
python .\bench.py -F ./input.txt -C 2
```

```text
+----------------------+-----------+----------+----------+---------+---------+---------+
|         Host         |  Success  |  Failed  |  Errors  |   Min   |   Max   |   Avg   |
+----------------------+-----------+----------+----------+---------+---------+---------+
|  https://yandex.ru   |     0     |    0     |    2     |         |         |         |
+----------------------+-----------+----------+----------+---------+---------+---------+
|  https://google.com  |     2     |    0     |    0     |  1.729  |   1.75  |   1.74  |
+----------------------+-----------+----------+----------+---------+---------+---------+
|    https://vk.com    |     2     |    0     |    0     |  1.019  |  1.054  |  1.036  |
+----------------------+-----------+----------+----------+---------+---------+---------+
```

### Вывод в файл

```console
python .\bench.py -H "https://yandex.ru" -O "output.txt"
```

```console
cat ./output.txt
```

```text
+---------------------+-----------+----------+----------+---------+---------+---------+
|         Host        |  Success  |  Failed  |  Errors  |   Min   |   Max   |   Avg   |
+---------------------+-----------+----------+----------+---------+---------+---------+
|  https://yandex.ru  |     1     |    0     |    0     |  1.191  |  1.191  |  1.191  |
+---------------------+-----------+----------+----------+---------+---------+---------+
```

### Одновременно все виды запросов (Success, Failed, Errors)

```console
python .\bench.py -H "https://yandex.ru,https://google.com/404,https://anime.forever" -C 1
```

```text
+--------------------------+-----------+----------+----------+---------+---------+---------+
|           Host           |  Success  |  Failed  |  Errors  |   Min   |   Max   |   Avg   |
+--------------------------+-----------+----------+----------+---------+---------+---------+
|    https://yandex.ru     |     1     |    0     |    0     |  1.219  |  1.219  |  1.219  |
+--------------------------+-----------+----------+----------+---------+---------+---------+
|  https://google.com/404  |     0     |    1     |    0     |  1.252  |  1.252  |  1.252  |
+--------------------------+-----------+----------+----------+---------+---------+---------+
|  https://anime.forever   |     0     |    0     |    1     |         |         |         |
+--------------------------+-----------+----------+----------+---------+---------+---------+
```

### Попытка ввести неправильный хост

```console
python .\bench.py -H "tatar_songs" -C 1
```

```text
Error: Argument "tatar_songs" must be a valid URL.
```

### Попытки ввода и в консоли, и с файла

```console
python .\bench.py -H "https://yandex.ru" -F "input.txt" -C 1
python .\bench.py -H "tatar_songs" -F "input.txt" -C 1
python .\bench.py -H "https://yandex.ru" -F "this_file_dont_exist.not_txt" -C 1
python .\bench.py -H "tatar_songs" -F "this_file_dont_exist.not_txt" -C 1
python .\bench.py -H "tatar_songs" -F "invalid_hosts.txt" -C 1
python .\bench.py -H "https://yandex.ru"" -F "invalid_hosts.txt" -C 1
```

```text
sites_checker: error: argument -F/--file: not allowed with argument -H/--hosts
sites_checker: error: argument -F/--file: not allowed with argument -H/--hosts
sites_checker: error: argument -F/--file: not allowed with argument -H/--hosts
sites_checker: error: argument -F/--file: not allowed with argument -H/--hosts
sites_checker: error: argument -F/--file: not allowed with argument -H/--hosts
sites_checker: error: argument -F/--file: not allowed with argument -H/--hosts
```

### Попытка ввести данные с несуществующего файла

```console
python .\bench.py -F "this_file_dont_exist.not_txt"
```

```text
Error: File "this_file_dont_exist.not_txt" does not exist.
```

### Попытка ввести данные с директории вместо файла

```console
python .\bench.py -F ".venv"
```

```text
Error: ".venv" is not a file.
```

### Попытка ввести данные с файла с неправильными URL

```console
cat .\invalid_hosts.txt
python .\bench.py -F ".\invalid_hosts.txt"
```

```text
best_anime_songs
Error: Argument "best_anime_songs" must be a valid URL
```

### Попытки написать небылицу вместо аргумента --count

```console
python .\bench.py -F "https://yandex.ru" -C 0
python .\bench.py -F "https://yandex.ru" -C -1
python .\bench.py -F "https://yandex.ru" -C 1.1
python .\bench.py -F "https://yandex.ru" -C -132.1
python .\bench.py -F "https://yandex.ru" -C "cat"
python .\bench.py -F "https://yandex.ru" -C "https://google.com/"
```

```text
usage: sites_checker [-h] [-C COUNT] (-H HOSTS | -F FILE) [-O OUTPUT]
sites_checker: error: argument -C/--count: Argument "0" must be greater than 0.
usage: sites_checker [-h] [-C COUNT] (-H HOSTS | -F FILE) [-O OUTPUT]
sites_checker: error: argument -C/--count: Argument "-1" must be greater than 0.
usage: sites_checker [-h] [-C COUNT] (-H HOSTS | -F FILE) [-O OUTPUT]
sites_checker: error: argument -C/--count: Argument "1.1" must be an integer.
usage: sites_checker [-h] [-C COUNT] (-H HOSTS | -F FILE) [-O OUTPUT]
sites_checker: error: argument -C/--count: Argument "-132.1" must be an integer.
usage: sites_checker [-h] [-C COUNT] (-H HOSTS | -F FILE) [-O OUTPUT]
sites_checker: error: argument -C/--count: Argument "cat" must be an integer.
usage: sites_checker [-h] [-C COUNT] (-H HOSTS | -F FILE) [-O OUTPUT]
sites_checker: error: argument -C/--count: Argument "https://google.com/" must be an integer.
```


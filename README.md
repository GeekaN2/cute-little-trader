# cute-little-trader

Скрипт для торговли дельта нейтральной стратегией во имя фарма поинтов в боте pvp.trade.
Ссылка на бота: https://pvp.trade/join/jbzxu3

Бот приватный, распространяйте только среди криптомашин. Чем меньше людей о нем знает, тем проще нам фармить поинты.
По вопросам к @geekan

```
# Помощь со списком всех команд
./cute-little-trader.exe --help
```

Пример использования

```
# Запуск скрипта через .exe
./cute-little-trader.exe --config ./config.json
```

```
# Запуск скрипта через python
python index.py --config ./config.json
```

```
# Скрипт со всем возможными аргументами
./cute-little-trader.exe --config ./config.json --margin 100 --leverage 5 --duration-min 10 --duration-max 90 --sleep-orders 3 6 --sleep-iteration 60 --random-sleep 3 6
```

# Описание конфига json

api - api id и hash для управления юзерботами (пользователями). Создается на my.telegram.org в пункте API Development Tools. Можно воспринимать это API как клиент для телеграма, который может отправлять сообщения, получать сообщения, и т.д. от имени пользователя.
pairs - список пар для торговли (название пары: вес для рандома, чтобы определенные пары чаще попадались в рандоме)
proxies - список прокси для торговли, количество прокси равно количеству аккаунтов, бот подстроиться, будет делить маржу между аккаунтами, если их больше двух

Желательно покупать socks5 прокси, стоят порядка 100-150 рублей на месяц за штуку.

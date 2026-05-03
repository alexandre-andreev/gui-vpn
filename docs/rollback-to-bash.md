# Откат: управление VPN без awg-gui

Инструкция для случаев, когда приложение недоступно или не работает.

---

## Управление туннелем через bash

Все операции, которые выполняет awg-gui, можно воспроизвести штатными системными командами.

### Запустить туннель

```bash
sudo systemctl start awg-quick@wg0.service
```

### Остановить туннель

```bash
sudo systemctl stop awg-quick@wg0.service
```

### Перезапустить туннель

```bash
sudo systemctl restart awg-quick@wg0.service
```

### Включить автозапуск при загрузке

```bash
sudo systemctl enable awg-quick@wg0.service
```

### Отключить автозапуск

```bash
sudo systemctl disable awg-quick@wg0.service
```

---

## Смена конфигурации вручную

Чтобы переключиться на другой сервер:

```bash
# 1. Остановить туннель
sudo systemctl stop awg-quick@wg0.service

# 2. Заменить конфигурацию (пример: GermanyBerlinS7.conf)
sudo cp /path/to/GermanyBerlinS7.conf /etc/amnezia/amneziawg/wg0.conf

# 3. Запустить туннель с новой конфигурацией
sudo systemctl start awg-quick@wg0.service
```

---

## Восстановление исходного wg0.conf

При первом применении конфигурации через awg-gui создаётся резервная копия:

```
/etc/amnezia/amneziawg/wg0.conf.original
```

### Восстановить через интерфейс (если приложение запускается)

Настройки → кнопка **«Восстановить исходный wg0.conf»**

### Восстановить вручную

```bash
# Проверить наличие резервной копии
ls -la /etc/amnezia/amneziawg/wg0.conf.original

# Восстановить
sudo cp /etc/amnezia/amneziawg/wg0.conf.original \
        /etc/amnezia/amneziawg/wg0.conf

# Перезапустить туннель
sudo systemctl restart awg-quick@wg0.service
```

### Если резервной копии нет

Резервная копия создаётся только при первом вызове «Применить конфигурацию» через awg-gui. Если `wg0.conf.original` отсутствует — приложение ни разу не меняло конфиг, и текущий `wg0.conf` является оригинальным.

---

## Удаление awg-gui

Удалить PolicyKit-политику и helper-скрипт:

```bash
sudo rm /usr/local/lib/awg-gui/awg-gui-helper
sudo rmdir /usr/local/lib/awg-gui          # если каталог пуст
sudo rm /usr/share/polkit-1/actions/org.awg-gui.policy
```

Удалить Python-пакет и виртуальное окружение:

```bash
cd ~/awg-gui
rm -rf .venv awg_gui.egg-info
```

Удалить настройки и логи (опционально):

```bash
rm -rf ~/.local/share/awg-gui
rm -f ~/.config/awg-gui/config.json
```

Удалить автозапуск приложения (если был включён):

```bash
rm -f ~/.config/autostart/awg-gui.desktop
```

После удаления awg-gui туннель продолжит работать, пока его не остановить вручную (`systemctl stop awg-quick@wg0`).

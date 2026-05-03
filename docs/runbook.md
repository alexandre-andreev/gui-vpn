# Runbook: awg-gui

Операционные инструкции для диагностики и устранения проблем.

---

## 1. Запуск приложения

```bash
cd ~/awg-gui
.venv/bin/awg-gui
```

Или через ярлык в меню (если включён автозапуск приложения через Настройки).

Лог-файл: `~/.local/share/awg-gui/awg-gui.log`

```bash
tail -f ~/.local/share/awg-gui/awg-gui.log
```

---

## 2. Проверка статуса туннеля

### Через системный сервис

```bash
systemctl status awg-quick@wg0.service
```

Ожидаемый вывод при активном туннеле:
```
● awg-quick@wg0.service - AmneziaWG via wg-quick(8) for wg0
     Loaded: loaded (/lib/systemd/system/awg-quick@.service; enabled)
     Active: active (exited) since ...
```

### Через wg show

```bash
sudo wg show
```

Показывает активный интерфейс, публичный ключ, endpoint и статистику трафика.

### Проверка сетевого интерфейса

```bash
ip link show wg0
ip addr show wg0
```

---

## 3. Ошибки pkexec / отсутствие прав

### Симптом: диалог аутентификации не появляется

1. Убедитесь, что `polkit` установлен и запущен:
   ```bash
   systemctl status polkit
   ```
2. Проверьте, что helper-скрипт установлен:
   ```bash
   ls -la /usr/local/lib/awg-gui/awg-gui-helper
   # ожидается: -rwxr-xr-x 1 root root
   ```
3. Проверьте, что policy-файл установлен:
   ```bash
   ls /usr/share/polkit-1/actions/org.awg-gui.policy
   ```
4. Если файлы отсутствуют — переустановите:
   ```bash
   sudo bash install.sh
   ```

### Симптом: ошибка "Command not found" в интерфейсе

`pkexec` не найден в `PATH`. Установите:
```bash
sudo apt install policykit-1
```

### Симптом: pkexec завершается с ошибкой авторизации

- Пользователь нажал «Отмена» в диалоге аутентификации.
- Или сессия не является локальной (например, SSH без display). PolicyKit требует активную локальную сессию.

---

## 4. Где искать логи

| Источник | Путь / команда |
|----------|---------------|
| Лог приложения | `~/.local/share/awg-gui/awg-gui.log` |
| Systemd-журнал сервиса | `journalctl -u awg-quick@wg0.service -n 50` |
| Системный журнал (pkexec) | `journalctl -t polkit-agent -n 20` |
| Kernel/сеть | `journalctl -k \| grep -i wireguard` |

---

## 5. Туннель поднят, но интернет не работает

1. Проверьте, что `wg0.conf` содержит корректный `DNS`:
   ```bash
   grep -i dns /etc/amnezia/amneziawg/wg0.conf
   ```
2. Проверьте маршруты:
   ```bash
   ip route show
   ```
   Должен быть маршрут через `wg0`.
3. Проверьте endpoint сервера:
   ```bash
   sudo wg show wg0
   # поле endpoint и latest handshake
   ```
   Если `latest handshake` старше 3 минут — соединение разорвано. Попробуйте **Переключить** или выбрать другой сервер.
4. Попробуйте перезапустить туннель:
   ```bash
   sudo systemctl restart awg-quick@wg0.service
   ```

---

## 6. Восстановление исходного конфига

Если `wg0.conf` был заменён приложением и нужно вернуть оригинал:

**Через интерфейс:** Настройки → «Восстановить исходный wg0.conf»

**Вручную:**
```bash
sudo cp /etc/amnezia/amneziawg/wg0.conf.original \
        /etc/amnezia/amneziawg/wg0.conf
sudo systemctl restart awg-quick@wg0.service
```

Подробнее: [rollback-to-bash.md](rollback-to-bash.md)

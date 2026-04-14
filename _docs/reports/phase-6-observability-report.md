# Phase Report: phase-6-observability

Date: 2026-04-15
Spec: `_docs/specs/phase-6-observability.yaml`
Status: done

## Done

- В `OllamaClient` добавлено pre-request логирование provider-facing `messages` context.
- В логах теперь фиксируются `request_type`, `message_count`, `total_chars` и `estimated_tokens`.
- В `ChatService` добавана передача типа вызова: `regular_reply` и `summary_generation`.
- Добавлен конфиг-флаг `LOG_MODEL_CONTEXT`, включенный по умолчанию и позволяющий отключить полный context log.
- В context log добавлена базовая redaction типовых секретов: `token`, `telegram_bot_token`, `api_key`, `password`, `Authorization: Bearer`.
- Добавлены тесты клиента на observability, redaction и новый config-флаг.
- Обновлены `context-dump`, roadmap, spec и архитектурные документы.

## Not Done

- Не добавлялись внешние observability-системы, метрики или tracing.
- Точный tokenizer-based count не реализован: используется явная оценка по длине текста.
- Полный `pytest` в текущем окружении не запускался: при проверке оказалось, что `pytest` в среде отсутствует (`zsh: command not found: pytest`).

## Decisions Made

- Логировать нужно provider-facing context после materialization роли `summary`, чтобы в логах было видно именно то, что уходит в модель.
- Size metrics считаются в `OllamaClient`, чтобы они соответствовали фактическому запросу к провайдеру.
- Полный context log остается управляемым через отдельный config-флаг, но включен по умолчанию для этой фазы.

## Deviations From Spec

- Добавлена базовая redaction нескольких типовых секретных шаблонов, но без попытки решить полный production-grade sanitization свободного текста.

## Risks / Follow-ups

- Текущая redaction не гарантирует удаление всех возможных секретов из пользовательских сообщений.
- Оценочный token count может заметно расходиться с реальным tokenizer модели.
- Полный context logging делает логи чувствительными для production и может сильно увеличить их объем.

## Inputs For Next Phase

- В `phase-7-tests` стоит довести покрытие до полного прогона всего regression-набора, включая observability-ветки.
- Полезно добавить отдельные тесты на `logging_config` и на поведение логов при ошибках Ollama.
- Если observability будет развиваться дальше, стоит вынести redaction и context formatting в отдельный helper.

## Files Changed

- `app/clients/ollama_client.py`
- `app/config.py`
- `app/main.py`
- `app/services/chat_service.py`
- `tests/test_chat_service.py`
- `tests/test_config.py`
- `tests/test_ollama_client.py`
- `_docs/context-dump.md`
- `_docs/architecture/components.md`
- `_docs/architecture/runtime-flows.md`
- `_docs/roadmap.yaml`
- `_docs/specs/phase-6-observability.yaml`
- `_docs/reports/phase-6-observability-report.md`

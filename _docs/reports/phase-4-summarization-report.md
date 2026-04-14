# Phase Report: phase-4-summarization

Date: 2026-04-15
Spec: `_docs/specs/phase-4-summarization.yaml`
Status: done

## Done

- В `app/services/chat_service.py` добавлен отдельный summary workflow перед обычным reply flow.
- При превышении `SUMMARY_TRIGGER_MESSAGES` сервис выделяет старый префикс истории и отправляет его в модель отдельным LLM-call с summarization prompt.
- Добавлен отдельный prompt-файл `app/prompts/summarization_prompt.txt`.
- После генерации summary старая часть истории заменяется одним сообщением с ролью `summary` через `ConversationStore.replace_after_summary(...)`.
- Последующие запросы используют `summary` вместе со свежим хвостом истории.
- Добавлены настройки `SUMMARIZATION_PROMPT_PATH`, `SUMMARY_TRIGGER_MESSAGES` и `SUMMARY_MAX_CHARS`.
- Добавлена валидация новых настроек в `app/config.py`, включая инвариант `SUMMARY_TRIGGER_MESSAGES < MAX_HISTORY_MESSAGES`.
- Добавлено ограничение длины summary через `SUMMARY_MAX_CHARS`.
- Повторная суммаризация ограничена текущей policy: existing `summary` не пересжимается сразу, пока не накопится новый достаточный хвост обычных сообщений.
- Existing trimming policy из `phase-3` сохранена и продолжает работать поверх history с `summary`.
- Wiring `ChatService` в `app/main.py` обновлен под новые summary-настройки.
- Добавлены тесты на активацию summary branch, замену старой истории одним `summary`, повторное использование `summary` в следующем запросе и валидацию нового конфига.
- Обновлены spec, roadmap и context dump по фактическому завершению фазы.

## Not Done

- Не реализовано персистентное хранение summary вне текущего in-memory storage.
- Не реализована иерархическая или многоуровневая summary-система.
- Не добавлена отдельная observability для различения regular reply и summary call в логах.
- Не выполнен полноценный запуск `pytest` в текущем агентском окружении, потому что в нем отсутствует модуль `pytest`.
- Не переведен основной model contract на явный `system` message; это остается scope следующей `phase-5-system-prompt`.

## Decisions Made

- Summary встроена в уже существующий `messages` contract как обычное сообщение с ролью `summary`, без отдельного storage backend.
- Сервис сначала пытается сжать старый префикс истории, и только потом применяет обычный runtime trimming для запроса пользователя.
- Для summary выбран отдельный prompt-файл, чтобы не смешивать обычный ответ и summarization workflow.
- Summary сохраняется коротким и утилитарным: текст нормализуется и обрезается по `SUMMARY_MAX_CHARS`.
- Existing `summary` удерживается в начале истории, а повторная суммаризация зависит от накопления нового несжатого хвоста.
- Порог summary сделан конфигурируемым, стартовое значение оставлено `5` в соответствии с ранее зафиксированным design guidance.

## Deviations From Spec

- Существенных отклонений от spec нет.
- В рамках этой фазы summary и обычный вызов модели еще не различаются через отдельную observability или типизированный client contract; различие пока выражено только разными prompt и местом вызова в сервисе.
- Формальная зависимость на `phase-5-system-prompt` остается не полностью закрытой: summary prompt уже отделен, но основной system prompt еще не материализуется как `system` message в общем context array.

## Risks / Follow-ups

- Качество summary зависит от модели и может терять нюансы старой истории.
- Inline summarization добавляет дополнительную задержку перед основным ответом при длинной истории.
- Текущая policy защиты от деградации простая; при длином диалоге качество summary может постепенно ухудшаться без более строгих правил обновления.
- До установки и запуска `pytest` в рабочем окружении регрессионная проверка ограничивалась smoke-check сценарием.
- При переходе к `phase-5-system-prompt` нужно аккуратно совместить новый messages contract с уже реализованным summary flow.

## Inputs For Next Phase

- `phase-5-system-prompt` должна сохранить разделение между основным prompt и summarization prompt, уже введенное в этой фазе.
- При переводе на полный messages context `summary` должен остаться частью того же runtime-контракта и идти перед свежим хвостом истории.
- Новый `system` message нельзя проектировать так, чтобы он ломал current summary replacement flow в store.
- При добавлении observability стоит различать `regular_reply` и `summary_generation` как два разных типа LLM-вызова.

## Files Changed

- `app/config.py`
- `app/main.py`
- `app/services/chat_service.py`
- `app/prompts/summarization_prompt.txt`
- `tests/test_chat_service.py`
- `tests/test_config.py`
- `_docs/context-dump.md`
- `_docs/roadmap.yaml`
- `_docs/specs/phase-4-summarization.yaml`

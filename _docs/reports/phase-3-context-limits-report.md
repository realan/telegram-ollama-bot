# Phase Report: phase-3-context-limits

Date: 2026-04-14
Spec: `_docs/specs/phase-3-context-limits.yaml`
Status: done

## Done

- В `app/config.py` добавлены конфигурируемые лимиты `MAX_HISTORY_MESSAGES` и `MAX_CONTEXT_CHARS`.
- Для новых лимитов добавлена валидация: `MAX_HISTORY_MESSAGES >= 2`, `MAX_CONTEXT_CHARS > 0`, оба значения должны быть целыми числами.
- `ChatService` расширен trimming policy перед вызовом модели.
- Primary trimming реализован по количеству сообщений: сохраняется самый свежий хвост истории.
- Secondary trimming реализован по суммарной длине `content` как safeguard поверх message-count policy.
- Новый `user` message, обрабатываемый сейчас, всегда сохраняется в runtime context.
- Если в истории присутствует `summary`, он удерживается раньше свежего хвоста и не удаляется раньше обычных старых сообщений.
- Порядок сообщений после trimming сохраняется.
- Trimming применяется только к runtime context перед моделью и не меняет содержимое `ConversationStore`.
- Wiring `ChatService` в `app/main.py` обновлен под новые настройки лимитов.
- Добавлены тесты на trimming по количеству сообщений, сохранение порядка, защиту нового `user` message, поведение с `summary` и валидацию лимитов конфига.
- Обновлены spec, roadmap и context dump по фактическому завершению фазы.

## Not Done

- Не реализован summarization workflow.
- Не реализовано сжатие или trimming сохраненной истории в store.
- Не менялся storage backend.
- Не добавлено полное логирование model context.
- Не реализована token-oriented optimization.
- Полный запуск `pytest` не выполнен, потому что в текущем окружении отсутствует модуль `pytest`.

## Decisions Made

- Базовая стратегия trimming оставлена максимально простой: сначала limit по количеству сообщений, затем safeguard по длине текста.
- Default значения приняты как `MAX_HISTORY_MESSAGES=10` и `MAX_CONTEXT_CHARS=4000`.
- Policy применяется только в `ChatService` при сборке runtime context, чтобы не менять storage semantics раньше `phase-4-summarization`.
- `summary` учитывается уже сейчас как часть контракта, хотя его генерация еще не реализована.
- При превышении char-limit сначала удаляются самые старые обычные сообщения, и только потом, при необходимости, `summary`.

## Deviations From Spec

- Существенных отклонений от spec нет.
- Порог для включения summary не был введен как runtime-настройка, хотя он упомянут в roadmap; это не реализовывалось намеренно, потому что сама summarization остается вне scope `phase-3-context-limits`.
- Валидация и тесты сделаны шире минимального изменения, чтобы trimming policy была проверяемой и не ломала будущий контракт.

## Risks / Follow-ups

- Сохраненная per-user история продолжает расти в памяти процесса, потому что trimming пока применяется только к runtime context.
- Слишком маленькие лимиты могут ухудшить качество ответов модели из-за потери полезного хвоста диалога.
- При переходе к `phase-4-summarization` нужно аккуратно совместить replace logic в store и уже существующий runtime trimming.
- До установки `pytest` в окружение регрессионная проверка ограничена compile/smoke-проверками.

## Inputs For Next Phase

- `phase-4-summarization` должна опираться на уже существующий инвариант: `summary` идет перед свежим хвостом истории.
- Логика summary не должна ломать правило сохранения текущего `user` message в runtime context.
- Если summary будет заменять старый префикс в store, runtime trimming должен продолжить работать без изменения ролей и порядка сообщений.
- При следующем расширении тестов стоит сохранить текущие сценарии trimming как регрессионную базу.

## Files Changed

- `app/config.py`
- `app/main.py`
- `app/services/chat_service.py`
- `tests/test_chat_service.py`
- `tests/test_config.py`
- `_docs/context-dump.md`
- `_docs/roadmap.yaml`
- `_docs/specs/phase-3-context-limits.yaml`

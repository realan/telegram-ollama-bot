# Phase Report: phase-2-memory

Date: 2026-04-14
Spec: `_docs/specs/phase-2-memory.yaml`
Status: done

## Done

- Добавлен новый пакет `app/memory/` с runtime-типом `Message`, protocol `ConversationStore` и in-memory реализацией `InMemoryConversationStore`.
- Реализовано хранение истории отдельно по `user_id` в формате `{role, content}`.
- Для нового пользователя store корректно возвращает пустую историю.
- `ChatService` переведен на контракт `handle_user_message(user_id, text)` и теперь читает историю пользователя перед вызовом модели.
- В runtime context перед вызовом модели передается история пользователя плюс новое `user` message.
- После успешного ответа модели в историю сохраняется пара сообщений `user` и `assistant`.
- `chat_handler` в Telegram-слое остался тонким boundary и передает в сервис только `user_id` и текст.
- `OllamaClient` минимально адаптирован под прием `messages` без запуска phase-5: внутренняя история materialize-ится в prompt string для текущего `generate(...)` API.
- Добавлены тесты на изоляцию истории двух пользователей, сохранение `assistant` reply, новый запрос без истории и отсутствие записи при ошибке модели.
- Обновлены `phase-2-memory` в spec, roadmap и context dump.

## Not Done

- Не реализованы trimming и ограничение длины истории.
- Не реализован summarization workflow.
- `system prompt` не переведен в полноценный provider-facing `messages context`.
- Не добавлено полное логирование model context.
- Не добавлено persistent storage.
- Полный запуск `pytest` не выполнен, потому что модуль `pytest` отсутствует в текущем окружении.

## Decisions Made

- Память вынесена в отдельный модуль `app/memory/`, а не встроена в handler или service.
- Storage contract сразу сохранен совместимым с будущим summary workflow через методы `append_many`, `replace_after_summary` и `clear`.
- Telegram-specific объекты не попадают в memory layer; segregation выполняется только по `user_id`.
- Новый `user` message формируется в `ChatService`, а не в handler.
- В store запись происходит только после успешного ответа модели: сохраняется сразу консистентная пара `user`/`assistant`, без висячих пользовательских сообщений после ошибок Ollama.
- На текущей фазе история остается внутренним `messages` array, а на границе с Ollama временно преобразуется в prompt string.

## Deviations From Spec

- Существенных отклонений от spec нет.
- Вместо перехода на provider-facing `messages` API выполнена минимальная адаптация `OllamaClient` через рендеринг истории в prompt string. Это соответствует scope, потому что phase-5 еще не начата.
- Дополнительно обработан защитный case отсутствующего `from_user` в Telegram message, чтобы не допустить неявного смешивания истории.

## Risks / Follow-ups

- In-memory история теряется при рестарте процесса.
- Без trimming история будет расти без ограничений до `phase-3-context-limits`.
- Текущее текстовое materialization history в prompt string может потребовать корректировки при переходе на настоящий messages API провайдера.
- Если в следующей фазе trimming будет реализован без учета `summary`, можно нарушить уже зафиксированный storage contract.

## Inputs For Next Phase

- `phase-3-context-limits` должна работать поверх уже существующего `ConversationStore` и не переносить хранение обратно в сервис.
- Trim logic должен сохранять порядок сообщений и не удалять новый `user` message.
- Будущая materialization `system prompt` должна учитывать, что per-user history уже хранится отдельно от prompt.
- Тесты следующей фазы должны расширять текущие проверки изоляции истории, а не заменять их.

## Files Changed

- `app/memory/__init__.py`
- `app/memory/types.py`
- `app/memory/conversation_store.py`
- `app/services/chat_service.py`
- `app/bot/handlers/chat.py`
- `app/clients/ollama_client.py`
- `app/main.py`
- `tests/test_chat_service.py`
- `_docs/specs/phase-2-memory.yaml`
- `_docs/roadmap.yaml`
- `_docs/context-dump.md`

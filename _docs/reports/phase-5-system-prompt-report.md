# Phase Report: phase-5-system-prompt

Date: 2026-04-15
Spec: `_docs/specs/phase-5-system-prompt.yaml`
Status: done

## Done

- `ChatService` теперь собирает фактический runtime context как ordered `messages` array с первым `system` message.
- Контракт `OllamaClient` переведен с `prompt + system` на единый `messages` array.
- Вызов Ollama переведен на `chat(messages=...)`.
- Основной reply prompt и summarization prompt остались раздельными и используются в разных model contexts.
- Тесты `tests/test_chat_service.py` обновлены под новый контракт и дополняют проверки положения `system` message.
- Обновлены `_docs/context-dump.md`, `_docs/roadmap.yaml`, `_docs/specs/phase-5-system-prompt.yaml`, архитектурные документы.

## Not Done

- Не добавлялось полное observability логирование контекста: это вынесено в следующую фазу по spec.
- Не запускались полноценные `pytest`-тесты, потому что в текущем окружении отсутствует установленный `pytest`.

## Decisions Made

- Внутренний `system prompt` materialize-ится в `ChatService`, а не скрывается внутри клиента.
- Для provider-facing совместимости внутренняя роль `summary` адаптируется в `OllamaClient` к обычному user message с явным префиксом.
- Summarization workflow использует тот же client contract, что и обычный ответ, но со своим отдельным `system` prompt.

## Deviations From Spec

- Добавлен явный `system-3` task в roadmap для фиксации обновленного client contract, хотя в spec он уже был описан текстом.

## Risks / Follow-ups

- Нужно покрыть отдельно unit-тестами `OllamaClient`, включая адаптацию `summary` и обработку chat-response payload.
- Поведение materialized `summary` в Ollama зависит от модели; это стоит наблюдать в phase-6 observability.
- Prompt-файлы по-прежнему читаются с диска на каждый запрос.

## Inputs For Next Phase

- В `phase-6-observability` можно логировать уже финальный ordered `messages` context без скрытых prompt-каналов.
- Стоит логировать тип вызова: `reply` против `summary`.
- Для логов нужно отдельно учитывать внутренний `summary` и provider-facing materialized message.

## Files Changed

- `app/services/chat_service.py`
- `app/clients/ollama_client.py`
- `tests/test_chat_service.py`
- `_docs/context-dump.md`
- `_docs/architecture/components.md`
- `_docs/architecture/runtime-flows.md`
- `_docs/roadmap.yaml`
- `_docs/specs/phase-5-system-prompt.yaml`
- `_docs/reports/phase-5-system-prompt-report.md`

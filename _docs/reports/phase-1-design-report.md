# Phase Report: phase-1-design

Date: 2026-04-14
Spec: `_docs/specs/phase-1-design.yaml`
Status: done

## Done

- Зафиксирован единый внутренний runtime-контракт `messages` в формате `{role, content}`.
- Зафиксированы допустимые роли проекта: `system`, `user`, `assistant`, `summary`.
- Определено, что `system prompt` не хранится в per-user history и материализуется первым элементом фактического model context.
- Зафиксирован abstraction `ConversationStore` для per-user истории с минимальными операциями `read`, `append`, `append_many`, `replace_after_summary`, `clear`.
- Зафиксировано, что `summary` хранится в той же истории, что и обычные сообщения, но как отдельная внутренняя роль.
- Зафиксирована context policy: primary limit по числу сообщений, secondary safety limit по суммарной длине текста.
- Уточнены зоны ответственности будущих изменений для `app/services/`, `app/clients/`, `app/config.py`, `app/prompts/` и нового `app/memory/`.
- Обновлены `phase-1-design` в spec, roadmap и context dump.

## Not Done

- Не реализована runtime-память по пользователям.
- Не реализован trimming истории.
- Не реализован summarization workflow.
- `OllamaClient` не переведен на messages API.
- Не добавлено логирование полного model context.
- Код приложения и тесты не менялись.

## Decisions Made

- Внутренний source of truth для контекста модели: ordered `messages` array.
- `summary` остается внутренней runtime-ролью проекта, а provider-specific materialization откладывается на границу model client.
- `ConversationStore` выбран как минимальный storage contract для следующих фаз.
- Segregation key для истории: `user_id`.
- Ближайшая реализация памяти должна быть in-memory и жить в отдельном модуле `app/memory/`.
- Порог `summary_trigger_messages` зафиксирован как стартовый ориентир `5`, при этом он должен быть меньше `max_history_messages`.

## Deviations From Spec

- Существенных отклонений от spec не было.
- Вместо правок кода решения оформлены через ADR, потому что spec прямо допускает документальную фиксацию без feature-реализации.

## Risks / Follow-ups

- Внутренняя роль `summary` потребует аккуратной materialization при переходе на provider messages API.
- Если в `phase-2-memory` store будет реализован слишком узко, это усложнит `replace_after_summary` в `phase-4-summarization`.
- До `phase-3-context-limits` numeric thresholds остаются design guidance, а не runtime-конфигом.
- In-memory память в следующей фазе останется неперсистентной и будет теряться при рестарте процесса.

## Inputs For Next Phase

- `phase-2-memory` должна реализовать `ConversationStore` и изоляцию истории по `user_id`.
- Telegram handler должен передавать в сервис `user_id` и текст, не управляя историей напрямую.
- `ChatService` должен собирать history flow вокруг уже зафиксированного `messages` контракта.
- `system prompt` пока можно оставить вне store, но его место в фактическом context уже определено.
- Summary-aware операции уже заложены в storage contract, хотя сам summary workflow еще не реализуется.

## Files Changed

- `_docs/specs/phase-1-design.yaml`
- `_docs/roadmap.yaml`
- `_docs/context-dump.md`
- `_docs/architecture/components.md`
- `_docs/decisions/001-context-contract-and-memory.md`

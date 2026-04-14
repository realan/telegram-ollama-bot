# ADR 001: Messages Context, Memory Abstraction, Context Policy

## Status

Accepted

## Date

2026-04-14

## Context

После MVP проекту нужен единый контракт для model context, чтобы следующие фазы
про память, trimming, summarization, system prompt и observability не начали
по-разному трактовать историю диалога.

Сейчас:

- `ChatService` работает с одним новым пользовательским текстом
- `OllamaClient` вызывает `generate(prompt=..., system=...)`
- история сообщений отсутствует
- system prompt не существует как элемент общего runtime context

Нужно зафиксировать внутренний проектный контракт до перехода к реализации.

## Decision

### 1. Единый внутренний формат сообщений

Внутри приложения модельный контекст описывается как упорядоченный массив
сообщений:

```yaml
messages:
  - role: system | user | assistant | summary
    content: string
```

Инварианты:

- `messages` сохраняет хронологический порядок
- каждый элемент содержит только `role` и `content`
- `content` всегда является непустой строкой после нормализации
- проектный runtime-контракт допускает только роли `system`, `user`,
  `assistant`, `summary`

### 2. Положение system prompt

`system prompt` не хранится в per-user history store.

Он загружается отдельно и материализуется только при сборке фактического
контекста модели. В собранном контексте `system` всегда идет первым элементом.

Базовая форма:

```yaml
messages:
  - role: system
    content: <system prompt>
  - role: ...
    content: ...
```

### 3. Как summary сосуществует с обычной историей

`summary` является частью того же внутреннего `messages` контракта, что и обычная
история, но имеет отдельную семантику:

- `assistant` — реальный ответ модели пользователю в основном диалоге
- `summary` — сжатое представление старой части истории, созданное отдельным
  workflow

Решение:

- `summary` хранится в той же per-user истории, что и обычные сообщения
- в истории допускается не более одного актуального summary-сегмента
- summary представляет более старую часть диалога и должен идти перед свежими
  `user`/`assistant` сообщениями
- при обновлении summary store выполняет операцию замены старого префикса истории
  на новый summary-элемент

Иллюстрация stored history:

```yaml
messages:
  - role: summary
    content: <summary of older turns>
  - role: user
    content: <recent user message>
  - role: assistant
    content: <recent assistant message>
```

Важно:

- `summary` остается внутренней ролью проекта
- provider-facing клиент не должен принимать Telegram-специфичные объекты
- если внешний messages API не поддерживает роль `summary`, ее materialization
  выполняется на границе model client в provider-compatible роль без изменения
  внутреннего store-контракта

### 4. Memory abstraction

Для хранения истории вводится отдельный abstraction:

`ConversationStore`

Минимальный целевой интерфейс для следующих фаз:

```python
class ConversationStore(Protocol):
    async def read(self, user_id: int) -> list[Message]: ...
    async def append(self, user_id: int, message: Message) -> None: ...
    async def append_many(self, user_id: int, messages: list[Message]) -> None: ...
    async def replace_after_summary(
        self,
        user_id: int,
        summary_message: Message,
        tail_messages: list[Message],
    ) -> None: ...
    async def clear(self, user_id: int) -> None: ...
```

Правила:

- сегрегация истории определяется только по внутреннему `user_id`
- store ничего не знает о Telegram update/message objects
- store отвечает только за хранение и замену истории
- решение о том, какие сообщения войдут в фактический context модели, остается в
  сервисном слое

Для ближайшей реализации базовым вариантом считается in-memory store в новом
модуле `app/memory/`.

### 5. Context policy

Основная стратегия ограничения контекста:

1. primary limit: по количеству сообщений
2. secondary safety limit: по суммарной длине `content`

Инварианты policy:

- новый `user` message нельзя удалять
- `system` всегда должен быть первым в фактическом model context
- если актуальный `summary` существует, его нельзя терять раньше свежего хвоста
- порядок оставшихся сообщений после trim сохраняется
- trimming работает с history segment и не меняет source system prompt

Зафиксированные ориентиры для следующих фаз:

- `summary_trigger_messages` должен быть меньше `max_history_messages`
- `summary_trigger_messages` можно стартово принять равным `5`
- `max_history_messages` и `max_context_chars` должны стать конфигурируемыми в
  phase-3
- если лимит по сообщениям еще не достигнут, но превышен safety limit по длине,
  разрешен дополнительный trim старого префикса истории

### 6. Responsibility split for next phases

Следующее расширение модулей должно выглядеть так:

- `app/bot/handlers/chat.py`
  Принимает `user_id` и текст, но не управляет историей напрямую.
- `app/services/chat_service.py`
  Собирает runtime context, вызывает store, применяет context policy.
- `app/memory/`
  Новый пакет для `ConversationStore` и in-memory реализации.
- `app/clients/ollama_client.py`
  На phase-5 получает уже собранный messages context и адаптирует его под
  provider API.
- `app/config.py`
  На phase-3 вводит настройки лимитов.
- `app/prompts/`
  На phase-4 получает отдельный summarization prompt.

## Consequences

Плюсы:

- `ChatService`, memory layer и model client получают явные границы
- summary и observability строятся на одном и том же внутреннем формате
- system prompt перестает быть скрытым параметром и становится частью
  материализованного model context

Минусы и ограничения:

- внутренняя роль `summary` потребует явной materialization на provider boundary
- in-memory store останется временным решением и не переживет рестарт процесса
- точные numeric thresholds пока фиксируются как design guidance, а не как
  реализованная конфигурация

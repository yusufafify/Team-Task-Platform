# Apps

Rule: one app per domain; business logic in `services.py`.

- `accounts`: the email-login user.
- `teams`: teams and membership, with the role on the membership.
- `tasks`: tasks and their comments.
- `chat`: team messages.
- `notifications`: in-app notifications and Expo device tokens.
- `ai`: the LLM provider, rate limits and call log.
- `assistant`: the chatbot: its private threads, snapshot, tools and answer cache.

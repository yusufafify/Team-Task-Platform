# Apps

Rule: one app per domain; business logic in `services.py`.

- `accounts`: the email-login user.
- `teams`: teams and membership, with the role on the membership.
- `tasks`: tasks and their comments.
- `chat`: team messages.
- `notifications`: in-app notifications, Expo device tokens and the live socket.
- `ai`: the LLM provider, rate limits and call log.
- `assistant`: the chatbot: its private threads, snapshot, tools, answer cache and search.

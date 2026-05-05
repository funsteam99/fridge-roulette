# TODO

## Reliability and AI Response Stability

- Add recipe schema validation for required fields:
  - `dish_name`
  - `ingredients_needed`
  - `steps`
  - `chef_secret`
- Normalize incomplete AI responses instead of failing silently.
- Improve user-facing API error messages:
  - invalid API key
  - unsupported model name
  - quota or billing issue
  - temporary API/network failure
  - malformed AI JSON response
- Retry once when the model returns malformed JSON.
- Add focused tests for:
  - culinary intent filtering
  - prompt injection blocking
  - AI response cleanup
  - incomplete recipe handling

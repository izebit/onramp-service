# authorization

Shared JWT authorization module for services in this repo. Validates `Authorization: Bearer <token>` and returns the payload when it contains `client_ref` (string) and `expiration_at` (Unix timestamp). Uses `SECRET_KEY` and `AUTHENTICATION_DISABLED` from the environment.

## Usage

In a service (onramp, webhook):

```python
from authorization import get_jwt_payload, JWT_ALGORITHM

# In a FastAPI router:
jwt_payload: dict = Depends(get_jwt_payload)
```

Ensure the service sets `SECRET_KEY` and `AUTHENTICATION_DISABLED` (e.g. in `.env` or app config).

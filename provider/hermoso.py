from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from hermoso_client import HermosoClient, HermosoError


class HermosoProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        """One free, read-only call: GET /v1/credits. It answers 401 for a bad key and spends nothing."""
        try:
            HermosoClient.from_credentials(credentials).credits()
        except HermosoError as err:
            raise ToolProviderCredentialValidationError(str(err)) from None
        except Exception as err:  # noqa: BLE001
            raise ToolProviderCredentialValidationError(
                f"Could not validate the Hermoso API key ({type(err).__name__})."
            ) from None

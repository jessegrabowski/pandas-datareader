from pandas import DataFrame

from pandas_datareader._utils import RemoteDataError
from pandas_datareader.base import _BaseReader
from pandas_datareader.yahoo.headers import DEFAULT_HEADERS

_DEFAULT_PARAMS = {
    "lang": "en-US",
    "corsDomain": "finance.yahoo.com",
    ".tsrc": "finance",
}
_CRUMB_URL = "https://query1.finance.yahoo.com/v1/test/getcrumb"
_COOKIE_URL = "https://fc.yahoo.com"


class YahooQuotesReader(_BaseReader):
    """Get current Yahoo Finance quote for one or more symbols."""

    def __init__(
        self,
        symbols: str | list[str] | None = None,
        start=None,
        end=None,
        retry_count: int = 3,
        pause: float = 0.1,
        session=None,
    ) -> None:
        super().__init__(
            symbols=symbols,
            start=start,
            end=end,
            retry_count=retry_count,
            pause=pause,
            session=session,
        )
        self.headers = session.headers if session is not None else DEFAULT_HEADERS

    @property
    def url(self) -> str:
        """API URL."""
        return "https://query1.finance.yahoo.com/v7/finance/quote"

    def read(self) -> DataFrame:
        """Read quotes for one or more symbols.

        Returns
        -------
        df : DataFrame
            One row per symbol, indexed by ticker.
        """
        symbols = [self.symbols] if isinstance(self.symbols, str) else list(self.symbols)
        params = {"symbols": ",".join(symbols), "crumb": self._get_crumb(), **_DEFAULT_PARAMS}
        results = self._get_response(self.url, params=params, headers=self.headers).json()
        results = results["quoteResponse"]["result"]
        if not results:
            raise RemoteDataError(f"No quotes fetched for {symbols}")

        df = DataFrame(results).set_index("symbol")
        df["price"] = df["regularMarketPrice"]
        return df

    def _get_crumb(self, *args) -> str:
        """Prime the session cookie and return a Yahoo API crumb.

        The v7 quote endpoint rejects requests without a cookie/crumb pair. Fetch a cookie from
        Yahoo, then exchange it for a crumb that authorizes the quote request.
        """
        self.session.get(_COOKIE_URL, headers=self.headers, timeout=self.timeout)
        return self.session.get(_CRUMB_URL, headers=self.headers, timeout=self.timeout).text

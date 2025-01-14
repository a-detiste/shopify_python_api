import re
import sys


class ApiAccessError(Exception):
    pass


class ApiAccess:

    SCOPE_DELIMITER = ","
    SCOPE_RE = re.compile(r"\A(?P<unauthenticated>unauthenticated_)?(write|read)_(?P<resource>.*)\Z")
    IMPLIED_SCOPE_RE = re.compile(r"\A(?P<unauthenticated>unauthenticated_)?write_(?P<resource>.*)\Z")

    def __init__(self, scopes):
        if isinstance(scopes, str):
            scopes = scopes.split(self.SCOPE_DELIMITER)

        self.__store_scopes(scopes)

    def covers(self, api_access):
        return api_access._compressed_scopes <= self._expanded_scopes

    def __str__(self):
        return self.SCOPE_DELIMITER.join(self._compressed_scopes)

    def __iter__(self):
        return iter(self._compressed_scopes)

    def __eq__(self, other):
        return type(self) == type(other) and self._compressed_scopes == other._compressed_scopes

    def __store_scopes(self, scopes):
        sanitized_scopes = frozenset(filter(None, [scope.strip() for scope in scopes]))
        self.__validate_scopes(sanitized_scopes)
        implied_scopes = frozenset(self.__implied_scope(scope) for scope in sanitized_scopes)
        self._compressed_scopes = sanitized_scopes - implied_scopes
        self._expanded_scopes = sanitized_scopes.union(implied_scopes)

    def __validate_scopes(self, scopes):
        for scope in scopes:
            if not self.SCOPE_RE.match(scope):
                error_message = "'{s}' is not a valid access scope".format(s=scope)
                raise ApiAccessError(error_message)

    def __implied_scope(self, scope):
        match = self.IMPLIED_SCOPE_RE.match(scope)
        if match:
            return "{unauthenticated}read_{resource}".format(
                unauthenticated=match.group("unauthenticated") or "",
                resource=match.group("resource"),
            )

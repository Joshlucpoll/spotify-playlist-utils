import requests
from spotipy.oauth2 import SpotifyOAuth, SpotifyOauthError


class ModifiedSpotifyAuth(SpotifyOAuth):
    def __init__(
            self, client_id=None, client_secret=None, redirect_uri=None,
            state=None, scope=None, cache_path=None, username=None,
            proxies=None, show_dialog=False, requests_session=True,
            requests_timeout=None, open_browser=True, cache_handler=None):
        super().__init__(client_id, client_secret, redirect_uri, state, scope,
                         cache_path, username, proxies, show_dialog, requests_session,
                         requests_timeout, open_browser, cache_handler)

    def get_access_token(self, code=None, as_dict=True, check_cache=True):
        """ Gets the access token for the app given the code

            Parameters:
                - code - the response code
                - as_dict - a boolean indicating if returning the access token
                            as a token_info dictionary, otherwise it will be returned
                            as a string.
        """
        if check_cache:
            token_info = self.validate_token(
                self.cache_handler.get_cached_token())
            if token_info is not None:
                if self.is_token_expired(token_info):
                    token_info = self.refresh_access_token(
                        token_info["refresh_token"]
                    )
                return token_info if as_dict else token_info["access_token"]

        if not code:
            raise SpotifyOauthError('No access code provided')

        payload = {
            "redirect_uri": self.redirect_uri,
            "code": code,
            "grant_type": "authorization_code",
        }
        if self.scope:
            payload["scope"] = self.scope
        if self.state:
            payload["state"] = self.state

        headers = self._make_authorization_headers()

        try:
            response = self._session.post(
                self.OAUTH_TOKEN_URL,
                data=payload,
                headers=headers,
                verify=True,
                proxies=self.proxies,
                timeout=self.requests_timeout,
            )
            response.raise_for_status()
            token_info = response.json()
            token_info = self._add_custom_values_to_token_info(token_info)
            self.cache_handler.save_token_to_cache(token_info)
            return token_info if as_dict else token_info["access_token"]
        except requests.exceptions.HTTPError as http_error:
            response = http_error.response
            try:
                error_payload = response.json()
                error = error_payload.get('error')
                error_description = error_payload.get('error_description')
            except ValueError:
                # if the response cannnot be decoded into JSON (which raises a ValueError),
                # then try do decode it into text

                # if we receive an empty string (which is falsy), then replace it with `None`
                error = response.txt or None
                error_description = None

            raise SpotifyOauthError(
                'error: {0}, error_description: {1}'.format(
                    error, error_description
                ),
                error=error,
                error_description=error_description
            )

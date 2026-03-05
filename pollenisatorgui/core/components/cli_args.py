"""Centralized CLI argument parsing for Pollenisator command-line tools.

Provides --url and --key arguments shared across pollup, pollex,
pollterminal, pollwatch and pollworker.

Typical usage in an entry-point function::

    from pollenisatorgui.core.components.cli_args import build_common_parser, apply_common_args

    parser = build_common_parser(description='My tool')
    # add tool-specific arguments here …
    args = parser.parse_args()
    apply_common_args(args)   # sets up connection; exits on failure
"""

import argparse
import sys
import urllib.parse


def build_common_parser(**kwargs):
    """Return an :class:`argparse.ArgumentParser` pre-loaded with ``--url`` and ``--key``.

    Any keyword argument accepted by :class:`argparse.ArgumentParser`
    (e.g. *description*, *add_help*) can be forwarded via ``**kwargs``.

    The returned parser can be used directly or passed as an element of
    the *parents* list when building a more specific parser.
    """
    parser = argparse.ArgumentParser(**kwargs)
    parser.add_argument(
        '--url',
        metavar='URL',
        default=None,
        help=(
            'Server base URL, e.g. https://myserver or http://myserver:8080. '
            'Bypasses the interactive host/port/https prompts. '
            'Port defaults to 443 for https and 80 for http when omitted.'
        ),
    )
    parser.add_argument(
        '--key',
        metavar='API_KEY',
        default=None,
        help=(
            'API key for non-interactive authentication. '
            'Bypasses the login and pentest-selection prompts entirely. '
            'The pentest scope is inferred server-side from the key.'
        ),
    )
    return parser


def apply_common_args(args):
    """Apply ``--url`` / ``--key`` parsed arguments to the shared APIClient.

    Must be called after the first :meth:`APIClient.getInstance` call so
    that the singleton already exists.

    * If ``--url`` is given, the client configuration file is updated with
      the parsed host / port / https values so that the next
      :meth:`APIClient.tryConnection` call uses the supplied server address.
    * If ``--key`` is given, :meth:`APIClient.loginWithApiKey` is called
      immediately.  The process exits with a non-zero status on failure.

    Returns ``True`` if authentication was completed via ``--key`` (no
    further interactive prompts needed), ``False`` otherwise.
    """
    import pollenisatorgui.core.components.utils as utils
    from pollenisatorgui.core.components.apiclient import APIClient

    apiclient = APIClient.getInstance()

    if args.url:
        raw = args.url.strip()
        # Prepend a scheme when the user typed a bare hostname / IP
        if not raw.startswith('http://') and not raw.startswith('https://'):
            raw = 'https://' + raw
        parsed = urllib.parse.urlparse(raw)
        scheme = parsed.scheme          # 'http' or 'https'
        host = parsed.hostname
        port = parsed.port
        if port is None:
            port = 443 if scheme == 'https' else 80
        cfg = utils.loadClientConfig()
        cfg['host'] = host
        cfg['port'] = port
        cfg['https'] = (scheme == 'https')
        utils.saveClientConfig(cfg)

    if args.key:
        # force=True skips restoring the old api_key / JWT from client.cfg,
        # so the explicit --key value is always the one that gets applied.
        if not apiclient.tryConnection(force=True):
            print('ERROR: Could not reach the server. '
                  'Check --url or the saved configuration.')
            sys.exit(1)
        if not apiclient.loginWithApiKey(args.key):
            print('ERROR: API key authentication failed.')
            sys.exit(1)
        return True

    return False

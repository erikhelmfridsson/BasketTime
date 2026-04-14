import json
import os
import urllib.error
import urllib.parse
import urllib.request


class ProfixioError(Exception):
    pass


def _base_url():
    return os.environ.get("PROFIXIO_BASE_URL", "https://www.profixio.com/app").rstrip("/")


def _api_secret():
    secret = os.environ.get("PROFIXIO_API_SECRET", "").strip()
    if not secret:
        raise ProfixioError("PROFIXIO_API_SECRET is not set")
    return secret


def _request_json(path, params=None):
    base = _base_url()
    url = base + path
    if params:
        qs = urllib.parse.urlencode(params)
        url = url + ("&" if "?" in url else "?") + qs
    req = urllib.request.Request(url, method="GET")
    req.add_header("X-Api-Secret", _api_secret())
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8")
        except Exception:
            pass
        raise ProfixioError(f"HTTP {e.code} from Profixio: {body[:500]}")
    except Exception as e:
        raise ProfixioError(str(e))


def get_userinfo():
    return _request_json("/api/userinfo")


def list_organisation_tournaments(organisation_id, page=1, limit=500):
    return _request_json(f"/api/organisations/{urllib.parse.quote(str(organisation_id))}/tournaments", {"page": page, "limit": limit})


def list_tournament_teams(tournament_id, page=1, limit=500, player_list=False):
    params = {"page": page, "limit": limit}
    if player_list:
        params["playerList"] = 1
    return _request_json(f"/api/tournaments/{int(tournament_id)}/teams", params)


def list_tournament_matches(tournament_id, page=1, limit=500):
    return _request_json(f"/api/tournaments/{int(tournament_id)}/matches", {"page": page, "limit": limit})


def _paginate(fetch_page_fn):
    page = 1
    out = []
    while True:
        payload = fetch_page_fn(page)
        if isinstance(payload, dict) and "data" in payload and "meta" in payload:
            out.extend(payload.get("data") or [])
            meta = payload.get("meta") or {}
            last_page = int(meta.get("last_page") or page)
            if page >= last_page:
                break
            page += 1
            continue
        # Non-paginated fallback
        if isinstance(payload, dict) and "data" in payload:
            out.extend(payload.get("data") or [])
        elif isinstance(payload, list):
            out.extend(payload)
        break
    return out


def fetch_all_organisation_tournaments(organisation_id):
    return _paginate(lambda page: list_organisation_tournaments(organisation_id, page=page))


def fetch_all_tournament_teams(tournament_id, player_list=False):
    return _paginate(lambda page: list_tournament_teams(tournament_id, page=page, player_list=player_list))


def fetch_all_tournament_matches(tournament_id):
    return _paginate(lambda page: list_tournament_matches(tournament_id, page=page))


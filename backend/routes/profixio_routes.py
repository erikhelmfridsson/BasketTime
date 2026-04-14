import json
import logging
import sys
from datetime import datetime

from flask import Blueprint, request
from sqlalchemy import or_

from backend.auth import get_current_user, login_required
from backend.models import (
    ProfixioMatch,
    ProfixioPlayer,
    ProfixioTeam,
    ProfixioTournament,
    UserProfixioPlayerLink,
    UserProfixioTeamLink,
    db,
)
from backend.profixio_client import (
    ProfixioError,
    fetch_all_organisation_tournaments,
    fetch_all_tournament_matches,
    fetch_all_tournament_teams,
    get_userinfo,
)

bp = Blueprint("profixio", __name__, url_prefix="/api/profixio")

logger = logging.getLogger("baskettime.profixio")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s in %(name)s: %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


def _now():
    return datetime.utcnow()


@bp.route("/userinfo", methods=["GET"])
@login_required
def profixio_userinfo():
    try:
        return get_userinfo()
    except ProfixioError as e:
        return {"error": str(e)}, 502


@bp.route("/tournaments", methods=["GET"])
@login_required
def profixio_list_tournaments():
    organisation_id = (request.args.get("organisationId") or "").strip()
    if not organisation_id:
        return {"error": "organisationId required"}, 400
    try:
        tournaments = fetch_all_organisation_tournaments(organisation_id)
    except ProfixioError as e:
        return {"error": str(e)}, 502
    # Cache minimal tournament info
    now = _now()
    for item in tournaments:
        try:
            tid = int(item.get("id"))
        except Exception:
            continue
        name = item.get("name") or item.get("title") or ""
        raw = json.dumps(item, ensure_ascii=False)
        existing = db.session.get(ProfixioTournament, tid)
        if existing:
            existing.organisation_id = organisation_id
            existing.name = name
            existing.raw_json = raw
            existing.updated_at = now
        else:
            db.session.add(ProfixioTournament(id=tid, organisation_id=organisation_id, name=name, raw_json=raw, updated_at=now))
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
    return {"tournaments": tournaments}


@bp.route("/sync", methods=["POST"])
@login_required
def profixio_sync():
    data = request.get_json() or {}
    organisation_id = (data.get("organisationId") or "").strip()
    tournament_id = data.get("tournamentId")
    if tournament_id is None:
        return {"error": "tournamentId required"}, 400
    try:
        tournament_id_int = int(tournament_id)
    except Exception:
        return {"error": "tournamentId must be integer"}, 400

    now = _now()
    # Teams (try with playerList=1 first; if not permitted, fallback to without)
    teams = []
    used_player_list = False
    try:
        teams = fetch_all_tournament_teams(tournament_id_int, player_list=True)
        used_player_list = True
    except ProfixioError:
        teams = fetch_all_tournament_teams(tournament_id_int, player_list=False)

    matches = fetch_all_tournament_matches(tournament_id_int)

    # Cache tournaments if org provided
    if organisation_id:
        existing_tour = db.session.get(ProfixioTournament, tournament_id_int)
        if existing_tour:
            existing_tour.organisation_id = organisation_id
            existing_tour.updated_at = now

    # Upsert teams and players (if available in payload)
    players_count = 0
    for team in teams:
        try:
            team_id = int(team.get("id"))
        except Exception:
            continue
        team_name = team.get("name") or ""
        club_name = ""
        club = team.get("club") or {}
        if isinstance(club, dict):
            club_name = club.get("name") or ""
        raw_team = json.dumps(team, ensure_ascii=False)
        existing_team = ProfixioTeam.query.filter_by(id=team_id, tournament_id=tournament_id_int).first()
        if existing_team:
            existing_team.name = team_name
            existing_team.club_name = club_name
            existing_team.raw_json = raw_team
            existing_team.updated_at = now
        else:
            db.session.add(ProfixioTeam(id=team_id, tournament_id=tournament_id_int, name=team_name, club_name=club_name, raw_json=raw_team, updated_at=now))

        # Players can be present when playerList=1
        player_list = team.get("playerList") or team.get("players") or []
        if isinstance(player_list, list):
            for p in player_list:
                if not isinstance(p, dict):
                    continue
                pid = p.get("id")
                if pid is None:
                    continue
                try:
                    pid_int = int(pid)
                except Exception:
                    continue
                pname = p.get("name") or ""
                jersey = p.get("jerseyNumber")
                birth = p.get("birthDate")
                raw_player = json.dumps(p, ensure_ascii=False)
                existing_player = ProfixioPlayer.query.filter_by(id=pid_int, tournament_id=tournament_id_int).first()
                if existing_player:
                    existing_player.team_id = team_id
                    existing_player.name = pname
                    existing_player.jersey_number = str(jersey) if jersey is not None else None
                    existing_player.birth_date = str(birth) if birth is not None else None
                    existing_player.raw_json = raw_player
                    existing_player.updated_at = now
                else:
                    db.session.add(ProfixioPlayer(
                        id=pid_int,
                        tournament_id=tournament_id_int,
                        team_id=team_id,
                        name=pname,
                        jersey_number=str(jersey) if jersey is not None else None,
                        birth_date=str(birth) if birth is not None else None,
                        raw_json=raw_player,
                        updated_at=now,
                    ))
                players_count += 1

    matches_count = 0
    for m in matches:
        if not isinstance(m, dict):
            continue
        mid = m.get("id")
        if mid is None:
            continue
        try:
            mid_int = int(mid)
        except Exception:
            continue
        start_time = m.get("startTime") or m.get("start_time") or m.get("time") or ""
        ht = m.get("homeTeam") or {}
        at = m.get("awayTeam") or {}
        home_team_id = None
        away_team_id = None
        if isinstance(ht, dict) and ht.get("id") is not None:
            try:
                home_team_id = int(ht.get("id"))
            except Exception:
                home_team_id = None
        if isinstance(at, dict) and at.get("id") is not None:
            try:
                away_team_id = int(at.get("id"))
            except Exception:
                away_team_id = None
        raw_match = json.dumps(m, ensure_ascii=False)
        existing_match = ProfixioMatch.query.filter_by(id=mid_int, tournament_id=tournament_id_int).first()
        if existing_match:
            existing_match.start_time = str(start_time) if start_time else None
            existing_match.home_team_id = home_team_id
            existing_match.away_team_id = away_team_id
            existing_match.raw_json = raw_match
            existing_match.updated_at = now
        else:
            db.session.add(ProfixioMatch(
                id=mid_int,
                tournament_id=tournament_id_int,
                start_time=str(start_time) if start_time else None,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                raw_json=raw_match,
                updated_at=now,
            ))
        matches_count += 1

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception("Failed to cache profixio sync tournament_id=%s", tournament_id_int)
        return {"error": "Could not store profixio data"}, 500

    return {
        "ok": True,
        "tournamentId": tournament_id_int,
        "teams": len(teams),
        "matches": matches_count,
        "players": players_count,
        "usedPlayerList": used_player_list,
    }


@bp.route("/search", methods=["GET"])
@login_required
def profixio_search():
    kind = (request.args.get("kind") or "").strip().lower()
    query = (request.args.get("q") or "").strip()
    tournament_id = request.args.get("tournamentId")
    limit = int(request.args.get("limit") or 50)
    limit = max(1, min(200, limit))
    tournament_id_int = None
    if tournament_id:
        try:
            tournament_id_int = int(tournament_id)
        except Exception:
            tournament_id_int = None

    if kind not in ("teams", "players", "matches"):
        return {"error": "kind must be teams|players|matches"}, 400

    if kind == "teams":
        q = ProfixioTeam.query
        if tournament_id_int is not None:
            q = q.filter_by(tournament_id=tournament_id_int)
        if query:
            like = f"%{query}%"
            q = q.filter(or_(ProfixioTeam.name.ilike(like), ProfixioTeam.club_name.ilike(like)))
        rows = q.order_by(ProfixioTeam.updated_at.desc()).limit(limit).all()
        return {"teams": [{"id": r.id, "tournamentId": r.tournament_id, "name": r.name or "", "clubName": r.club_name or ""} for r in rows]}

    if kind == "players":
        q = ProfixioPlayer.query
        if tournament_id_int is not None:
            q = q.filter_by(tournament_id=tournament_id_int)
        if query:
            like = f"%{query}%"
            q = q.filter(ProfixioPlayer.name.ilike(like))
        rows = q.order_by(ProfixioPlayer.updated_at.desc()).limit(limit).all()
        return {"players": [{"id": r.id, "tournamentId": r.tournament_id, "teamId": r.team_id, "name": r.name or "", "jerseyNumber": r.jersey_number or ""} for r in rows]}

    # matches
    q = ProfixioMatch.query
    if tournament_id_int is not None:
        q = q.filter_by(tournament_id=tournament_id_int)
    if query:
        like = f"%{query}%"
        q = q.filter(ProfixioMatch.raw_json.ilike(like))
    rows = q.order_by(ProfixioMatch.updated_at.desc()).limit(limit).all()
    return {"matches": [{"id": r.id, "tournamentId": r.tournament_id, "startTime": r.start_time or "", "homeTeamId": r.home_team_id, "awayTeamId": r.away_team_id} for r in rows]}


@bp.route("/links", methods=["GET"])
@login_required
def profixio_links():
    user = get_current_user()
    team_links = UserProfixioTeamLink.query.filter_by(user_id=user.id).all()
    player_links = UserProfixioPlayerLink.query.filter_by(user_id=user.id).all()
    return {
        "teamLinks": [{"localTeamId": x.local_team_id, "profixioTeamId": x.profixio_team_id, "tournamentId": x.tournament_id} for x in team_links],
        "playerLinks": [{"localTeamId": x.local_team_id, "localPlayerId": x.local_player_id, "profixioPlayerId": x.profixio_player_id, "tournamentId": x.tournament_id} for x in player_links],
    }


@bp.route("/link/team", methods=["POST"])
@login_required
def profixio_link_team():
    user = get_current_user()
    data = request.get_json() or {}
    local_team_id = (data.get("localTeamId") or "").strip()
    profixio_team_id = data.get("profixioTeamId")
    tournament_id = data.get("tournamentId")
    if not local_team_id or profixio_team_id is None or tournament_id is None:
        return {"error": "localTeamId, profixioTeamId, tournamentId required"}, 400
    try:
        profixio_team_id_int = int(profixio_team_id)
        tournament_id_int = int(tournament_id)
    except Exception:
        return {"error": "profixioTeamId and tournamentId must be integer"}, 400
    existing = UserProfixioTeamLink.query.filter_by(user_id=user.id, local_team_id=local_team_id).first()
    if existing:
        existing.profixio_team_id = profixio_team_id_int
        existing.tournament_id = tournament_id_int
    else:
        db.session.add(UserProfixioTeamLink(user_id=user.id, local_team_id=local_team_id, profixio_team_id=profixio_team_id_int, tournament_id=tournament_id_int))
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return {"error": "Could not save link"}, 500
    return {"ok": True}


@bp.route("/link/player", methods=["POST"])
@login_required
def profixio_link_player():
    user = get_current_user()
    data = request.get_json() or {}
    local_team_id = (data.get("localTeamId") or "").strip()
    local_player_id = (data.get("localPlayerId") or "").strip()
    profixio_player_id = data.get("profixioPlayerId")
    tournament_id = data.get("tournamentId")
    if not local_team_id or not local_player_id or profixio_player_id is None or tournament_id is None:
        return {"error": "localTeamId, localPlayerId, profixioPlayerId, tournamentId required"}, 400
    try:
        profixio_player_id_int = int(profixio_player_id)
        tournament_id_int = int(tournament_id)
    except Exception:
        return {"error": "profixioPlayerId and tournamentId must be integer"}, 400
    existing = UserProfixioPlayerLink.query.filter_by(user_id=user.id, local_team_id=local_team_id, local_player_id=local_player_id).first()
    if existing:
        existing.profixio_player_id = profixio_player_id_int
        existing.tournament_id = tournament_id_int
    else:
        db.session.add(UserProfixioPlayerLink(
            user_id=user.id,
            local_team_id=local_team_id,
            local_player_id=local_player_id,
            profixio_player_id=profixio_player_id_int,
            tournament_id=tournament_id_int,
        ))
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return {"error": "Could not save link"}, 500
    return {"ok": True}


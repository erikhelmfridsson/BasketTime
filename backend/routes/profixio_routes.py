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
  ProfixioSyncConfig,
  ProfixioSyncState,
    UserProfixioPlayerLink,
    UserProfixioTeamLink,
    db,
)
from backend.profixio_client import (
    ProfixioError,
    fetch_all_organisation_tournaments,
    get_userinfo,
)
from backend.profixio_sync import sync_tournament

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

    try:
        result = sync_tournament(tournament_id_int, organisation_id=organisation_id or None)
        db.session.commit()
        return result
    except ProfixioError as e:
        db.session.rollback()
        return {"error": str(e)}, 502
    except Exception:
        db.session.rollback()
        logger.exception("Failed to cache profixio sync tournament_id=%s", tournament_id_int)
        return {"error": "Could not store profixio data"}, 500


@bp.route("/admin/config", methods=["GET", "POST", "DELETE"])
@login_required
def profixio_admin_config():
    # Admin-skydd görs här för att inte låsa ute vanliga användare från sök/sync.
    from backend.auth import admin_required

    @admin_required
    def _handle():
        if request.method == "GET":
            rows = ProfixioSyncConfig.query.order_by(ProfixioSyncConfig.updated_at.desc()).all()
            return {
                "configs": [
                    {
                        "id": r.id,
                        "tournamentId": r.tournament_id,
                        "organisationId": r.organisation_id or "",
                        "enabled": bool(r.enabled),
                        "updatedAt": r.updated_at.isoformat() if r.updated_at else "",
                    }
                    for r in rows
                ]
            }

        if request.method == "POST":
            data = request.get_json() or {}
            tournament_id = data.get("tournamentId")
            organisation_id = (data.get("organisationId") or "").strip() or None
            enabled = data.get("enabled")
            if tournament_id is None:
                return {"error": "tournamentId required"}, 400
            try:
                tid = int(tournament_id)
            except Exception:
                return {"error": "tournamentId must be integer"}, 400
            row = ProfixioSyncConfig.query.filter_by(tournament_id=tid).first()
            now = _now()
            if row:
                row.organisation_id = organisation_id
                if enabled is not None:
                    row.enabled = 1 if bool(enabled) else 0
                row.updated_at = now
            else:
                row = ProfixioSyncConfig(
                    tournament_id=tid,
                    organisation_id=organisation_id,
                    enabled=1 if (enabled is None or bool(enabled)) else 0,
                    updated_at=now,
                )
                db.session.add(row)
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                return {"error": "Could not save config"}, 500
            return {"ok": True}

        # DELETE
        cfg_id = request.args.get("id")
        if not cfg_id:
            return {"error": "id required"}, 400
        try:
            cfg_id_int = int(cfg_id)
        except Exception:
            return {"error": "id must be integer"}, 400
        row = db.session.get(ProfixioSyncConfig, cfg_id_int)
        if not row:
            return {"ok": True}
        db.session.delete(row)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            return {"error": "Could not delete config"}, 500
        return {"ok": True}

    return _handle()


@bp.route("/admin/run-now", methods=["POST"])
@login_required
def profixio_admin_run_now():
    from backend.auth import admin_required

    @admin_required
    def _handle():
        data = request.get_json() or {}
        tournament_id = data.get("tournamentId")
        organisation_id = (data.get("organisationId") or "").strip() or None
        if tournament_id is None:
            return {"error": "tournamentId required"}, 400
        try:
            tid = int(tournament_id)
        except Exception:
            return {"error": "tournamentId must be integer"}, 400
        try:
            result = sync_tournament(tid, organisation_id=organisation_id)
            db.session.commit()
            return result
        except ProfixioError as e:
            db.session.rollback()
            return {"error": str(e)}, 502
        except Exception:
            db.session.rollback()
            logger.exception("Admin run-now failed tournament_id=%s", tid)
            return {"error": "Could not store profixio data"}, 500

    return _handle()


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


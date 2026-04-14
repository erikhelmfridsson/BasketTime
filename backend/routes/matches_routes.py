"""
Matches API: list, create (save/update), get, delete.

All historik (matchlista) och statistik i frontend baseras på dessa
matcher, så om något går fel här loggar vi tydligt till stderr.
"""
import logging
import sys

from flask import Blueprint, request

from backend.auth import get_current_user, login_required
from backend.models import Match, MatchPlayer, db

bp = Blueprint("matches", __name__, url_prefix="/api/matches")

logger = logging.getLogger("baskettime.matches")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(name)s: %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


def _match_to_response(m):
    return {
        "id": m.id,
        "name": m.name,
        "dateISO": m.date_iso,
        "matchSeconds": m.match_seconds,
        "teamId": m.team_id or "",
        "teamNameAtTime": m.team_name_at_time or "",
        "players": [
            {
                "playerId": p.player_id,
                "playerNameAtTime": p.player_name_at_time,
                "secondsOnCourt": p.seconds_on_court,
                "assists": p.assists,
                "fouls": p.fouls,
                "goals": p.goals,
                "shots": getattr(p, "shots", 0),
                "madeShots": getattr(p, "made_shots", 0),
            }
            for p in sorted(m.players, key=lambda x: x.ord)
        ],
    }


@bp.route("", methods=["GET"])
@login_required
def list_matches():
    user = get_current_user()
    try:
        matches = (
            Match.query.filter_by(user_id=user.id)
            .order_by(Match.created_at.desc())
            .all()
        )
        logger.info("Loaded %s matches for user_id=%s", len(matches), user.id)
    except Exception:
        logger.exception("Failed to list matches for user_id=%s", user.id)
        return {"error": "Could not load matches"}, 500
    return {"matches": [_match_to_response(m) for m in matches]}


@bp.route("", methods=["POST"])
@login_required
def save_match():
    user = get_current_user()
    data = request.get_json() or {}
    match_id = (data.get("id") or "").strip()
    if not match_id:
        return {"error": "Match id required"}, 400
    name = (data.get("name") or "").strip() or "Match"
    date_iso = data.get("dateISO") or data.get("date_iso") or ""
    match_seconds = int(data.get("matchSeconds") or data.get("match_seconds") or 0)
    team_id = data.get("teamId") or data.get("team_id") or ""
    team_name_at_time = data.get("teamNameAtTime") or data.get("team_name_at_time") or ""
    players_data = data.get("players") or []

    logger.info(
        "Saving match id=%s for user_id=%s name=%r date_iso=%r players=%d",
        match_id,
        user.id,
        name,
        date_iso,
        len(players_data),
    )

    try:
        match = Match.query.filter_by(id=match_id, user_id=user.id).first()
        if match:
            match.name = name
            match.date_iso = date_iso
            match.match_seconds = match_seconds
            match.team_id = team_id
            match.team_name_at_time = team_name_at_time
            for mp in match.players:
                db.session.delete(mp)
        else:
            match = Match(
                id=match_id,
                user_id=user.id,
                name=name,
                date_iso=date_iso,
                match_seconds=match_seconds,
                team_id=team_id,
                team_name_at_time=team_name_at_time,
            )
            db.session.add(match)

        for i, entry in enumerate(players_data):
            if not isinstance(entry, dict):
                continue
            mp = MatchPlayer(
                match_id=match_id,
                ord=i,
                player_id=str(entry.get("playerId", "p" + str(i + 1))),
                player_name_at_time=str(
                    entry.get("playerNameAtTime", "Spelare " + str(i + 1))
                ),
                seconds_on_court=int(entry.get("secondsOnCourt", 0)),
                assists=int(entry.get("assists", 0)),
                fouls=int(entry.get("fouls", 0)),
                goals=int(entry.get("goals", 0)),
                shots=int(entry.get("shots", 0)),
                made_shots=int(entry.get("madeShots", 0)),
            )
            db.session.add(mp)
        db.session.commit()
        logger.info("Saved match id=%s for user_id=%s", match_id, user.id)
    except Exception:
        logger.exception("Failed to save match id=%s for user_id=%s", match_id, user.id)
        db.session.rollback()
        return {"error": "Could not save match"}, 500

    return _match_to_response(match), 201


@bp.route("/<match_id>", methods=["GET"])
@login_required
def get_match(match_id):
    user = get_current_user()
    try:
        match = Match.query.filter_by(id=match_id, user_id=user.id).first()
    except Exception:
        logger.exception("Failed to load match id=%s for user_id=%s", match_id, user.id)
        return {"error": "Could not load match"}, 500
    if not match:
        return {"error": "Match not found"}, 404
    return _match_to_response(match)


@bp.route("/<match_id>", methods=["DELETE"])
@login_required
def delete_match(match_id):
    user = get_current_user()
    try:
        match = Match.query.filter_by(id=match_id, user_id=user.id).first()
        if not match:
            return {"error": "Match not found"}, 404
        db.session.delete(match)
        db.session.commit()
        logger.info("Deleted match id=%s for user_id=%s", match_id, user.id)
    except Exception:
        logger.exception(
            "Failed to delete match id=%s for user_id=%s", match_id, user.id
        )
        db.session.rollback()
        return {"error": "Could not delete match"}, 500
    return "", 204


@bp.route("/clear", methods=["POST"])
@login_required
def clear_all():
    user = get_current_user()
    try:
        # Undvik bulk-delete: den kan hoppa över ORM-cascades och lämna orphans
        # (särskilt i SQLite där foreign key constraints kan vara avstängda).
        matches = Match.query.filter_by(user_id=user.id).all()
        deleted = len(matches)
        for m in matches:
            db.session.delete(m)
        db.session.commit()
        logger.info("Cleared %s matches for user_id=%s", deleted, user.id)
    except Exception:
        logger.exception("Failed to clear matches for user_id=%s", user.id)
        db.session.rollback()
        return {"error": "Could not clear matches"}, 500
    return "", 204

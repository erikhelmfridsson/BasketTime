import json
import logging
import sys
from datetime import datetime

from backend.models import ProfixioMatch, ProfixioPlayer, ProfixioTeam, ProfixioTournament, db
from backend.profixio_client import ProfixioError, fetch_all_tournament_matches, fetch_all_tournament_teams

logger = logging.getLogger("baskettime.profixio.sync")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s in %(name)s: %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


def _now():
    return datetime.utcnow()


def sync_tournament(tournament_id, organisation_id=None):
    """
    Hämtar och cachar lag/spelare/matcher för en turnering.
    Returnerar dict med räknare och flaggor.
    """
    tournament_id_int = int(tournament_id)
    now = _now()

    teams = []
    used_player_list = False
    try:
        teams = fetch_all_tournament_teams(tournament_id_int, player_list=True)
        used_player_list = True
    except ProfixioError:
        teams = fetch_all_tournament_teams(tournament_id_int, player_list=False)

    matches = fetch_all_tournament_matches(tournament_id_int)

    if organisation_id:
        existing_tour = db.session.get(ProfixioTournament, tournament_id_int)
        if existing_tour:
            existing_tour.organisation_id = organisation_id
            existing_tour.updated_at = now

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
            db.session.add(
                ProfixioTeam(
                    id=team_id,
                    tournament_id=tournament_id_int,
                    name=team_name,
                    club_name=club_name,
                    raw_json=raw_team,
                    updated_at=now,
                )
            )

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
                    db.session.add(
                        ProfixioPlayer(
                            id=pid_int,
                            tournament_id=tournament_id_int,
                            team_id=team_id,
                            name=pname,
                            jersey_number=str(jersey) if jersey is not None else None,
                            birth_date=str(birth) if birth is not None else None,
                            raw_json=raw_player,
                            updated_at=now,
                        )
                    )
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
            db.session.add(
                ProfixioMatch(
                    id=mid_int,
                    tournament_id=tournament_id_int,
                    start_time=str(start_time) if start_time else None,
                    home_team_id=home_team_id,
                    away_team_id=away_team_id,
                    raw_json=raw_match,
                    updated_at=now,
                )
            )
        matches_count += 1

    return {
        "ok": True,
        "tournamentId": tournament_id_int,
        "teams": len(teams),
        "matches": matches_count,
        "players": players_count,
        "usedPlayerList": used_player_list,
    }


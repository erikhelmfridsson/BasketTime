"""
Publika API-endpoints utan inloggning (read-only).
Används av landningssidor, t.ex. översikt över alla sparade matcher.
"""
import logging
import sys

from flask import Blueprint, request

from backend.models import Match

bp = Blueprint("public", __name__, url_prefix="/api/public")


@bp.after_request
def _public_cors(response):
    """Tillåt landningssidor på annan domän (t.ex. statisk baskettime.se) att läsa API."""
    if request.method == "GET":
        response.headers["Access-Control-Allow-Origin"] = "*"
    return response

logger = logging.getLogger("baskettime.public")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s in %(name)s: %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Max antal matcher per svar (skydd mot mycket stora svar)
PUBLIC_MATCHES_LIMIT = 500


@bp.route("/matches", methods=["GET"])
def list_matches_public():
    """Alla sparade matcher med spelardata (alla användare). Endast läsning."""
    try:
        matches = (
            Match.query.order_by(Match.created_at.desc()).limit(PUBLIC_MATCHES_LIMIT).all()
        )
        logger.info("Public matches list: %s rows", len(matches))
    except Exception:
        logger.exception("Public matches list failed")
        return {"error": "Could not load matches"}, 500
    return {"matches": [m.to_dict() for m in matches]}

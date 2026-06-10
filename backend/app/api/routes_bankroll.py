from __future__ import annotations
from fastapi import APIRouter, HTTPException, status
from app.api.deps import DbDep
from app.schemas.bankroll import BetIn, SettleIn
from app.services.bankroll import (
    place_bet, settle_bet, delete_bet, get_bankroll_state
)

router = APIRouter()


def _bet_to_dict(bet) -> dict:
    return {
        "id": bet.id,
        "key": bet.key,
        "pick": bet.pick,
        "team": bet.team,
        "market": bet.market,
        "stake": bet.stake,
        "dec": bet.dec,
        "status": bet.status,
        "pnl": bet.pnl,
        "placed_at": bet.placed_at.isoformat() if bet.placed_at else None,
    }


@router.get("/bankroll")
def get_bankroll(db: DbDep):
    state = get_bankroll_state(db)
    return {
        "balance": state["balance"],
        "start": state["start"],
        "open_bets": [_bet_to_dict(b) for b in state["open_bets"]],
        "settled_bets": [_bet_to_dict(b) for b in state["settled_bets"]],
    }


@router.post("/bankroll/bets", status_code=status.HTTP_201_CREATED)
def create_bet(body: BetIn, db: DbDep):
    bet = place_bet(
        db,
        key=body.key,
        pick=body.pick,
        team=body.team,
        market=body.market,
        stake=body.stake,
        dec=body.dec,
    )
    return _bet_to_dict(bet)


@router.delete("/bankroll/bets/{bet_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_bet(bet_id: int, db: DbDep):
    try:
        delete_bet(db, bet_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/bankroll/bets/{bet_id}/settle")
def settle(bet_id: int, body: SettleIn, db: DbDep):
    if body.result not in ("won", "lost", "void"):
        raise HTTPException(status_code=422, detail="result must be won|lost|void")
    try:
        bet = settle_bet(db, bet_id, body.result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _bet_to_dict(bet)

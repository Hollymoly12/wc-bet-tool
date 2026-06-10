"""Bankroll and bet ledger service."""
from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.models import Bet, BankrollTxn

START_BALANCE = 100.0


def place_bet(db: Session, key: str, pick: str, team: str, market: str,
              stake: float, dec: float) -> Bet:
    """Create an open bet and record the stake transaction."""
    now = datetime.now(timezone.utc)
    bet = Bet(
        key=key,
        pick=pick,
        team=team,
        market=market,
        stake=stake,
        dec=dec,
        status="open",
        pnl=0.0,
        placed_at=now,
    )
    db.add(bet)
    db.flush()
    txn = BankrollTxn(kind="bet", amount=-stake, bet_id=bet.id, created_at=now)
    db.add(txn)
    db.commit()
    db.refresh(bet)
    return bet


def settle_bet(db: Session, bet_id: int, result: str) -> Bet:
    """Settle a bet with result won|lost|void. Records a BankrollTxn."""
    bet = db.get(Bet, bet_id)
    if bet is None:
        raise ValueError(f"Bet {bet_id} not found")
    if bet.status != "open":
        raise ValueError(f"Bet {bet_id} is not open (status={bet.status})")

    now = datetime.now(timezone.utc)
    if result == "won":
        pnl = bet.stake * (bet.dec - 1)
        bet.status = "won"
    elif result == "lost":
        pnl = -bet.stake
        bet.status = "lost"
    elif result == "void":
        pnl = 0.0
        bet.status = "void"
    else:
        raise ValueError(f"Invalid result: {result}")

    bet.pnl = round(pnl, 2)
    txn = BankrollTxn(kind="settle", amount=pnl, bet_id=bet.id, created_at=now)
    db.add(txn)
    db.commit()
    db.refresh(bet)
    return bet


def delete_bet(db: Session, bet_id: int) -> None:
    """Delete an open bet (no settle). Also remove stake txn."""
    bet = db.get(Bet, bet_id)
    if bet is None:
        raise ValueError(f"Bet {bet_id} not found")
    if bet.status != "open":
        raise ValueError(f"Bet {bet_id} is not open")
    # Remove related transactions
    db.query(BankrollTxn).filter(BankrollTxn.bet_id == bet_id).delete()
    db.delete(bet)
    db.commit()


def get_balance(db: Session) -> float:
    """Compute current balance = START + sum of settled pnl."""
    settled = db.query(Bet).filter(Bet.status != "open").all()
    pnl_sum = sum(b.pnl for b in settled)
    return round(START_BALANCE + pnl_sum, 2)


def get_bankroll_state(db: Session) -> dict:
    """Return full bankroll state dict."""
    all_bets = db.query(Bet).order_by(Bet.placed_at.desc()).all()
    open_bets = [b for b in all_bets if b.status == "open"]
    settled_bets = [b for b in all_bets if b.status != "open"]
    balance = get_balance(db)
    return {
        "balance": balance,
        "start": START_BALANCE,
        "currency": "€",
        "open_bets": open_bets,
        "settled_bets": settled_bets,
    }

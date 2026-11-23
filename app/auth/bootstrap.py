"""Set a local password for an existing account from a trusted terminal."""

from argparse import ArgumentParser
from getpass import getpass

from sqlalchemy import delete, select

from app.auth.passwords import hasher
from app.database import SessionLocal
from app.models import RefreshSession, User


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("email", help="Email of an existing account")
    parser.add_argument("--admin", action="store_true", help="Grant administrator access")
    args = parser.parse_args()

    password = getpass("Password: ")
    if not 8 <= len(password) <= 256 or password != getpass("Repeat password: "):
        parser.error("Use 8–256 characters and enter the same password twice")

    with SessionLocal.begin() as db:
        user = db.scalar(select(User).where(User.email == args.email).with_for_update())
        if user is None:
            parser.error("Account was not found")
        user.password_hash = hasher.hash(password)
        if args.admin:
            user.is_admin = True

        # Revoke previously issued credentials when setting a new password.
        db.execute(delete(RefreshSession).where(RefreshSession.user_id == user.id))

    print("Local credentials updated")


if __name__ == "__main__":
    main()

from flask_sqlalchemy import SQLAlchemy
from uuid import uuid4
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class User(db.Model):
    username: Mapped[str] = mapped_column(String, primary_key=True)
    password: Mapped[str] = mapped_column(String, nullable=False)

class UserAuth(db.Model):
    username: Mapped[str] = mapped_column(String,
                                          ForeignKey("user.username"),
                                          primary_key=True,
                                         )
    token: Mapped[str] = mapped_column(String,
                                       nullable=False,
                                       unique=True,
                                       server_default=str(uuid4()),
                                      )

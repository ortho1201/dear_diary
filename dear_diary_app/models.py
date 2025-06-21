from datetime import datetime
from passlib.hash import bcrypt
from flask_login import UserMixin
from dear_diary_app import db, login_manager

friend_table = db.Table(
    "friends",
    db.Column("user_id",  db.Integer, db.ForeignKey("user.id")),
    db.Column("friend_id", db.Integer, db.ForeignKey("user.id"))
)

class User(UserMixin, db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    friends = db.relationship(
        "User",
        secondary=friend_table,
        primaryjoin=id==friend_table.c.user_id,
        secondaryjoin=id==friend_table.c.friend_id,
        backref="friend_of"
    )

    def set_pw(self, raw):  self.password = bcrypt.hash(raw)
    def check_pw(self, raw): return bcrypt.verify(raw, self.password)

class Diary(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    body      = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_public = db.Column(db.Boolean, default=False)
    user_id   = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

@login_manager.user_loader
def load_user(uid): return User.query.get(int(uid))

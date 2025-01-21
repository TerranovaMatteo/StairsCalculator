from models.conn import db
#from app import db -> commented due to circular input

class APIKey(db.Model):
    __tablename__ = 'api_keys'

    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(100), nullable=False)
    api_key = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return f"<APIKey(user='{self.user}', api_key='{self.api_key}')>"

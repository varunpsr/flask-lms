import base64
from datetime import datetime, timedelta, date
import json
import os
from flask import current_app, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    first_name = db.Column(db.String(200), nullable=True)
    last_name = db.Column(db.String(200), nullable=True)
    email = db.Column(db.String(250), index=True, unique=True)
    password = db.Column(db.String(128))
    token = db.Column(db.String(32), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)
    books = db.relationship('BookIssueHistory', backref='books_issued', lazy='dynamic')

    def __repr__(self):
        return '<User, {}>'.format(self.username)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'username': self.username,
            'borrow_cost': self.borrow_costs(),
            '_links': {
                'self': url_for('api.get_user', id=self.id),
            }
        }
        if include_email:
            data['email'] = self.email
        return data

    def from_dict(self, data, new_user=False):
        for field in ['username', 'email', 'about_me']:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])

    def get_token(self, expires_in=3600):
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        db.session.commit()
        return self.token

    def revoke_token(self):
        self.token_expiration = datetime.utcnow() - timedelta(seconds=1)

    def borrow_costs(self):
        sum = 0
        for book in self.books:
            if book.return_date is None:
                sum += book.borrow_cost()
        return sum

    @staticmethod
    def check_token(token):
        user = User.query.filter_by(token=token).first()
        if user is None or user.token_expiration < datetime.utcnow():
            return None
        return user



class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), index=True)
    books = db.relationship('Book', backref='books', lazy='dynamic')

    def __repr__(self):
        return '<Author {}>'.format(self.name)

    def to_dict(self):
        data = {
            'id': self.id,
            'name': self.name,
            '_links': {
                'self': url_for('api.get_author', id=self.id),
            }
        }
        return data

    def from_dict(self, data):
        for field in ['name']:
            if field in data:
                setattr(self, field, data[field])


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), index=True)
    isbn = db.Column(db.String(13), index=True, unique=True)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'))

    def __repr__(self):
        return '<Book {}>'.format(self.name)

    def to_dict(self):
        data = {
            'id': self.id,
            'name': self.name,
            'isbn': self.isbn,
            'author_id': self.author_id,
            '_links': {
                'self': url_for('api.get_book', id=self.id),
                'author': url_for('api.get_author', id=self.author_id),
            }
        }
        return data

    def from_dict(self, data):
        for field in ['name', 'isbn', 'author_id']:
            if field in data:
                setattr(self, field, data[field])


class BookIssueHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    issue_date = db.Column(db.Date, index=True, nullable=False)
    return_date = db.Column(db.Date, index=True, nullable=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    issuer_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<IssueRecord: {}>'.format(self.id)

    def to_dict(self):
        data = {
            'id': self.id,
            'issue_date': self.issue_date,
            'return_date': self.return_date,
            'book_id': self.book_id,
            'issuer_id': self.issuer_id,
            'borrow_cost': self.borrow_cost(),
            '_links': {
                'self': url_for('api.get_book', id=self.id),
            }
        }
        return data

    def from_dict(self, data):
        for field in ['issue_date', 'return_date', 'book_id', 'issuer_id']:
            if field in data:
                setattr(self, field, data[field])

    def borrow_cost(self):
        if self.return_date is None:
            return_date = datetime.today().date()
        else:
            return_date = self.return_date
        number_of_days = (self.issue_date - return_date).days
        cost_per_day = 1
        return number_of_days * cost_per_day
from flask import jsonify, request, url_for, g, abort
from datetime import date, datetime
from app import db
from app.models import Book, BookIssueHistory, User, Author
from app.main.auth import token_auth
from app.main.errors import bad_request
from app.main import bp


@bp.route('/author/<int:id>', methods=['GET'])
@token_auth.login_required
def get_author(id):
    return jsonify(Author.query.get_or_404(id).to_dict())


@bp.route('/author', methods=['POST'])
def create_author():
    data = request.get_json() or {}
    if 'name' not in data:
        return bad_request('must include name')
    if Author.query.filter_by(name=data['name']).first():
        return bad_request('please use a different name')
    author = Author()
    author.from_dict(data)
    db.session.add(author)
    db.session.commit()
    response = jsonify(author.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_author', id=author.id)
    return response

@bp.route('/book/<int:id>', methods=['GET'])
@token_auth.login_required
def get_book(id):
    return jsonify(Book.query.get_or_404(id).to_dict())


@bp.route('/book', methods=['POST'])
def create_book():
    data = request.get_json() or {}
    if 'name' not in data or 'isbn' not in data or 'author_id' not in data:
        return bad_request('must include name')
    if Book.query.filter_by(name=data['name']).first():
        return bad_request('please use a different name')
    if Book.query.filter_by(isbn=data['isbn']).first():
        return bad_request('Two books can not have the same ISBN.')
    book = Book()
    book.from_dict(data)
    db.session.add(book)
    db.session.commit()
    response = jsonify(book.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_book', id=book.id)
    return response

@bp.route('/borrow/<int:id>', methods=['GET'])
@token_auth.login_required
def get_borrow_details(id):
    return jsonify(BookIssueHistory.query.get_or_404(id).to_dict())

@bp.route('/book/<int:book_id>/borrow/<int:user_id>', methods=['GET'])
@token_auth.login_required
def borrow_book(book_id, user_id):
    if g.current_user.id != user_id:
        abort(403)
    user = User.query.get_or_404(g.current_user.id)
    book = Book.query.get_or_404(book_id)
    issued_book = BookIssueHistory()
    issued_book.book_id = book.id
    issued_book.issuer_id = user.id
    issued_book.issue_date = datetime.today().date()
    db.session.add(issued_book)
    db.session.commit()
    response = jsonify(issued_book.to_dict())
    response.status_code = 201
    return response
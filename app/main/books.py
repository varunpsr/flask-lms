from flask import jsonify, request, url_for, g, abort
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
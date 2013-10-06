# -*- coding: utf-8 -*-
import sys
import datetime

# Flask
from flask import Flask, request, jsonify, make_response, abort

# SQL Alchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# commute4good
import config
from model import commute4good

# Flask Application
api = Flask(__name__)


@api.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error': 'Invalid data'}), 400)


@api.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


# Bind engine - postgresql
engine = create_engine("postgresql://%s:%s@%s:%s/%s" % (config.postgres.username,
                                                        config.postgres.password,
                                                        config.postgres.hostname,
                                                        config.postgres.port,
                                                        config.postgres.database
                                                        )
                       )

# Start session
Session = sessionmaker(bind=engine)
pg_session = Session()


@api.route('/geolocation', methods=['POST'])
def new_position():
    if not request.json or not 'user_id' in request.json or not 'lon' in request.json or not 'lat' in request.json:
        abort(400)

    # Check User
    user = pg_session.query(commute4good.User).filter_by(id=request.json['user_id']).first()
    if user is None:
        return jsonify({"error": "Not found"}), 403

    # Update user position
    user.lon = request.json['lon']
    user.lat = request.json['lat']
    user.last_accessed_at = datetime.datetime.now()
    pg_session.add(user)
    pg_session.commit()

    # Create log
    geolocation = commute4good.Geolocation()
    geolocation.user_id = user.id
    geolocation.lon = request.json['lon']
    geolocation.lat = request.json['lat']
    geolocation.created_at = datetime.datetime.now()
    pg_session.add(geolocation)
    pg_session.commit()

    # Prepare response data
    data = {
        "id": geolocation.id,
        "user_id": geolocation.user_id,
        "lon": geolocation.lon,
        "lat": geolocation.lat,
        "created_at": geolocation.created_at
    }

    # Send data jsonified as response
    return jsonify(data), 200


@api.route('/users/<int:profil_id>', methods=['GET'])
def user_profil(profil_id):

    # Check User
    user = pg_session.query(commute4good.User).filter_by(id=profil_id).first()
    if user is None:
        return jsonify({"error": "Not found"}), 404

    # Prepare response data
    data = {
        "id": user.id,
        "firstname": user.firstname,
        "lastname": user.lastname,
        "pseudo": user.pseudo,
        "email": user.email,
        "photo_path": user.photo_path,
        "created_at": user.created_at,
        "last_accessed_at": user.last_accessed_at,
        "lon": user.lon,
        "lat": user.lat,
        "connected": user.connected
    }

    # Badges
    user_badges = pg_session.query(commute4good.UsersBadge).filter_by(user_id=profil_id)
    badges = []
    for user_badge in user_badges:
        badge = pg_session.query(commute4good.Badge).filter_by(id=user_badge.badge_id).first()

        if badge is not None:
            item = {
                "id": badge.id,
                "name": badge.name,
                "description": badge.description,
                "icon_path": badge.icon_path,
                "created_at": badge.icon_path,
                "last_earned_at": badge.last_earned_at,
                "popularity": badge.popularity,
                "min_interactions": badge.min_interactions,
            }
            badges.append(item)

    data["badges"] = badges

    # Tags
    user_tags = pg_session.query(commute4good.UsersTag).filter_by(user_id=profil_id)
    tags = []
    for user_tag in user_tags:
        tag = pg_session.query(commute4good.Tag).filter_by(id=user_tag.tag_id).first()

        if tag is not None:
            item = {
                "id": tag.id,
                "name": tag.name,
                "description": tag.description,
                "popularity": tag.popularity
            }
            tags.append(item)

    data["tags"] = tags

    # Send data jsonified as response
    return jsonify(data)


@api.route('/tags', methods=['POST'])
def new_tag():
    if not request.json or not 'user_id' in request.json or not 'name' in request.json:
        abort(400)

    tag = pg_session.query(commute4good.Tag).filter(commute4good.Tag.name.like("%" + request.json['name'] + "%")).first()

    if tag is None:
        # Create a new Tag
        _tag = commute4good.Tag()
        _tag.name = request.json['name']
        pg_session.add(_tag)
        pg_session.commit()
        tag = _tag

    # TODO: Check existence before save
    # Create jointure
    user_tag = commute4good.UsersTag()
    user_tag.user_id = request.json['user_id']
    user_tag.tag_id = tag.id
    user_tag.added_at = datetime.datetime.now()
    pg_session.add(user_tag)
    pg_session.commit()

    # Prepare response data
    data = {
        "id": user_tag.id,
        "user_id": user_tag.user_id,
        "tag_id": user_tag.tag_id,
        "name": tag.name,
        "description": tag.description,
        "popularity": tag.popularity,
        "added_at": user_tag.added_at
    }

    # Send data jsonified as response
    return jsonify(data), 200


@api.route('/users', methods=['PUT'])
def update_user():

    if not request.json or not 'user_id' in request.json:
        abort(400)

    user = pg_session.query(commute4good.User).filter_by(id=request.json['user_id']).first()

    if user is None:
        return jsonify({"error": "Not found"}), 403

    # TODO: Check user authorization -> 403 on failure

    # Update fields
    try:
        if request.json['firstname'] != "":
            user.firstname = request.json['firstname']
    except Exception:
        pass

    try:
        if request.json['lastname'] != "":
            user.firstname = request.json['lastname']
    except Exception:
        pass

    try:
        if request.json['pseudo'] != "":
            user.firstname = request.json['pseudo']
    except Exception:
        pass

    try:
        if request.json['email'] != "":
            user.firstname = request.json['email']
    except Exception:
        pass

    try:
        if request.json['md5_hash'] != "":
            user.firstname = request.json['md5_hash']
    except Exception:
        pass

    try:
        if request.json['photo_path'] != "":
            user.firstname = request.json['photo_path']
    except Exception:
        pass

    pg_session.add(user)
    pg_session.commit()

    # Prepare response data
    data = {
        "id": user.id,
        "firstname": user.firstname,
        "lastname": user.lastname,
        "pseudo": user.pseudo,
        "email": user.email,
        "photo_path": user.photo_path,
        "created_at": user.created_at,
        "last_accessed_at": user.last_accessed_at,
        "lon": user.lon,
        "lat": user.lat,
        "connected": user.connected
    }

    # Send data jsonified as response
    return jsonify(data)


@api.route('/users/login', methods=['POST'])
def create_token():
    # Check User identification
    if not request.json or not 'pseudo' in request.json or not 'md5_hash' in request.json:
        abort(400)

    # Search user
    user = pg_session.query(commute4good.User).filter_by(pseudo=request.json['pseudo'],
                                                         md5_hash=request.json['md5_hash']).first()

    # User not found
    if user is None:
        return jsonify({"error": "Not found"}), 403

    # Update last connection log
    user.last_accessed_at = datetime.datetime.now()
    pg_session.add(user)
    pg_session.commit()

    # Prepare response data
    data = {
        "id": user.id,
        "firstname": user.firstname,
        "lastname": user.lastname,
        "pseudo": user.pseudo,
        "email": user.email,
        "photo_path": user.photo_path,
        "created_at": user.created_at,
        "last_accessed_at": user.last_accessed_at,
        "lon": user.lon,
        "lat": user.lat,
        "connected": user.connected
    }

    # Send data jsonified as response
    return jsonify(data)

# Run as an executable
if __name__ == '__main__':
    api.run(debug=True)

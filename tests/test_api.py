import json
from app import create_app
from extensions import db
from models import User


def setup_app():
    app = create_app()
    app.config['TESTING'] = True
    return app


def test_ho_cau_and_loai_ca_api(tmp_path):
    app = setup_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
        admin = User(username='admin', email='admin@example.com', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

        client = app.test_client()
        # login by setting session
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin.id)
            sess['_fresh'] = True

        # create pond
        rv = client.post('/api/ho_cau', json={'name': 'Pond A', 'address': 'Addr', 'price_per_hour': 100})
        assert rv.status_code == 201
        data = rv.get_json()
        pid = data['id']

        # get pond
        rv = client.get(f'/api/ho_cau/{pid}')
        assert rv.status_code == 200

        # update pond
        rv = client.put(f'/api/ho_cau/{pid}', json={'price_per_hour': 150})
        assert rv.status_code == 200

        # create fish
        rv = client.post('/api/loai_ca', json={'name': 'Fish A', 'price': 50})
        assert rv.status_code == 201
        fid = rv.get_json()['id']

        # list fishes
        rv = client.get('/api/loai_ca')
        assert rv.status_code == 200

        # delete fish
        rv = client.delete(f'/api/loai_ca/{fid}')
        assert rv.status_code == 200


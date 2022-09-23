from flask import Flask, jsonify, request


class LocalDevAuthorizerServer:

    def mock_server_builder(self):
        app = Flask(__name__)

        @app.route('/oauth/me')
        def authorizer_resp():
            if 'authorization' not in request.headers:
                return "", 403

            tk = request.headers['authorization']

            if 'Bearer' in tk:
                tk = tk.split(' ')[1]

            return jsonify({
                'access_token': tk,
                'expires_in': 0,
                'issued_at': 0,
                'refresh_token': None,
                'uid': "test",
                'username': "test",
                'points': 0,
                'admin': False
            })

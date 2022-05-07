"""
  Credits to https://github.com/sayyid5416
  Proxy to restrict bots that are not owned by you
"""
from typing import List
from os import environ as env
from requests import request as got
from flask import Flask, request as req, send_file
from flask.json import jsonify
from flask_cors import CORS

app: Flask = Flask(__name__)
CORS(app)
allowedBotIds = env.get('ALLOWED_BOT_IDS', '').split(',')
errors = {
  '401': {'ok': False, 'error_code': 401, 'description': 'Unauthorized'},
  '404': {'ok': False, 'error_code': 404, 'description': 'Not found'}
}

def sanitize(token: str) -> str:
  return token.replace('bot', '', 1)


def is_unauthorized(token: str):
  bot_id, token = unpack(sanitize(token).split(':'), 2)
  return bot_id not in allowedBotIds or token is None


def make_error(code: int):
  return jsonify(errors[str(code)]), code


def get_path_data(path: str):
  token, *__, filename = unpack(path.split('/'), 5)
  return filename, token


def unpack(source: List[str], target: int, default_value=None):
  num = len(source)
  if num < target:
    return [*source, *([default_value] * (target - len(source)))]
  if num > target:
    return source[0:target]
  return source


def request():
  """ Send all HTTP request to telegram-bot-api local server """
  rdata = req.get_data() # Capture data before cleaning
  content_type = 'application/json' # Fix Content-Type header when opening URL in browser

  if 'Content-Type' in req.headers:
    content_type = req.headers['Content-Type']

  return got(
    method=req.method,
    url=req.url.replace(req.host_url, 'http://127.0.0.1:8081/'),
    headers={'Content-Type': content_type, 'Connection': 'keep-alive'},
    params=req.args,
    data=rdata
  )


@app.route('/file/<path:u_path>', methods=['GET'])
def file(u_path: str):
  """ Handle local files """
  filename, token = get_path_data(u_path)

  if is_unauthorized(token):
    return make_error(401)

  # Check if file exists via HTTP request for more faster
  res = request()

  if res.status_code != 200:
    return make_error(404)

  return send_file(
    path_or_file=f'/{sanitize(u_path)}',
    mimetype=res.headers['content-type'],
    download_name=filename,
    as_attachment=True
  )


@app.route('/', defaults={'u_path': ''})
@app.route('/<path:u_path>', methods=['GET', 'POST'])
def api(u_path: str):
  """ Handle all API request """
  __, token = get_path_data(u_path)

  if is_unauthorized(token):
    return make_error(401)

  res = request()
  return jsonify(res.json()), res.status_code


if __name__ == '__main__':
  app.run(port=8282)
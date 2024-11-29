# TMDB-Microservice

# Deployment
<b> Guide: </b> [Digital Ocean Guide](https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu)

<b> TLDR: </b> on a linux server run:
- `python3 -m venv venv`
- `source venv/bin/activate`
- `cd tmdb`
- `pip install -r requirements.txt`
- `python ./manage.py makemigrations`
- `python ./manage.py migrate` * (if any migrations)

<b>Run server locally:</b>
- `python ./manage.py runserver <port>` <b>(do not use in production!)</b>

# Start/stop server
- <b> Start: </b> `sudo systemctl start gunicorn_tmdb.socket`
- <b> Stop: </b> `sudo systemctl stop gunicorn_tmdb.socket`

# Other commands
- `sudo systemctl daemon-reload`
- `sudo systemctl restart gunicorn_tmdb.socket gunicorn_tmdb.service`
- `sudo nginx -t && sudo systemctl restart nginx`
- `sudo systemctl status gunicorn_tmdb`
- `sudo journalctl -u gunicorn_tmdb`
- `sudo journalctl -u gunicorn_tmdb.socket`
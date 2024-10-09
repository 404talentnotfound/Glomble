sudo kill -9 `pgrep uwsgi`
sudo uwsgi uwsgi.ini --daemonize /etc/nginx/uwsgi.log

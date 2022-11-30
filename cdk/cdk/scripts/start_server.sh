cd /home/ec2-user
pwd
ls
source image_uri.sh
docker-compose pull
docker-compose up -d db
sleep 5
docker-compose up --pull --force-recreate --no-deps -d app

## Tbd
sudo docker run \
--name="confluence" -d \
-p 8090:8090 \
-p 8091:8091 \
-v ~/confluence-home/confluence-docker:/var/atlassian/application-data/confluence \
-e TZ=Australia/Brisbane \
atlassian/confluence-server \


sudo docker run \
--rm -it \
--name searchtest \
-e TZ=Europe/Prague \
-v "$(pwd)":"$(pwd)" \
jankorinek/search_pdf:1.0.0 \
--folder="$(pwd)" \
--keyword='cluster'

sudo docker compose up --build
docker pull jankorinek/search_pdf
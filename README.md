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
--name search_in_pdfs \
-e TZ=Europe/Prague \
-v "$(pwd)":"$(pwd)" \
jankorinek/search_pdf:latest \
--folder="$(pwd)" \
--keyword='cluster'

sudo docker compose up --build
docker pull jankorinek/search_pdf:latest
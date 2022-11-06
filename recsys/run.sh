cd botify
docker compose stop
docker compose up -d --build
cd ../sim
sleep 180
export PYTHONPATH=${PWD}
python sim/run.py --episodes 5000 --recommender remote --config config/env.yml --seed 42
cd ../script
export PYTHONPATH=${PWD}
python dataclient.py --user mob202299 log2hdfs --cleanup updated_recommender
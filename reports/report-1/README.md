## Data

1. docker

```bash
docker run -d -p 27017:27017 --name mongo mongo
```

2. import data
```bash
mongorestore --gzip --archive=mongodump-JiraRepos_2023-03-07-16\ 00.archive --nsFrom="JiraRepos.*" --nsTo="JiraRepos.*"
mongorestore --gzip --archive=mongodump-MiningDesignDecisions-lite.archive --nsFrom="MiningDesignDecisions.*" --nsTo="MiningDesignDecisions.*"
```

3. Preprocessing
```bash
python data/preprocessing/preprocessing.py
```

4. Pandera validation
```bash
python data/preprocessing/pandera_check.py
```
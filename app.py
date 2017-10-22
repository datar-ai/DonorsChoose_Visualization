from flask import Flask, Response
from flask import render_template
from pymongo import MongoClient
import json
from bson import json_util
from bson.json_util import dumps
from neo4j.v1 import GraphDatabase, basic_auth
import requests


app = Flask(__name__)

MONGODB_HOST = 'localhost'
MONGODB_PORT = 27017
DBS_NAME = 'donorschoose'
COLLECTION_NAME = 'projects'
FIELDS = {'school_state': True, 'resource_type': True, 'poverty_level': True, 'date_posted': True, 'total_donations': True, '_id': False}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/donorschoose/projects")
def donorschoose_projects():
    connection = MongoClient(MONGODB_HOST, MONGODB_PORT)
    collection = connection[DBS_NAME][COLLECTION_NAME]
    # projects = collection.find(projection=FIELDS, limit=100000)
    # projects = collection.find(projection=FIELDS, limit=5000)
    # projects = collection.find(projection=FIELDS, limit=1)
    projects = collection.find({}, FIELDS)
    json_projects = []
    for project in projects:
        json_projects.append(project)
    json_projects = json.dumps(json_projects, default=json_util.default)
    connection.close()
    return json_projects


@app.route("/neo4j")
def neo4j():
    return render_template("index3.html")


def build_dict(seq, key):
    return dict((d[key], dict(d, index=index)) for (index, d) in enumerate(seq))


@app.route("/neo4j/graphdata")
def graphdata():
    # Neo4j connect
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=basic_auth("neo4j", "games123"))
    # Open Neo4j session
    try:
        db = driver.session()
        results = db.run('MATCH (n)-[r:NER_IN]->(News:News) WHERE News.title CONTAINS {query} AND r.score > 0.6 RETURN News, collect(n) as n '
                         'UNION MATCH (n)-[r:NER_IN]->(News:News) WHERE News.text CONTAINS {query} AND r.score > 0.6 RETURN News,collect(n) as n',
                         {"query": "工業4.0"})
    except Exception as e:
        print('*** ', e)

    nodes = []
    rels = []
    i = 0
    for record in results:
        nodes.append({"id": i, "oid": record["News"].id, "type": "News", "labels": record["News"].properties["title"],
                      "properties": record["News"]})
        target = i
        i += 1
        for name in record['n']:
            topic = {"id": i, "oid": name.id, "type": next(iter(name.labels)), "labels": name.properties["name"],
                     "properties": name}
            info_by_oid = build_dict(nodes, key="oid")
            try:
                source = info_by_oid[topic["oid"]]
            except KeyError:
                nodes.append(topic)
                source = i
                i += 1
            else:
                source = source["id"]
            rels.append({"source": source, "target": target})
    return Response(dumps({"nodes": nodes, "links": rels}),
                    mimetype="application/json")


"""
            try:
                source = nodes.index(topic["oid"])
            except ValueError:
                nodes.append(topic)
                # source = name.id
                source = i
                i += 1
"""


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

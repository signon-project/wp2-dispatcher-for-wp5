# Copyright 2021-2023 FINCONS GROUP AG within the Horizon 2020
# European project SignON under grant agreement no. 101017255.

# Licensed under the Apache License, Version 2.0 (the "License"); 
# you may not use this file except in compliance with the License. 
# You may obtain a copy of the License at 

#     http://www.apache.org/licenses/LICENSE-2.0 

# Unless required by applicable law or agreed to in writing, software 
# distributed under the License is distributed on an "AS IS" BASIS, 
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. 
# See the License for the specific language governing permissions and 
# limitations under the License.


#!/usr/bin/env python
import getopt
import json
import os
import sys
from os import makedirs
from os import path
from time import time, sleep

import boto3
import botocore
import pika
import requests
import yaml

from ExceptionHandler.exceptionHandler import handleException

argv = sys.argv[1:]
configFile = 'config.yml'
opts, args = getopt.getopt(argv,"hc:",["config="])
for opt, arg in opts:
    if opt == '-h':
        print ('pipeline.py -c <config-file-path>')
        sys.exit()
    elif opt in ("-c", "--config"):
        configFile = arg
print('Config file:', configFile)

with open(configFile, 'rb') as f:
    conf = yaml.safe_load(f.read())
print('RabbitMQ host:', conf['rabbitmq']['host'])
print('RabbitMQ WP5 queue:', conf['rabbitmq']['wp5-queue'])

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=conf['rabbitmq']['host']))
channel = connection.channel()

def now():
    return round(time() * 1000)

def on_request(ch, method, props, body):
    my_json = body.decode('utf8')
    data = json.loads(my_json)

    data['MessageSynthesis'] = {}
    data['MessageSynthesis']['T4WP5'] = now()

    print("\n|WP5| - Message - |WP5|\n")

    correlationID = data['RabbitMQ']['correlationID']
    replyTo = data['RabbitMQ']['replyTo']

    data['SourceLanguageProcessing'] = json.dumps(data['SourceLanguageProcessing'])
    data['IntermediateRepresentation'] = json.dumps(data['IntermediateRepresentation'])
    data['MessageSynthesis'] = json.dumps(data['MessageSynthesis'])

    response_string = json.dumps(data)

    ch.basic_publish(exchange='',
                     routing_key=replyTo,
                     properties=pika.BasicProperties(correlation_id = correlationID),
                     body=response_string)
    print(" [x] Message Sent to Orchetsrator")

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='signon.wp5.queue', on_message_callback=on_request, auto_ack=True)
print(" [x] Awaiting WP4 requests")
channel.start_consuming()

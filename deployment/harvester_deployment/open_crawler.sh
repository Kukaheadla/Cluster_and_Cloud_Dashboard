#!/bin/bash

. ./openrc.sh

ansible-playbook -i hosts.ini -u ubuntu --key-file=~/.ssh/demo.pem crawler.yaml
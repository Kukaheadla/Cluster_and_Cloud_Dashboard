#!/bin/bash

. ./openrc.sh

ansible-playbook -i hosts -u ubuntu --key-file=~/.ssh/demo.pem crawler.yaml
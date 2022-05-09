. ./openrc.sh

ansible-playbook -i inventory.ini -u ubuntu --key-file=~/.ssh/project-key.pem swarm.yaml